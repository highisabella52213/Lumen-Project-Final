import http from "node:http";
import net from "node:net";
import tls from "node:tls";
import { fileURLToPath } from "node:url";
import { realpathSync } from "node:fs";

/*
 * Lumen public self-contained Railway service installer — v28.0.0
 * Every user deploys this folder as a service in their own Railway account.
 * Runs on Node.js 22 with node:net/node:tls.
 * It does not persist submitted tokens and never writes them to logs.
 */

const SOURCE_OWNER = "highisabella52213";
const SOURCE_REPO = "Lumen-Project-Final";
const SOURCE_FULL = SOURCE_OWNER + "/" + SOURCE_REPO;
const GITHUB_API = "https://api.github.com";
const RAILWAY_API = "https://backboard.railway.com/graphql/v2";
const INSTALLER_VERSION = "28.0.0";
const MAX_BODY_BYTES = 24 * 1024;
const MAX_UPSTREAM_BYTES = 4 * 1024 * 1024;
const HTTP_PROXIES = Object.freeze([
  Object.freeze({ hostname: "176.111.37.216", port: 39811 }),
  Object.freeze({ hostname: "107.167.18.122", port: 443 }),
  Object.freeze({ hostname: "130.110.103.245", port: 3128 }),
  Object.freeze({ hostname: "176.111.37.5", port: 39811 }),
  Object.freeze({ hostname: "94.249.197.220", port: 40001 }),
  Object.freeze({ hostname: "13.203.138.32", port: 3001 }),
]);
const PROXY_PROBE_TIMEOUT_MS = 8000;
const DIRECT_PROBE_TIMEOUT_MS = 10000;
const NETWORK_SELECTION_TIMEOUT_MS = 45000;
const ALLOWED_UPSTREAMS = new Set(["api.github.com", "backboard.railway.com"]);

class InstallError extends Error {
  constructor(code, step, messageEn, messageFa, status = 400) {
    super(messageEn);
    this.code = code;
    this.step = step;
    this.messageEn = messageEn;
    this.messageFa = messageFa;
    this.status = status;
  }
}

const SECURITY_HEADERS = {
  "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
  Pragma: "no-cache",
  Expires: "0",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
};

function randomSecret(bytes = 32) {
  const data = new Uint8Array(bytes);
  crypto.getRandomValues(data);
  let binary = "";
  for (const value of data) binary += String.fromCharCode(value);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function jsonResponse(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { ...SECURITY_HEADERS, "Content-Type": "application/json; charset=utf-8" },
  });
}

function htmlResponse() {
  const nonce = randomSecret(18);
  const csp = [
    "default-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    "script-src 'nonce-" + nonce + "'",
    "style-src 'nonce-" + nonce + "' https://fonts.googleapis.com",
    "connect-src 'self'",
    "img-src 'none'",
    "font-src https://fonts.gstatic.com",
    "object-src 'none'",
    "worker-src 'none'",
  ].join("; ");
  return new Response(INSTALLER_HTML.replaceAll("__NONCE__", nonce), {
    status: 200,
    headers: {
      ...SECURITY_HEADERS,
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": csp,
    },
  });
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function deploymentPollDelayMs() {
  const overridden = Number(globalThis.__LUMEN_TEST_DEPLOYMENT_POLL_MS__);
  return Number.isFinite(overridden) && overridden >= 0 ? overridden : 20_000;
}

function emitProgress(report, update) {
  try { report(Object.freeze({ ...update, updatedAt: new Date().toISOString() })); } catch (_) {}
}

function transportError(code, messageEn, messageFa, status = 502) {
  return new InstallError(code, "network", messageEn, messageFa, status);
}

function safeHeaderValue(value) {
  const text = String(value == null ? "" : value);
  if (/[\r\n\0]/.test(text)) throw transportError("INVALID_UPSTREAM_HEADER", "An internal upstream header was invalid.", "یکی از هدرهای داخلی مقصد نامعتبر بود.", 500);
  return text;
}

function decodeChunked(body) {
  const chunks = [];
  let offset = 0;
  let size = 0;
  while (offset < body.length) {
    const lineEnd = body.indexOf("\r\n", offset, "latin1");
    if (lineEnd < 0 || lineEnd - offset > 32) throw new Error("invalid chunk header");
    const line = body.subarray(offset, lineEnd).toString("ascii").split(";", 1)[0].trim();
    if (!/^[0-9a-fA-F]+$/.test(line)) throw new Error("invalid chunk size");
    const length = Number.parseInt(line, 16);
    offset = lineEnd + 2;
    if (length === 0) return Buffer.concat(chunks, size);
    if (!Number.isSafeInteger(length) || length < 0 || offset + length + 2 > body.length) throw new Error("truncated chunk");
    const chunk = body.subarray(offset, offset + length);
    chunks.push(chunk); size += chunk.length;
    if (size > MAX_UPSTREAM_BYTES) throw new Error("response too large");
    offset += length;
    if (body[offset] !== 13 || body[offset + 1] !== 10) throw new Error("invalid chunk ending");
    offset += 2;
  }
  throw new Error("missing final chunk");
}

function openProxyTunnel(targetHostname, timeoutMs, proxy) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let handshake = Buffer.alloc(0);
    let secure = null;
    const raw = net.createConnection({ host: proxy.hostname, port: proxy.port });
    const timeoutError = () => transportError("HTTP_PROXY_TIMEOUT", "The configured HTTP proxy timed out.", "زمان انتظار پروکسی HTTP تنظیم‌شده به پایان رسید.", 504);
    let watchdog = null;
    const fail = (error) => {
      if (settled) return;
      settled = true;
      if (watchdog) clearTimeout(watchdog);
      try { if (secure) secure.destroy(); } catch (_) {}
      try { raw.destroy(); } catch (_) {}
      reject(error instanceof InstallError ? error : transportError("HTTP_PROXY_UNAVAILABLE", "The configured HTTP proxy could not establish a secure connection.", "پروکسی HTTP تنظیم‌شده نتوانست اتصال امن را برقرار کند."));
    };
    // A socket timeout alone is insufficient during every TLS edge case. This
    // independent wall-clock watchdog guarantees that a dead proxy can never
    // leave deploymentNetworkState stuck on `checking` forever.
    watchdog = setTimeout(() => fail(timeoutError()), timeoutMs);
    raw.setNoDelay(true);
    raw.setTimeout(timeoutMs, () => fail(timeoutError()));
    raw.once("error", fail);
    raw.once("end", () => fail(transportError("HTTP_PROXY_CLOSED", "The configured HTTP proxy closed the tunnel early.", "پروکسی HTTP تونل را زودتر از موعد بست.")));
    raw.once("close", () => fail(transportError("HTTP_PROXY_CLOSED", "The configured HTTP proxy closed the tunnel early.", "پروکسی HTTP تونل را زودتر از موعد بست.")));
    raw.once("connect", () => {
      raw.write("CONNECT " + targetHostname + ":443 HTTP/1.1\r\nHost: " + targetHostname + ":443\r\nProxy-Connection: keep-alive\r\nUser-Agent: Lumen-Installer-Proxy/23\r\n\r\n");
    });
    const onData = (chunk) => {
      handshake = Buffer.concat([handshake, Buffer.from(chunk)]);
      if (handshake.length > 16 * 1024) return fail(transportError("HTTP_PROXY_RESPONSE", "The HTTP proxy returned an invalid response.", "پروکسی HTTP پاسخ نامعتبر برگرداند."));
      const boundary = handshake.indexOf("\r\n\r\n");
      if (boundary < 0) return;
      raw.off("data", onData);
      const head = handshake.subarray(0, boundary).toString("latin1");
      const status = Number((head.match(/^HTTP\/1\.[01]\s+(\d{3})/i) || [])[1] || 0);
      if (status !== 200) return fail(transportError("HTTP_PROXY_REJECTED", "The HTTP proxy rejected the tunnel request (HTTP " + status + ").", "پروکسی HTTP درخواست تونل را رد کرد (HTTP " + status + ")."));
      if (handshake.length !== boundary + 4) return fail(transportError("HTTP_PROXY_INJECTION", "The HTTP proxy returned unexpected bytes before TLS.", "پروکسی HTTP پیش از TLS داده غیرمنتظره فرستاد."));
      raw.setTimeout(0);
      raw.off("error", fail);
      secure = tls.connect({ socket: raw, servername: targetHostname, rejectUnauthorized: true, ALPNProtocols: ["http/1.1"] });
      secure.setTimeout(timeoutMs, () => fail(timeoutError()));
      secure.once("error", fail);
      secure.once("end", () => fail(transportError("UPSTREAM_TLS_CLOSED", "The secure proxy connection closed during setup.", "اتصال امن پروکسی هنگام راه‌اندازی بسته شد.")));
      secure.once("close", () => fail(transportError("UPSTREAM_TLS_CLOSED", "The secure proxy connection closed during setup.", "اتصال امن پروکسی هنگام راه‌اندازی بسته شد.")));
      secure.once("secureConnect", () => {
        if (settled) return;
        if (!secure.authorized || (secure.alpnProtocol && secure.alpnProtocol !== "http/1.1")) {
          return fail(transportError("UPSTREAM_TLS_FAILED", "The secure connection through the proxy could not be verified.", "اتصال امن از داخل پروکسی قابل تأیید نبود."));
        }
        settled = true;
        if (watchdog) clearTimeout(watchdog);
        secure.setTimeout(0);
        secure.off("error", fail);
        resolve(secure);
      });
    };
    raw.on("data", onData);
  });
}

function responseIsComplete(raw) {
  const boundary = raw.indexOf("\r\n\r\n");
  if (boundary < 0) return false;
  if (boundary > 64 * 1024) throw new Error("HTTP headers too large");
  const head = raw.subarray(0, boundary).toString("latin1");
  const lengthMatch = head.match(/\r\ncontent-length:\s*(\d+)/i);
  if (lengthMatch) return raw.length >= boundary + 4 + Number(lengthMatch[1]);
  if (/\r\ntransfer-encoding:[^\r\n]*chunked/i.test(head)) {
    try { decodeChunked(raw.subarray(boundary + 4)); return true; }
    catch (error) {
      if (["truncated chunk", "missing final chunk", "invalid chunk header"].includes(String(error && error.message))) return false;
      throw error;
    }
  }
  return false;
}

function collectHttpResponse(socket, timeoutMs) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true; clearTimeout(timer);
      const raw = Buffer.concat(chunks, total);
      try { socket.destroy(); } catch (_) {}
      resolve(raw);
    };
    const fail = (error) => {
      if (settled) return;
      settled = true; clearTimeout(timer);
      try { socket.destroy(); } catch (_) {}
      reject(error);
    };
    const timer = setTimeout(() => fail(transportError("UPSTREAM_TIMEOUT", "A remote service took too long to respond on the selected route.", "پاسخ سرویس مقصد در مسیر انتخاب‌شده بیش از حد طول کشید.", 504)), timeoutMs);
    socket.on("data", (chunk) => {
      const part = Buffer.from(chunk); total += part.length;
      if (total > MAX_UPSTREAM_BYTES + 64 * 1024) return fail(transportError("UPSTREAM_RESPONSE_TOO_LARGE", "A remote service returned too much data.", "حجم پاسخ سرویس مقصد بیش از حد مجاز بود."));
      chunks.push(part);
      try { if (responseIsComplete(Buffer.concat(chunks, total))) finish(); }
      catch (_) { fail(transportError("UPSTREAM_RESPONSE", "A remote service returned an unreadable response on the selected route.", "سرویس مقصد در مسیر انتخاب‌شده پاسخ قابل‌خواندن نداد.")); }
    });
    socket.once("error", () => fail(transportError("UPSTREAM_UNAVAILABLE", "A remote service could not be reached on the selected route.", "ارتباط با سرویس مقصد در مسیر انتخاب‌شده برقرار نشد.")));
    socket.once("timeout", () => fail(transportError("UPSTREAM_TIMEOUT", "A remote service took too long to respond on the selected route.", "پاسخ سرویس مقصد در مسیر انتخاب‌شده بیش از حد طول کشید.", 504)));
    socket.once("end", finish);
  });
}

async function proxyFetch(url, options = {}, timeoutMs = 18000, proxy) {
  if (!proxy || !/^(?:\d{1,3}\.){3}\d{1,3}$/.test(String(proxy.hostname)) || !Number.isInteger(proxy.port)) throw transportError("INVALID_PROXY", "An invalid proxy route was selected.", "مسیر پروکسی انتخاب‌شده نامعتبر است.", 500);
  const target = new URL(url);
  if (target.protocol !== "https:" || !ALLOWED_UPSTREAMS.has(target.hostname) || (target.port && target.port !== "443")) {
    throw transportError("UPSTREAM_NOT_ALLOWED", "The requested upstream is not allowed.", "سرویس مقصد درخواست‌شده مجاز نیست.", 500);
  }
  const method = String(options.method || "GET").toUpperCase();
  if (!/^(GET|POST|PUT|PATCH|DELETE)$/.test(method)) throw transportError("METHOD_NOT_ALLOWED", "The upstream request method is not allowed.", "روش درخواست مقصد مجاز نیست.", 500);
  const body = options.body == null ? Buffer.alloc(0) : Buffer.from(String(options.body), "utf8");
  if (body.length > MAX_BODY_BYTES) throw transportError("UPSTREAM_BODY_TOO_LARGE", "The upstream request is too large.", "حجم درخواست مقصد بیش از حد مجاز است.", 500);
  const headers = new Headers(options.headers || {});
  const lines = [];
  for (const [name, value] of headers.entries()) {
    const lower = name.toLowerCase();
    if (["host", "connection", "proxy-connection", "content-length", "transfer-encoding", "accept-encoding"].includes(lower)) continue;
    lines.push(name + ": " + safeHeaderValue(value));
  }
  lines.push("Host: " + target.hostname, "Connection: close", "Accept-Encoding: identity");
  if (body.length) lines.push("Content-Length: " + body.length);
  const requestHead = method + " " + (target.pathname || "/") + target.search + " HTTP/1.1\r\n" + lines.join("\r\n") + "\r\n\r\n";
  let socket;
  try {
    socket = await openProxyTunnel(target.hostname, timeoutMs, proxy);
    socket.write(Buffer.concat([Buffer.from(requestHead, "utf8"), body]));
    const raw = await collectHttpResponse(socket, timeoutMs);
    const boundary = raw.indexOf("\r\n\r\n");
    if (boundary < 0 || boundary > 64 * 1024) throw new Error("missing HTTP headers");
    const headerText = raw.subarray(0, boundary).toString("latin1");
    const statusMatch = headerText.match(/^HTTP\/1\.[01]\s+(\d{3})(?:\s+([^\r\n]*))?/i);
    if (!statusMatch) throw new Error("invalid HTTP status");
    const status = Number(statusMatch[1]);
    let responseBody = raw.subarray(boundary + 4);
    const responseHeaders = new Headers();
    let chunked = false;
    let contentLength = null;
    for (const line of headerText.split("\r\n").slice(1)) {
      const colon = line.indexOf(":"); if (colon < 1) continue;
      const name = line.slice(0, colon).trim(); const value = line.slice(colon + 1).trim(); const lower = name.toLowerCase();
      if (lower === "transfer-encoding" && value.toLowerCase().includes("chunked")) chunked = true;
      else if (lower === "content-length") contentLength = Number(value);
      else if (!["connection", "proxy-connection", "keep-alive", "upgrade", "content-encoding"].includes(lower)) responseHeaders.append(name, value);
    }
    if (chunked) responseBody = decodeChunked(responseBody);
    else if (Number.isFinite(contentLength) && contentLength >= 0) {
      if (responseBody.length < contentLength) throw new Error("truncated HTTP body");
      responseBody = responseBody.subarray(0, contentLength);
    }
    if (responseBody.length > MAX_UPSTREAM_BYTES) throw new Error("response too large");
    responseHeaders.set("Content-Length", String(responseBody.length));
    return new Response(status === 204 || status === 304 ? null : responseBody, { status, statusText: statusMatch[2] || "", headers: responseHeaders });
  } catch (error) {
    if (error instanceof InstallError) throw error;
    throw transportError("UPSTREAM_RESPONSE", "A remote service returned an unreadable response through the HTTP proxy.", "سرویس مقصد از داخل پروکسی پاسخ قابل‌خواندن نداد.");
  } finally {
    try { if (socket) socket.destroy(); } catch (_) {}
  }
}

function routeLabel(route) {
  return route.kind === "direct" ? "Direct (Railway)" : "http://" + route.proxy.hostname + ":" + route.proxy.port;
}

async function directFetch(url, options = {}, timeoutMs = 18000) {
  const target = new URL(url);
  if (target.protocol !== "https:" || !ALLOWED_UPSTREAMS.has(target.hostname) || (target.port && target.port !== "443")) {
    throw transportError("UPSTREAM_NOT_ALLOWED", "The requested upstream is not allowed.", "سرویس مقصد درخواست‌شده مجاز نیست.", 500);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal, redirect: "error" });
  } catch (error) {
    if (error && error.name === "AbortError") throw transportError("DIRECT_TIMEOUT", "The direct Railway route timed out.", "زمان انتظار مسیر مستقیم Railway به پایان رسید.", 504);
    throw transportError("DIRECT_UNAVAILABLE", "The direct Railway route could not reach the remote service.", "مسیر مستقیم Railway نتوانست به سرویس مقصد متصل شود.");
  } finally { clearTimeout(timer); }
}

async function routeFetch(route, url, options = {}, timeoutMs = 18000) {
  const testTransport = globalThis.__LUMEN_TEST_ROUTE_FETCH__;
  if (typeof testTransport === "function") return await testTransport(route, url, { ...options, redirect: "error" }, timeoutMs);
  return route.kind === "direct" ? directFetch(url, options, timeoutMs) : proxyFetch(url, options, timeoutMs, route.proxy);
}

async function probeRoute(route, index) {
  const started = Date.now();
  let githubOk = false;
  let railwayOk = false;
  let failureCode = "PROBE_FAILED";
  try {
    const githubResponse = await routeFetch(route, GITHUB_API + "/meta", {
      method: "GET", headers: { Accept: "application/vnd.github+json", "User-Agent": "Lumen-Network-Probe/26" },
    }, route.kind === "direct" ? DIRECT_PROBE_TIMEOUT_MS : PROXY_PROBE_TIMEOUT_MS);
    if (!githubResponse.ok) throw new Error("GitHub HTTP " + githubResponse.status);
    githubOk = true;
  } catch (error) {
    failureCode = error instanceof InstallError ? error.code : "GITHUB_PROBE_FAILED";
  }
  // Keep the two target checks sequential. Six proxy routes are tested in
  // parallel, staying within Railway's six simultaneous socket limit.
  try {
    const railwayResponse = await routeFetch(route, RAILWAY_API, {
      method: "POST", headers: { Accept: "application/json", "Content-Type": "application/json", "User-Agent": "Lumen-Network-Probe/26" },
      body: JSON.stringify({ query: "query LumenNetworkProbe { __typename }", variables: {} }),
    }, route.kind === "direct" ? DIRECT_PROBE_TIMEOUT_MS : PROXY_PROBE_TIMEOUT_MS);
    if (railwayResponse.status < 200 || railwayResponse.status >= 500) throw new Error("Railway HTTP " + railwayResponse.status);
    railwayOk = true;
  } catch (error) {
    if (githubOk) failureCode = error instanceof InstallError ? error.code : "RAILWAY_PROBE_FAILED";
  }
  return {
    ok: githubOk && railwayOk,
    githubOk,
    railwayOk,
    route,
    index,
    label: routeLabel(route),
    latencyMs: Math.max(1, Date.now() - started),
    code: githubOk && railwayOk ? undefined : failureCode,
  };
}

async function selectTransportInternal() {
  // Test all supplied proxies and direct Railway egress on every scan. Public
  // proxy success does not prove that Authorization headers will be accepted.
  const proxyRoutes = HTTP_PROXIES.map((proxy) => ({ kind: "proxy", proxy }));
  const proxyChecksPromise = Promise.all(proxyRoutes.map((route, index) => probeRoute(route, index)));
  const directCheckPromise = probeRoute({ kind: "direct" }, HTTP_PROXIES.length);
  const [proxyChecks, directCheck] = await Promise.all([proxyChecksPromise, directCheckPromise]);
  const checks = [...proxyChecks, directCheck];
  const healthy = proxyChecks.filter((item) => item.ok).sort((left, right) => left.latencyMs - right.latencyMs || left.index - right.index);

  // Direct is preferred for token-bearing control-plane operations. Verified
  // HTTP CONNECT proxies remain ordered fallbacks when direct egress is down.
  if (directCheck.ok) return { route: directCheck.route, selected: directCheck, checks };
  if (healthy.length) return { route: healthy[0].route, selected: healthy[0], checks };
  const error = new InstallError("ALL_NETWORK_ROUTES_FAILED", "network", "All configured proxies and the direct Railway route failed the GitHub/Railway checks.", "همه پروکسی‌های تنظیم‌شده و مسیر مستقیم Railway در بررسی GitHub و Railway ناموفق بودند.", 502);
  error.networkChecks = checks;
  throw error;
}

async function selectTransport() {
  const override = Number(globalThis.__LUMEN_TEST_SELECTION_TIMEOUT_MS__);
  const timeoutMs = Number.isFinite(override) && override > 0 ? override : NETWORK_SELECTION_TIMEOUT_MS;
  let timer;
  try {
    return await Promise.race([
      selectTransportInternal(),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new InstallError(
          "NETWORK_SCAN_TIMEOUT", "network",
          "Network route checks exceeded their hard deadline.",
          "بررسی مسیرهای شبکه از مهلت نهایی عبور کرد.", 504,
        )), timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function fetchWithTimeout(route, url, options, timeoutMs = 18000) {
  return routeFetch(route, url, options, timeoutMs);
}

function routeFailureSummary(route, error) {
  return {
    label: routeLabel(route),
    code: error instanceof InstallError ? error.code : "ROUTE_AUTH_FAILED",
    step: error instanceof InstallError ? error.step : "network",
  };
}

async function selectAuthenticatedTransport(network, githubToken, _railwayToken) {
  const directCandidate = network.checks.find((item) => item.ok && item.route && item.route.kind === "direct");
  const proxyCandidates = network.checks
    .filter((item) => item.ok && item.route && item.route.kind === "proxy")
    .sort((left, right) => left.latencyMs - right.latencyMs || left.index - right.index);
  const candidates = [...(directCandidate ? [directCandidate] : []), ...proxyCandidates];
  const attempts = [];
  const credentialErrors = [];

  // Only GitHub identity is safe as a universal credential preflight. Railway's
  // `me` query is account-token-only and rejects some otherwise usable scoped
  // tokens, which caused v24's false NO_AUTHENTICATED_ROUTE result.
  for (const candidate of candidates) {
    const route = candidate.route;
    try {
      const identity = await github(route, githubToken, "/user", { step: "github-token" });
      return {
        route,
        selected: candidate,
        identity,
        checks: network.checks,
        authChecks: [...attempts, { label: routeLabel(route), ok: true, githubOk: true, railwayReachable: true }],
      };
    } catch (error) {
      attempts.push({ ...routeFailureSummary(route, error), ok: false });
      if (error instanceof InstallError && ["GITHUB_TOKEN_INVALID", "GITHUB_PERMISSION"].includes(error.code)) credentialErrors.push(error);
    }
  }

  const allCodes = credentialErrors.map((error) => error.code);
  if (allCodes.length && allCodes.every((code) => code === "GITHUB_TOKEN_INVALID")) throw credentialErrors[0];
  if (allCodes.length && allCodes.every((code) => code === "GITHUB_PERMISSION")) throw credentialErrors[0];
  const error = new InstallError(
    "NO_GITHUB_AUTH_ROUTE", "github-token",
    "No network route could validate the GitHub token.",
    "هیچ مسیر شبکه‌ای نتوانست توکن GitHub را اعتبارسنجی کند.",
    502,
  );
  error.routeAttempts = attempts;
  throw error;
}

function githubError(status, step) {
  if (status === 401) return new InstallError("GITHUB_TOKEN_INVALID", step, "The GitHub token is invalid or expired.", "توکن GitHub نامعتبر یا منقضی است.", 401);
  if (status === 403) return new InstallError("GITHUB_PERMISSION", step, "GitHub denied this action. Create a classic token with the public_repo scope and check rate limits.", "GitHub این عملیات را رد کرد. توکن کلاسیک را با دسترسی public_repo بسازید و محدودیت درخواست را بررسی کنید.", 403);
  if (status === 422) return new InstallError("GITHUB_CONFLICT", step, "GitHub could not create the fork. A repository with the same name may already exist.", "GitHub نتوانست فورک را بسازد؛ ممکن است مخزنی هم‌نام از قبل وجود داشته باشد.", 409);
  return new InstallError("GITHUB_API_ERROR", step, "GitHub could not complete this step.", "GitHub نتوانست این مرحله را انجام دهد.", 502);
}

async function github(route, token, path, options = {}) {
  const response = await fetchWithTimeout(route, GITHUB_API + path, {
    method: options.method || "GET",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "User-Agent": "Lumen-Railway-Installer/26",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (options.allow404 && response.status === 404) return null;
  if (!response.ok) throw githubError(response.status, options.step || "github");
  if (response.status === 204) return null;
  try {
    return await response.json();
  } catch (_) {
    throw new InstallError("GITHUB_RESPONSE", options.step || "github", "GitHub returned an unreadable response.", "پاسخ GitHub قابل خواندن نبود.", 502);
  }
}

async function ensureFork(route, githubToken, login) {
  const encodedLogin = encodeURIComponent(login);
  let repo = await github(route, githubToken, "/repos/" + encodedLogin + "/" + SOURCE_REPO, { allow404: true, step: "fork" });
  if (repo) {
    const parent = repo.parent && repo.parent.full_name ? String(repo.parent.full_name) : "";
    if (!repo.fork || parent.toLowerCase() !== SOURCE_FULL.toLowerCase()) {
      throw new InstallError("FORK_NAME_CONFLICT", "fork", "Your account already has a repository named " + SOURCE_REPO + " that is not a fork of the official source. Rename or remove it, then retry.", "در حساب شما مخزنی با نام " + SOURCE_REPO + " وجود دارد که فورک سورس رسمی نیست. نام آن را تغییر دهید یا حذف کنید و دوباره تلاش کنید.", 409);
    }
    return repo;
  }

  await github(route, githubToken, "/repos/" + SOURCE_FULL + "/forks", {
    method: "POST",
    body: { default_branch_only: true },
    step: "fork",
  });

  for (let attempt = 0; attempt < 18; attempt += 1) {
    await wait(1400 + Math.min(attempt, 5) * 250);
    repo = await github(route, githubToken, "/repos/" + encodedLogin + "/" + SOURCE_REPO, { allow404: true, step: "fork" });
    if (repo) {
      const parent = repo.parent && repo.parent.full_name ? String(repo.parent.full_name) : "";
      if (repo.fork && parent.toLowerCase() === SOURCE_FULL.toLowerCase()) return repo;
    }
  }
  throw new InstallError("FORK_TIMEOUT", "fork", "The fork is still being prepared by GitHub. Wait one minute and run the installer again.", "GitHub هنوز در حال آماده‌سازی فورک است. یک دقیقه صبر کنید و نصب را دوباره اجرا کنید.", 504);
}

function railwayError(status) {
  if (status === 401 || status === 403) return new InstallError("RAILWAY_TOKEN_INVALID", "railway-token", "The Railway account token is invalid or lacks account access.", "توکن حساب Railway نامعتبر است یا دسترسی حساب ندارد.", 401);
  return new InstallError("RAILWAY_API_ERROR", "railway", "Railway could not complete this request.", "Railway نتوانست درخواست را انجام دهد.", 502);
}

async function railway(route, token, query, variables, step) {
  const response = await fetchWithTimeout(route, RAILWAY_API, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "User-Agent": "Lumen-Railway-Installer/26",
    },
    body: JSON.stringify({ query, variables }),
  }, 22000);
  if (!response.ok) throw railwayError(response.status);
  let result;
  try {
    result = await response.json();
  } catch (_) {
    throw new InstallError("RAILWAY_RESPONSE", step, "Railway returned an unreadable response.", "پاسخ Railway قابل خواندن نبود.", 502);
  }
  if (Array.isArray(result.errors) && result.errors.length) {
    const rawMessages = result.errors.map((item) => String(item && item.message ? item.message : "Railway request failed"));
    const safeDetails = rawMessages.join(" | ").replaceAll(token, "[redacted]").replace(/[\r\n\0]+/g, " ").slice(0, 360);
    const messages = safeDetails.toLowerCase();
    let error;
    if (messages.includes("not authorized") || messages.includes("unauthorized") || messages.includes("not authenticated") || messages.includes("invalid token")) {
      error = new InstallError("RAILWAY_TOKEN_INVALID", "railway-token", "Railway rejected this token. Create an Account Token with No workspace selected; workspace and project tokens cannot create a personal project.", "Railway این توکن را نپذیرفت. در Account → Tokens یک Account Token با گزینه No workspace بسازید؛ توکن Workspace یا Project نمی‌تواند پروژه شخصی جدید بسازد.", 401);
    } else if (messages.includes("github") || messages.includes("repository") || messages.includes("repo")) {
      error = new InstallError("RAILWAY_GITHUB_NOT_CONNECTED", step, "Railway cannot access the fork. Connect GitHub in Railway Account → Integrations, grant access to the fork, then retry.", "Railway به فورک دسترسی ندارد. در Railway از Account ← Integrations، گیت‌هاب را متصل و دسترسی فورک را فعال کنید، سپس دوباره تلاش کنید.", 409);
    } else if (messages.includes("limit") || messages.includes("plan") || messages.includes("volume")) {
      error = new InstallError("RAILWAY_PLAN_LIMIT", step, "A Railway plan or resource limit blocked this step. Check your account usage and project limits.", "محدودیت پلن یا منابع Railway مانع این مرحله شد. مصرف حساب و محدودیت‌های پروژه را بررسی کنید.", 409);
    } else {
      error = new InstallError("RAILWAY_GRAPHQL_ERROR", step, "Railway rejected the " + step + " step.", "Railway مرحله «" + step + "» را رد کرد.", 502);
    }
    error.safeDetails = safeDetails;
    throw error;
  }
  return result.data || {};
}

function workspaceList(value) {
  if (Array.isArray(value)) return value;
  if (value && Array.isArray(value.edges)) return value.edges.map((edge) => edge && edge.node).filter(Boolean);
  return [];
}

async function ensureWorkspace(route, railwayToken, ownerLogin) {
  const workspaceName = ("Lumen " + String(ownerLogin || "Workspace")).slice(0, 48);
  const listed = await railway(
    route,
    railwayToken,
    "query InstallerWorkspaces { me { workspaces { id name } } }",
    {},
    "workspace-list"
  );
  const available = workspaceList(listed.me && listed.me.workspaces)
    .filter((item) => item && typeof item.id === "string" && item.id.length > 0);
  const existing = available.find((item) => String(item.name || "").toLowerCase() === workspaceName.toLowerCase());
  if (existing) return { id: existing.id, name: String(existing.name || workspaceName), mode: "reused-lumen" };

  // Workspace creation is not exposed in every Railway public schema. Discover
  // it at runtime; create a dedicated Lumen workspace when supported, otherwise
  // reuse the first accessible workspace and still pass its required ID.
  try {
    const capability = await railway(
      route,
      railwayToken,
      'query InstallerWorkspaceCapability { __type(name: "Mutation") { fields { name } } }',
      {},
      "workspace-capability"
    );
    const fields = capability.__type && Array.isArray(capability.__type.fields) ? capability.__type.fields : [];
    if (fields.some((field) => field && field.name === "workspaceCreate")) {
      const created = await railway(
        route,
        railwayToken,
        "mutation InstallerWorkspaceCreate($input: WorkspaceCreateInput!) { workspaceCreate(input: $input) { id name } }",
        { input: { name: workspaceName } },
        "workspace-create"
      );
      const workspace = created.workspaceCreate;
      if (workspace && typeof workspace.id === "string" && workspace.id) {
        return { id: workspace.id, name: String(workspace.name || workspaceName), mode: "created" };
      }
    }
  } catch (_) {
    // A schema without workspaceCreate, or an account plan that disallows new
    // workspaces, falls back to the account's existing accessible workspace.
  }

  if (available.length) {
    const fallback = available[0];
    return { id: fallback.id, name: String(fallback.name || "Railway Workspace"), mode: "reused-existing" };
  }
  throw new InstallError(
    "WORKSPACE_REQUIRED", "workspace",
    "No accessible Railway workspace was found and this API account cannot create one. Create a workspace in Railway, then retry with an Account Token.",
    "هیچ Workspace قابل دسترسی پیدا نشد و API این حساب هم اجازه ساخت آن را نداد. ابتدا در Railway یک Workspace بسازید و سپس با Account Token دوباره تلاش کنید.",
    409,
  );
}

function railwayProjectName(ownerLogin, entropy = Date.now().toString(36)) {
  const owner = String(ownerLogin || "app")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "app";
  const tag = String(entropy || "deploy")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .slice(-8) || "deploy";
  const ownerLimit = Math.max(1, 32 - "lumen--".length - tag.length);
  return ("lumen-" + owner.slice(0, ownerLimit).replace(/-+$/g, "") + "-" + tag)
    .replace(/-+/g, "-")
    .slice(0, 32)
    .replace(/-+$/g, "");
}

async function provisionRailway(route, railwayToken, githubToken, fork, branch, commitSha, adminPassword, report = () => {}) {
  emitProgress(report, { phase: "workspace", step: 3, titleFa: "کشف یا ساخت Workspace", titleEn: "Resolving or creating Workspace" });
  const workspace = await ensureWorkspace(route, railwayToken, fork.owner.login);
  emitProgress(report, { phase: "project", step: 4, titleFa: "ساخت Project داخل Workspace", titleEn: "Creating Project in Workspace" });
  let projectName = railwayProjectName(fork.owner.login);
  let created;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      created = await railway(
        route,
        railwayToken,
        "mutation InstallerProject($input: ProjectCreateInput!) { projectCreate(input: $input) { id name environments { edges { node { id name } } } } }",
        { input: { workspaceId: workspace.id, name: projectName, description: "Lumen installed by the Railway installer", defaultEnvironmentName: "production" } },
        "project"
      );
      break;
    } catch (error) {
      if (attempt === 0 && /invalid project name/i.test(String(error && error.safeDetails || ""))) {
        projectName = railwayProjectName("app", randomSecret(12));
        continue;
      }
      throw error;
    }
  }
  const project = created.projectCreate;
  if (!project || !project.id) throw new InstallError("PROJECT_CREATE_FAILED", "project", "Railway did not return the new project.", "Railway پروژه جدید را برنگرداند.", 502);

  let environment = project.environments && project.environments.edges && project.environments.edges[0] ? project.environments.edges[0].node : null;
  if (!environment || !environment.id) {
    const loaded = await railway(
      route,
      railwayToken,
      "query InstallerProjectEnvironment($projectId: String!, $isEphemeral: Boolean) { environments(projectId: $projectId, isEphemeral: $isEphemeral) { edges { node { id name } } } }",
      { projectId: project.id, isEphemeral: false },
      "environment"
    );
    environment = loaded.environments && loaded.environments.edges && loaded.environments.edges[0] ? loaded.environments.edges[0].node : null;
  }
  if (!environment || !environment.id) throw new InstallError("ENVIRONMENT_MISSING", "environment", "Railway did not create the production environment.", "Railway محیط production را ایجاد نکرد.", 502);

  emitProgress(report, { phase: "service", step: 5, titleFa: "ساخت سرویس و تنظیم Virginia و IPv6", titleEn: "Creating service with Virginia and IPv6" });
  // Create an empty service first, then configure it before connecting the source.
  const serviceResult = await railway(
    route,
    railwayToken,
    "mutation InstallerService($input: ServiceCreateInput!) { serviceCreate(input: $input) { id name } }",
    { input: { projectId: project.id, environmentId: environment.id, name: "Lumen" } },
    "service"
  );
  const service = serviceResult.serviceCreate;
  if (!service || !service.id) throw new InstallError("SERVICE_CREATE_FAILED", "service", "Railway did not return the new service.", "Railway سرویس جدید را برنگرداند.", 502);

  await railway(
    route,
    railwayToken,
    "mutation InstallerServiceSettings($serviceId: String!, $environmentId: String!, $input: ServiceInstanceUpdateInput!) { serviceInstanceUpdate(serviceId: $serviceId, environmentId: $environmentId, input: $input) }",
    { serviceId: service.id, environmentId: environment.id, input: { startCommand: "python main.py", healthcheckPath: "/health", healthcheckTimeout: 300, ipv6EgressEnabled: true, region: "us-east4-eqdc4a", multiRegionConfig: { "us-east4-eqdc4a": { numReplicas: 1 } } } },
    "service-settings"
  );

  const variables = {
    ADMIN_PASSWORD: adminPassword,
    SECRET_KEY: randomSecret(48),
    DATA_DIR: "/data",
    PORT: "8000",
    PYTHONUNBUFFERED: "1",
    PROXY_REPOSITORY_MANUAL_REFRESH_KEY: randomSecret(36),
    LUMEN_UPSTREAM_REPO: SOURCE_FULL,
    LUMEN_FORK_REPO: String(fork.full_name),
    LUMEN_GITHUB_TOKEN: githubToken,
    LUMEN_RAILWAY_TOKEN: railwayToken,
    RAILWAY_GIT_BRANCH: branch,
    LUMEN_INSTALLER_VERSION: INSTALLER_VERSION,
    LUMEN_CREDENTIAL_SOURCE: "installer",
    LUMEN_REQUIRE_PERSISTENT_STORAGE: "1",
  };
  await railway(
    route,
    railwayToken,
    "mutation InstallerVariables($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }",
    { input: { projectId: project.id, environmentId: environment.id, serviceId: service.id, variables, skipDeploys: true } },
    "variables"
  );

  emitProgress(report, { phase: "volume", step: 6, titleFa: "اتصال فضای دائمی /data", titleEn: "Attaching persistent /data storage" });
  await railway(
    route,
    railwayToken,
    "mutation InstallerVolume($input: VolumeCreateInput!) { volumeCreate(input: $input) { id name } }",
    { input: { projectId: project.id, serviceId: service.id, environmentId: environment.id, mountPath: "/data" } },
    "volume"
  );

  emitProgress(report, { phase: "domain", step: 7, titleFa: "ساخت دامنه عمومی", titleEn: "Creating public domain" });
  const domainResult = await railway(
    route,
    railwayToken,
    "mutation InstallerDomain($input: ServiceDomainCreateInput!) { serviceDomainCreate(input: $input) { id domain } }",
    { input: { serviceId: service.id, environmentId: environment.id, targetPort: 8000 } },
    "domain"
  );
  const domain = domainResult.serviceDomainCreate && domainResult.serviceDomainCreate.domain ? String(domainResult.serviceDomainCreate.domain) : "";
  if (!/^[a-z0-9.-]+$/i.test(domain)) throw new InstallError("DOMAIN_CREATE_FAILED", "domain", "Railway did not return a valid public domain.", "Railway دامنه عمومی معتبری برنگرداند.", 502);

  await railway(
    route,
    railwayToken,
    "mutation InstallerSource($id: String!, $input: ServiceConnectInput!) { serviceConnect(id: $id, input: $input) { id } }",
    { id: service.id, input: { repo: String(fork.full_name), branch } },
    "source"
  );

  emitProgress(report, { phase: "deploy", step: 8, titleFa: "شروع Deployment در Virginia", titleEn: "Starting deployment in Virginia", deploymentStatus: "QUEUED", attempt: 0, maxAttempts: 7 });
  const deployResult = await railway(
    route,
    railwayToken,
    "mutation InstallerDeploy($serviceId: String!, $environmentId: String!, $commitSha: String!) { serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId, commitSha: $commitSha) }",
    { serviceId: service.id, environmentId: environment.id, commitSha },
    "deploy"
  );
  const deploymentId = String(deployResult.serviceInstanceDeployV2 || "");
  if (!deploymentId) throw new InstallError("DEPLOYMENT_ID_MISSING", "deploy", "Railway did not return a deployment ID.", "Railway شناسه Deployment را برنگرداند.", 502);
  let deploymentStatus = "QUEUED";
  let lastPollError = "";
  for (let attempt = 1; attempt <= 7; attempt += 1) {
    emitProgress(report, {
      phase: "deployment-status", step: 8, attempt, maxAttempts: 7, deploymentStatus,
      titleFa: "وضعیت Deployment: " + deploymentStatus,
      titleEn: "Deployment status: " + deploymentStatus,
      detailFa: "۲۰ ثانیه انتظار؛ بررسی " + attempt + " از ۷",
      detailEn: "Waiting 20 seconds; check " + attempt + " of 7",
    });
    await wait(deploymentPollDelayMs());
    try {
      const checked = await railway(route, railwayToken, "query InstallerDeployment($id: String!) { deployment(id: $id) { id status } }", { id: deploymentId }, "deployment-status");
      deploymentStatus = checked.deployment && checked.deployment.status ? String(checked.deployment.status).toUpperCase() : "NO_RESPONSE";
      lastPollError = "";
    } catch (error) {
      deploymentStatus = "NO_RESPONSE";
      lastPollError = String(error && (error.safeDetails || error.messageEn || error.message) || "").slice(0, 180);
    }
    emitProgress(report, {
      phase: "deployment-status", step: 8, attempt, maxAttempts: 7, deploymentStatus,
      titleFa: "وضعیت Deployment: " + deploymentStatus,
      titleEn: "Deployment status: " + deploymentStatus,
      detailFa: "نتیجه بررسی " + attempt + " از ۷",
      detailEn: "Result from check " + attempt + " of 7",
    });
    if (deploymentStatus === "SUCCESS") break;
    if (["FAILED", "CRASHED", "REMOVED"].includes(deploymentStatus)) {
      const failed = new InstallError("DEPLOYMENT_FAILED", "deployment-status", "Railway deployment ended with status " + deploymentStatus + ".", "Deployment در Railway با وضعیت " + deploymentStatus + " متوقف شد.", 502);
      failed.safeDetails = "Deployment status: " + deploymentStatus;
      throw failed;
    }
  }
  if (deploymentStatus !== "SUCCESS") {
    const timeout = new InstallError("DEPLOYMENT_TIMEOUT", "deployment-status", "The deployment did not reach SUCCESS after 7 checks spaced 20 seconds apart.", "Deployment پس از ۷ بررسی با فاصله‌های ۲۰ ثانیه‌ای به وضعیت SUCCESS نرسید.", 504);
    timeout.safeDetails = "Last deployment status: " + deploymentStatus + (lastPollError ? " | " + lastPollError : "");
    throw timeout;
  }
  return {
    workspaceId: workspace.id,
    workspaceName: workspace.name,
    workspaceMode: workspace.mode,
    panelUrl: "https://" + domain + "/dashboard",
    railwayProjectUrl: "https://railway.com/project/" + encodeURIComponent(project.id),
    projectId: project.id,
    serviceId: service.id,
    environmentId: environment.id,
    deploymentId,
    deploymentStatus,
  };
}

function validateTokenShape(value, kind) {
  if (typeof value !== "string") return "";
  const token = value.trim();
  if (token.length < 20 || token.length > 600 || /[\u0000-\u001f\u007f]/.test(token)) {
    throw new InstallError(kind.toUpperCase() + "_TOKEN_FORMAT", kind + "-token", "The " + kind + " token format is not valid.", "فرمت توکن " + (kind === "github" ? "GitHub" : "Railway") + " معتبر نیست.", 400);
  }
  return token;
}

async function installPayload(payload, options = {}) {
  let githubToken = validateTokenShape(payload && payload.githubToken, "github");
  let railwayToken = validateTokenShape(payload && payload.railwayToken, "railway");
  const report = typeof options.onProgress === "function" ? options.onProgress : () => {};
  try {
    emitProgress(report, { phase: "network", step: 0, titleFa: "بررسی مسیرهای شبکه", titleEn: "Checking network routes" });
    const publicNetwork = await selectTransport();
    const network = await selectAuthenticatedTransport(publicNetwork, githubToken, railwayToken);
    const route = network.route;
    const identity = network.identity;
    const login = identity && identity.login ? String(identity.login) : "";
    if (!/^[A-Za-z0-9-]{1,39}$/.test(login)) throw new InstallError("GITHUB_IDENTITY", "github-token", "GitHub did not return a valid account.", "GitHub حساب معتبری برنگرداند.", 502);

    emitProgress(report, { phase: "star", step: 1, titleFa: "استار کردن سورس رسمی", titleEn: "Starring official source" });
    await github(route, githubToken, "/user/starred/" + SOURCE_FULL, { method: "PUT", step: "star" });
    emitProgress(report, { phase: "fork", step: 2, titleFa: "ساخت یا بررسی Fork", titleEn: "Creating or verifying Fork" });
    const fork = await ensureFork(route, githubToken, login);
    const branch = String(fork.default_branch || "main");
    const commit = await github(route, githubToken, "/repos/" + encodeURIComponent(login) + "/" + SOURCE_REPO + "/commits/" + encodeURIComponent(branch), { step: "fork" });
    if (!commit || !/^[0-9a-f]{40}$/i.test(String(commit.sha || ""))) throw new InstallError("FORK_COMMIT", "fork", "The fork has no deployable branch commit yet.", "فورک هنوز کامیت قابل دیپلوی ندارد.", 502);

    const adminPassword = randomSecret(18);
    const railwayResult = await provisionRailway(route, railwayToken, githubToken, fork, branch, String(commit.sha), adminPassword, report);
    return {
      ok: true,
      installerVersion: INSTALLER_VERSION,
      source: SOURCE_FULL,
      forkUrl: String(fork.html_url || ("https://github.com/" + fork.full_name)),
      forkRepository: String(fork.full_name),
      branch,
      adminPassword,
      networkRoute: { kind: route.kind, label: routeLabel(route), latencyMs: network.selected.latencyMs },
      networkChecks: network.checks.map((item) => ({ label: item.label, ok: item.ok, latencyMs: item.latencyMs, code: item.ok ? undefined : item.code })),
      authenticatedRouteChecks: network.authChecks,
      ...railwayResult,
    };
  } finally {
    githubToken = "";
    railwayToken = "";
  }
}

async function parseInstallRequest(request) {
  const requestUrl = new URL(request.url);
  const origin = request.headers.get("Origin");
  if (origin && origin !== requestUrl.origin) {
    throw new InstallError("ORIGIN_REJECTED", "request", "This installation request came from another origin.", "درخواست نصب از مبدأ دیگری ارسال شده است.", 403);
  }
  const contentType = request.headers.get("Content-Type") || "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    throw new InstallError("CONTENT_TYPE", "request", "Send installation data as JSON.", "اطلاعات نصب باید به‌صورت JSON ارسال شود.", 415);
  }
  const declared = Number(request.headers.get("Content-Length") || "0");
  if (declared > MAX_BODY_BYTES) throw new InstallError("BODY_TOO_LARGE", "request", "The request is too large.", "حجم درخواست بیش از حد مجاز است.", 413);
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) throw new InstallError("BODY_TOO_LARGE", "request", "The request is too large.", "حجم درخواست بیش از حد مجاز است.", 413);
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (_) {
    throw new InstallError("INVALID_JSON", "request", "The request body is not valid JSON.", "بدنه درخواست JSON معتبر نیست.", 400);
  }
  return payload;
}

async function handleInstall(request, options = {}) {
  return installPayload(await parseInstallRequest(request), options);
}

function installErrorDetail(error, requestId = randomSecret(9)) {
  const known = error instanceof InstallError;
  return {
    code: known ? error.code : "INTERNAL_ERROR",
    step: known ? error.step : "internal",
    messageEn: known ? error.messageEn : "The installer encountered an internal error.",
    messageFa: known ? error.messageFa : "نصاب با یک خطای داخلی روبه‌رو شد.",
    details: known && error.safeDetails ? error.safeDetails : undefined,
    routeAttempts: known && error.routeAttempts ? error.routeAttempts : undefined,
    requestId,
  };
}

function publicProgress(update) {
  const value = update && typeof update === "object" ? update : {};
  return {
    phase: String(value.phase || "running").slice(0, 48),
    step: Number.isInteger(value.step) ? Math.max(0, Math.min(8, value.step)) : 0,
    titleFa: String(value.titleFa || "نصب در حال اجراست").slice(0, 160),
    titleEn: String(value.titleEn || "Installation is running").slice(0, 160),
    detailFa: value.detailFa ? String(value.detailFa).slice(0, 180) : undefined,
    detailEn: value.detailEn ? String(value.detailEn).slice(0, 180) : undefined,
    deploymentStatus: value.deploymentStatus ? String(value.deploymentStatus).slice(0, 40) : undefined,
    attempt: Number.isInteger(value.attempt) ? value.attempt : undefined,
    maxAttempts: Number.isInteger(value.maxAttempts) ? value.maxAttempts : undefined,
  };
}

function cleanInstallJobs() {
  const now = Date.now();
  for (const [id, job] of installJobs) {
    if (job.state !== "running" && now - job.updatedAtMs > INSTALL_JOB_TTL_MS) installJobs.delete(id);
  }
}

function startInstallJob(payload) {
  cleanInstallJobs();
  const installId = randomSecret(24);
  const startedAt = new Date().toISOString();
  installJobs.set(installId, { state: "running", startedAt, updatedAt: startedAt, updatedAtMs: Date.now(), ...publicProgress({ phase: "accepted", step: 0 }) });
  activeInstalls += 1;
  let secretPayload = payload;
  void installPayload(secretPayload, {
    onProgress(update) {
      const current = installJobs.get(installId);
      if (!current || current.state !== "running") return;
      installJobs.set(installId, { ...current, ...publicProgress(update), updatedAt: new Date().toISOString(), updatedAtMs: Date.now() });
    },
  }).then((result) => {
    const current = installJobs.get(installId) || {};
    installJobs.set(installId, { ...current, state: "completed", phase: "completed", step: 9, titleFa: "Deployment با موفقیت انجام شد", titleEn: "Deployment completed successfully", result, updatedAt: new Date().toISOString(), updatedAtMs: Date.now() });
  }).catch((error) => {
    const detail = installErrorDetail(error);
    console.error(`[install:${detail.requestId}] code=${detail.code} step=${detail.step}` + (detail.details ? ` details=${detail.details}` : ""));
    const current = installJobs.get(installId) || {};
    installJobs.set(installId, { ...current, state: "failed", phase: "failed", titleFa: detail.messageFa, titleEn: detail.messageEn, error: detail, updatedAt: new Date().toISOString(), updatedAtMs: Date.now() });
  }).finally(() => {
    secretPayload = null;
    activeInstalls = Math.max(0, activeInstalls - 1);
  });
  return installId;
}

const INSTALLER_HTML = `<!doctype html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<title>Lumen Setup</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&amp;display=swap">
<style nonce="__NONCE__">
:root{
 --md-ref-typeface-brand:"Vazirmatn","Segoe UI",Tahoma,sans-serif;--md-ref-typeface-plain:"Vazirmatn","Segoe UI",Tahoma,sans-serif;
 --md-sys-color-primary:#3f5f90;--md-sys-color-on-primary:#fff;--md-sys-color-primary-container:#d6e3ff;--md-sys-color-on-primary-container:#0a1c36;
 --md-sys-color-secondary:#555f71;--md-sys-color-on-secondary:#fff;--md-sys-color-secondary-container:#d9e3f8;--md-sys-color-on-secondary-container:#121c2b;
 --md-sys-color-tertiary:#705575;--md-sys-color-on-tertiary:#fff;--md-sys-color-tertiary-container:#fad8fd;--md-sys-color-on-tertiary-container:#29132e;
 --md-sys-color-error:#ba1a1a;--md-sys-color-on-error:#fff;--md-sys-color-error-container:#ffdad6;--md-sys-color-on-error-container:#410002;
 --md-sys-color-surface:#f9f9ff;--md-sys-color-on-surface:#191c20;--md-sys-color-on-surface-variant:#43474e;
 --md-sys-color-surface-container-lowest:#fff;--md-sys-color-surface-container-low:#f3f3fa;--md-sys-color-surface-container:#ededf4;--md-sys-color-surface-container-high:#e7e8ee;--md-sys-color-surface-container-highest:#e1e2e8;
 --md-sys-color-outline:#74777f;--md-sys-color-outline-variant:#c4c6d0;--md-sys-color-inverse-surface:#2e3035;--md-sys-color-inverse-on-surface:#f0f0f7;--md-sys-color-inverse-primary:#a9c7fb;
 --md-sys-shape-corner-small:8px;--md-sys-shape-corner-medium:12px;--md-sys-shape-corner-large:16px;--md-sys-shape-corner-large-increased:20px;--md-sys-shape-corner-extra-large:28px;--md-sys-shape-corner-extra-large-increased:32px;--md-sys-shape-corner-extra-extra-large:48px;--md-sys-shape-corner-full:9999px;
 --md-sys-motion-easing-emphasized:cubic-bezier(.2,0,0,1);--md-sys-motion-easing-enter:cubic-bezier(.05,.7,.1,1);--md-sys-motion-duration-short4:200ms;--md-sys-motion-duration-medium2:300ms;--md-sys-motion-duration-medium4:400ms;
 --space-1:8px;--space-2:16px;--space-3:24px;--space-4:32px;--space-5:48px;
}
html[data-theme="dark"]{
 --md-sys-color-primary:#a9c7fb;--md-sys-color-on-primary:#0a305f;--md-sys-color-primary-container:#274777;--md-sys-color-on-primary-container:#d6e3ff;
 --md-sys-color-secondary:#bdc7dc;--md-sys-color-on-secondary:#273141;--md-sys-color-secondary-container:#3d4758;--md-sys-color-on-secondary-container:#d9e3f8;
 --md-sys-color-tertiary:#ddbce0;--md-sys-color-on-tertiary:#3f2844;--md-sys-color-tertiary-container:#573e5c;--md-sys-color-on-tertiary-container:#fad8fd;
 --md-sys-color-error:#ffb4ab;--md-sys-color-on-error:#690005;--md-sys-color-error-container:#93000a;--md-sys-color-on-error-container:#ffdad6;
 --md-sys-color-surface:#111318;--md-sys-color-on-surface:#e2e2e9;--md-sys-color-on-surface-variant:#c4c6d0;
 --md-sys-color-surface-container-lowest:#0c0e13;--md-sys-color-surface-container-low:#191c20;--md-sys-color-surface-container:#1d2024;--md-sys-color-surface-container-high:#282a2f;--md-sys-color-surface-container-highest:#33353a;
 --md-sys-color-outline:#8e9099;--md-sys-color-outline-variant:#44474f;--md-sys-color-inverse-surface:#e2e2e9;--md-sys-color-inverse-on-surface:#2e3035;--md-sys-color-inverse-primary:#3f5f90;
}
*{box-sizing:border-box}html{min-height:100%;background:var(--md-sys-color-surface)}body{min-height:100vh;margin:0;color:var(--md-sys-color-on-surface);font-family:var(--md-ref-typeface-plain);background:var(--md-sys-color-surface);transition:background var(--md-sys-motion-duration-medium4) var(--md-sys-motion-easing-emphasized),color var(--md-sys-motion-duration-medium2)}button,input,a{font:inherit}button,a{tap-highlight-color:transparent}.shell{width:min(1120px,calc(100% - 48px));margin-inline:auto;padding-block:16px 48px}.topbar{height:72px;display:flex;align-items:center;justify-content:space-between;gap:16px;border-bottom:1px solid var(--md-sys-color-outline-variant)}.brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.01em}.brand-mark{width:44px;height:44px;border-radius:var(--md-sys-shape-corner-large) var(--md-sys-shape-corner-large) var(--md-sys-shape-corner-small) var(--md-sys-shape-corner-large);display:grid;place-items:center;background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);font-size:20px}.controls{display:flex;gap:8px}.icon-btn{min-width:48px;height:48px;border:0;border-radius:var(--md-sys-shape-corner-full);display:inline-grid;place-items:center;padding-inline:14px;background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface);cursor:pointer;transition:transform var(--md-sys-motion-duration-short4) var(--md-sys-motion-easing-emphasized),background var(--md-sys-motion-duration-short4)}.icon-btn:hover{background:var(--md-sys-color-surface-container-highest);transform:translateY(-1px)}.icon-btn:active,.filled:active,.tonal:active{transform:scale(.96);border-radius:var(--md-sys-shape-corner-large)}.layout{display:grid;grid-template-columns:1fr;gap:16px;align-items:stretch;margin-top:24px}.hero,.panel{min-width:0;border-radius:var(--md-sys-shape-corner-extra-extra-large);overflow:hidden}.hero{padding:28px 32px;background:var(--md-sys-color-surface-container);color:var(--md-sys-color-on-surface);display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,.5fr);align-items:center;gap:32px;min-height:0;position:relative;border:1px solid var(--md-sys-color-outline-variant)}.hero:after{display:none}.eyebrow{display:inline-flex;align-items:center;gap:8px;width:max-content;max-width:100%;padding:8px 14px;border-radius:var(--md-sys-shape-corner-full);background:color-mix(in srgb,var(--md-sys-color-on-primary-container) 9%,transparent);font-size:.78rem;font-weight:750}.hero h1{font-family:var(--md-ref-typeface-brand);font-size:clamp(1.8rem,3vw,2.6rem);line-height:1.35;letter-spacing:-.02em;margin:16px 0 10px;max-width:none}.hero p{font-size:1rem;line-height:1.85;max-width:52ch;margin:0;color:var(--md-sys-color-on-surface-variant)}.source-card{position:relative;z-index:1;padding:18px;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-surface-container-lowest);color:var(--md-sys-color-on-surface);border:1px solid var(--md-sys-color-outline-variant)}.source-label{font-size:.72rem;color:var(--md-sys-color-on-surface-variant);margin-bottom:8px}.source-name{font-weight:780;overflow-wrap:anywhere}.source-meta{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}.chip{padding:7px 11px;border-radius:var(--md-sys-shape-corner-small);background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);font-size:.7rem;font-weight:700}.panel{padding:32px;background:var(--md-sys-color-surface-container-lowest);border:1px solid var(--md-sys-color-outline-variant)}.view{max-width:920px;margin-inline:auto}#install-form{display:grid;grid-template-columns:1fr 1fr;column-gap:20px}.guide,.notice,#install-button{grid-column:1/-1}.guide{grid-template-columns:repeat(3,minmax(0,1fr))}.view[hidden]{display:none}.panel-head{display:flex;align-items:flex-start;gap:16px;margin-bottom:28px}.step-number{width:52px;height:52px;flex:0 0 52px;border-radius:var(--md-sys-shape-corner-large-increased) var(--md-sys-shape-corner-large-increased) var(--md-sys-shape-corner-small) var(--md-sys-shape-corner-large-increased);background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);display:grid;place-items:center;font-size:1.1rem;font-weight:850}.panel h2{font:750 1.6rem/1.25 var(--md-ref-typeface-brand);margin:2px 0 6px}.muted{color:var(--md-sys-color-on-surface-variant);font-size:.84rem;line-height:1.65;margin:0}.field{margin-bottom:18px}.field-top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px}.field label{font-size:.82rem;font-weight:760}.direct-link{min-height:44px;display:inline-flex;align-items:center;padding-inline:8px;color:var(--md-sys-color-primary);font-size:.72rem;font-weight:750;text-decoration:none;border-radius:var(--md-sys-shape-corner-full)}.direct-link:hover{text-decoration:underline}.input-wrap{position:relative}.input-wrap input{width:100%;height:56px;border:1px solid var(--md-sys-color-outline);border-radius:var(--md-sys-shape-corner-small) var(--md-sys-shape-corner-small) 0 0;padding:0 52px 0 16px;background:var(--md-sys-color-surface-container-lowest);color:var(--md-sys-color-on-surface);direction:ltr;text-align:left;outline:0;transition:border var(--md-sys-motion-duration-short4),background var(--md-sys-motion-duration-short4)}[dir="rtl"] .input-wrap input{padding:0 16px 0 52px}.input-wrap input:focus{border:2px solid var(--md-sys-color-primary);padding-inline-start:15px}.reveal{position:absolute;inset-inline-end:4px;top:4px;width:48px;height:48px;border:0;background:transparent;color:var(--md-sys-color-on-surface-variant);border-radius:var(--md-sys-shape-corner-full);cursor:pointer}.support{display:block;margin-top:7px;color:var(--md-sys-color-on-surface-variant);font-size:.69rem;line-height:1.55}.guide{display:grid;gap:8px;margin:24px 0}.guide-row{display:grid;grid-template-columns:36px minmax(0,1fr) auto;gap:10px;align-items:center;padding:12px;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-surface-container)}.guide-icon{width:36px;height:36px;border-radius:var(--md-sys-shape-corner-medium);display:grid;place-items:center;background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);font-weight:850}.guide-copy b{display:block;font-size:.78rem}.guide-copy span{display:block;font-size:.66rem;color:var(--md-sys-color-on-surface-variant);margin-top:3px}.guide a{min-width:48px;height:48px;border-radius:var(--md-sys-shape-corner-full);display:grid;place-items:center;color:var(--md-sys-color-primary);text-decoration:none}.notice{display:flex;gap:10px;padding:14px 16px;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);font-size:.7rem;line-height:1.65;margin-bottom:18px}.filled,.tonal{min-height:52px;border:0;border-radius:var(--md-sys-shape-corner-full);padding:0 22px;display:inline-flex;align-items:center;justify-content:center;gap:10px;font-weight:780;cursor:pointer;transition:transform var(--md-sys-motion-duration-short4) var(--md-sys-motion-easing-emphasized),border-radius var(--md-sys-motion-duration-short4),background var(--md-sys-motion-duration-short4)}.filled{width:100%;background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary)}.filled:hover{background:color-mix(in srgb,var(--md-sys-color-primary) 92%,var(--md-sys-color-on-primary))}.filled:disabled{opacity:.55;cursor:wait}.tonal{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);text-decoration:none}.progress-head{text-align:center;padding:12px 0 28px}.spinner{width:72px;height:72px;border-radius:26px 26px 8px 26px;margin:0 auto 20px;background:var(--md-sys-color-primary-container);position:relative;animation:morph 2.4s var(--md-sys-motion-easing-emphasized) infinite}.spinner:before{content:"";position:absolute;inset:18px;border:4px solid var(--md-sys-color-primary);border-inline-end-color:transparent;border-radius:50%;animation:spin .8s linear infinite}.steps{display:grid;gap:8px}.progress-step{display:grid;grid-template-columns:40px 1fr auto;gap:12px;align-items:center;padding:12px 14px;border-radius:var(--md-sys-shape-corner-large);color:var(--md-sys-color-on-surface-variant)}.progress-step.active{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}.progress-step.done{color:var(--md-sys-color-primary)}.step-dot{width:40px;height:40px;border-radius:var(--md-sys-shape-corner-full);display:grid;place-items:center;border:1px solid var(--md-sys-color-outline-variant);font-weight:800}.active .step-dot{background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);border-color:transparent}.done .step-dot{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}.progress-step span{font-size:.8rem;font-weight:690}.progress-step small{font-size:.65rem}.success-mark,.error-mark{width:76px;height:76px;border-radius:28px 28px 8px 28px;display:grid;place-items:center;font-size:2rem;margin-bottom:22px}.success-mark{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}.error-mark{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}.result{margin:22px 0;display:grid;gap:10px}.result-row{padding:14px;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-surface-container);display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center}.result-row label{display:block;color:var(--md-sys-color-on-surface-variant);font-size:.66rem;margin-bottom:5px}.result-row code{display:block;direction:ltr;text-align:left;overflow-wrap:anywhere;font-size:.75rem;color:var(--md-sys-color-on-surface)}.copy{width:48px;height:48px;border:0;border-radius:var(--md-sys-shape-corner-full);background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);cursor:pointer}.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}.error-box{padding:16px;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container);line-height:1.7;margin:18px 0;font-size:.8rem}.footer{text-align:center;color:var(--md-sys-color-on-surface-variant);font-size:.68rem;padding-top:24px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@keyframes spin{to{transform:rotate(360deg)}}@keyframes morph{50%{border-radius:50% 24% 50% 32%;transform:rotate(4deg)}}@keyframes drift{to{transform:translate(-24px,-16px) rotate(10deg)}}
@media(max-width:839px){.hero{grid-template-columns:1fr;padding:28px}.hero h1{max-width:none}.source-card{margin-top:8px}.panel{padding:28px}#install-form{grid-template-columns:1fr}.guide,.notice,#install-button{grid-column:1}.guide{grid-template-columns:1fr}}
@media(max-width:599px){.shell{width:min(100% - 24px,1040px);padding-block:12px 32px}.topbar{height:60px}.layout{margin-top:12px;gap:12px}.hero,.panel{border-radius:var(--md-sys-shape-corner-extra-large)}.hero{padding:22px;min-height:0}.hero h1{font-size:2rem}.panel{padding:24px 18px}.guide-row{grid-template-columns:36px 1fr auto}.actions{grid-template-columns:1fr}.result-row{grid-template-columns:minmax(0,1fr) 48px}.controls .lang-text{display:none}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
 <div class="brand"><div class="brand-mark">L</div><span>Lumen Setup</span></div>
 <div class="controls">
  <button class="icon-btn" id="theme" type="button" aria-label="Toggle color theme"><span aria-hidden="true">◐</span></button>
  <button class="icon-btn" id="language" type="button" aria-label="Change language"><span aria-hidden="true">文</span><span class="lang-text">EN</span></button>
 </div>
</header>
<main class="layout">
 <section class="hero" aria-labelledby="hero-title">
  <div><div class="eyebrow"><span aria-hidden="true">✦</span><span data-fa="نصاب عمومی Lumen · نسخه ۲۸" data-en="Public Lumen installer · v28">نصاب عمومی Lumen · نسخه ۲۸</span></div><h1 id="hero-title" data-fa="نصب Lumen روی Railway" data-en="Install Lumen on Railway">نصب Lumen روی Railway</h1><p data-fa="فقط دو توکن را وارد کنید. نصاب مخزن رسمی را فورک می‌کند، فضای دائمی و تنظیمات Railway را می‌سازد و لینک پنل را تحویل می‌دهد." data-en="Enter two tokens. The installer forks the official repository, configures persistent storage and Railway, deploys the service, and returns the panel URL.">فقط دو توکن را وارد کنید. نصاب مخزن رسمی را فورک می‌کند، فضای دائمی و تنظیمات Railway را می‌سازد و لینک پنل را تحویل می‌دهد.</p></div>
  <div class="source-card"><div class="source-label" data-fa="سورس ثابت و رسمی" data-en="Fixed official source">سورس ثابت و رسمی</div><div class="source-name">highisabella52213/Lumen-Project-Final</div><div class="source-meta"><span class="chip">WS only</span><span class="chip">Railway</span><span class="chip">v28</span><span class="chip">6 proxies + direct</span></div></div>
 </section>
 <section class="panel">
  <div class="view" id="form-view">
   <div class="panel-head"><div class="step-number">01</div><div><h2 data-fa="دسترسی‌های نصب" data-en="Installation access">دسترسی‌های نصب</h2><p class="muted" data-fa="نصاب توکن‌ها را نگه‌داری یا لاگ نمی‌کند؛ پس از بررسی، آن‌ها داخل متغیرهای محافظت‌شده Railway خودتان ثبت می‌شوند." data-en="The installer never persists or logs tokens; after verification, they are stored in your own protected Railway service variables.">نصاب توکن‌ها را نگه‌داری یا لاگ نمی‌کند؛ پس از بررسی، آن‌ها داخل متغیرهای محافظت‌شده Railway خودتان ثبت می‌شوند.</p></div></div>
   <form id="install-form" novalidate>
    <div class="field"><div class="field-top"><label for="github-token" data-fa="توکن GitHub" data-en="GitHub token">توکن GitHub</label><a class="direct-link" href="https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Railway%20Installer" target="_blank" rel="noopener noreferrer" data-fa="ساخت مستقیم ↗" data-en="Create token ↗">ساخت مستقیم ↗</a></div><div class="input-wrap"><input id="github-token" type="password" required autocomplete="new-password" spellcheck="false" aria-describedby="github-help"><button class="reveal" type="button" data-reveal="github-token" aria-label="Show or hide GitHub token">◉</button></div><small class="support" id="github-help" data-fa="توکن کلاسیک با دسترسی public_repo؛ برای فورک و استار مخزن عمومی." data-en="Classic token with public_repo scope, used to fork and star the public source.">توکن کلاسیک با دسترسی public_repo؛ برای فورک و استار مخزن عمومی.</small></div>
    <div class="field"><div class="field-top"><label for="railway-token" data-fa="توکن حساب Railway" data-en="Railway account token">توکن حساب Railway</label><a class="direct-link" href="https://railway.com/account/tokens" target="_blank" rel="noopener noreferrer" data-fa="ساخت مستقیم ↗" data-en="Create token ↗">ساخت مستقیم ↗</a></div><div class="input-wrap"><input id="railway-token" type="password" required autocomplete="new-password" spellcheck="false" aria-describedby="railway-help"><button class="reveal" type="button" data-reveal="railway-token" aria-label="Show or hide Railway token">◉</button></div><small class="support" id="railway-help" data-fa="در Account → Tokens گزینه No workspace را انتخاب و Account Token بسازید؛ Workspace/Project Token قابل استفاده نیست." data-en="In Account → Tokens choose No workspace and create an Account Token; workspace/project tokens are not supported.">در Account → Tokens گزینه No workspace را انتخاب و Account Token بسازید؛ Workspace/Project Token قابل استفاده نیست.</small></div>
    <div class="guide" aria-label="Preparation guide">
     <div class="guide-row"><div class="guide-icon">1</div><div class="guide-copy"><b data-fa="توکن GitHub را بسازید" data-en="Create GitHub token">توکن GitHub را بسازید</b><span data-fa="لینک بالا با public_repo آماده است" data-en="The link above preselects public_repo">لینک بالا با public_repo آماده است</span></div><a href="https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Railway%20Installer" target="_blank" rel="noopener noreferrer" aria-label="Open GitHub token page">↗</a></div>
     <div class="guide-row"><div class="guide-icon">2</div><div class="guide-copy"><b data-fa="Account Token ریلوی را بسازید" data-en="Create Railway Account Token">Account Token ریلوی را بسازید</b><span data-fa="از Account → Tokens با انتخاب No workspace" data-en="From Account → Tokens with No workspace selected">از Account → Tokens با انتخاب No workspace</span></div><a href="https://railway.com/account/tokens" target="_blank" rel="noopener noreferrer" aria-label="Open Railway token page">↗</a></div>
     <div class="guide-row"><div class="guide-icon">3</div><div class="guide-copy"><b data-fa="GitHub را به Railway متصل کنید" data-en="Connect GitHub to Railway">GitHub را به Railway متصل کنید</b><span data-fa="اجازه دسترسی به فورک Lumen را بدهید" data-en="Grant Railway access to the Lumen fork">اجازه دسترسی به فورک Lumen را بدهید</span></div><a href="https://railway.com/account/integrations" target="_blank" rel="noopener noreferrer" aria-label="Open Railway integrations">↗</a></div>
    </div>
    <div class="notice"><span aria-hidden="true">◆</span><span data-fa="این فایل برای استفاده عمومی است، اما هر شخص باید نسخه خودش را در حساب Railway خودش دیپلوی کند. ابتدا هر شش پروکسی روی همان سرویس Railway آزمایش می‌شوند؛ سریع‌ترین مسیر سالم انتخاب می���شود و فقط اگر همه ناموفق باشند اتصال مستقیم بررسی می‌شود. هرگز توکن را در نصب‌کننده متعلق به شخص دیگری وارد نکنید." data-en="This file is public, but every user must deploy a personal copy in their own Railway account. All proxies and direct egress are tested by the Railway service; token-bearing operations prefer direct egress and use healthy proxies as fallbacks. Never enter tokens into another person's installer.">این فایل برای استفاده عمومی است، اما هر شخص باید نسخه خودش را در حساب Railway خودش دیپلوی کند. همه پروکسی‌ها و مسیر مستقیم روی همان سرویس Railway آزمایش می‌شوند؛ برای عملیات دارای توکن ابتدا مسیر مستقیم و سپس پروکسی‌های سالم امتحان می‌شوند. هرگز توکن را در نصب‌کننده متعلق به شخص دیگری وارد نکنید.</span></div>
    <button class="filled" id="install-button" type="submit"><span aria-hidden="true">✦</span><span data-fa="شروع نصب خودکار" data-en="Start automated setup">شروع نصب خودکار</span></button>
   </form>
  </div>
  <div class="view" id="progress-view" hidden aria-live="polite"><div class="progress-head"><div class="spinner" aria-hidden="true"></div><h2 id="progress-title" data-fa="ستاپ در حال اجراست" data-en="Setup is running">ستاپ در حال اجراست</h2><p class="muted" id="progress-detail" data-fa="صفحه را نبندید؛ وضعیت واقعی Deployment نمایش داده می‌شود." data-en="Keep this page open; the live Deployment status appears here.">صفحه را نبندید؛ وضعیت واقعی Deployment نمایش داده می‌شود.</p></div><div class="steps" id="steps"></div></div>
  <div class="view" id="success-view" hidden aria-live="polite"><div class="success-mark">✓</div><h2 data-fa="پنل آماده شد" data-en="Your panel is ready">پنل آماده شد</h2><p class="muted" id="success-copy"></p><div class="result"><div class="result-row"><div><label data-fa="لینک پنل مدیریت" data-en="Management panel URL">لینک پنل مدیریت</label><code id="panel-url"></code></div><button class="copy" type="button" data-copy="panel-url" aria-label="Copy panel URL">⧉</button></div><div class="result-row"><div><label data-fa="رمز ادمین — فقط همین‌بار نمایش داده می‌شود" data-en="Admin password — shown once">رمز ادمین — فقط همین‌بار نمایش داده می‌شود</label><code id="admin-password"></code></div><button class="copy" type="button" data-copy="admin-password" aria-label="Copy admin password">⧉</button></div><div class="result-row"><div><label data-fa="فورک شما" data-en="Your fork">فو��ک شما</label><code id="fork-repository"></code></div><button class="copy" type="button" data-copy="fork-repository" aria-label="Copy fork repository">⧉</button></div><div class="result-row"><div><label data-fa="Workspace انتخاب‌شده" data-en="Selected workspace">Workspace انتخاب‌شده</label><code id="workspace-name"></code></div><button class="copy" type="button" data-copy="workspace-name" aria-label="Copy workspace name">⧉</button></div><div class="result-row"><div><label data-fa="مسیر شبکه انتخاب‌شده" data-en="Selected network route">مسیر شبکه انتخاب‌شده</label><code id="network-route"></code></div><button class="copy" type="button" data-copy="network-route" aria-label="Copy selected route">⧉</button></div></div><div class="actions"><a class="filled" id="open-panel" target="_blank" rel="noopener noreferrer" data-fa="باز کردن پنل" data-en="Open panel">باز کردن پنل</a><a class="tonal" id="open-railway" target="_blank" rel="noopener noreferrer" data-fa="نمایش در Railway" data-en="View in Railway">نمایش در Railway</a></div></div>
  <div class="view" id="error-view" hidden aria-live="assertive"><div class="error-mark">!</div><h2 data-fa="نصب متوقف شد" data-en="Setup stopped">نصب متوقف شد</h2><div class="error-box" id="error-message"></div><button class="tonal" id="retry" type="button" data-fa="بازگشت و تلاش دوباره" data-en="Go back and retry">بازگشت و تلاش دوباره</button></div>
 </section>
</main>
<div class="footer" data-fa="Lumen public installer · شش پروکسی با فالبک مستقیم" data-en="Lumen public installer · six proxies with direct fallback">Lumen public installer · شش پروکسی با فالبک مستقیم</div>
</div>
<script nonce="__NONCE__">
(function(){
 var lang=localStorage.getItem('lumen-installer-lang')||'fa';var theme=localStorage.getItem('lumen-installer-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');var liveProgress=null;
 var stepDefs=[['آزمایش مسیر مستقیم و همه پروکسی‌ها','Test direct egress and all proxies'],['استار کردن سورس رسمی','Star official source'],['ساخت یا بررسی فورک','Create or verify fork'],['کشف یا ساخت Workspace','Resolve or create workspace'],['ساخت پروژه Railway','Create Railway project'],['تنظیم متغیرها و سرویس','Configure service and variables'],['اتصال فضای دائمی /data','Attach persistent /data'],['ساخت دامنه عمومی','Generate public domain'],['شروع دیپلوی','Start deployment']];
 function applyLocale(){document.documentElement.lang=lang;document.documentElement.dir=lang==='fa'?'rtl':'ltr';document.querySelectorAll('[data-fa]').forEach(function(el){el.textContent=el.getAttribute(lang==='fa'?'data-fa':'data-en')});document.querySelector('.lang-text').textContent=lang==='fa'?'EN':'فا';renderSteps(window.__activeStep||0);renderLiveProgress(liveProgress)}
 function applyTheme(){document.documentElement.setAttribute('data-theme',theme)}
 function show(id){['form-view','progress-view','success-view','error-view'].forEach(function(name){document.getElementById(name).hidden=name!==id})}
 function renderSteps(active){var box=document.getElementById('steps');if(!box)return;box.innerHTML='';stepDefs.forEach(function(item,index){var row=document.createElement('div');row.className='progress-step '+(index<active?'done':index===active?'active':'');var dot=document.createElement('div');dot.className='step-dot';dot.textContent=index<active?'✓':String(index+1);var label=document.createElement('span');label.textContent=item[lang==='fa'?0:1];var state=document.createElement('small');state.textContent=index<active?(lang==='fa'?'انجام شد':'Done'):index===active?(lang==='fa'?'در حال انجام':'Working'):'—';row.append(dot,label,state);box.appendChild(row)})}
 document.getElementById('language').addEventListener('click',function(){lang=lang==='fa'?'en':'fa';localStorage.setItem('lumen-installer-lang',lang);applyLocale()});
 document.getElementById('theme').addEventListener('click',function(){theme=theme==='dark'?'light':'dark';localStorage.setItem('lumen-installer-theme',theme);applyTheme()});
 document.querySelectorAll('[data-reveal]').forEach(function(button){button.addEventListener('click',function(){var input=document.getElementById(button.getAttribute('data-reveal'));input.type=input.type==='password'?'text':'password'})});
 document.querySelectorAll('[data-copy]').forEach(function(button){button.addEventListener('click',function(){var text=document.getElementById(button.getAttribute('data-copy')).textContent;navigator.clipboard.writeText(text).then(function(){button.textContent='✓';setTimeout(function(){button.textContent='⧉'},1200)})})});
 document.getElementById('retry').addEventListener('click',function(){show('form-view')});
 function renderLiveProgress(status){if(!status)return;liveProgress=status;window.__activeStep=Number.isInteger(status.step)?status.step:window.__activeStep||0;renderSteps(window.__activeStep);var title=document.getElementById('progress-title'),detail=document.getElementById('progress-detail');title.textContent=lang==='fa'?(status.titleFa||'نصب در حال اجراست'):(status.titleEn||'Installation is running');var text=lang==='fa'?(status.detailFa||''):(status.detailEn||'');if(status.deploymentStatus)text+=(text?' · ':'')+(lang==='fa'?'وضعیت: ':'Status: ')+status.deploymentStatus;if(status.attempt&&status.maxAttempts)text+=(text?' · ':'')+(lang==='fa'?'بررسی ':'Check ')+status.attempt+'/'+status.maxAttempts;detail.textContent=text||(lang==='fa'?'صفحه را نبندید؛ وضعیت واقعی Deployment نمایش داده می‌شود.':'Keep this page open; the live Deployment status appears here.')}
 async function responseJson(response){var text=await response.text();try{return JSON.parse(text)}catch(_){throw{error:{code:'INVALID_INSTALLER_RESPONSE',step:'installer-response',messageFa:'نصاب پاسخ JSON معتبر برنگرداند؛ نصب با شناسه وضعیت ادامه پیدا نکرد.',messageEn:'The installer did not return valid JSON, so no status identifier was received.',details:'HTTP '+response.status}}}}
 async function pollInstall(installId){var transient=0;for(var poll=0;poll<300;poll+=1){try{var response=await fetch('/api/install/status?id='+encodeURIComponent(installId),{cache:'no-store',credentials:'same-origin'});var status=await responseJson(response);if(!response.ok||!status.ok)throw status;transient=0;renderLiveProgress(status);if(status.state==='completed')return status.result;if(status.state==='failed')throw{error:status.error};}catch(error){if(error&&error.error)throw error;transient+=1;if(transient>12)throw{error:{code:'STATUS_UNREACHABLE',step:'deployment-status',messageFa:'ارتباط با وضعیت نصب پس از چند تلاش برقرار نشد.',messageEn:'Installation status remained unreachable after repeated attempts.'}};document.getElementById('progress-detail').textContent=lang==='fa'?'در حال اتصال دوباره به وضعیت نصب…':'Reconnecting to installation status…'}await new Promise(function(resolve){setTimeout(resolve,2000)})}throw{error:{code:'STATUS_TIMEOUT',step:'deployment-status',messageFa:'زمان پیگیری وضعیت نصب تمام شد.',messageEn:'Installation status tracking timed out.'}}}
 function showSuccess(data){window.__activeStep=stepDefs.length;renderSteps(stepDefs.length);document.getElementById('panel-url').textContent=data.panelUrl;document.getElementById('admin-password').textContent=data.adminPassword;document.getElementById('fork-repository').textContent=data.forkRepository;document.getElementById('workspace-name').textContent=(data.workspaceName||'—')+' · '+(data.workspaceMode||'');document.getElementById('network-route').textContent=(data.networkRoute&&data.networkRoute.label)||'—';document.getElementById('open-panel').href=data.panelUrl;document.getElementById('open-railway').href=data.railwayProjectUrl;document.getElementById('success-copy').textContent=lang==='fa'?'Deployment با موفقیت به پایان رسید و پنل آماده است. رمز ادمین را همین حالا ذخیره کنید.':'Deployment completed successfully and the panel is ready. Save the admin password now.';show('success-view')}
 document.getElementById('install-form').addEventListener('submit',async function(event){event.preventDefault();var ghInput=document.getElementById('github-token'),rwInput=document.getElementById('railway-token');var gh=ghInput.value.trim(),rw=rwInput.value.trim();if(gh.length<20||rw.length<20){document.getElementById('error-message').textContent=lang==='fa'?'هر دو توکن را کامل وارد کنید.':'Enter both complete tokens.';show('error-view');return}ghInput.value='';rwInput.value='';liveProgress={step:0,titleFa:'آغاز نصب ایمن',titleEn:'Starting secure installation'};show('progress-view');renderLiveProgress(liveProgress);try{var response=await fetch('/api/install/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({githubToken:gh,railwayToken:rw}),cache:'no-store',credentials:'same-origin'});gh='';rw='';var accepted=await responseJson(response);if(!response.ok||!accepted.ok||!accepted.installId)throw accepted;var data=await pollInstall(accepted.installId);showSuccess(data)}catch(error){gh='';rw='';var detail=error&&error.error?error.error:null;var base=detail?(lang==='fa'?detail.messageFa:detail.messageEn):(lang==='fa'?'خطای نامشخصی در نصب رخ داد.':'An unknown installation error occurred.');var meta=detail?' ['+(detail.step||'unknown')+' / '+(detail.code||'UNKNOWN')+(detail.requestId?' / '+detail.requestId:'')+']':'';var extra=detail&&detail.details?' '+detail.details:'';document.getElementById('error-message').textContent=base+extra+meta;show('error-view')}});
 applyTheme();applyLocale();show('form-view');
})();
</script>
</body>
</html>`;


const NETWORK_REFRESH_MS = 5 * 60 * 1000;
const INSTALL_JOB_TTL_MS = 15 * 60 * 1000;
const installJobs = new Map();

function safeMessage(error) {
  return error instanceof InstallError ? error.messageEn : "The installer encountered an internal error.";
}
let activeInstalls = 0;
let networkRefreshPromise = null;
let deploymentNetworkState = Object.freeze({
  status: "checking",
  checkedAt: null,
  selectedRoute: null,
  checks: [],
  error: null,
});

async function refreshDeploymentNetwork() {
  if (networkRefreshPromise) return networkRefreshPromise;
  networkRefreshPromise = (async () => {
    deploymentNetworkState = Object.freeze({
      status: "checking",
      checkedAt: deploymentNetworkState.checkedAt,
      selectedRoute: deploymentNetworkState.selectedRoute,
      checks: deploymentNetworkState.checks,
      error: null,
    });
    try {
      const result = await selectTransport();
      deploymentNetworkState = Object.freeze({
        status: "ready",
        checkedAt: new Date().toISOString(),
        selectedRoute: Object.freeze({
          kind: result.route.kind,
          label: routeLabel(result.route),
          latencyMs: result.selected.latencyMs,
        }),
        checks: Object.freeze(result.checks.map((item) => Object.freeze({ ...item }))),
        error: null,
      });
    } catch (error) {
      deploymentNetworkState = Object.freeze({
        status: "failed",
        checkedAt: new Date().toISOString(),
        selectedRoute: null,
        checks: Object.freeze((error?.networkChecks || []).map((item) => Object.freeze({ ...item }))),
        error: safeMessage(error),
      });
    }
    return deploymentNetworkState;
  })().finally(() => { networkRefreshPromise = null; });
  return networkRefreshPromise;
}

function publicNetworkState() {
  return {
    status: deploymentNetworkState.status,
    checkedAt: deploymentNetworkState.checkedAt,
    selectedRoute: deploymentNetworkState.selectedRoute,
    checks: deploymentNetworkState.checks,
    error: deploymentNetworkState.error,
  };
}

function nodeHeaders(req) {
  const headers = new Headers();
  for (const [name, value] of Object.entries(req.headers)) {
    if (Array.isArray(value)) value.forEach((item) => headers.append(name, item));
    else if (value !== undefined) headers.set(name, value);
  }
  return headers;
}

function publicRequestUrl(req) {
  const forwardedProto = String(req.headers["x-forwarded-proto"] || "").split(",")[0].trim();
  const proto = forwardedProto || (req.socket.encrypted ? "https" : "http");
  const host = String(req.headers["x-forwarded-host"] || req.headers.host || "localhost").split(",")[0].trim();
  return `${proto}://${host}${req.url || "/"}`;
}

async function readNodeBody(req) {
  const parts = [];
  let size = 0;
  for await (const part of req) {
    size += part.length;
    if (size > MAX_BODY_BYTES) throw new InstallError("REQUEST_TOO_LARGE", "request", "Request body is too large.", "درخواست بیش از حد بزرگ است.", 413);
    parts.push(part);
  }
  return Buffer.concat(parts);
}

async function sendWebResponse(res, response) {
  res.statusCode = response.status;
  response.headers.forEach((value, name) => res.setHeader(name, value));
  res.end(Buffer.from(await response.arrayBuffer()));
}

function sendJson(res, status, value, extraHeaders = {}) {
  const body = Buffer.from(JSON.stringify(value));
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": String(body.length),
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    ...extraHeaders,
  });
  res.end(body);
}

async function nodeHandler(req, res) {
  try {
    const url = new URL(publicRequestUrl(req));
    if (req.method === "GET" && url.pathname === "/health") {
      const state = publicNetworkState();
      return sendJson(res, state.status === "ready" ? 200 : 503, state);
    }
    if (req.method === "GET" && url.pathname === "/api/network") {
      return sendJson(res, 200, publicNetworkState());
    }
    if (req.method === "POST" && url.pathname === "/api/network/refresh") {
      const state = await refreshDeploymentNetwork();
      return sendJson(res, state.status === "ready" ? 200 : 503, publicNetworkState());
    }
    if (req.method === "GET" && url.pathname === "/") {
      return sendWebResponse(res, htmlResponse());
    }
    if (req.method === "GET" && url.pathname === "/api/install/status") {
      cleanInstallJobs();
      const installId = String(url.searchParams.get("id") || "");
      const job = /^[A-Za-z0-9_-]{20,80}$/.test(installId) ? installJobs.get(installId) : null;
      if (!job) return sendJson(res, 404, { ok: false, error: { code: "INSTALL_NOT_FOUND", step: "deployment-status", messageFa: "شناسه نصب پیدا نشد یا منقضی شده است.", messageEn: "The installation identifier was not found or has expired." } });
      const { updatedAtMs, ...visible } = job;
      return sendJson(res, 200, { ok: true, installId, ...visible });
    }
    if (req.method === "POST" && url.pathname === "/api/install/start") {
      if (activeInstalls >= 4) return sendJson(res, 429, { ok: false, error: { code: "BUSY", step: "request", messageFa: "نصاب مشغول است؛ کمی بعد دوباره تلاش کنید.", messageEn: "The installer is busy. Try again shortly." } }, { "retry-after": "15" });
      const body = await readNodeBody(req);
      const request = new Request(url, { method: "POST", headers: nodeHeaders(req), body });
      const payload = await parseInstallRequest(request);
      validateTokenShape(payload && payload.githubToken, "github");
      validateTokenShape(payload && payload.railwayToken, "railway");
      const installId = startInstallJob(payload);
      return sendJson(res, 202, { ok: true, accepted: true, installId, statusUrl: "/api/install/status?id=" + encodeURIComponent(installId) });
    }
    if (req.method === "POST" && url.pathname === "/api/install") {
      if (activeInstalls >= 4) return sendJson(res, 429, { ok: false, code: "BUSY", message: "Installer is busy. Try again shortly." }, { "retry-after": "15" });
      const body = await readNodeBody(req);
      const request = new Request(url, { method: "POST", headers: nodeHeaders(req), body });
      activeInstalls += 1;
      try { return sendWebResponse(res, await handleInstall(request)); }
      finally { activeInstalls -= 1; }
    }
    return sendJson(res, 404, { ok: false, code: "NOT_FOUND", message: "Not found" });
  } catch (error) {
    const detail = installErrorDetail(error);
    console.error(`[install:${detail.requestId}] code=${detail.code} step=${detail.step}` + (detail.details ? ` details=${detail.details}` : ""));
    return sendJson(res, error instanceof InstallError ? error.status : 500, { ok: false, error: detail });
  }
}

export function createInstallerServer() {
  const server = http.createServer(nodeHandler);
  server.requestTimeout = 360_000;
  server.headersTimeout = 15_000;
  server.keepAliveTimeout = 5_000;
  return server;
}

export const __test = {
  HTTP_PROXIES,
  PROXY_PROBE_TIMEOUT_MS,
  DIRECT_PROBE_TIMEOUT_MS,
  NETWORK_SELECTION_TIMEOUT_MS,
  responseIsComplete,
  collectHttpResponse,
  decodeChunked,
  installPayload,
  htmlResponse,
  proxyFetch,
  directFetch,
  routeFetch,
  probeRoute,
  selectTransport,
  selectAuthenticatedTransport,
  ensureWorkspace,
  railwayProjectName,
  deploymentPollDelayMs,
  publicProgress,
  startInstallJob,
  installJobs,
  routeLabel,
  refreshDeploymentNetwork,
  publicNetworkState,
  nodeHandler,
};

async function start() {
  const port = Number.parseInt(process.env.PORT || "3000", 10);
  const server = createInstallerServer();
  server.listen(port, "0.0.0.0", () => {
    console.log(`Lumen Railway installer v28 listening on ${port}`);
    void refreshDeploymentNetwork();
  });
  const timer = setInterval(() => { void refreshDeploymentNetwork(); }, NETWORK_REFRESH_MS);
  timer.unref();
}

let isMain = false;
try {
  isMain = Boolean(process.argv[1]) && realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
} catch (_) {}
if (isMain) void start();
