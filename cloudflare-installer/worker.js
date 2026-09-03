import net from "node:net";
import tls from "node:tls";

/*
 * Lumen public one-file Cloudflare Worker installer — v20.0.0
 * Every user deploys this same file in their own Cloudflare Workers account.
 * Requires a Workers compatibility date of 2026-08-04 or later for node:net/node:tls.
 * It does not use KV, D1, Durable Objects, Cache API, analytics, or console logs.
 */

const SOURCE_OWNER = "highisabella52213";
const SOURCE_REPO = "Lumen-Project-Final";
const SOURCE_FULL = SOURCE_OWNER + "/" + SOURCE_REPO;
const GITHUB_API = "https://api.github.com";
const RAILWAY_API = "https://backboard.railway.com/graphql/v2";
const INSTALLER_VERSION = "20.0.0";
const MAX_BODY_BYTES = 24 * 1024;
const MAX_UPSTREAM_BYTES = 4 * 1024 * 1024;
const HTTP_PROXY = Object.freeze({ hostname: "176.111.37.216", port: 39811 });
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

function openProxyTunnel(targetHostname, timeoutMs) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let handshake = Buffer.alloc(0);
    const raw = net.createConnection({ host: HTTP_PROXY.hostname, port: HTTP_PROXY.port });
    const fail = (error) => {
      if (settled) return;
      settled = true;
      try { raw.destroy(); } catch (_) {}
      reject(error instanceof InstallError ? error : transportError("HTTP_PROXY_UNAVAILABLE", "The configured HTTP proxy could not establish a secure connection.", "پروکسی HTTP تنظیم‌شده نتوانست اتصال امن را برقرار کند."));
    };
    raw.setNoDelay(true);
    raw.setTimeout(timeoutMs, () => fail(transportError("HTTP_PROXY_TIMEOUT", "The configured HTTP proxy timed out.", "زمان انتظار پروکسی HTTP تنظیم‌شده به پایان رسید.", 504)));
    raw.once("error", fail);
    raw.once("connect", () => {
      raw.write("CONNECT " + targetHostname + ":443 HTTP/1.1\r\nHost: " + targetHostname + ":443\r\nProxy-Connection: keep-alive\r\nUser-Agent: Lumen-Installer-Proxy/20\r\n\r\n");
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
      const secure = tls.connect({ socket: raw, servername: targetHostname, rejectUnauthorized: true, ALPNProtocols: ["http/1.1"] });
      secure.setTimeout(timeoutMs, () => {
        try { secure.destroy(); } catch (_) {}
      });
      secure.once("error", fail);
      secure.once("secureConnect", () => {
        if (settled) return;
        if (!secure.authorized || (secure.alpnProtocol && secure.alpnProtocol !== "http/1.1")) {
          return fail(transportError("UPSTREAM_TLS_FAILED", "The secure connection through the proxy could not be verified.", "اتصال امن از داخل پروکسی قابل تأیید نبود."));
        }
        settled = true;
        secure.off("error", fail);
        resolve(secure);
      });
    };
    raw.on("data", onData);
  });
}

function collectHttpResponse(socket, timeoutMs) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    let settled = false;
    const fail = (error) => {
      if (settled) return;
      settled = true;
      try { socket.destroy(); } catch (_) {}
      reject(error);
    };
    const timer = setTimeout(() => fail(transportError("UPSTREAM_TIMEOUT", "A remote service took too long to respond through the HTTP proxy.", "پاسخ سرویس مقصد از داخل پروکسی بیش از حد طول کشید.", 504)), timeoutMs);
    socket.on("data", (chunk) => {
      const part = Buffer.from(chunk); total += part.length;
      if (total > MAX_UPSTREAM_BYTES + 64 * 1024) return fail(transportError("UPSTREAM_RESPONSE_TOO_LARGE", "A remote service returned too much data.", "حجم پاسخ سرویس مقصد بیش از حد مجاز بود."));
      chunks.push(part);
    });
    socket.once("error", () => fail(transportError("UPSTREAM_UNAVAILABLE", "A remote service could not be reached through the HTTP proxy.", "ارتباط با سرویس مقصد از داخل پروکسی برقرار نشد.")));
    socket.once("timeout", () => fail(transportError("UPSTREAM_TIMEOUT", "A remote service took too long to respond through the HTTP proxy.", "پاسخ سرویس مقصد از داخل پروکسی بیش از حد طول کشید.", 504)));
    socket.once("end", () => {
      if (settled) return;
      settled = true; clearTimeout(timer);
      resolve(Buffer.concat(chunks, total));
    });
  });
}

async function proxyFetch(url, options = {}, timeoutMs = 18000) {
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
    socket = await openProxyTunnel(target.hostname, timeoutMs);
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

async function fetchWithTimeout(url, options, timeoutMs = 18000) {
  try {
    // Tests inject a private transport; production always uses the enforced HTTP proxy.
    const testTransport = globalThis.__LUMEN_TEST_FETCH__;
    if (typeof testTransport === "function") return await testTransport(url, { ...options, redirect: "error" });
    return await proxyFetch(url, options, timeoutMs);
  } catch (error) {
    if (error instanceof InstallError) throw error;
    throw transportError("UPSTREAM_UNAVAILABLE", "A remote service could not be reached through the configured HTTP proxy.", "ارتباط با سرویس مقصد از طریق پروکسی HTTP تنظیم‌شده برقرار نشد.");
  }
}

function githubError(status, step) {
  if (status === 401) return new InstallError("GITHUB_TOKEN_INVALID", step, "The GitHub token is invalid or expired.", "توکن GitHub نامعتبر یا منقضی است.", 401);
  if (status === 403) return new InstallError("GITHUB_PERMISSION", step, "GitHub denied this action. Create a classic token with the public_repo scope and check rate limits.", "GitHub این عملیات را رد کرد. توکن کلاسیک را با دسترسی public_repo بسازید و محدودیت درخواست را بررسی کنید.", 403);
  if (status === 422) return new InstallError("GITHUB_CONFLICT", step, "GitHub could not create the fork. A repository with the same name may already exist.", "GitHub نتوانست فورک را بسازد؛ ممکن است مخزنی هم‌نام از قبل وجود داشته باشد.", 409);
  return new InstallError("GITHUB_API_ERROR", step, "GitHub could not complete this step.", "GitHub نتوانست این مرحله را انجام دهد.", 502);
}

async function github(token, path, options = {}) {
  const response = await fetchWithTimeout(GITHUB_API + path, {
    method: options.method || "GET",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "User-Agent": "Lumen-Cloudflare-Installer/20",
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

async function ensureFork(githubToken, login) {
  const encodedLogin = encodeURIComponent(login);
  let repo = await github(githubToken, "/repos/" + encodedLogin + "/" + SOURCE_REPO, { allow404: true, step: "fork" });
  if (repo) {
    const parent = repo.parent && repo.parent.full_name ? String(repo.parent.full_name) : "";
    if (!repo.fork || parent.toLowerCase() !== SOURCE_FULL.toLowerCase()) {
      throw new InstallError("FORK_NAME_CONFLICT", "fork", "Your account already has a repository named " + SOURCE_REPO + " that is not a fork of the official source. Rename or remove it, then retry.", "در حساب شما مخزنی با نام " + SOURCE_REPO + " وجود دارد که فورک سورس رسمی نیست. نام آن را تغییر دهید یا حذف کنید و دوباره تلاش کنید.", 409);
    }
    return repo;
  }

  await github(githubToken, "/repos/" + SOURCE_FULL + "/forks", {
    method: "POST",
    body: { default_branch_only: true },
    step: "fork",
  });

  for (let attempt = 0; attempt < 18; attempt += 1) {
    await wait(1400 + Math.min(attempt, 5) * 250);
    repo = await github(githubToken, "/repos/" + encodedLogin + "/" + SOURCE_REPO, { allow404: true, step: "fork" });
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

async function railway(token, query, variables, step) {
  const response = await fetchWithTimeout(RAILWAY_API, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      "User-Agent": "Lumen-Cloudflare-Installer/20",
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
    const messages = result.errors.map((item) => String(item && item.message ? item.message : "")).join(" ").toLowerCase();
    if (messages.includes("github") || messages.includes("repository") || messages.includes("repo")) {
      throw new InstallError("RAILWAY_GITHUB_NOT_CONNECTED", step, "Railway cannot access the fork. Connect GitHub in Railway Account → Integrations, grant access to the fork, then retry.", "Railway به فورک دسترسی ندارد. در Railway از Account ← Integrations، گیت‌هاب را متصل و دسترسی فورک را فعال کنید، سپس دوباره تلاش کنید.", 409);
    }
    if (messages.includes("limit") || messages.includes("plan") || messages.includes("volume")) {
      throw new InstallError("RAILWAY_PLAN_LIMIT", step, "A Railway plan or resource limit blocked this step. Check your account usage and project limits.", "محدودیت پلن یا منابع Railway مانع این مرحله شد. مصرف حساب و محدودیت‌های پروژه را بررسی کنید.", 409);
    }
    throw new InstallError("RAILWAY_GRAPHQL_ERROR", step, "Railway rejected the " + step + " step. Check account access and try again.", "Railway مرحله «" + step + "» را رد کرد. دسترسی حساب را بررسی و دوباره تلاش کنید.", 502);
  }
  return result.data || {};
}

async function provisionRailway(railwayToken, githubToken, fork, branch, adminPassword) {
  await railway(railwayToken, "query InstallerIdentity { me { id name email } }", {}, "railway-token");

  const projectName = "Lumen " + String(fork.owner.login).slice(0, 20) + " " + new Date().toISOString().slice(0, 10);
  const created = await railway(
    railwayToken,
    "mutation InstallerProject($input: ProjectCreateInput!) { projectCreate(input: $input) { id name environments { edges { node { id name } } } } }",
    { input: { name: projectName, description: "Lumen installed by the public one-file Cloudflare setup", defaultEnvironmentName: "production", prDeploys: false } },
    "project"
  );
  const project = created.projectCreate;
  if (!project || !project.id) throw new InstallError("PROJECT_CREATE_FAILED", "project", "Railway did not return the new project.", "Railway پروژه جدید را برنگرداند.", 502);

  let environment = project.environments && project.environments.edges && project.environments.edges[0] ? project.environments.edges[0].node : null;
  if (!environment || !environment.id) {
    const loaded = await railway(
      railwayToken,
      "query InstallerProjectEnvironment($id: String!) { project(id: $id) { environments { edges { node { id name } } } } }",
      { id: project.id },
      "environment"
    );
    environment = loaded.project && loaded.project.environments && loaded.project.environments.edges && loaded.project.environments.edges[0] ? loaded.project.environments.edges[0].node : null;
  }
  if (!environment || !environment.id) throw new InstallError("ENVIRONMENT_MISSING", "environment", "Railway did not create the production environment.", "Railway محیط production را ایجاد نکرد.", 502);

  const variables = {
    ADMIN_PASSWORD: adminPassword,
    SECRET_KEY: randomSecret(48),
    DATA_DIR: "/data",
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

  const serviceResult = await railway(
    railwayToken,
    "mutation InstallerService($input: ServiceCreateInput!) { serviceCreate(input: $input) { id name } }",
    { input: { projectId: project.id, name: "Lumen", source: { repo: String(fork.full_name) }, branch, variables, skipInitialDeploys: true } },
    "service"
  );
  const service = serviceResult.serviceCreate;
  if (!service || !service.id) throw new InstallError("SERVICE_CREATE_FAILED", "service", "Railway did not return the new service.", "Railway سرویس جدید را برنگرداند.", 502);

  await railway(
    railwayToken,
    "mutation InstallerServiceSettings($serviceId: String!, $environmentId: String!, $input: ServiceInstanceUpdateInput!) { serviceInstanceUpdate(serviceId: $serviceId, environmentId: $environmentId, input: $input) }",
    { serviceId: service.id, environmentId: environment.id, input: { startCommand: "python main.py", healthcheckPath: "/health", healthcheckTimeout: 300 } },
    "service-settings"
  );

  await railway(
    railwayToken,
    "mutation InstallerVolume($input: VolumeCreateInput!) { volumeCreate(input: $input) { id name } }",
    { input: { projectId: project.id, serviceId: service.id, environmentId: environment.id, mountPath: "/data" } },
    "volume"
  );

  const domainResult = await railway(
    railwayToken,
    "mutation InstallerDomain($input: ServiceDomainCreateInput!) { serviceDomainCreate(input: $input) { domain } }",
    { input: { serviceId: service.id, environmentId: environment.id, targetPort: 8000 } },
    "domain"
  );
  const domain = domainResult.serviceDomainCreate && domainResult.serviceDomainCreate.domain ? String(domainResult.serviceDomainCreate.domain) : "";
  if (!/^[a-z0-9.-]+$/i.test(domain)) throw new InstallError("DOMAIN_CREATE_FAILED", "domain", "Railway did not return a valid public domain.", "Railway دامنه عمومی معتبری برنگرداند.", 502);

  const deployResult = await railway(
    railwayToken,
    "mutation InstallerDeploy($serviceId: String!, $environmentId: String!) { serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId) }",
    { serviceId: service.id, environmentId: environment.id },
    "deploy"
  );
  const deploymentId = String(deployResult.serviceInstanceDeployV2 || "");
  let deploymentStatus = "QUEUED";
  if (deploymentId) {
    for (let attempt = 0; attempt < 4; attempt += 1) {
      await wait(1800);
      try {
        const checked = await railway(railwayToken, "query InstallerDeployment($id: String!) { deployment(id: $id) { id status } }", { id: deploymentId }, "deployment-status");
        deploymentStatus = checked.deployment && checked.deployment.status ? String(checked.deployment.status) : deploymentStatus;
        if (["SUCCESS", "FAILED", "CRASHED"].includes(deploymentStatus)) break;
      } catch (_) {
        break;
      }
    }
  }

  return {
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

async function installPayload(payload) {
  let githubToken = validateTokenShape(payload && payload.githubToken, "github");
  let railwayToken = validateTokenShape(payload && payload.railwayToken, "railway");
  try {
    const identity = await github(githubToken, "/user", { step: "github-token" });
    const login = identity && identity.login ? String(identity.login) : "";
    if (!/^[A-Za-z0-9-]{1,39}$/.test(login)) throw new InstallError("GITHUB_IDENTITY", "github-token", "GitHub did not return a valid account.", "GitHub حساب معتبری برنگرداند.", 502);

    await github(githubToken, "/user/starred/" + SOURCE_FULL, { method: "PUT", step: "star" });
    const fork = await ensureFork(githubToken, login);
    const branch = String(fork.default_branch || "main");
    const commit = await github(githubToken, "/repos/" + encodeURIComponent(login) + "/" + SOURCE_REPO + "/commits/" + encodeURIComponent(branch), { step: "fork" });
    if (!commit || !/^[0-9a-f]{40}$/i.test(String(commit.sha || ""))) throw new InstallError("FORK_COMMIT", "fork", "The fork has no deployable branch commit yet.", "فورک هنوز کامیت قابل دیپلوی ندارد.", 502);

    const adminPassword = randomSecret(18);
    const railwayResult = await provisionRailway(railwayToken, githubToken, fork, branch, adminPassword);
    return {
      ok: true,
      installerVersion: INSTALLER_VERSION,
      source: SOURCE_FULL,
      forkUrl: String(fork.html_url || ("https://github.com/" + fork.full_name)),
      forkRepository: String(fork.full_name),
      branch,
      adminPassword,
      ...railwayResult,
    };
  } finally {
    githubToken = "";
    railwayToken = "";
  }
}

async function handleInstall(request) {
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
  return installPayload(payload);
}

const worker = {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/") return htmlResponse();
    if (request.method === "POST" && url.pathname === "/api/install") {
      const requestId = randomSecret(8);
      try {
        const result = await handleInstall(request);
        return jsonResponse({ ...result, requestId });
      } catch (error) {
        const safe = error instanceof InstallError ? error : new InstallError("INSTALL_FAILED", "unknown", "Installation could not be completed.", "نصب کامل نشد.", 500);
        return jsonResponse({ ok: false, requestId, error: { code: safe.code, step: safe.step, messageEn: safe.messageEn, messageFa: safe.messageFa } }, safe.status);
      }
    }
    return jsonResponse({ ok: false, error: { code: "NOT_FOUND", messageEn: "Not found", messageFa: "یافت نشد" } }, 404);
  },
};

export const __test = { installPayload, handleInstall, randomSecret, htmlResponse, proxyFetch, decodeChunked };
export default worker;

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
  <div><div class="eyebrow"><span aria-hidden="true">✦</span><span data-fa="نصاب عمومی Lumen · نسخه ۲۰" data-en="Public Lumen installer · v20">نصاب عمومی Lumen · نسخه ۲۰</span></div><h1 id="hero-title" data-fa="نصب Lumen روی Railway" data-en="Install Lumen on Railway">نصب Lumen روی Railway</h1><p data-fa="فقط دو توکن را وارد کنید. نصاب مخزن رسمی را فورک می‌کند، فضای دائمی و تنظیمات Railway را می‌سازد و لینک پنل را تحویل می‌دهد." data-en="Enter two tokens. The installer forks the official repository, configures persistent storage and Railway, deploys the service, and returns the panel URL.">فقط دو توکن را وارد کنید. نصاب مخزن رسمی را فورک می‌کند، فضای دائمی و تنظیمات Railway را می‌سازد و لینک پنل را تحویل می‌دهد.</p></div>
  <div class="source-card"><div class="source-label" data-fa="سورس ثابت و رسمی" data-en="Fixed official source">سورس ثابت و رسمی</div><div class="source-name">highisabella52213/Lumen-Project-Final</div><div class="source-meta"><span class="chip">WS only</span><span class="chip">Railway</span><span class="chip">v20</span><span class="chip">HTTP proxy</span></div></div>
 </section>
 <section class="panel">
  <div class="view" id="form-view">
   <div class="panel-head"><div class="step-number">01</div><div><h2 data-fa="دسترسی‌های نصب" data-en="Installation access">دسترسی‌های نصب</h2><p class="muted" data-fa="Worker توکن‌ها را نگه‌داری یا لاگ نمی‌کند؛ پس از بررسی، آن‌ها داخل متغیرهای محافظت‌شده Railway خودتان ثبت می‌شوند." data-en="The Worker never persists or logs tokens; after verification, they are stored in your own protected Railway service variables.">Worker توکن‌ها را نگه‌داری یا لاگ نمی‌کند؛ پس از بررسی، آن‌ها داخل متغیرهای محافظت‌شده Railway خودتان ثبت می‌شوند.</p></div></div>
   <form id="install-form" novalidate>
    <div class="field"><div class="field-top"><label for="github-token" data-fa="توکن GitHub" data-en="GitHub token">توکن GitHub</label><a class="direct-link" href="https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Cloudflare%20Installer" target="_blank" rel="noopener noreferrer" data-fa="ساخت مستقیم ↗" data-en="Create token ↗">ساخت مستقیم ↗</a></div><div class="input-wrap"><input id="github-token" type="password" required autocomplete="new-password" spellcheck="false" aria-describedby="github-help"><button class="reveal" type="button" data-reveal="github-token" aria-label="Show or hide GitHub token">◉</button></div><small class="support" id="github-help" data-fa="توکن کلاسیک با دسترسی public_repo؛ برای فورک و استار مخزن عمومی." data-en="Classic token with public_repo scope, used to fork and star the public source.">توکن کلاسیک با دسترسی public_repo؛ برای فورک و استار مخزن عمومی.</small></div>
    <div class="field"><div class="field-top"><label for="railway-token" data-fa="توکن حساب Railway" data-en="Railway account token">توکن حساب Railway</label><a class="direct-link" href="https://railway.com/account/tokens" target="_blank" rel="noopener noreferrer" data-fa="ساخت مستقیم ↗" data-en="Create token ↗">ساخت مستقیم ↗</a></div><div class="input-wrap"><input id="railway-token" type="password" required autocomplete="new-password" spellcheck="false" aria-describedby="railway-help"><button class="reveal" type="button" data-reveal="railway-token" aria-label="Show or hide Railway token">◉</button></div><small class="support" id="railway-help" data-fa="Account Token لازم است؛ Project Token نمی‌تواند پروژه جدید بسازد." data-en="An Account Token is required; a Project Token cannot create a new project.">Account Token لازم است؛ Project Token نمی‌تواند پروژه جدید بسازد.</small></div>
    <div class="guide" aria-label="Preparation guide">
     <div class="guide-row"><div class="guide-icon">1</div><div class="guide-copy"><b data-fa="توکن GitHub را بسازید" data-en="Create GitHub token">توکن GitHub را بسازید</b><span data-fa="لینک بالا با public_repo آماده است" data-en="The link above preselects public_repo">لینک بالا با public_repo آماده است</span></div><a href="https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Cloudflare%20Installer" target="_blank" rel="noopener noreferrer" aria-label="Open GitHub token page">↗</a></div>
     <div class="guide-row"><div class="guide-icon">2</div><div class="guide-copy"><b data-fa="Account Token ریلوی را بسازید" data-en="Create Railway Account Token">Account Token ریلوی را بسازید</b><span data-fa="از صفحه Tokens در تنظیمات حساب" data-en="From the Tokens page in account settings">از صفحه Tokens در تنظیمات حساب</span></div><a href="https://railway.com/account/tokens" target="_blank" rel="noopener noreferrer" aria-label="Open Railway token page">↗</a></div>
     <div class="guide-row"><div class="guide-icon">3</div><div class="guide-copy"><b data-fa="GitHub را به Railway متصل کنید" data-en="Connect GitHub to Railway">GitHub را به Railway متصل کنید</b><span data-fa="اجازه دسترسی به فورک Lumen را بدهید" data-en="Grant Railway access to the Lumen fork">اجازه دسترسی به فورک Lumen را بدهید</span></div><a href="https://railway.com/account/integrations" target="_blank" rel="noopener noreferrer" aria-label="Open Railway integrations">↗</a></div>
    </div>
    <div class="notice"><span aria-hidden="true">◆</span><span data-fa="این فایل برای استفاده عمومی است، اما هر شخص باید نسخه خودش را در حساب Cloudflare خودش دیپلوی کند. درخواست‌های GitHub و Railway فقط از تونل TLS داخل پروکسی ثابت عبور می‌کنند. هرگز توکن را در Worker متعلق به شخص دیگری وارد نکنید." data-en="This file is public, but every user must deploy a personal copy in their own Cloudflare account. GitHub and Railway requests use TLS inside the enforced proxy tunnel. Never enter tokens into another person's Worker.">این فایل برای استفاده عمومی است، اما هر شخص باید نسخه خودش را در حساب Cloudflare خودش دیپلوی کند. درخواست‌های GitHub و Railway فقط از تونل TLS داخل پروکسی ثابت عبور می‌کنند. هرگز توکن را در Worker متعلق به شخص دیگری وارد نکنید.</span></div>
    <button class="filled" id="install-button" type="submit"><span aria-hidden="true">✦</span><span data-fa="شروع نصب خودکار" data-en="Start automated setup">شروع نصب خودکار</span></button>
   </form>
  </div>
  <div class="view" id="progress-view" hidden aria-live="polite"><div class="progress-head"><div class="spinner" aria-hidden="true"></div><h2 data-fa="ستاپ در حال اجراست" data-en="Setup is running">ستاپ در حال اجراست</h2><p class="muted" data-fa="صفحه را نبندید؛ ساخت فورک و دیپلوی ممکن است چند دقیقه زمان ببرد." data-en="Keep this page open. Fork creation and deployment may take a few minutes.">صفحه را نبندید؛ ساخت فورک و دیپلوی ممکن است چند دقیقه زمان ببرد.</p></div><div class="steps" id="steps"></div></div>
  <div class="view" id="success-view" hidden aria-live="polite"><div class="success-mark">✓</div><h2 data-fa="پنل آماده شد" data-en="Your panel is ready">پنل آماده شد</h2><p class="muted" id="success-copy"></p><div class="result"><div class="result-row"><div><label data-fa="لینک پنل مدیریت" data-en="Management panel URL">لینک پنل مدیریت</label><code id="panel-url"></code></div><button class="copy" type="button" data-copy="panel-url" aria-label="Copy panel URL">⧉</button></div><div class="result-row"><div><label data-fa="رمز ادمین — فقط همین‌بار نمایش داده می‌شود" data-en="Admin password — shown once">رمز ادمین — فقط همین‌بار نمایش داده می‌شود</label><code id="admin-password"></code></div><button class="copy" type="button" data-copy="admin-password" aria-label="Copy admin password">⧉</button></div><div class="result-row"><div><label data-fa="فورک شما" data-en="Your fork">فورک شما</label><code id="fork-repository"></code></div><button class="copy" type="button" data-copy="fork-repository" aria-label="Copy fork repository">⧉</button></div></div><div class="actions"><a class="filled" id="open-panel" target="_blank" rel="noopener noreferrer" data-fa="باز کردن پنل" data-en="Open panel">باز کردن پنل</a><a class="tonal" id="open-railway" target="_blank" rel="noopener noreferrer" data-fa="نمایش در Railway" data-en="View in Railway">نمایش در Railway</a></div></div>
  <div class="view" id="error-view" hidden aria-live="assertive"><div class="error-mark">!</div><h2 data-fa="نصب متوقف شد" data-en="Setup stopped">نصب متوقف شد</h2><div class="error-box" id="error-message"></div><button class="tonal" id="retry" type="button" data-fa="بازگشت و تلاش دوباره" data-en="Go back and retry">بازگشت و تلاش دوباره</button></div>
 </section>
</main>
<div class="footer" data-fa="Lumen public one-file installer · بدون ذخیره توکن در Worker · HTTP proxy enforced" data-en="Lumen public one-file installer · no Worker token persistence · enforced HTTP proxy">Lumen public one-file installer · بدون ذخیره توکن در Worker · HTTP proxy enforced</div>
</div>
<script nonce="__NONCE__">
(function(){
 var lang=localStorage.getItem('lumen-installer-lang')||'fa';var theme=localStorage.getItem('lumen-installer-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');var progressTimer=null;
 var stepDefs=[['اتصال امن از طریق پروکسی و اعتبارسنجی توکن‌ها','Secure proxy connection and token validation'],['استار کردن سورس رسمی','Star official source'],['ساخت یا بررسی فورک','Create or verify fork'],['ساخت پروژه Railway','Create Railway project'],['تنظیم متغیرها و سرویس','Configure service and variables'],['اتصال فضای دائمی /data','Attach persistent /data'],['ساخت دامنه عمومی','Generate public domain'],['شروع دیپلوی','Start deployment']];
 function applyLocale(){document.documentElement.lang=lang;document.documentElement.dir=lang==='fa'?'rtl':'ltr';document.querySelectorAll('[data-fa]').forEach(function(el){el.textContent=el.getAttribute(lang==='fa'?'data-fa':'data-en')});document.querySelector('.lang-text').textContent=lang==='fa'?'EN':'فا';renderSteps(window.__activeStep||0)}
 function applyTheme(){document.documentElement.setAttribute('data-theme',theme)}
 function show(id){['form-view','progress-view','success-view','error-view'].forEach(function(name){document.getElementById(name).hidden=name!==id})}
 function renderSteps(active){var box=document.getElementById('steps');if(!box)return;box.innerHTML='';stepDefs.forEach(function(item,index){var row=document.createElement('div');row.className='progress-step '+(index<active?'done':index===active?'active':'');var dot=document.createElement('div');dot.className='step-dot';dot.textContent=index<active?'✓':String(index+1);var label=document.createElement('span');label.textContent=item[lang==='fa'?0:1];var state=document.createElement('small');state.textContent=index<active?(lang==='fa'?'انجام شد':'Done'):index===active?(lang==='fa'?'در حال انجام':'Working'):'—';row.append(dot,label,state);box.appendChild(row)})}
 document.getElementById('language').addEventListener('click',function(){lang=lang==='fa'?'en':'fa';localStorage.setItem('lumen-installer-lang',lang);applyLocale()});
 document.getElementById('theme').addEventListener('click',function(){theme=theme==='dark'?'light':'dark';localStorage.setItem('lumen-installer-theme',theme);applyTheme()});
 document.querySelectorAll('[data-reveal]').forEach(function(button){button.addEventListener('click',function(){var input=document.getElementById(button.getAttribute('data-reveal'));input.type=input.type==='password'?'text':'password'})});
 document.querySelectorAll('[data-copy]').forEach(function(button){button.addEventListener('click',function(){var text=document.getElementById(button.getAttribute('data-copy')).textContent;navigator.clipboard.writeText(text).then(function(){button.textContent='✓';setTimeout(function(){button.textContent='⧉'},1200)})})});
 document.getElementById('retry').addEventListener('click',function(){show('form-view')});
 document.getElementById('install-form').addEventListener('submit',async function(event){event.preventDefault();var ghInput=document.getElementById('github-token'),rwInput=document.getElementById('railway-token');var gh=ghInput.value.trim(),rw=rwInput.value.trim();if(gh.length<20||rw.length<20){document.getElementById('error-message').textContent=lang==='fa'?'هر دو توکن را کامل وارد کنید.':'Enter both complete tokens.';show('error-view');return}ghInput.value='';rwInput.value='';show('progress-view');window.__activeStep=0;renderSteps(0);progressTimer=setInterval(function(){if(window.__activeStep<7){window.__activeStep+=1;renderSteps(window.__activeStep)}},3500);try{var response=await fetch('/api/install',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({githubToken:gh,railwayToken:rw}),cache:'no-store',credentials:'same-origin'});gh='';rw='';var data=await response.json();clearInterval(progressTimer);if(!response.ok||!data.ok)throw data;window.__activeStep=8;renderSteps(8);document.getElementById('panel-url').textContent=data.panelUrl;document.getElementById('admin-password').textContent=data.adminPassword;document.getElementById('fork-repository').textContent=data.forkRepository;document.getElementById('open-panel').href=data.panelUrl;document.getElementById('open-railway').href=data.railwayProjectUrl;document.getElementById('success-copy').textContent=lang==='fa'?'دیپلوی شروع شده است. اگر پنل فوراً باز نشد، ۱ تا ۳ دقیقه صبر کنید. رمز ادمین را همین حالا ذخیره کنید.':'Deployment has started. If the panel is not ready yet, wait 1–3 minutes. Save the admin password now.';show('success-view')}catch(error){clearInterval(progressTimer);gh='';rw='';var detail=error&&error.error?error.error:null;document.getElementById('error-message').textContent=detail?(lang==='fa'?detail.messageFa:detail.messageEn):(lang==='fa'?'خطای شبکه رخ داد. اتصال را بررسی کنید و دوباره تلاش کنید.':'A network error occurred. Check your connection and retry.');show('error-view')}});
 applyTheme();applyLocale();show('form-view');
})();
</script>
</body>
</html>`;
