# pages.py  -  Lumen Relay UI v16
# contains: LOGIN_HTML, DASHBOARD_HTML, get_public_page_html()


LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lumen Relay · Sign in</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0E1213;--card:rgba(21,26,27,0.9);--accent:#189BAD;--text:#F2F3F3;--dim:#8C9192;--mid:#BFBFBF;--border:rgba(24,155,173,0.2)}
html,body{height:100%;overflow:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Inter','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:20px}
.bg{position:fixed;inset:0;background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(24,155,173,0.1),transparent 70%),var(--bg);z-index:0}
.grid{position:fixed;inset:0;background-image:linear-gradient(rgba(24,155,173,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(24,155,173,0.04) 1px,transparent 1px);background-size:44px 44px;z-index:0}
.orb{position:fixed;border-radius:50%;filter:blur(90px);z-index:0;animation:fl 9s ease-in-out infinite}
.o1{width:380px;height:380px;background:rgba(24,155,173,0.07);top:-100px;right:-80px}
.o2{width:280px;height:280px;background:rgba(18,160,139,0.04);bottom:-60px;left:-60px;animation-delay:4s}
@keyframes fl{0%,100%{transform:translateY(0)}50%{transform:translateY(-18px)}}
.wrap{position:relative;z-index:10;width:100%;max-width:400px}
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:38px 34px 34px;backdrop-filter:blur(24px);box-shadow:0 0 80px rgba(24,155,173,0.07),0 20px 60px rgba(0,0,0,.5)}
.brand{display:flex;align-items:center;gap:14px;margin-bottom:28px}
.brand-img{width:48px;height:48px;border-radius:50%;overflow:hidden;border:1px solid var(--border);box-shadow:0 0 20px rgba(168,53,28,0.35),0 0 12px rgba(24,155,173,0.3);flex-shrink:0}
.brand-img img{width:100%;height:100%;object-fit:cover}
.brand-name{font-size:16px;font-weight:700;color:var(--text)}
.brand-sub{font-size:11px;color:var(--dim);margin-top:2px}
h1{font-size:21px;font-weight:700;color:var(--text);margin-bottom:5px;letter-spacing:-.02em}
.sub{font-size:12px;color:var(--mid);margin-bottom:24px;line-height:1.6}
.hint{display:flex;align-items:center;gap:10px;background:rgba(24,155,173,0.07);border:1px solid rgba(24,155,173,0.15);border-radius:10px;padding:10px 14px;margin-bottom:20px}
.hint-label{font-size:11px;color:var(--dim);flex:1}
.hint-val{font-family:ui-monospace,monospace;font-size:14px;font-weight:700;color:var(--accent);background:rgba(24,155,173,0.1);border:1px solid rgba(24,155,173,0.25);padding:3px 11px;border-radius:7px;cursor:pointer;transition:.15s;letter-spacing:.08em}
.hint-val:hover{background:rgba(24,155,173,0.22)}
.field{margin-bottom:18px}
.field label{display:block;font-size:10.5px;font-weight:600;color:var(--mid);margin-bottom:7px;text-transform:uppercase;letter-spacing:.06em}
.inp-wrap{position:relative}
input[type=password]{width:100%;padding:13px 16px 13px 44px;border-radius:11px;border:1px solid var(--border);background:rgba(0,0,0,.3);color:var(--text);font-family:inherit;font-size:14px;outline:none;transition:.2s}
input[type=password]:focus{border-color:rgba(24,155,173,.55);background:rgba(0,0,0,.4);box-shadow:0 0 0 3px rgba(24,155,173,.1)}
.ic{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--dim);font-size:18px;pointer-events:none;transition:.2s}
input:focus+.ic{color:var(--accent)}
.err{display:none;background:rgba(179,58,34,.08);border:1px solid rgba(179,58,34,.2);border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:12px;color:#E08167;align-items:center;gap:8px}
.err.show{display:flex}
.btn{width:100%;padding:13px;border-radius:11px;border:none;cursor:pointer;background:linear-gradient(135deg,#12A2B5,#A8351C);color:#fff;font-family:inherit;font-size:14px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;box-shadow:0 4px 20px rgba(168,53,28,.35);transition:.2s;position:relative;overflow:hidden}
.btn::before{content:'';position:absolute;inset:0;background:rgba(255,255,255,.08);opacity:0;transition:.2s}
.btn:hover::before{opacity:1}
.btn:disabled{opacity:.5;cursor:not-allowed}
.footer{margin-top:22px;padding-top:18px;border-top:1px solid var(--border);display:flex;align-items:center;justify-content:center;gap:8px;font-size:11px;color:var(--dim)}
.footer a{color:var(--accent);font-weight:600;text-decoration:none;display:flex;align-items:center;gap:4px}
@keyframes spin{to{transform:rotate(360deg)}}

/* ============ UI refinement layer ============ */
:root{--ink-brick:#791B0D;--ink-teal:#0D6A78;--ink-grey:#BFBFBF}
html{-webkit-text-size-adjust:100%}
body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;font-feature-settings:'ss01','ss02';line-height:1.7}
::selection{background:rgba(24,155,173,.32)}
*::-webkit-scrollbar{width:10px;height:10px}
*::-webkit-scrollbar-track{background:transparent}
*::-webkit-scrollbar-thumb{background:rgba(191,191,191,.22);border-radius:99px;border:2px solid transparent;background-clip:content-box}
*::-webkit-scrollbar-thumb:hover{background:rgba(24,155,173,.45);background-clip:content-box}
a,button,input,select,textarea{font-family:inherit}
button,a,.chip,.nav-it,.proto-card,.tog{transition:background .18s ease,color .18s ease,border-color .18s ease,transform .18s ease,box-shadow .18s ease}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{outline:2px solid #189BAD;outline-offset:2px;border-radius:10px}

body{font-size:15px}
.card{border-radius:22px;padding:40px 34px 30px}
.brand{margin-bottom:26px;padding-bottom:20px;border-bottom:1px solid var(--border)}
.brand-name{font-size:17px;font-weight:800;letter-spacing:-.01em}
.brand-sub{font-size:12px;color:var(--mid);margin-top:4px}
h1{font-size:24px;font-weight:800;line-height:1.4;margin-bottom:8px}
.sub{font-size:13.5px;line-height:1.85;color:var(--mid);margin-bottom:28px}
.field label{font-size:12px;font-weight:600;letter-spacing:.02em;text-transform:none;color:var(--mid);margin-bottom:9px}
input[type=password]{padding:15px 46px 15px 16px;font-size:15px;border-radius:12px}
.btn{padding:15px;font-size:15px;font-weight:700;border-radius:12px;background:linear-gradient(135deg,#12889B,#0D6A78);box-shadow:0 8px 24px rgba(13,106,120,.38)}
.btn:hover{transform:translateY(-1px);box-shadow:0 12px 30px rgba(13,106,120,.42)}
.btn:active{transform:translateY(0)}
.footer{margin-top:26px;padding-top:18px;font-size:12px;gap:6px;color:var(--dim)}
.err{font-size:12.5px;line-height:1.7;border-radius:12px;padding:12px 14px}

/* ---- iCloud style activity spinner ---- */
.aspin{display:inline-block;position:relative;width:18px;height:18px;color:currentColor;vertical-align:-4px}
.aspin b{position:absolute;top:0;left:50%;width:2px;height:5px;margin-left:-1px;border-radius:2px;background:currentColor;transform-origin:1px 9px;animation:aspin-fade 1s linear infinite;opacity:.12}
.aspin b:nth-child(1){transform:rotate(0deg);animation-delay:-0.917s}
.aspin b:nth-child(2){transform:rotate(30deg);animation-delay:-0.833s}
.aspin b:nth-child(3){transform:rotate(60deg);animation-delay:-0.750s}
.aspin b:nth-child(4){transform:rotate(90deg);animation-delay:-0.667s}
.aspin b:nth-child(5){transform:rotate(120deg);animation-delay:-0.583s}
.aspin b:nth-child(6){transform:rotate(150deg);animation-delay:-0.500s}
.aspin b:nth-child(7){transform:rotate(180deg);animation-delay:-0.417s}
.aspin b:nth-child(8){transform:rotate(210deg);animation-delay:-0.333s}
.aspin b:nth-child(9){transform:rotate(240deg);animation-delay:-0.250s}
.aspin b:nth-child(10){transform:rotate(270deg);animation-delay:-0.167s}
.aspin b:nth-child(11){transform:rotate(300deg);animation-delay:-0.083s}
.aspin b:nth-child(12){transform:rotate(330deg);animation-delay:-0.000s}
@keyframes aspin-fade{0%{opacity:1}100%{opacity:.12}}
.aspin-lg{width:30px;height:30px}
.aspin-lg b{width:3px;height:8px;margin-left:-1.5px;transform-origin:1.5px 15px}
.aspin-box{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:40px 20px;color:var(--t3);font-size:12.5px}
@media(prefers-reduced-motion:reduce){.aspin b{animation:none;opacity:.45}}

/* Lumen sign-in · Material 3 Expressive */
:root{color-scheme:dark;--md-sys-color-primary:#BDC7FF;--md-sys-color-on-primary:#22305F;--md-sys-color-primary-container:#394777;--md-sys-color-on-primary-container:#DEE1FF;--md-sys-color-secondary-container:#47465C;--md-sys-color-on-secondary-container:#E4E1FA;--md-sys-color-tertiary:#F2B99A;--md-sys-color-tertiary-container:#6D3B22;--md-sys-color-on-tertiary-container:#FFDCC8;--md-sys-color-error-container:#93000A;--md-sys-color-on-error-container:#FFDAD6;--md-sys-color-surface:#111318;--md-sys-color-surface-container-low:#191B21;--md-sys-color-surface-container:#1D1F25;--md-sys-color-surface-container-high:#27292F;--md-sys-color-on-surface:#E3E2E9;--md-sys-color-on-surface-variant:#C6C5D0;--md-sys-color-outline:#90909B;--md-sys-color-outline-variant:#46464F;--md-sys-shape-corner-small:8px;--md-sys-shape-corner-large:16px;--md-sys-shape-corner-extra-large:28px;--md-sys-shape-corner-extra-large-increased:36px;--md-sys-shape-corner-full:999px;--md-sys-motion-easing-emphasized:cubic-bezier(.2,0,0,1);--md-sys-motion-easing-emphasized-decelerate:cubic-bezier(.05,.7,.1,1);--bg:var(--md-sys-color-surface);--card:var(--md-sys-color-surface-container-low);--accent:var(--md-sys-color-primary);--text:var(--md-sys-color-on-surface);--dim:var(--md-sys-color-outline);--mid:var(--md-sys-color-on-surface-variant);--border:var(--md-sys-color-outline-variant)}
body{font-family:'Inter','Vazirmatn','Segoe UI',sans-serif;background:var(--md-sys-color-surface);padding:28px;isolation:isolate}.bg{background:radial-gradient(circle at 15% 80%,color-mix(in srgb,var(--md-sys-color-tertiary) 19%,transparent),transparent 34rem),radial-gradient(circle at 82% 9%,color-mix(in srgb,var(--md-sys-color-primary) 22%,transparent),transparent 38rem),var(--md-sys-color-surface)}.grid{background-image:linear-gradient(color-mix(in srgb,var(--md-sys-color-outline-variant) 30%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--md-sys-color-outline-variant) 30%,transparent) 1px,transparent 1px);background-size:64px 64px;mask-image:linear-gradient(135deg,#000,transparent 74%)}.orb{filter:blur(80px);animation:md-orbit 14s var(--md-sys-motion-easing-emphasized) infinite alternate}.o1{width:42vw;height:42vw;background:color-mix(in srgb,var(--md-sys-color-primary) 12%,transparent);top:-18vw;right:-8vw}.o2{width:36vw;height:36vw;background:color-mix(in srgb,var(--md-sys-color-tertiary) 9%,transparent);bottom:-18vw;left:-8vw}@keyframes md-orbit{to{transform:translate3d(24px,-16px,0) scale(1.08)}}
.wrap{max-width:1040px;display:flex;justify-content:flex-end;position:relative}.wrap::before{content:'FAST · PRIVATE · CONTROLLED';position:absolute;left:0;top:50%;transform:translateY(-50%) rotate(-90deg);transform-origin:center;font-size:.69rem;font-weight:700;letter-spacing:.26em;color:var(--md-sys-color-outline)}.card{width:460px;min-height:570px;display:flex;flex-direction:column;justify-content:center;padding:54px 48px 44px;border:1px solid var(--md-sys-color-outline-variant);border-radius:var(--md-sys-shape-corner-extra-large-increased) var(--md-sys-shape-corner-extra-large-increased) var(--md-sys-shape-corner-extra-large-increased) 72px;background:color-mix(in srgb,var(--md-sys-color-surface-container-low) 94%,transparent);box-shadow:0 30px 90px rgba(4,6,14,.46),inset 0 1px 0 color-mix(in srgb,var(--md-sys-color-primary) 15%,transparent);backdrop-filter:blur(28px) saturate(1.15);animation:md-card-in 650ms var(--md-sys-motion-easing-emphasized-decelerate)}@keyframes md-card-in{from{opacity:0;transform:translateY(32px) scale(.96)}to{opacity:1;transform:none}}.card::before{content:'11';position:absolute;right:38px;top:34px;width:52px;height:52px;display:grid;place-items:center;border-radius:18px;background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);font-weight:800;box-shadow:0 12px 26px rgba(4,6,14,.22)}
.brand{border:0;margin:0 0 38px;padding:0}.brand::before{content:'';width:54px;height:54px;display:block;border-radius:18px;background:var(--md-sys-color-primary);box-shadow:inset 0 0 0 10px var(--md-sys-color-primary-container);margin-right:15px}.brand-name{font-size:1.1rem;color:var(--md-sys-color-on-surface)}.brand-sub{font-size:.75rem;color:var(--md-sys-color-on-surface-variant)}h1{font-size:2.25rem;line-height:1.12;letter-spacing:-.045em;margin-bottom:12px}.sub{font-size:.88rem;line-height:1.75;color:var(--md-sys-color-on-surface-variant);margin-bottom:30px}.field label{font-size:.76rem;color:var(--md-sys-color-on-surface-variant);margin:0 0 9px 4px}.inp-wrap{position:relative}input[type=password]{min-height:56px;padding:15px 16px 15px 50px;border:1px solid var(--md-sys-color-outline);border-radius:var(--md-sys-shape-corner-small);background:var(--md-sys-color-surface-container);color:var(--md-sys-color-on-surface);font-size:.95rem}input[type=password]:focus{border-color:var(--md-sys-color-primary);background:var(--md-sys-color-surface-container-high);box-shadow:0 0 0 3px color-mix(in srgb,var(--md-sys-color-primary) 22%,transparent)}.ic{left:17px;color:var(--md-sys-color-on-surface-variant)}.btn{min-height:56px;border-radius:var(--md-sys-shape-corner-full);background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);box-shadow:none;font-size:.9rem;transition:transform 180ms var(--md-sys-motion-easing-emphasized),border-radius 180ms}.btn:hover{transform:translateY(-3px);box-shadow:0 14px 34px rgba(4,6,14,.28)}.btn:active{transform:scale(.97);border-radius:var(--md-sys-shape-corner-large)}.err{border:0;background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container);border-radius:var(--md-sys-shape-corner-large)}.footer{border-color:var(--md-sys-color-outline-variant);color:var(--md-sys-color-outline);margin-top:32px}.footer i{color:var(--md-sys-color-primary)}
@media(max-width:700px){body{padding:16px}.wrap{justify-content:center}.wrap::before{display:none}.card{width:min(100%,460px);min-height:0;padding:42px 28px 32px;border-radius:var(--md-sys-shape-corner-extra-large);}.card::before{right:24px;top:24px}h1{font-size:1.9rem}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}

</style>
</head>
<body>
<div class="bg"></div><div class="grid"></div>
<div class="orb o1"></div><div class="orb o2"></div>
<div class="wrap">
  <div class="card">
    <div class="brand">
      <div><div class="brand-name">Lumen Relay</div><div class="brand-sub">Private operator console</div></div>
    </div>
    <h1>Enter the relay room</h1>
    <p class="sub">A focused control surface for routes, subscribers, and live traffic.</p>
    <div class="err" id="err"><i class="ti ti-alert-circle"></i><span id="err-text"></span></div>
    <form id="form">
      <div class="field">
        <label>Administrator password</label>
        <div class="inp-wrap">
          <input type="password" id="pw" placeholder="Enter your password" autofocus required>
          <i class="ti ti-lock ic"></i>
        </div>
      </div>
      <button class="btn" type="submit" id="btn"><i class="ti ti-login-2"></i> Sign In</button>
    </form>
    <div class="footer"><i class="ti ti-shield-lock"></i> Encrypted connection · administrator only</div>
  </div>
</div>
<script>
document.getElementById('form').addEventListener('submit',async e=>{
  e.preventDefault();
  const btn=document.getElementById('btn'),err=document.getElementById('err'),et=document.getElementById('err-text');
  err.classList.remove('show');btn.disabled=true;
  btn.innerHTML='<span class="aspin"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></span> Signing in...';
  try{
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:document.getElementById('pw').value})});
    if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'Error');}
    location.href='/dashboard';
  }catch(e){
    et.textContent=e.message;err.classList.add('show');
    btn.disabled=false;btn.innerHTML='<i class="ti ti-login-2"></i> Sign In';
  }
});
</script>
</body></html>"""


LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="dark">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lumen · System status</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>
*{box-sizing:border-box}html,body{margin:0;min-height:100%}:root{color-scheme:dark;--p:#bdc7ff;--on-p:#22305f;--pc:#394777;--on-pc:#dee1ff;--ter:#f2b99a;--tc:#6d3b22;--on-tc:#ffdcc8;--surface:#111318;--low:#191b21;--mid:#1d1f25;--high:#27292f;--text:#e3e2e9;--muted:#c6c5d0;--outline:#46464f;--ok:#8fd6b8;--shape:32px;--ease:cubic-bezier(.2,0,0,1)}[data-theme="light"]{color-scheme:light;--p:#52639a;--on-p:#fff;--pc:#dee1ff;--on-pc:#0c1b4b;--ter:#865228;--tc:#ffdcc8;--on-tc:#311300;--surface:#faf8ff;--low:#f4f2fa;--mid:#eeecf4;--high:#e2e1e9;--text:#1a1b20;--muted:#45464f;--outline:#c7c6d0;--ok:#176b4f}body{font-family:'Vazirmatn','Segoe UI',Arial,sans-serif;color:var(--text);background:radial-gradient(circle at 10% 90%,color-mix(in srgb,var(--ter) 10%,transparent),transparent 32rem),radial-gradient(circle at 88% 4%,color-mix(in srgb,var(--p) 16%,transparent),transparent 34rem),var(--surface);display:grid;place-items:center;padding:24px;overflow-x:hidden}.shell{width:min(1120px,100%)}.bar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:24px}.brand{display:flex;align-items:center;gap:12px;font-weight:780}.mark{width:46px;height:46px;border-radius:16px;background:var(--pc);box-shadow:inset 0 0 0 10px color-mix(in srgb,var(--p) 48%,transparent)}.actions{display:flex;gap:8px}.icon-btn,.lang-btn{min-height:46px;border:0;border-radius:999px;background:var(--high);color:var(--text);padding:0 16px;font:700 .8rem inherit;cursor:pointer}.icon-btn{width:46px;padding:0}.grid{display:grid;grid-template-columns:1.25fr .75fr;gap:18px}.hero,.health{background:color-mix(in srgb,var(--low) 94%,transparent);border:1px solid var(--outline);border-radius:var(--shape);overflow:hidden}.hero{min-height:560px;padding:54px;display:flex;flex-direction:column;justify-content:space-between;position:relative}.eyebrow{display:inline-flex;align-items:center;gap:8px;color:var(--p);font-size:.75rem;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.live-dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 6px color-mix(in srgb,var(--ok) 15%,transparent)}h1{font-size:clamp(3rem,7vw,6.4rem);line-height:.9;letter-spacing:-.07em;margin:28px 0 24px;max-width:7ch}.lead{max-width:50ch;color:var(--muted);font-size:1rem;line-height:1.8}.signal-scene{position:absolute;right:-70px;bottom:-80px;width:390px;height:390px;opacity:.76;pointer-events:none}.orbit{position:absolute;inset:48px;border:1px solid color-mix(in srgb,var(--p) 46%,transparent);border-radius:50%;animation:turn 34s linear infinite}.orbit::before,.orbit::after{content:'';position:absolute;width:18px;height:18px;border-radius:6px;background:var(--p);top:20px;left:48px;box-shadow:0 0 24px color-mix(in srgb,var(--p) 45%,transparent)}.orbit::after{width:12px;height:12px;top:auto;left:auto;right:18px;bottom:80px;background:var(--ter)}.core{position:absolute;inset:124px;border-radius:44px;background:var(--pc);transform:rotate(14deg);animation:breathe 6s var(--ease) infinite alternate}.core::after{content:'';position:absolute;inset:28px;border-radius:24px;background:var(--p);opacity:.42}@keyframes turn{to{transform:rotate(1turn)}}@keyframes breathe{to{transform:rotate(20deg) scale(1.05)}}.health{padding:24px;display:flex;flex-direction:column;gap:14px}.health-head{display:flex;align-items:center;justify-content:space-between;padding:4px 4px 14px}.health-title{font-size:1.1rem;font-weight:760}.status{display:flex;align-items:center;gap:8px;background:color-mix(in srgb,var(--ok) 14%,transparent);color:var(--ok);padding:8px 12px;border-radius:999px;font-size:.75rem;font-weight:750}.metric{background:var(--mid);border-radius:22px;padding:20px;min-height:104px;display:flex;flex-direction:column;justify-content:space-between}.metric:nth-child(3){background:var(--pc);color:var(--on-pc)}.metric:nth-child(4){background:var(--tc);color:var(--on-tc)}.label{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;opacity:.7}.value{font-size:1.72rem;font-weight:790;letter-spacing:-.035em}.foot{margin-top:auto;padding:18px 5px 3px;color:var(--muted);font-size:.72rem;display:flex;justify-content:space-between;gap:12px}.loading{opacity:.55}@media(max-width:800px){body{padding:14px}.grid{grid-template-columns:1fr}.hero{min-height:460px;padding:34px}.health{display:grid;grid-template-columns:1fr 1fr}.health-head,.foot{grid-column:1/-1}.signal-scene{width:280px;height:280px}.orbit{inset:38px}.core{inset:94px}h1{font-size:clamp(3.2rem,16vw,5rem)}}@media(max-width:480px){.health{grid-template-columns:1fr}.health-head,.foot{grid-column:auto}.hero{padding:28px;min-height:430px}.signal-scene{right:-110px;opacity:.5}.foot{flex-direction:column}}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important}}
</style>
</head>
<body>
<main class="shell">
  <header class="bar"><div class="brand"><span class="mark"></span><span>Lumen</span></div><div class="actions"><button class="lang-btn" id="lang" onclick="toggleLang()">FA</button><button class="icon-btn" onclick="toggleTheme()" aria-label="Toggle theme"><i class="ti ti-sun" id="theme-icon"></i></button></div></header>
  <div class="grid">
    <section class="hero">
      <div><div class="eyebrow"><span class="live-dot"></span><span data-en="System online" data-fa="سامانه آنلاین است">System online</span></div><h1 data-en="Quietly fast." data-fa="سریع، بی‌صدا.">Quietly fast.</h1><p class="lead" data-en="Public system availability and live health, presented without exposing administrative controls." data-fa="وضعیت دسترسی و سلامت زنده سامانه، بدون نمایش کنترل‌های مدیریتی.">Public system availability and live health, presented without exposing administrative controls.</p></div>
      <div class="signal-scene"><div class="orbit"></div><div class="core"></div></div>
    </section>
    <aside class="health">
      <div class="health-head"><div class="health-title" data-en="Service health" data-fa="سلامت سرویس">Service health</div><div class="status"><span class="live-dot"></span><span id="health-status" data-en="Healthy" data-fa="سالم">Healthy</span></div></div>
      <div class="metric"><span class="label" data-en="Uptime" data-fa="زمان فعالیت">Uptime</span><strong class="value loading" id="uptime">—</strong></div>
      <div class="metric"><span class="label" data-en="Live connections" data-fa="اتصالات زنده">Live connections</span><strong class="value loading" id="connections">—</strong></div>
      <div class="metric"><span class="label" data-en="Active configs" data-fa="کانفیگ‌های فعال">Active configs</span><strong class="value loading" id="configs">—</strong></div>
      <div class="metric"><span class="label" data-en="Network" data-fa="شبکه">Network</span><strong class="value" id="transport">Operational</strong></div>
      <div class="foot"><span id="version">Lumen · v13</span><span data-en="Refreshes every 8 seconds" data-fa="به‌روزرسانی هر ۸ ثانیه">Refreshes every 8 seconds</span></div>
    </aside>
  </div>
</main>
<script>
let lang=localStorage.getItem('lumen-public-lang')||'en';
function applyLang(){document.documentElement.lang=lang;document.documentElement.dir=lang==='fa'?'rtl':'ltr';document.querySelectorAll('[data-en]').forEach(e=>e.textContent=e.dataset[lang]);document.getElementById('lang').textContent=lang==='fa'?'EN':'FA'}
function toggleLang(){lang=lang==='en'?'fa':'en';localStorage.setItem('lumen-public-lang',lang);applyLang()}
function toggleTheme(){const h=document.documentElement;const light=h.dataset.theme==='light';h.dataset.theme=light?'dark':'light';document.getElementById('theme-icon').className='ti '+(light?'ti-sun':'ti-moon')}
async function health(){try{const r=await fetch('/health',{cache:'no-store'}),d=await r.json();document.getElementById('uptime').textContent=d.uptime||'—';document.getElementById('connections').textContent=d.connections??'—';document.getElementById('configs').textContent=d.active_configs??'—';document.getElementById('transport').textContent=lang==='fa'?'پایدار':'Operational';document.getElementById('version').textContent='Lumen · v'+(d.version||'13');document.querySelectorAll('.loading').forEach(e=>e.classList.remove('loading'))}catch(e){const s=document.getElementById('health-status');s.textContent=lang==='fa'?'در حال بررسی':'Checking';}}
applyLang();health();setInterval(health,8000);
</script>
</body></html>"""


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lumen Relay · Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0E1213;--bg2:#151A1B;--bg3:#1C2325;
  --card:#171C1D;--card-b:rgba(24,155,173,0.13);--card-bh:rgba(24,155,173,0.28);
  --accent:#189BAD;--accent2:#3FB6C4;--accent-d:rgba(24,155,173,0.12);
  --green:#12A08B;--green-bg:rgba(18,160,139,0.1);--green-t:#3EC3AE;
  --red:#B33A22;--red-bg:rgba(179,58,34,0.1);--red-t:#E08167;
  --amber:#C08A2E;--amber-bg:rgba(192,138,46,0.1);--amber-t:#E4BE74;
  --purple:#A8351C;--purple-bg:rgba(168,53,28,0.1);
  --t1:#F2F3F3;--t2:#BFBFBF;--t3:#8C9192;
  --sidebar-w:248px;--radius:16px;
  --shadow:0 4px 24px rgba(0,0,0,0.35);
}
[data-theme="light"]{
  --bg:#F1F1F0;--bg2:#E8E8E7;--bg3:#DCDCDA;
  --card:#FFFFFF;--card-b:rgba(24,155,173,0.15);--card-bh:rgba(24,155,173,0.35);
  --accent:#0D6A78;--accent2:#0A5561;--accent-d:rgba(13,106,120,0.08);
  --green:#0E7F70;--green-bg:rgba(14,127,112,0.08);--green-t:#0B5B50;
  --red:#911F0C;--red-bg:rgba(145,31,12,0.08);--red-t:#791B0D;
  --amber:#A5701F;--amber-bg:rgba(165,112,31,0.08);--amber-t:#7A5215;
  --purple:#8E2712;--purple-bg:rgba(142,39,18,0.08);
  --t1:#191C1D;--t2:#45494A;--t3:#6E7375;
  --shadow:0 4px 20px rgba(0,0,0,0.1);
}
html,body{height:100%}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Inter','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:var(--bg);color:var(--t1);min-height:100vh;display:flex;font-size:14px;transition:background .3s,color .3s}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--bg3);border-radius:3px}
a{color:inherit;text-decoration:none}
.sidebar{width:var(--sidebar-w);min-height:100vh;background:var(--bg2);border-right:1px solid var(--card-b);display:flex;flex-direction:column;flex-shrink:0;position:fixed;left:0;top:0;bottom:0;z-index:200;transition:transform .25s cubic-bezier(.4,0,.2,1),background .3s,border-color .3s}
.logo{display:flex;align-items:center;gap:12px;padding:20px 16px 16px;border-bottom:1px solid var(--card-b)}
.logo-img{width:38px;height:38px;border-radius:50%;overflow:hidden;border:1px solid var(--card-b);box-shadow:0 0 14px rgba(168,53,28,.3),0 0 8px rgba(24,155,173,.25);flex-shrink:0}
.logo-img img{width:100%;height:100%;object-fit:cover}
.logo-name{font-size:13.5px;font-weight:700;color:var(--t1)}
.logo-sub{font-size:10px;color:var(--t3);margin-top:1px}
.sb-close{display:none;position:absolute;right:12px;top:20px;background:var(--accent-d);border:1px solid var(--card-b);color:var(--t2);width:30px;height:30px;border-radius:8px;font-size:16px;align-items:center;justify-content:center;cursor:pointer}
.nav-wrap{flex:1;overflow-y:auto;padding:6px 0 8px}
.nav-sec{padding:14px 14px 4px;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--t3);font-weight:700}
.nav-it{display:flex;align-items:center;gap:9px;padding:9px 14px;color:var(--t3);font-size:12.5px;cursor:pointer;border-left:2px solid transparent;transition:all .15s;margin:1px 6px}
.nav-it i{font-size:16px;width:18px;text-align:center;flex-shrink:0}
.nav-it:hover{background:var(--accent-d);color:var(--t2)}
.nav-it.on{background:var(--accent-d);color:var(--t1);border-left-color:var(--accent);font-weight:600}
.nav-badge{margin-left:auto;background:rgba(24,155,173,0.15);color:var(--accent2);font-size:9px;padding:1px 6px;border-radius:20px;font-weight:700}
.sb-foot{padding:12px 14px;border-top:1px solid var(--card-b)}
.tg-btn{display:flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#0D6A78,#094F59);color:#fff;border-radius:9px;padding:10px;font-size:12.5px;font-weight:600;font-family:inherit;border:none;cursor:pointer;width:100%;transition:.15s}
.tg-btn:hover{filter:brightness(1.1)}
.theme-btn{display:flex;align-items:center;justify-content:center;gap:7px;background:var(--accent-d);color:var(--t2);border-radius:9px;padding:8px;font-size:12px;font-weight:500;font-family:inherit;border:1px solid var(--card-b);cursor:pointer;width:100%;transition:.15s;margin-bottom:7px}
.theme-btn:hover{background:var(--card-b);color:var(--t1)}
.logout-btn{display:flex;align-items:center;justify-content:center;gap:7px;background:var(--red-bg);color:var(--red-t);border-radius:9px;padding:8px;font-size:12px;font-weight:500;font-family:inherit;border:1px solid rgba(179,58,34,0.2);cursor:pointer;width:100%;transition:.15s;margin-top:6px}
.logout-btn:hover{background:rgba(179,58,34,0.2)}
.mob-top{display:none;position:fixed;top:0;right:0;left:0;height:52px;background:var(--bg2);border-bottom:1px solid var(--card-b);z-index:150;align-items:center;justify-content:space-between;padding:0 14px;transition:background .3s}
.mob-top .ml{display:flex;align-items:center;gap:9px}
.mob-logo{width:28px;height:28px;border-radius:50%;overflow:hidden;box-shadow:0 0 8px rgba(168,53,28,.35)}
.mob-logo img{width:100%;height:100%;object-fit:cover}
.mob-title{color:var(--t1);font-size:13px;font-weight:700}
.mob-right{display:flex;gap:6px}
.menu-btn,.theme-mob{background:var(--accent-d);border:1px solid var(--card-b);color:var(--t2);width:34px;height:34px;border-radius:8px;font-size:17px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:.15s}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:190;backdrop-filter:blur(3px)}
.overlay.show{display:block}
.main{margin-left:var(--sidebar-w);flex:1;padding:28px 28px 60px;min-width:0;transition:margin .25s}
.pg{display:none}
.pg.on{display:block;animation:fi .2s ease}
@keyframes fi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:12px}
.tb-title{font-size:18px;font-weight:700;color:var(--t1);display:flex;align-items:center;gap:8px;letter-spacing:-.02em}
.tb-title i{color:var(--accent);font-size:20px}
.tb-sub{font-size:11px;color:var(--t3);margin-top:4px}
.tb-right{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.badge{font-size:10px;padding:3px 10px;border-radius:20px;font-weight:700;display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
.bg-green{background:var(--green-bg);color:var(--green-t)}
.bg-blue{background:var(--accent-d);color:var(--accent2)}
.bg-amber{background:var(--amber-bg);color:var(--amber-t)}
.bg-red{background:var(--red-bg);color:var(--red-t)}
.bg-purple{background:var(--purple-bg);color:#D8705A}
.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;display:inline-block}
.dg{background:var(--green)}.dr{background:var(--red)}.da{background:var(--amber)}.db{background:var(--accent)}
.pulse{animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-bottom:18px}
.metric{background:var(--card);border:1px solid var(--card-b);border-radius:var(--radius);padding:17px 17px 14px;transition:all .2s;position:relative;overflow:hidden;cursor:default}
.metric::after{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--accent);opacity:0;transition:.2s}
.metric:hover{border-color:var(--card-bh);transform:translateY(-2px);box-shadow:var(--shadow)}
.metric:hover::after{opacity:1}
.metric.suc::after{background:var(--green)}
.metric.dan::after{background:var(--red)}
/* ══════ traffic page ══════ */
.traf-hero{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:13px;margin-bottom:18px}
.traf-main-stat{background:linear-gradient(155deg,var(--bg3) 0%,var(--card) 60%);border:1px solid var(--card-b);border-radius:20px;padding:22px 24px;position:relative;overflow:hidden}
.traf-main-stat::before{content:'';position:absolute;top:-50px;left:-50px;width:200px;height:200px;background:radial-gradient(circle,var(--accent-d),transparent 70%);pointer-events:none}
.traf-main-label{font-size:10.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.08em;display:flex;align-items:center;gap:6px;margin-bottom:10px;position:relative;z-index:1}
.traf-main-val{font-size:34px;font-weight:800;color:var(--t1);line-height:1;letter-spacing:-.02em;display:flex;align-items:baseline;gap:6px;position:relative;z-index:1}
.traf-main-val span{font-size:14px;font-weight:500;color:var(--t3)}
.traf-trend{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;padding:4px 10px;border-radius:20px;margin-top:12px;position:relative;z-index:1}
.traf-trend.up{background:var(--green-bg);color:var(--green-t)}
.traf-trend.down{background:var(--red-bg);color:var(--red-t)}
.traf-mini{background:var(--card);border:1px solid var(--card-b);border-radius:20px;padding:18px 19px;display:flex;flex-direction:column;justify-content:space-between;transition:.2s}
.traf-mini:hover{border-color:var(--card-bh);transform:translateY(-2px)}
.traf-mini-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.traf-mini-icon{width:32px;height:32px;border-radius:9px;background:var(--accent-d);color:var(--accent);display:flex;align-items:center;justify-content:center;font-size:15px}
.traf-mini-icon.pk{background:var(--amber-bg);color:var(--amber)}
.traf-mini-icon.lo{background:var(--purple-bg);color:var(--purple)}
.traf-mini-label{font-size:9.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.traf-mini-val{font-size:21px;font-weight:800;color:var(--t1);letter-spacing:-.01em}
.traf-mini-sub{font-size:9.5px;color:var(--t3);margin-top:3px}

.traf-chart-card{background:var(--card);border:1px solid var(--card-b);border-radius:22px;padding:22px 24px 18px;box-shadow:var(--shadow);margin-bottom:16px}
.traf-chart-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;flex-wrap:wrap;gap:10px}
.traf-chart-title{font-size:14px;font-weight:800;color:var(--t1);display:flex;align-items:center;gap:8px}
.traf-chart-title i{color:var(--accent);font-size:18px}
.traf-chart-sub{font-size:10.5px;color:var(--t3);margin-top:3px}
.traf-legend{display:flex;gap:14px;align-items:center}
.traf-legend-item{display:flex;align-items:center;gap:6px;font-size:10.5px;color:var(--t2);font-weight:600}
.traf-legend-dot{width:8px;height:8px;border-radius:3px}
.traf-range-tabs{display:flex;gap:4px;background:var(--accent-d);padding:3px;border-radius:10px;border:1px solid var(--card-b)}
.traf-range-tab{padding:6px 13px;border-radius:8px;font-size:10.5px;font-weight:700;color:var(--t3);cursor:pointer;transition:.15s;border:none;background:transparent;font-family:inherit}
.traf-range-tab.on{background:var(--accent);color:#fff;box-shadow:0 2px 8px rgba(24,155,173,.35)}
.traf-chart-body{height:320px;margin-top:14px;position:relative}

@media(max-width:900px){.traf-hero{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.traf-hero{grid-template-columns:1fr}.traf-chart-body{height:260px}}
.m-icon{width:34px;height:34px;border-radius:8px;background:var(--accent-d);display:flex;align-items:center;justify-content:center;margin-bottom:11px;color:var(--accent);font-size:17px}
.m-icon.suc{background:var(--green-bg);color:var(--green)}
.m-icon.dan{background:var(--red-bg);color:var(--red)}
.m-icon.pur{background:var(--purple-bg);color:var(--purple)}
.m-label{font-size:10px;color:var(--t3);margin-bottom:4px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.m-val{font-size:25px;font-weight:700;color:var(--t1);line-height:1;letter-spacing:-.02em}
.m-unit{font-size:12px;font-weight:400;color:var(--t3)}
.m-sub{font-size:10px;color:var(--t3);margin-top:6px;display:flex;align-items:center;gap:3px}
.vless-box{background:linear-gradient(135deg,var(--bg3) 0%,var(--bg2) 100%);border:1px solid var(--card-b);border-radius:18px;padding:20px 22px;margin-bottom:18px;box-shadow:var(--shadow);position:relative;overflow:hidden;transition:background .3s}
.vless-box::before{content:'';position:absolute;top:-50px;left:-50px;width:180px;height:180px;background:radial-gradient(circle,var(--accent-d),transparent 70%);pointer-events:none}
.vl-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:13px;flex-wrap:wrap;gap:8px}
.vl-title{color:var(--t2);font-size:11px;display:flex;align-items:center;gap:6px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.vl-title i{color:var(--accent);font-size:15px}
.vl-code{background:rgba(0,0,0,.18);border:1px solid var(--card-b);border-radius:9px;padding:13px 15px;font-size:11px;font-family:ui-monospace,monospace;color:var(--accent2);word-break:break-all;line-height:1.8;letter-spacing:.01em}
[data-theme="light"] .vl-code{background:rgba(0,0,0,.04)}
.vl-actions{display:flex;gap:8px;margin-top:13px;flex-wrap:wrap}
.btn{font-family:inherit;font-size:12px;font-weight:500;border-radius:9px;padding:8px 14px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;border:none;transition:all .15s;white-space:nowrap}
.btn i{font-size:13px}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-p{background:linear-gradient(135deg,#12A2B5,#A8351C);color:#fff;box-shadow:0 2px 14px rgba(168,53,28,.35)}
.btn-p:hover{background:#0D6A78;box-shadow:0 4px 18px rgba(24,155,173,.4)}
.btn-o{background:transparent;border:1px solid var(--card-b);color:var(--t2)}
.btn-o:hover{background:var(--accent-d);border-color:rgba(24,155,173,.3)}
.btn-g{background:var(--accent-d);color:var(--accent2);border:1px solid rgba(24,155,173,.15)}
.btn-g:hover{background:rgba(24,155,173,.22)}
.btn-d{background:var(--red-bg);color:var(--red-t);border:1px solid rgba(179,58,34,.2)}
.btn-d:hover{background:rgba(179,58,34,.2)}
.btn-pur{background:var(--purple-bg);color:#D8705A;border:1px solid rgba(168,53,28,.2)}
.btn-pur:hover{background:rgba(168,53,28,.22)}
.btn-amber{background:var(--amber-bg);color:var(--amber-t);border:1px solid rgba(192,138,46,.2)}
.btn-amber:hover{background:rgba(192,138,46,.22)}
.btn-sm{padding:5px 9px;font-size:10.5px;border-radius:7px}
.btn-icon{width:30px;height:30px;padding:0;justify-content:center;border-radius:5px}
.card{background:var(--card);border:1px solid var(--card-b);border-radius:var(--radius);padding:18px 20px;transition:border-color .2s,background .3s}
.card:hover{border-color:var(--card-bh)}
.card-title{font-size:12.5px;font-weight:700;color:var(--t1);margin-bottom:15px;display:flex;align-items:center;gap:7px}
.card-title i{font-size:16px;color:var(--accent)}
.ml-auto{margin-left:auto}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-bottom:16px}
.g3{display:grid;grid-template-columns:2fr 1fr;gap:13px;margin-bottom:16px}
.mb16{margin-bottom:16px}
.sr{display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(24,155,173,0.05);font-size:12px}
.sr:last-child{border-bottom:none}
.sr-k{color:var(--t2);display:flex;align-items:center;gap:6px}
.sr-k i{font-size:13px;color:var(--t3)}
.sr-v{color:var(--t1);font-weight:600;font-size:11.5px}
.ch{position:relative;height:230px}
.ch-lg{position:relative;height:330px}
.ch-sm{position:relative;height:185px}
.exp-chip{font-size:9px;padding:3px 8px;border-radius:6px;font-weight:700;display:inline-flex;align-items:center;gap:3px}
.ec-ok{background:var(--green-bg);color:var(--green-t)}
.ec-warn{background:var(--amber-bg);color:var(--amber-t)}
.ec-exp{background:var(--red-bg);color:var(--red-t)}
.ec-inf{background:var(--accent-d);color:var(--accent2)}
.tog{width:19px;height:34px;border-radius:19px;background:rgba(120,124,125,0.25);position:relative;cursor:pointer;transition:.2s;flex-shrink:0;border:none}
.tog::after{content:'';position:absolute;width:13px;height:13px;border-radius:50%;background:#fff;left:3px;bottom:3px;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.tog.on{background:var(--green)}
.tog.on::after{bottom:18px}
.form-row{display:flex;gap:9px;flex-wrap:wrap;align-items:flex-end}
.fg{display:flex;flex-direction:column;gap:5px}
.fg label{font-size:10px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.fi,.fs{padding:9px 12px;border-radius:9px;border:1px solid var(--card-b);background:rgba(0,0,0,.18);color:var(--t1);font-family:inherit;font-size:12px;outline:none;transition:.15s;min-width:100px}
[data-theme="light"] .fi,[data-theme="light"] .fs{background:rgba(0,0,0,.04)}
.fi::placeholder{color:var(--t3)}
.fi:focus,.fs:focus{border-color:rgba(24,155,173,.45);background:rgba(0,0,0,.25);box-shadow:0 0 0 3px rgba(24,155,173,.08)}
.fs option{background:var(--bg2)}
[data-theme="light"] .fs option{background:#fff}
.cl{background:var(--accent-d);border:1px solid rgba(24,155,173,.15);border-radius:10px;padding:11px 13px;font-size:11px;color:var(--t2);display:flex;gap:9px;align-items:flex-start;line-height:1.8;margin-top:12px}
.cl i{font-size:15px;color:var(--accent);margin-top:1px;flex-shrink:0}
.cl.amber{background:var(--amber-bg);border-color:rgba(192,138,46,.2);color:var(--amber-t)}
/* ══════ config builder panel ══════ */
.create-panel{background:linear-gradient(155deg,var(--bg3) 0%,var(--card) 55%);border:1px solid var(--card-b);border-radius:22px;padding:0;overflow:hidden;box-shadow:var(--shadow);margin-bottom:16px;position:relative}
.create-panel::before{content:'';position:absolute;top:-60px;left:-60px;width:220px;height:220px;background:radial-gradient(circle,var(--accent-d),transparent 70%);pointer-events:none}
.cp-head{display:flex;align-items:center;gap:13px;padding:22px 24px 18px;position:relative;z-index:1}
.cp-head-icon{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px;flex-shrink:0;box-shadow:0 6px 18px rgba(24,155,173,.35)}
.cp-head-text{flex:1;min-width:0}
.cp-head-title{font-size:15px;font-weight:800;color:var(--t1);letter-spacing:-.01em}
.cp-head-sub{font-size:11px;color:var(--t3);margin-top:2px}
.cp-body{padding:2px 24px 22px;position:relative;z-index:1}
.cp-row{display:grid;grid-template-columns:1.3fr 1fr;gap:14px;margin-bottom:16px}
.cp-block{background:rgba(0,0,0,.14);border:1px solid var(--card-b);border-radius:14px;padding:14px 16px}
[data-theme="light"] .cp-block{background:rgba(13,106,120,.03)}
.cp-block-label{font-size:10px;font-weight:800;color:var(--t2);text-transform:uppercase;letter-spacing:.08em;display:flex;align-items:center;gap:6px;margin-bottom:11px}
.cp-block-label i{color:var(--accent);font-size:14px}
.cp-input-full{width:100%;padding:10px 13px;border-radius:10px;border:1px solid var(--card-b);background:rgba(0,0,0,.18);color:var(--t1);font-family:inherit;font-size:12.5px;outline:none;transition:.15s}
[data-theme="light"] .cp-input-full{background:#fff}
.cp-input-full:focus{border-color:rgba(24,155,173,.5);box-shadow:0 0 0 3px rgba(24,155,173,.1)}
.cp-input-full::placeholder{color:var(--t3)}
.cp-mini-row{display:flex;gap:8px;margin-top:9px}
.cp-quota-inputs{display:flex;gap:8px}
.cp-quota-inputs .cp-input-full{flex:1}
.cp-quota-inputs select.cp-input-full{flex:0 0 76px}
.chip-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}
.chip{font-size:10.5px;font-weight:700;padding:5px 12px;border-radius:8px;background:var(--accent-d);color:var(--t2);border:1px solid var(--card-b);cursor:pointer;transition:.15s;white-space:nowrap}
.chip:hover{background:rgba(24,155,173,.18);color:var(--accent2)}
.chip.active{background:var(--accent);color:#fff;border-color:var(--accent);box-shadow:0 3px 10px rgba(24,155,173,.35)}
.proto-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:9px}
.proto-card{border:1.5px solid var(--card-b);border-radius:13px;padding:13px 12px;cursor:pointer;transition:.18s;text-align:center;position:relative;background:rgba(0,0,0,.1)}
[data-theme="light"] .proto-card{background:#fff}
.proto-card:hover{border-color:var(--card-bh);transform:translateY(-1px)}
.proto-card.active{border-color:var(--accent);background:var(--accent-d);box-shadow:0 0 0 3px rgba(24,155,173,.1)}
.proto-card.active .proto-card-check{opacity:1;transform:scale(1)}
.proto-card-check{position:absolute;top:7px;right:7px;width:16px;height:16px;border-radius:50%;background:var(--accent);color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;opacity:0;transform:scale(.5);transition:.18s}
.proto-card-icon{width:32px;height:32px;border-radius:9px;background:var(--accent-d);color:var(--accent);display:flex;align-items:center;justify-content:center;font-size:16px;margin:0 auto 8px}
.proto-card.active .proto-card-icon{background:var(--accent);color:#fff}
.proto-card-title{font-size:11px;font-weight:800;color:var(--t1)}
.proto-card-desc{font-size:9px;color:var(--t3);margin-top:3px;line-height:1.5}
.cp-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-top:16px;border-top:1px solid var(--card-b);flex-wrap:wrap}
.cp-footer-note{display:flex;align-items:center;gap:8px;font-size:10.5px;color:var(--t3);line-height:1.7;flex:1;min-width:220px}
.cp-footer-note i{color:var(--accent);font-size:15px;flex-shrink:0}
.cp-submit-btn{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;border-radius:13px;padding:13px 26px;font-family:inherit;font-size:13px;font-weight:800;cursor:pointer;display:flex;align-items:center;gap:8px;box-shadow:0 6px 20px rgba(24,155,173,.35);transition:.18s;white-space:nowrap}
.cp-submit-btn:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(24,155,173,.45)}
.cp-submit-btn:active{transform:translateY(0) scale(.98)}
@media(max-width:760px){
  .cp-row{grid-template-columns:1fr}
  .proto-cards{grid-template-columns:1fr}
  .cp-footer{flex-direction:column;align-items:stretch}
  .cp-submit-btn{justify-content:center}
}
/* ══════ server info panel ══════ */
.srv-panel{background:linear-gradient(155deg,var(--bg3) 0%,var(--card) 60%);border:1px solid var(--card-b);border-radius:22px;overflow:hidden;box-shadow:var(--shadow);position:relative}
.srv-panel::before{content:'';position:absolute;top:-60px;left:-60px;width:200px;height:200px;background:radial-gradient(circle,var(--accent-d),transparent 70%);pointer-events:none}
.srv-hero{display:flex;align-items:center;gap:14px;padding:22px 24px;position:relative;z-index:1;border-bottom:1px solid var(--card-b)}
.srv-hero-icon{width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;flex-shrink:0;box-shadow:0 6px 18px rgba(24,155,173,.35)}
.srv-hero-text{flex:1;min-width:0}
.srv-hero-domain{font-size:15px;font-weight:800;color:var(--t1);word-break:break-all}
.srv-hero-sub{font-size:10.5px;color:var(--t3);margin-top:4px;display:flex;align-items:center;gap:6px}
.srv-tiles{display:grid;grid-template-columns:1fr 1fr;gap:11px;padding:20px 22px 22px;position:relative;z-index:1}
.srv-tile{display:flex;align-items:center;gap:11px;background:rgba(0,0,0,.14);border:1px solid var(--card-b);border-radius:13px;padding:12px 14px;transition:.18s}
[data-theme="light"] .srv-tile{background:rgba(13,106,120,.03)}
.srv-tile:hover{border-color:var(--card-bh);transform:translateY(-1px)}
.srv-tile-icon{width:34px;height:34px;border-radius:10px;background:var(--accent-d);color:var(--accent);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.srv-tile-text{min-width:0}
.srv-tile-label{font-size:9.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px}
.srv-tile-val{font-size:12px;font-weight:700;color:var(--t1);word-break:break-word}

/* ══════ change-password panel ══════ */
.pw-panel{background:linear-gradient(155deg,var(--bg3) 0%,var(--card) 60%);border:1px solid var(--card-b);border-radius:22px;overflow:hidden;box-shadow:var(--shadow);position:relative}
.pw-panel::before{content:'';position:absolute;top:-60px;right:-60px;width:200px;height:200px;background:radial-gradient(circle,var(--purple-bg),transparent 70%);pointer-events:none}
.pw-hero{display:flex;align-items:center;gap:14px;padding:22px 24px 18px;position:relative;z-index:1}
.pw-hero-icon{width:50px;height:50px;border-radius:14px;background:linear-gradient(135deg,var(--purple),#6B1A0B);display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;flex-shrink:0;box-shadow:0 6px 18px rgba(168,53,28,.35)}
.pw-hero-text{flex:1;min-width:0}
.pw-hero-title{font-size:15px;font-weight:800;color:var(--t1)}
.pw-hero-sub{font-size:10.5px;color:var(--t3);margin-top:3px}
.pw-body{padding:2px 24px 22px;position:relative;z-index:1}
.pw-field{position:relative;margin-bottom:13px}
.pw-field label{display:block;font-size:10px;font-weight:700;color:var(--t2);text-transform:uppercase;letter-spacing:.06em;margin-bottom:7px}
.pw-input{width:100%;padding:11px 42px 11px 14px;border-radius:11px;border:1px solid var(--card-b);background:rgba(0,0,0,.18);color:var(--t1);font-family:inherit;font-size:12.5px;outline:none;transition:.15s}
[data-theme="light"] .pw-input{background:#fff}
.pw-input:focus{border-color:rgba(168,53,28,.5);box-shadow:0 0 0 3px rgba(168,53,28,.1)}
.pw-eye{position:absolute;right:12px;top:34px;background:none;border:none;color:var(--t3);cursor:pointer;font-size:16px;padding:4px;display:flex}
.pw-eye:hover{color:var(--purple)}
.pw-strength{height:4px;border-radius:3px;background:var(--accent-d);margin-top:8px;overflow:hidden;display:flex;gap:3px}
.pw-strength-seg{flex:1;height:100%;border-radius:3px;background:rgba(120,124,125,.2);transition:.25s}
.pw-strength-label{font-size:9.5px;color:var(--t3);margin-top:5px;display:flex;align-items:center;gap:5px}
.pw-reqs{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px;margin-bottom:16px}
.pw-req{font-size:9.5px;padding:4px 10px;border-radius:7px;background:var(--accent-d);color:var(--t3);font-weight:600;display:flex;align-items:center;gap:4px;transition:.18s}
.pw-req.met{background:var(--green-bg);color:var(--green-t)}
.pw-submit{width:100%;justify-content:center;background:linear-gradient(135deg,var(--purple),#6B1A0B);color:#fff;border:none;border-radius:12px;padding:12px;font-family:inherit;font-size:13px;font-weight:800;cursor:pointer;display:flex;align-items:center;gap:8px;box-shadow:0 6px 18px rgba(168,53,28,.32);transition:.18s}
.pw-submit:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(168,53,28,.42)}
.pw-submit:active{transform:translateY(0) scale(.98)}

/* ══════ active connections ══════ */
.conn-hero{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.conn-hero-tile{background:var(--card);border:1px solid var(--card-b);border-radius:16px;padding:16px 18px;position:relative;overflow:hidden;transition:.2s}
.conn-hero-tile:hover{border-color:var(--card-bh);transform:translateY(-2px);box-shadow:var(--shadow)}
.conn-hero-tile::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent)}
.conn-hero-icon{width:32px;height:32px;border-radius:9px;background:var(--green-bg);color:var(--green-t);display:flex;align-items:center;justify-content:center;font-size:15px;margin-bottom:10px}
.conn-hero-tile:nth-child(2) .conn-hero-icon{background:var(--accent-d);color:var(--accent)}
.conn-hero-tile:nth-child(3) .conn-hero-icon{background:var(--purple-bg);color:var(--purple)}
.conn-hero-tile:nth-child(4) .conn-hero-icon{background:var(--amber-bg);color:var(--amber)}
.conn-hero-label{font-size:9.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}
.conn-hero-val{font-size:21px;font-weight:800;color:var(--t1);line-height:1;letter-spacing:-.02em}
.conn-hero-unit{font-size:11px;color:var(--t3);font-weight:500}

.conn-toolbar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.conn-toolbar-title{font-size:12px;font-weight:800;color:var(--t2);display:flex;align-items:center;gap:7px;text-transform:uppercase;letter-spacing:.06em}
.conn-toolbar-title i{color:var(--green);font-size:15px}
.conn-live-badge{display:flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;color:var(--green-t);background:var(--green-bg);padding:5px 12px;border-radius:20px;border:1px solid rgba(18,160,139,.2)}
.conn-live-dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 1.6s infinite}

.conn-grid-v2{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.conn-card-v2{background:var(--card);border:1px solid var(--card-b);border-radius:18px;padding:0;overflow:hidden;transition:all .22s cubic-bezier(.4,0,.2,1);position:relative}
.conn-card-v2:hover{border-color:var(--card-bh);transform:translateY(-3px);box-shadow:0 14px 32px rgba(0,0,0,.22)}
.conn-card-v2-glow{position:absolute;top:-40px;left:-40px;width:140px;height:140px;background:radial-gradient(circle,rgba(18,160,139,.1),transparent 70%);pointer-events:none}
.conn-card-v2-top{display:flex;align-items:center;gap:12px;padding:16px 17px 13px;position:relative;z-index:1}
.conn-avatar{width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,var(--green),#0F8374);display:flex;align-items:center;justify-content:center;color:#fff;font-size:18px;flex-shrink:0;position:relative;box-shadow:0 4px 14px rgba(18,160,139,.3)}
.conn-avatar::after{content:'';position:absolute;inset:-4px;border-radius:16px;border:1.5px solid var(--green);opacity:.4;animation:breathe2 2.4s ease-in-out infinite}
@keyframes breathe2{0%,100%{transform:scale(1);opacity:.4}50%{transform:scale(1.12);opacity:0}}
.conn-card-v2-id{flex:1;min-width:0}
.conn-ip-v2{font-family:ui-monospace,monospace;font-size:14px;font-weight:800;color:var(--t1);display:flex;align-items:center;gap:6px}
.conn-ip-copy{background:none;border:none;color:var(--t3);cursor:pointer;font-size:12px;padding:2px;display:flex;transition:.15s}
.conn-ip-copy:hover{color:var(--accent)}
.conn-label-v2{font-size:10.5px;color:var(--t3);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.conn-status-pill{font-size:9px;font-weight:800;padding:4px 9px;border-radius:20px;background:var(--green-bg);color:var(--green-t);display:flex;align-items:center;gap:4px;white-space:nowrap;flex-shrink:0}
.conn-card-v2-divider{height:1px;background:linear-gradient(90deg,transparent,var(--card-b) 15%,var(--card-b) 85%,transparent);margin:0 17px}
.conn-card-v2-body{padding:14px 17px 16px}
.conn-proto-row{margin-bottom:12px}
.conn-stat-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.conn-stat-box{display:flex;align-items:center;gap:8px}
.conn-stat-icon{width:26px;height:26px;border-radius:8px;background:var(--accent-d);color:var(--accent);display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
.conn-stat-icon.time{background:var(--purple-bg);color:var(--purple)}
.conn-stat-text-label{font-size:8.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.conn-stat-text-val{font-size:11.5px;font-weight:700;color:var(--t1);margin-top:1px}
.conn-duration-track{height:5px;border-radius:4px;background:var(--accent-d);overflow:hidden;position:relative}
.conn-duration-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--green),#4FCFB8);position:relative;overflow:hidden}
.conn-duration-fill::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent);width:40%;animation:shimmer 1.8s linear infinite}
@keyframes shimmer{0%{transform:translateX(-120%)}100%{transform:translateX(280%)}}

.conn-empty-v2{text-align:center;padding:70px 20px;background:var(--card);border:1px dashed var(--card-b);border-radius:20px}
.conn-empty-v2-icon{width:64px;height:64px;border-radius:18px;background:var(--accent-d);display:flex;align-items:center;justify-content:center;font-size:28px;color:var(--t3);margin:0 auto 16px}
.conn-empty-v2-title{font-size:13.5px;font-weight:700;color:var(--t2);margin-bottom:5px}
.conn-empty-v2-sub{font-size:11px;color:var(--t3)}

@media(max-width:760px){.conn-hero{grid-template-columns:1fr 1fr}}
@media(max-width:500px){.conn-grid-v2{grid-template-columns:1fr}}

@media(max-width:560px){.srv-tiles{grid-template-columns:1fr}}
.cl.amber i{color:var(--amber)}
.sub-box{background:rgba(168,53,28,.07);border:1px solid rgba(168,53,28,.2);border-radius:10px;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:11px}
.sub-url{font-family:ui-monospace,monospace;font-size:10.5px;color:#D8705A;word-break:break-all;flex:1}
.spbar{height:4px;border-radius:3px;background:var(--accent-d);margin-top:5px;overflow:hidden}
.spfill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--accent2));transition:width 1s}
.empty{text-align:center;padding:50px 20px;color:var(--t3)}
.empty i{font-size:40px;opacity:.3;margin-bottom:12px;display:block}
.empty p{font-size:12.5px;margin-top:4px}
/* ══════ sub groups ══════ */
.subs-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.subs-search{flex:1;min-width:200px;position:relative}
.subs-search input{width:100%;padding:11px 15px 11px 40px;border-radius:12px;border:1px solid var(--card-b);background:var(--card);color:var(--t1);font-family:inherit;font-size:12.5px;outline:none;transition:.15s}
.subs-search input:focus{border-color:rgba(168,53,28,.5);box-shadow:0 0 0 3px rgba(168,53,28,.1)}
.subs-search i{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:15px}

.sub-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px;margin-bottom:18px}
.sub-card{background:var(--card);border:1px solid var(--card-b);border-radius:20px;padding:0;overflow:hidden;transition:all .25s cubic-bezier(.4,0,.2,1);position:relative}
.sub-card:hover{border-color:var(--card-bh);transform:translateY(-4px);box-shadow:0 16px 36px rgba(0,0,0,.24)}
.sub-card-top{background:linear-gradient(155deg,var(--purple-bg) 0%,transparent 65%);padding:20px 20px 16px;position:relative}
.sub-card-top::before{content:'';position:absolute;top:-30px;left:-30px;width:130px;height:130px;background:radial-gradient(circle,rgba(168,53,28,.14),transparent 70%);pointer-events:none}
.sub-card-head-v2{display:flex;align-items:flex-start;gap:13px;position:relative;z-index:1}
.sub-card-icon{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,var(--purple),#6B1A0B);display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px;flex-shrink:0;box-shadow:0 6px 16px rgba(168,53,28,.35)}
.sub-card-titles{flex:1;min-width:0}
.sub-card-name-v2{font-size:15.5px;font-weight:800;color:var(--t1);letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sub-card-desc-v2{font-size:11px;color:var(--t3);margin-top:3px;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.sub-card-lock-badge{flex-shrink:0;width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px}
.sub-card-lock-badge.locked{background:var(--amber-bg);color:var(--amber-t)}
.sub-card-lock-badge.open{background:var(--green-bg);color:var(--green-t)}

.sub-card-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:0;position:relative;z-index:1;margin-top:16px;background:rgba(0,0,0,.14);border:1px solid var(--card-b);border-radius:13px;overflow:hidden}
[data-theme="light"] .sub-card-stats{background:rgba(142,39,18,.03)}
.sub-card-stat{padding:11px 8px;text-align:center;border-right:1px solid var(--card-b)}
.sub-card-stat:last-child{border-right:none}
.sub-card-stat-val{font-size:15px;font-weight:800;color:var(--t1);line-height:1.2}
.sub-card-stat-label{font-size:8.5px;color:var(--t3);font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-top:4px}

.sub-card-url-row{margin:14px 20px 0;background:rgba(168,53,28,.08);border:1px dashed rgba(168,53,28,.25);border-radius:11px;padding:9px 12px;display:flex;align-items:center;gap:8px}
.sub-card-url-text{font-family:ui-monospace,monospace;font-size:9.5px;color:#D8705A;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sub-card-url-copy{background:none;border:none;color:var(--purple);cursor:pointer;font-size:13px;padding:3px;display:flex;flex-shrink:0;transition:.15s}
.sub-card-url-copy:hover{color:#D8705A;transform:scale(1.1)}

.sub-card-bottom{padding:14px 20px 18px;display:flex;gap:7px;flex-wrap:wrap}
.sub-card-bottom .btn{flex:1;justify-content:center;min-width:fit-content}

.subs-empty-v2{text-align:center;padding:70px 20px;background:var(--card);border:1px dashed var(--card-b);border-radius:20px;grid-column:1/-1}
.subs-empty-v2-icon{width:64px;height:64px;border-radius:18px;background:var(--purple-bg);display:flex;align-items:center;justify-content:center;font-size:28px;color:var(--purple);margin:0 auto 16px}
.subs-empty-v2-title{font-size:13.5px;font-weight:700;color:var(--t2);margin-bottom:5px}
.subs-empty-v2-sub{font-size:11px;color:var(--t3)}

/* ══════ create-group modal ══════ */
.modal-v2{background:var(--card);border:1px solid var(--card-b);border-radius:22px;padding:0;max-width:430px;width:calc(100% - 32px);max-height:92vh;overflow-y:auto;position:relative;animation:fi .2s ease;box-shadow:0 24px 70px rgba(0,0,0,.5)}
.modal-v2-head{background:linear-gradient(155deg,rgba(168,53,28,.14) 0%,transparent 65%);padding:18px 22px 14px;position:relative;overflow:hidden}
.modal-v2-head::before{content:'';position:absolute;top:-50px;left:-50px;width:160px;height:160px;background:radial-gradient(circle,rgba(168,53,28,.2),transparent 70%);pointer-events:none}
.modal-v2-close{position:absolute;top:14px;right:14px;background:var(--accent-d);border:1px solid var(--card-b);color:var(--t2);width:30px;height:30px;border-radius:9px;font-size:15px;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2;transition:.15s}
.modal-v2-close:hover{background:var(--red-bg);color:var(--red-t);border-color:rgba(179,58,34,.25)}
.modal-v2-icon{width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,var(--purple),#6B1A0B);display:flex;align-items:center;justify-content:center;color:#fff;font-size:19px;margin-bottom:10px;position:relative;z-index:1;box-shadow:0 8px 18px rgba(168,53,28,.4)}
.modal-v2-title{font-size:15.5px;font-weight:800;color:var(--t1);position:relative;z-index:1;letter-spacing:-.01em}
.modal-v2-sub{font-size:10.5px;color:var(--t3);margin-top:3px;position:relative;z-index:1;line-height:1.6}
.modal-v2-body{padding:16px 22px 20px;border-top:1px solid var(--card-b)}
.modal-v2-field{margin-bottom:11px}
.modal-v2-field label{display:flex;align-items:center;gap:5px;font-size:9.5px;font-weight:800;color:var(--t2);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.modal-v2-field label i{color:var(--purple);font-size:13px}
.modal-v2-input-wrap{position:relative}
.modal-v2-input-wrap>i{position:absolute;right:13px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:14px;pointer-events:none;transition:.15s;z-index:1}
.modal-v2-input{width:100%;padding:9px 38px 9px 13px;border-radius:11px;border:1px solid var(--card-b);background:rgba(0,0,0,.2);color:var(--t1);font-family:inherit;font-size:12.5px;outline:none;transition:.18s}
[data-theme="light"] .modal-v2-input{background:rgba(142,39,18,.04)}
.modal-v2-input::placeholder{color:var(--t3)}
.modal-v2-input:focus{border-color:rgba(168,53,28,.55);box-shadow:0 0 0 3px rgba(168,53,28,.12);background:rgba(0,0,0,.28)}
[data-theme="light"] .modal-v2-input:focus{background:#fff}
.modal-v2-input:focus~i{color:var(--purple)}
.modal-v2-hint{background:rgba(24,155,173,.08);border:1px solid rgba(24,155,173,.18);border-radius:11px;padding:9px 12px;font-size:10px;color:var(--t2);display:flex;gap:7px;align-items:flex-start;line-height:1.6;margin-top:2px}
.modal-v2-hint i{font-size:14px;color:var(--accent);margin-top:1px;flex-shrink:0}
.modal-v2-footer{display:flex;gap:8px;margin-top:15px}
.modal-v2-btn-cancel{flex:.75;justify-content:center;padding:10px;border-radius:11px;background:transparent;border:1px solid var(--card-b);color:var(--t2);font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;transition:.15s;display:flex;align-items:center}
.modal-v2-btn-cancel:hover{background:var(--accent-d);color:var(--t1)}
.modal-v2-btn-submit{flex:1;justify-content:center;padding:10px;border-radius:11px;background:linear-gradient(135deg,var(--purple),#6B1A0B);color:#fff;border:none;font-family:inherit;font-size:12px;font-weight:800;cursor:pointer;display:flex;align-items:center;gap:6px;box-shadow:0 6px 18px rgba(168,53,28,.4);transition:.18s}
.modal-v2-btn-submit:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(168,53,28,.5)}
.modal-v2-btn-submit:active{transform:translateY(0) scale(.98)}

/* ══════ config picker modal ══════ */
.lmodal-head{background:linear-gradient(155deg,var(--accent-d) 0%,transparent 70%);padding:22px 24px 18px;position:relative;border-bottom:1px solid var(--card-b)}
.lmodal-icon-row{display:flex;align-items:center;gap:12px;position:relative;z-index:1}
.lmodal-icon{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;color:#fff;font-size:19px;flex-shrink:0;box-shadow:0 6px 16px rgba(24,155,173,.35)}
.lmodal-title-v2{font-size:14.5px;font-weight:800;color:var(--t1)}
.lmodal-sub-v2{font-size:10.5px;color:var(--t3);margin-top:2px}
.lmodal-search{margin-top:14px;position:relative}
.lmodal-search input{width:100%;padding:10px 13px 10px 38px;border-radius:11px;border:1px solid var(--card-b);background:rgba(0,0,0,.2);color:var(--t1);font-family:inherit;font-size:12px;outline:none}
[data-theme="light"] .lmodal-search input{background:#fff}
.lmodal-search input:focus{border-color:rgba(24,155,173,.5);box-shadow:0 0 0 3px rgba(24,155,173,.1)}
.lmodal-search i{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--t3);font-size:14px}
.lmodal-quickbar{display:flex;gap:8px;margin-top:11px;position:relative;z-index:1}
.lmodal-qbtn{font-size:10px;font-weight:700;padding:5px 11px;border-radius:8px;background:var(--accent-d);color:var(--accent2);border:1px solid var(--card-b);cursor:pointer;transition:.15s;font-family:inherit}
.lmodal-qbtn:hover{background:rgba(24,155,173,.2)}
.lmodal-count{margin-left:auto;font-size:10.5px;color:var(--t3);display:flex;align-items:center}

.lmodal-list{padding:10px 14px;max-height:360px;overflow-y:auto}
.lrow-v2{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:13px;cursor:pointer;transition:.15s;margin-bottom:4px;border:1px solid transparent}
.lrow-v2:hover{background:var(--accent-d)}
.lrow-v2.checked{background:rgba(24,155,173,.1);border-color:rgba(24,155,173,.25)}
.lrow-v2-check{width:20px;height:20px;border-radius:7px;border:2px solid var(--card-b);flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:.15s;background:rgba(0,0,0,.14)}
.lrow-v2.checked .lrow-v2-check{background:var(--accent);border-color:var(--accent)}
.lrow-v2-check i{font-size:12px;color:#fff;opacity:0;transform:scale(.5);transition:.15s}
.lrow-v2.checked .lrow-v2-check i{opacity:1;transform:scale(1)}
.lrow-v2-avatar{width:34px;height:34px;border-radius:10px;background:var(--accent-d);color:var(--accent);display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.lrow-v2.checked .lrow-v2-avatar{background:var(--accent);color:#fff}
.lrow-v2-info{flex:1;min-width:0}
.lrow-v2-name{font-size:12.5px;font-weight:700;color:var(--t1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lrow-v2-meta{font-size:9.5px;color:var(--t3);margin-top:2px;display:flex;align-items:center;gap:6px}
.lrow-v2-status{font-size:9px;font-weight:800;padding:3px 9px;border-radius:20px;flex-shrink:0;white-space:nowrap}
.lrow-v2-status.on{background:var(--green-bg);color:var(--green-t)}
.lrow-v2-status.off{background:var(--red-bg);color:var(--red-t)}

.lmodal-footer{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:16px 24px;border-top:1px solid var(--card-b)}
.lmodal-footer-info{font-size:10.5px;color:var(--t3);display:flex;align-items:center;gap:6px}
.lmodal-footer-info i{color:var(--accent)}
.lmodal-footer-btns{display:flex;gap:8px}

@media(max-width:500px){.sub-grid{grid-template-columns:1fr}.sub-card-stats{grid-template-columns:repeat(3,1fr)}}

.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:500;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.modal-bg.open{display:flex}
.modal{background:var(--card);border:1px solid var(--card-b);border-radius:20px;padding:28px 26px;max-width:520px;width:calc(100% - 32px);max-height:90vh;overflow-y:auto;position:relative;animation:fi .2s ease}
.modal-close{position:absolute;top:14px;right:14px;background:var(--accent-d);border:1px solid var(--card-b);color:var(--t2);width:30px;height:30px;border-radius:8px;font-size:16px;display:flex;align-items:center;justify-content:center;cursor:pointer;border:none}
.modal-title{font-size:16px;font-weight:700;color:var(--t1);margin-bottom:18px;display:flex;align-items:center;gap:8px}
.modal-title i{color:var(--accent)}
.lrow{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid rgba(24,155,173,.05)}
.lrow:last-child{border-bottom:none}
.lrow-check{width:16px;height:16px;border-radius:4px;cursor:pointer;accent-color:var(--accent)}
.lrow-label{flex:1;font-size:12px;color:var(--t1)}
.lrow-badge{font-size:9px;padding:2px 7px;border-radius:5px;background:var(--green-bg);color:var(--green-t);font-weight:700}
.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%) translateY(40px);background:var(--card);border:1px solid var(--card-b);color:var(--t1);border-radius:10px;padding:10px 18px;font-size:12.5px;opacity:0;transition:all .25s;z-index:999;pointer-events:none;display:flex;align-items:center;gap:8px;box-shadow:var(--shadow);white-space:nowrap}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast.ok{border-color:rgba(18,160,139,.3);background:var(--green-bg);color:var(--green-t)}
.toast.err{border-color:rgba(179,58,34,.3);background:var(--red-bg);color:var(--red-t)}
.dash-footer{border-top:1px solid var(--card-b);margin-top:14px;padding-top:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
.df-text{font-size:10px;color:var(--t3)}
.df-link{font-size:11.5px;color:var(--accent2);display:flex;align-items:center;gap:5px;font-weight:600}

/* ══════ configs ══════ */
.cfg-grid{display:flex;flex-direction:column;gap:10px}
.cfg-card{background:var(--card);border:1px solid var(--card-b);border-radius:14px;padding:0;transition:all .2s cubic-bezier(.4,0,.2,1);position:relative;overflow:hidden}
.cfg-card:hover{border-color:var(--card-bh);box-shadow:0 6px 24px rgba(0,0,0,.18)}
.cfg-card.is-off{opacity:.6}
.cfg-card.is-exp{opacity:.78}
.cfg-row{display:flex;align-items:center;gap:16px;padding:14px 18px}
.cfg-status-dot{width:9px;height:9px;border-radius:50%;background:var(--green);flex-shrink:0;box-shadow:0 0 0 3px var(--green-bg)}
.cfg-card.is-off .cfg-status-dot{background:var(--red);box-shadow:0 0 0 3px var(--red-bg)}
.cfg-card.is-exp .cfg-status-dot{background:var(--amber);box-shadow:0 0 0 3px var(--amber-bg)}
.cfg-identity{display:flex;flex-direction:column;gap:3px;min-width:150px;flex-shrink:0}
.cfg-label{font-size:13.5px;font-weight:700;color:var(--t1);display:flex;align-items:center;gap:7px}
.cfg-sub-meta{display:flex;align-items:center;gap:8px;font-size:10px;color:var(--t3)}
.cfg-uuid-mini{font-family:ui-monospace,monospace;font-size:9.5px;color:var(--accent2);background:var(--accent-d);padding:2px 7px;border-radius:5px;cursor:pointer;transition:.15s}
.cfg-uuid-mini:hover{background:rgba(24,155,173,.2)}
.cfg-divider-v{width:1px;align-self:stretch;background:var(--card-b);flex-shrink:0}
.cfg-usage-col{flex:1;min-width:160px;display:flex;flex-direction:column;gap:5px}
.ubar{height:5px;border-radius:4px;background:rgba(24,155,173,0.1);overflow:hidden}
.ubar-f{height:100%;border-radius:4px;transition:width .4s ease}
.utxt{font-size:10px;color:var(--t3);display:flex;justify-content:space-between}
.cfg-exp-col{flex-shrink:0;min-width:110px}
.cfg-badges-col{display:flex;flex-direction:column;gap:5px;flex-shrink:0;align-items:flex-end}
.cfg-actions{display:flex;gap:5px;flex-shrink:0}
.proto-chip{font-size:9px;padding:3px 8px;border-radius:6px;font-weight:700;white-space:nowrap}
.pc-ws{background:var(--accent-d);color:var(--accent2)}
.pc-ultra{background:var(--green-bg);color:var(--green-t)}
.pc-auto{background:var(--accent-d);color:var(--accent)}
.cfg-sub-tag{font-size:9.5px;color:var(--t3);display:flex;align-items:center;gap:4px;white-space:nowrap}
.cfg-sub-tag i{color:var(--purple);font-size:11px}
.tog{width:19px;height:30px;border-radius:19px;background:rgba(120,124,125,0.25);position:relative;cursor:pointer;transition:.2s;flex-shrink:0;border:none}
.tog::after{content:'';position:absolute;width:13px;height:13px;border-radius:50%;background:#fff;left:3px;top:3px;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.tog.on::after{top:14px}
.tog.on{background:var(--green)}

@media(max-width:880px){
  .cfg-row{flex-wrap:wrap}
  .cfg-divider-v{display:none}
  .cfg-usage-col{min-width:100%;order:5}
}

/* ── below 768px: switch to mobile cards ── */
@media(max-width:768px){
  .cfg-grid{display:grid;grid-template-columns:1fr;gap:13px}
  .cfg-card{border-radius:16px}
  .cfg-row{flex-direction:column;align-items:stretch;gap:12px;padding:16px}
  .cfg-row-top{display:flex;align-items:center;justify-content:space-between;gap:10px}
  .cfg-identity{min-width:0;flex:1}
  .cfg-usage-col{min-width:0}
  .cfg-exp-col{min-width:0}
  .cfg-badges-col{flex-direction:row;align-items:center;flex-wrap:wrap}
  .cfg-actions{flex-wrap:wrap;border-top:1px solid var(--card-b);padding-top:10px;margin-top:2px;width:100%}
}

/* ══════ active connections with IP ���═════ */
.conn-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.conn-card{background:var(--card);border:1px solid var(--card-b);border-radius:16px;padding:15px 17px;transition:.2s;position:relative;overflow:hidden}
.conn-card:hover{border-color:var(--card-bh);transform:translateY(-1px)}
.conn-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--green)}
.conn-ip-row{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.conn-ip-icon{width:32px;height:32px;border-radius:9px;background:var(--green-bg);color:var(--green-t);display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
.conn-ip{font-family:ui-monospace,monospace;font-size:13px;font-weight:700;color:var(--t1)}
.conn-label{font-size:10.5px;color:var(--t3);margin-top:1px}
.conn-meta{display:flex;justify-content:space-between;align-items:center;font-size:10px;color:var(--t3);padding-top:10px;border-top:1px solid var(--card-b)}

/* ══════ Activity Log ══════ */
.log-timeline{display:flex;flex-direction:column}
.log-item{display:flex;gap:12px;padding:11px 0;border-bottom:1px solid rgba(24,155,173,.05);position:relative}
.log-item:last-child{border-bottom:none}
.log-ic{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.log-ic.ok{background:var(--green-bg);color:var(--green-t)}
.log-ic.err{background:var(--red-bg);color:var(--red-t)}
.log-ic.warn{background:var(--amber-bg);color:var(--amber-t)}
.log-ic.info{background:var(--accent-d);color:var(--accent2)}
.log-body{flex:1;min-width:0}
.log-msg{font-size:12.5px;color:var(--t1);line-height:1.6}
.log-time{font-size:9.5px;color:var(--t3);margin-top:2px;display:flex;align-items:center;gap:5px}
.log-kind{font-size:8.5px;padding:1px 7px;border-radius:10px;background:var(--accent-d);color:var(--accent2);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.erow{padding:9px 0;border-bottom:1px solid rgba(24,155,173,.05)}
.erow:last-child{border-bottom:none}
.etime{color:var(--t3);font-size:9.5px;margin-bottom:3px;display:flex;align-items:center;gap:4px}
.emsg{color:var(--red-t);font-family:ui-monospace,monospace;background:var(--red-bg);padding:6px 9px;border-radius:6px;word-break:break-all;font-size:10.5px}

@media(max-width:1050px){
  .sidebar{transform:translateX(-100%)}
  .sidebar.open{transform:translateX(0);box-shadow:10px 0 40px rgba(0,0,0,.4)}
  .sb-close{display:flex}
  .main{margin-left:0;padding-top:70px}
  .mob-top{display:flex}
  .metrics{grid-template-columns:1fr 1fr}
  .g2,.g3{grid-template-columns:1fr}
}
@media(max-width:500px){
  .metrics{grid-template-columns:1fr}
  .main{padding:62px 12px 50px}
  .sub-grid,.cfg-grid,.conn-grid{grid-template-columns:1fr}
}

/* ============ UI refinement layer ============ */
:root{--ink-brick:#791B0D;--ink-teal:#0D6A78;--ink-grey:#BFBFBF}
html{-webkit-text-size-adjust:100%}
body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;font-feature-settings:'ss01','ss02';line-height:1.7}
::selection{background:rgba(24,155,173,.32)}
*::-webkit-scrollbar{width:10px;height:10px}
*::-webkit-scrollbar-track{background:transparent}
*::-webkit-scrollbar-thumb{background:rgba(191,191,191,.22);border-radius:99px;border:2px solid transparent;background-clip:content-box}
*::-webkit-scrollbar-thumb:hover{background:rgba(24,155,173,.45);background-clip:content-box}
a,button,input,select,textarea{font-family:inherit}
button,a,.chip,.nav-it,.proto-card,.tog{transition:background .18s ease,color .18s ease,border-color .18s ease,transform .18s ease,box-shadow .18s ease}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{outline:2px solid #189BAD;outline-offset:2px;border-radius:10px}

/* ============ Exit IP / managed proxy panel ============ */
.ob-body{padding:18px;display:grid;gap:15px}
.ob-field label{display:block;margin-bottom:6px;font-size:13px;font-weight:600;opacity:.85}
.ob-field input,.ob-field select,.ob-field textarea{width:100%;padding:11px 12px;border-radius:11px;border:1px solid rgba(191,191,191,.2);background:rgba(255,255,255,.04);color:inherit;font-size:13.5px;outline:none}
.ob-field input:focus,.ob-field select:focus,.ob-field textarea:focus{border-color:rgba(24,155,173,.6);background:rgba(24,155,173,.06)}
.ob-field textarea{resize:vertical;min-height:74px;line-height:1.6;direction:ltr;text-align:left}
.ob-field input{direction:ltr;text-align:left}
.ob-hint{margin-top:6px;font-size:11.5px;opacity:.62;line-height:1.65}
.ob-hint code{background:rgba(191,191,191,.14);padding:1px 5px;border-radius:5px;font-size:11px;direction:ltr;display:inline-block}
.ob-grid2{display:grid;grid-template-columns:1fr 1fr;gap:15px}
.ob-check{display:flex;align-items:center;gap:9px;font-size:13px;opacity:.9;cursor:pointer}
.ob-check input{width:16px;height:16px;accent-color:#189BAD;cursor:pointer}
.ob-actions{display:flex;gap:10px;flex-wrap:wrap}
.ob-actions .pw-submit{flex:1;min-width:150px}
.ob-out{display:none;margin:0;padding:13px;border-radius:11px;background:rgba(0,0,0,.28);border:1px solid rgba(191,191,191,.16);font-size:11.5px;line-height:1.7;white-space:pre-wrap;word-break:break-all;direction:ltr;text-align:left;max-height:280px;overflow:auto}
.ob-badge{display:inline-flex;align-items:center;gap:5px;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:700}
.ob-badge.on{background:rgba(29,168,106,.16);color:#4ade80}
.ob-badge.off{background:rgba(191,191,191,.14);color:#BFBFBF}
@media(max-width:640px){.ob-grid2{grid-template-columns:1fr}}

body{font-size:14.5px}
.logo-img,.mob-logo{display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0D6A78,#791B0D);color:#fff;border-radius:13px;box-shadow:0 4px 14px rgba(13,106,120,.35);border:none}
.logo-img{width:40px;height:40px;font-size:20px}
.mob-logo{width:30px;height:30px;font-size:16px;border-radius:10px}
.logo-name{font-size:15.5px;font-weight:800;letter-spacing:-.01em}
.logo-sub{font-size:11.5px;letter-spacing:.03em}
.nav-sec{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.75;margin-top:18px}
.nav-it{font-size:14.5px;font-weight:500;border-radius:12px;padding:11px 13px;gap:11px}
.nav-it.on{font-weight:700}
.tb-title{font-size:23px;font-weight:800;letter-spacing:-.02em;line-height:1.4}
.tb-sub{font-size:13px;line-height:1.75;margin-top:5px}
.card{border-radius:18px}
.card-title{font-size:15px;font-weight:700;letter-spacing:-.01em;margin-bottom:16px}
.metric{border-radius:18px;padding:20px}
.m-label{font-size:12.5px;font-weight:600;letter-spacing:.01em}
.m-val{font-size:31px;font-weight:800;letter-spacing:-.03em;line-height:1.25}
.m-unit{font-size:14px;font-weight:600;margin-inline-start:5px;opacity:.75}
.m-sub{font-size:12px;line-height:1.6}
.btn{border-radius:12px;font-weight:600;letter-spacing:0;gap:8px}
.btn:hover{transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn-sm{font-size:12.5px}
.badge{font-size:11.5px;font-weight:600;letter-spacing:.01em;border-radius:99px}
.chip{border-radius:99px;font-size:12.5px;font-weight:600}
.fi,.fs,.cp-input-full,.modal-v2-input,.subs-search input{border-radius:12px;font-size:14px}
.fg label,.cp-block-label{font-size:12.5px;font-weight:600;letter-spacing:.01em}
.vl-code,.sub-url,.cfg-uuid-mini{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;line-height:1.9;letter-spacing:.01em;word-break:break-all}
.sr{padding:11px 0}
.sr-k{font-size:13.5px}
.sr-v{font-size:13px;font-weight:600}
.cl{border-radius:12px;font-size:12.5px;line-height:1.8}
.modal,.modal-v2{border-radius:20px}
.modal-title,.modal-v2-title,.lmodal-title-v2{font-size:17px;font-weight:800;letter-spacing:-.01em}
.modal-v2-sub,.lmodal-sub-v2{font-size:12.5px;line-height:1.75}
.toast{border-radius:14px;font-size:13.5px;font-weight:600}
.log-msg,.emsg{font-size:13.5px;line-height:1.75}
.log-time,.etime{font-size:11.5px;letter-spacing:.02em}
.empty{font-size:13.5px;line-height:1.9}
.dash-footer{font-size:12.5px}

/* ---- iCloud style activity spinner ---- */
.aspin{display:inline-block;position:relative;width:18px;height:18px;color:currentColor;vertical-align:-4px}
.aspin b{position:absolute;top:0;left:50%;width:2px;height:5px;margin-left:-1px;border-radius:2px;background:currentColor;transform-origin:1px 9px;animation:aspin-fade 1s linear infinite;opacity:.12}
.aspin b:nth-child(1){transform:rotate(0deg);animation-delay:-0.917s}
.aspin b:nth-child(2){transform:rotate(30deg);animation-delay:-0.833s}
.aspin b:nth-child(3){transform:rotate(60deg);animation-delay:-0.750s}
.aspin b:nth-child(4){transform:rotate(90deg);animation-delay:-0.667s}
.aspin b:nth-child(5){transform:rotate(120deg);animation-delay:-0.583s}
.aspin b:nth-child(6){transform:rotate(150deg);animation-delay:-0.500s}
.aspin b:nth-child(7){transform:rotate(180deg);animation-delay:-0.417s}
.aspin b:nth-child(8){transform:rotate(210deg);animation-delay:-0.333s}
.aspin b:nth-child(9){transform:rotate(240deg);animation-delay:-0.250s}
.aspin b:nth-child(10){transform:rotate(270deg);animation-delay:-0.167s}
.aspin b:nth-child(11){transform:rotate(300deg);animation-delay:-0.083s}
.aspin b:nth-child(12){transform:rotate(330deg);animation-delay:-0.000s}
@keyframes aspin-fade{0%{opacity:1}100%{opacity:.12}}
.aspin-lg{width:30px;height:30px}
.aspin-lg b{width:3px;height:8px;margin-left:-1.5px;transform-origin:1.5px 15px}
.aspin-box{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:40px 20px;color:var(--t3);font-size:12.5px}
@media(prefers-reduced-motion:reduce){.aspin b{animation:none;opacity:.45}}

/* ═══════════════════════════════════════════════════════════════════════════
   Lumen Console · Material 3 Expressive web implementation
   Seed family: indigo / plum / copper. Components consume semantic tokens.
   ═══════════════════════════════════════════════════════════════════════════ */
:root{
  color-scheme:dark;
  --md-sys-color-primary:#BDC7FF;
  --md-sys-color-on-primary:#22305F;
  --md-sys-color-primary-container:#394777;
  --md-sys-color-on-primary-container:#DEE1FF;
  --md-sys-color-secondary:#C7C5DD;
  --md-sys-color-on-secondary:#303044;
  --md-sys-color-secondary-container:#47465C;
  --md-sys-color-on-secondary-container:#E4E1FA;
  --md-sys-color-tertiary:#F2B99A;
  --md-sys-color-on-tertiary:#51250E;
  --md-sys-color-tertiary-container:#6D3B22;
  --md-sys-color-on-tertiary-container:#FFDCC8;
  --md-sys-color-error:#FFB4AB;
  --md-sys-color-on-error:#690005;
  --md-sys-color-error-container:#93000A;
  --md-sys-color-on-error-container:#FFDAD6;
  --md-sys-color-surface:#111318;
  --md-sys-color-on-surface:#E3E2E9;
  --md-sys-color-on-surface-variant:#C6C5D0;
  --md-sys-color-surface-container-lowest:#0B0E13;
  --md-sys-color-surface-container-low:#191B21;
  --md-sys-color-surface-container:#1D1F25;
  --md-sys-color-surface-container-high:#27292F;
  --md-sys-color-surface-container-highest:#32343A;
  --md-sys-color-surface-dim:#111318;
  --md-sys-color-surface-bright:#37393F;
  --md-sys-color-outline:#90909B;
  --md-sys-color-outline-variant:#46464F;
  --md-sys-color-inverse-surface:#E3E2E9;
  --md-sys-color-inverse-on-surface:#2E3036;
  --md-sys-color-inverse-primary:#52639A;
  --md-ref-typeface-brand:'Roboto Flex','Vazirmatn','Segoe UI',sans-serif;
  --md-ref-typeface-plain:'Roboto Flex','Vazirmatn','Segoe UI',sans-serif;
  --md-sys-shape-corner-extra-small:4px;
  --md-sys-shape-corner-small:8px;
  --md-sys-shape-corner-medium:12px;
  --md-sys-shape-corner-large:16px;
  --md-sys-shape-corner-large-increased:20px;
  --md-sys-shape-corner-extra-large:28px;
  --md-sys-shape-corner-extra-large-increased:32px;
  --md-sys-shape-corner-extra-extra-large:48px;
  --md-sys-shape-corner-full:9999px;
  --md-sys-motion-easing-emphasized:cubic-bezier(.2,0,0,1);
  --md-sys-motion-easing-emphasized-decelerate:cubic-bezier(.05,.7,.1,1);
  --md-sys-motion-easing-emphasized-accelerate:cubic-bezier(.3,0,.8,.15);
  --md-sys-motion-duration-short:180ms;
  --md-sys-motion-duration-medium:320ms;
  --md-sys-motion-duration-long:500ms;
  --bg:var(--md-sys-color-surface);
  --bg2:var(--md-sys-color-surface-container);
  --bg3:var(--md-sys-color-surface-container-highest);
  --card:var(--md-sys-color-surface-container-low);
  --card-b:var(--md-sys-color-outline-variant);
  --card-bh:var(--md-sys-color-outline);
  --accent:var(--md-sys-color-primary);
  --accent2:var(--md-sys-color-primary);
  --accent-d:var(--md-sys-color-primary-container);
  --green:#8FD6B8;--green-bg:#173D32;--green-t:#A9EECF;
  --red:var(--md-sys-color-error);--red-bg:var(--md-sys-color-error-container);--red-t:var(--md-sys-color-on-error-container);
  --amber:var(--md-sys-color-tertiary);--amber-bg:var(--md-sys-color-tertiary-container);--amber-t:var(--md-sys-color-on-tertiary-container);
  --purple:var(--md-sys-color-secondary);--purple-bg:var(--md-sys-color-secondary-container);
  --t1:var(--md-sys-color-on-surface);--t2:var(--md-sys-color-on-surface-variant);--t3:var(--md-sys-color-outline);
  --sidebar-w:288px;
  --radius:var(--md-sys-shape-corner-large-increased);
  --shadow:0 18px 44px rgba(4,6,14,.26),0 3px 10px rgba(4,6,14,.18);
}
[data-theme="light"]{
  color-scheme:light;
  --md-sys-color-primary:#52639A;
  --md-sys-color-on-primary:#FFFFFF;
  --md-sys-color-primary-container:#DEE1FF;
  --md-sys-color-on-primary-container:#0C1B4B;
  --md-sys-color-secondary:#5E5D72;
  --md-sys-color-on-secondary:#FFFFFF;
  --md-sys-color-secondary-container:#E4E1FA;
  --md-sys-color-on-secondary-container:#1B1B2C;
  --md-sys-color-tertiary:#865228;
  --md-sys-color-on-tertiary:#FFFFFF;
  --md-sys-color-tertiary-container:#FFDCC8;
  --md-sys-color-on-tertiary-container:#311300;
  --md-sys-color-error:#BA1A1A;
  --md-sys-color-on-error:#FFFFFF;
  --md-sys-color-error-container:#FFDAD6;
  --md-sys-color-on-error-container:#410002;
  --md-sys-color-surface:#FAF8FF;
  --md-sys-color-on-surface:#1A1B20;
  --md-sys-color-on-surface-variant:#45464F;
  --md-sys-color-surface-container-lowest:#FFFFFF;
  --md-sys-color-surface-container-low:#F4F2FA;
  --md-sys-color-surface-container:#EEECF4;
  --md-sys-color-surface-container-high:#E8E7EE;
  --md-sys-color-surface-container-highest:#E2E1E9;
  --md-sys-color-surface-dim:#DAD9E1;
  --md-sys-color-surface-bright:#FAF8FF;
  --md-sys-color-outline:#767680;
  --md-sys-color-outline-variant:#C7C6D0;
  --md-sys-color-inverse-surface:#2F3036;
  --md-sys-color-inverse-on-surface:#F1F0F7;
  --md-sys-color-inverse-primary:#BDC7FF;
  --green:#1C6B50;--green-bg:#B9F2D5;--green-t:#123E30;
  --shadow:0 20px 46px rgba(40,43,65,.12),0 3px 12px rgba(40,43,65,.08);
}
html{background:var(--md-sys-color-surface);scroll-behavior:smooth}
body{
  font-family:var(--md-ref-typeface-plain);
  background:
    radial-gradient(circle at 78% -8%,color-mix(in srgb,var(--md-sys-color-primary) 15%,transparent) 0,transparent 34rem),
    radial-gradient(circle at 12% 88%,color-mix(in srgb,var(--md-sys-color-tertiary) 9%,transparent) 0,transparent 30rem),
    var(--md-sys-color-surface);
  color:var(--md-sys-color-on-surface);
  letter-spacing:.01em;
}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:-1;background-image:linear-gradient(color-mix(in srgb,var(--md-sys-color-outline-variant) 22%,transparent) 1px,transparent 1px),linear-gradient(90deg,color-mix(in srgb,var(--md-sys-color-outline-variant) 18%,transparent) 1px,transparent 1px);background-size:64px 64px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.32),transparent 68%)}
::selection{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}
.sidebar{
  width:var(--sidebar-w);min-height:0;left:16px;top:16px;bottom:16px;
  border:1px solid var(--md-sys-color-outline-variant);border-right:1px solid var(--md-sys-color-outline-variant);
  border-radius:var(--md-sys-shape-corner-extra-large-increased);
  background:color-mix(in srgb,var(--md-sys-color-surface-container) 94%,transparent);
  backdrop-filter:blur(24px) saturate(1.15);box-shadow:var(--shadow);overflow:hidden;
}
.logo{padding:24px 20px 18px;border-bottom:0;gap:14px}
.logo-img,.mob-logo{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container);border-radius:var(--md-sys-shape-corner-large)!important;box-shadow:none;border:1px solid color-mix(in srgb,var(--md-sys-color-primary) 32%,transparent)}
.logo-img{width:48px;height:48px;font-size:24px}
.logo-name{font:700 1.05rem/1.35 var(--md-ref-typeface-brand);color:var(--md-sys-color-on-surface)}
.logo-sub{font-size:.72rem;color:var(--md-sys-color-on-surface-variant);margin-top:3px}
.nav-wrap{padding:8px 12px 16px}
.nav-sec{padding:18px 14px 8px;font-size:.67rem;letter-spacing:.12em;color:var(--md-sys-color-outline);font-weight:700}
.nav-it{min-height:48px;margin:2px 0;padding:10px 14px;border:0;border-radius:var(--md-sys-shape-corner-full);color:var(--md-sys-color-on-surface-variant);font-size:.86rem;font-weight:560;gap:12px;transition:background var(--md-sys-motion-duration-short),color var(--md-sys-motion-duration-short),transform var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized)}
.nav-it i{width:24px;font-size:20px}.nav-it:hover{background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface);transform:translateX(3px)}
.nav-it.on{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);font-weight:720;border:0}
.nav-it.on i{color:var(--md-sys-color-primary)}
.nav-badge{margin-left:auto;background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);min-width:24px;text-align:center;padding:2px 8px}
.sb-foot{padding:12px 16px 18px;border-top:1px solid var(--md-sys-color-outline-variant);background:var(--md-sys-color-surface-container-low)}
.theme-btn,.logout-btn{min-height:44px;border-radius:var(--md-sys-shape-corner-full);border:0;font-weight:650}
.theme-btn{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}
.logout-btn{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}
.main{margin-left:calc(var(--sidebar-w) + 32px);padding:24px 28px 72px;min-height:100vh}
.pg{max-width:1240px;margin:0 auto}.pg.on{animation:md-page-in var(--md-sys-motion-duration-long) var(--md-sys-motion-easing-emphasized-decelerate)}
@keyframes md-page-in{from{opacity:0;transform:translateY(20px) scale(.992)}to{opacity:1;transform:none}}
.topbar{position:sticky;top:16px;z-index:80;min-height:72px;align-items:center;padding:12px 16px 12px 20px;margin-bottom:24px;border:1px solid var(--md-sys-color-outline-variant);border-radius:var(--md-sys-shape-corner-extra-large);background:color-mix(in srgb,var(--md-sys-color-surface-container-low) 86%,transparent);backdrop-filter:blur(24px) saturate(1.2);box-shadow:0 6px 20px rgba(4,6,14,.08)}
.tb-title{font:720 1.45rem/1.45 var(--md-ref-typeface-brand);letter-spacing:-.02em;color:var(--md-sys-color-on-surface)}
.tb-title i{width:40px;height:40px;display:grid;place-items:center;border-radius:var(--md-sys-shape-corner-large);background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container);font-size:21px}.tb-sub{font-size:.78rem;color:var(--md-sys-color-on-surface-variant);margin-left:52px;margin-top:-5px}
.metrics{gap:16px;margin-bottom:24px}.metric{min-height:168px;padding:22px;border:0;border-radius:var(--md-sys-shape-corner-extra-large);background:var(--md-sys-color-surface-container-low);box-shadow:none;display:flex;flex-direction:column;justify-content:space-between}
.metric:nth-child(1){border-radius:var(--md-sys-shape-corner-extra-extra-large) var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large)}
.metric:nth-child(2){background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}
.metric:nth-child(3){background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}
.metric:nth-child(4){background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);border-radius:var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-extra-large) var(--md-sys-shape-corner-extra-large) var(--md-sys-shape-corner-extra-large)}
.metric::after{display:none}.metric:hover{border:0;transform:translateY(-5px) rotateX(1deg);box-shadow:var(--shadow)}
.m-icon{width:44px;height:44px;border-radius:var(--md-sys-shape-corner-large);background:color-mix(in srgb,currentColor 12%,transparent);color:currentColor}.m-label{font-size:.75rem;color:currentColor;opacity:.78}.m-val{font:760 2.25rem/1.1 var(--md-ref-typeface-brand);color:currentColor}.m-sub{color:currentColor;opacity:.68}
.card,.vless-box,.create-panel,.conn-card,.sub-card,.traf-chart-card,.srv-panel{border:1px solid var(--md-sys-color-outline-variant);background:var(--md-sys-color-surface-container-low);border-radius:var(--md-sys-shape-corner-extra-large);box-shadow:none}
.card:hover,.conn-card:hover,.sub-card:hover{border-color:var(--md-sys-color-outline);transform:translateY(-3px);box-shadow:0 14px 36px rgba(4,6,14,.12)}
.card-title{font:700 1rem/1.5 var(--md-ref-typeface-brand);color:var(--md-sys-color-on-surface)}
.vless-box{padding:24px;background:var(--md-sys-color-surface-container-lowest);position:relative;overflow:hidden}.vless-box::after{content:'';position:absolute;right:-80px;top:-100px;width:260px;height:260px;border-radius:50%;background:var(--md-sys-color-primary-container);filter:blur(4px);opacity:.22;pointer-events:none}.vl-code{position:relative;border:1px solid var(--md-sys-color-outline-variant);background:var(--md-sys-color-surface-container);border-radius:var(--md-sys-shape-corner-large);padding:18px}
.btn,.pw-submit,.cp-submit-btn{min-height:48px;border-radius:var(--md-sys-shape-corner-full)!important;border:0;font:700 .86rem/1 var(--md-ref-typeface-plain);padding:0 22px;transition:transform var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized),filter var(--md-sys-motion-duration-short),background var(--md-sys-motion-duration-short)}
.btn-p,.pw-submit,.cp-submit-btn{background:var(--md-sys-color-primary)!important;color:var(--md-sys-color-on-primary)!important}.btn-g,.btn-o{background:var(--md-sys-color-secondary-container)!important;color:var(--md-sys-color-on-secondary-container)!important;border:0!important}.btn-pur{background:var(--md-sys-color-tertiary-container)!important;color:var(--md-sys-color-on-tertiary-container)!important}.btn-d{background:var(--md-sys-color-error-container)!important;color:var(--md-sys-color-on-error-container)!important}.btn:hover,.pw-submit:hover,.cp-submit-btn:hover{transform:translateY(-3px);filter:brightness(1.04)}.btn:active,.pw-submit:active,.cp-submit-btn:active{transform:scale(.97);border-radius:var(--md-sys-shape-corner-large)!important}
.btn-icon{width:48px!important;min-width:48px;padding:0!important}.badge,.proto-chip,.chip,.cfg-sub-tag,.endpoint-status{border-radius:var(--md-sys-shape-corner-full);font-weight:680}.badge{padding:7px 12px}.bg-blue,.pc-ws{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}.bg-purple{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}
.create-panel{overflow:hidden;border:0;background:var(--md-sys-color-surface-container-lowest);box-shadow:0 20px 55px rgba(4,6,14,.12)}
.cp-head{padding:26px 28px;background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container);border:0}.cp-head-icon{width:56px;height:56px;border-radius:var(--md-sys-shape-corner-large-increased);background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);font-size:27px}.cp-head-title{font:760 1.35rem/1.4 var(--md-ref-typeface-brand)}.cp-head-sub{color:var(--md-sys-color-on-primary-container);opacity:.74}.cp-body{padding:28px;display:grid;gap:20px}.cp-block{background:var(--md-sys-color-surface-container-low);border:0;border-radius:var(--md-sys-shape-corner-large-increased);padding:20px}.cp-row{gap:16px}.cp-block-label{font:700 .8rem/1.4 var(--md-ref-typeface-plain);color:var(--md-sys-color-on-surface);margin-bottom:12px}.cp-block-label i{color:var(--md-sys-color-primary)}
.fi,.fs,.cp-input-full,.modal-v2-input,.subs-search input,.ob-field input,.ob-field select,.ob-field textarea{min-height:52px;border:1px solid var(--md-sys-color-outline)!important;border-radius:var(--md-sys-shape-corner-small)!important;background:var(--md-sys-color-surface-container-lowest)!important;color:var(--md-sys-color-on-surface)!important;padding:13px 15px;outline:0;transition:border-color var(--md-sys-motion-duration-short),box-shadow var(--md-sys-motion-duration-short),background var(--md-sys-motion-duration-short)}
.fi:focus,.fs:focus,.cp-input-full:focus,.modal-v2-input:focus,.subs-search input:focus,.ob-field input:focus,.ob-field select:focus,.ob-field textarea:focus{border-color:var(--md-sys-color-primary)!important;box-shadow:0 0 0 3px color-mix(in srgb,var(--md-sys-color-primary) 22%,transparent);background:var(--md-sys-color-surface-container-low)!important}.chip{min-height:36px;display:inline-flex;align-items:center;padding:0 14px;background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface-variant);border:0}.chip.active{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}
.endpoint-studio{padding:0;overflow:hidden;background:var(--md-sys-color-surface-container)}.endpoint-studio-head{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:20px 22px;border-bottom:1px solid var(--md-sys-color-outline-variant)}.endpoint-studio-sub{font-size:.77rem;color:var(--md-sys-color-on-surface-variant);margin-top:3px}.endpoint-status{display:inline-flex;align-items:center;gap:7px;padding:8px 12px;background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);font-size:.72rem;white-space:nowrap}.endpoint-status.custom{background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container)}.endpoint-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:20px 22px}.endpoint-field{padding:18px;background:var(--md-sys-color-surface-container-low);border-radius:var(--md-sys-shape-corner-large-increased)}.endpoint-field>label{display:flex;align-items:center;gap:8px;font-weight:720;margin-bottom:10px}.step-dot{width:26px;height:26px;display:grid;place-items:center;border-radius:50%;background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);font-size:.72rem}.endpoint-custom{animation:md-field-in 260ms var(--md-sys-motion-easing-emphasized-decelerate)}@keyframes md-field-in{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}.endpoint-help{font-size:.72rem;line-height:1.55;color:var(--md-sys-color-on-surface-variant);margin-top:8px}.endpoint-help code{color:var(--md-sys-color-primary)}.endpoint-ltr{direction:ltr;text-align:left;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.endpoint-preview{display:flex;align-items:center;justify-content:center;gap:18px;padding:16px 22px;background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface)}.endpoint-preview>div{display:flex;align-items:center;gap:10px;min-width:0}.endpoint-preview span{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--md-sys-color-on-surface-variant)}.endpoint-preview code{font-size:.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--md-sys-color-primary)}.endpoint-preview>i{color:var(--md-sys-color-tertiary)}
.proto-card{min-height:112px;border:0!important;border-radius:var(--md-sys-shape-corner-extra-large)!important;background:var(--md-sys-color-secondary-container)!important;color:var(--md-sys-color-on-secondary-container)!important}.proto-card.active{box-shadow:inset 0 0 0 2px var(--md-sys-color-secondary)}.proto-card-icon{background:var(--md-sys-color-primary-container)!important;color:var(--md-sys-color-on-primary-container)!important}
.cfg-grid{gap:16px}.cfg-card{border:1px solid var(--md-sys-color-outline-variant);border-radius:var(--md-sys-shape-corner-extra-large);background:var(--md-sys-color-surface-container-low);overflow:hidden;transition:transform var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized),border-color var(--md-sys-motion-duration-short),box-shadow var(--md-sys-motion-duration-medium)}.cfg-card:hover{transform:translateY(-4px);border-color:var(--md-sys-color-outline);box-shadow:var(--shadow)}.cfg-row{padding:20px}.cfg-status-dot{width:10px;height:10px;background:var(--green);box-shadow:0 0 0 5px color-mix(in srgb,var(--green) 16%,transparent)}.cfg-uuid-mini{background:var(--md-sys-color-surface-container-high);border-radius:var(--md-sys-shape-corner-full);padding:4px 9px}.cfg-badges-col{align-items:flex-start;max-width:250px}.cfg-sub-tag{padding:4px 9px;background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface-variant);max-width:240px;overflow:hidden;text-overflow:ellipsis}.cfg-sub-tag i{color:var(--md-sys-color-tertiary)}.endpoint-tag{font-family:ui-monospace,SFMono-Regular,monospace}.tog{width:32px;height:52px;background:var(--md-sys-color-surface-container-highest)}.tog::after{width:22px;height:22px;left:5px;top:5px;background:var(--md-sys-color-outline)}.tog.on{background:var(--md-sys-color-primary)}.tog.on::after{top:25px;background:var(--md-sys-color-on-primary)}
.modal-bg{background:color-mix(in srgb,var(--md-sys-color-surface) 56%,transparent);backdrop-filter:blur(12px)}.modal,.modal-v2,.lmodal{border:1px solid var(--md-sys-color-outline-variant);border-radius:var(--md-sys-shape-corner-extra-large-increased);background:var(--md-sys-color-surface-container-high);box-shadow:0 28px 80px rgba(4,6,14,.38);animation:md-dialog-in 380ms var(--md-sys-motion-easing-emphasized-decelerate)}@keyframes md-dialog-in{from{opacity:0;transform:translateY(24px) scale(.94)}to{opacity:1;transform:none}}.modal-close,.modal-v2-close,.sb-close{width:48px;height:48px;border-radius:var(--md-sys-shape-corner-full);background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container);border:0}
.toast{min-height:52px;padding:14px 18px;border-radius:var(--md-sys-shape-corner-small);background:var(--md-sys-color-inverse-surface);color:var(--md-sys-color-inverse-on-surface);box-shadow:var(--shadow)}
.mob-top{height:72px;padding:0 16px;background:color-mix(in srgb,var(--md-sys-color-surface-container) 88%,transparent);border-bottom:1px solid var(--md-sys-color-outline-variant);backdrop-filter:blur(20px)}.menu-btn,.theme-mob{width:48px;height:48px;border-radius:var(--md-sys-shape-corner-full);border:0;background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}
@media(max-width:1050px){.sidebar{left:12px;top:12px;bottom:12px;transform:translateX(calc(-100% - 28px))}.sidebar.open{transform:translateX(0)}.main{margin-left:0;padding:92px 24px 72px}.topbar{top:84px}.mob-top{display:flex}.metrics{grid-template-columns:repeat(2,1fr)}}
@media(max-width:839px){.endpoint-grid{grid-template-columns:1fr}.endpoint-preview{align-items:stretch;flex-direction:column;gap:10px}.endpoint-preview>i{transform:rotate(90deg);align-self:center}.cp-row{grid-template-columns:1fr!important}.cfg-row{padding:18px}.cfg-badges-col{max-width:none}.topbar{position:relative;top:auto}.main{padding:88px 16px 48px}}
@media(max-width:599px){.metrics{grid-template-columns:1fr}.metric{min-height:150px}.cp-body{padding:16px}.cp-head{padding:22px 18px}.endpoint-studio-head{align-items:flex-start;flex-direction:column}.endpoint-grid{padding:14px}.endpoint-preview{padding:14px}.main{padding-left:12px;padding-right:12px}.topbar{border-radius:var(--md-sys-shape-corner-large-increased);padding:12px}.tb-sub{margin-left:0}.tb-right{width:100%}.tb-right .btn{flex:1}.cfg-actions{display:grid;grid-template-columns:repeat(4,48px);justify-content:start}.modal,.modal-v2{width:calc(100vw - 24px);max-height:calc(100vh - 24px);overflow:auto;border-radius:var(--md-sys-shape-corner-extra-large)}}
@media(hover:hover){.btn:hover,.nav-it:hover,.chip:hover{filter:brightness(1.04)}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}


/* ═══════════════════════════════════════════════════════════════════════════
   Lumen Relay v16 · command rail + route studio
   A second expressive composition, intentionally unlike the v11 sidebar.
   ═══════════════════════════════════════════════════════════════════════════ */
:root{--command-rail-w:108px;--v12-card-gap:18px}
body{padding-right:0}
.sidebar{left:auto!important;right:16px!important;top:16px!important;bottom:16px!important;width:var(--command-rail-w)!important;min-height:0!important;border-radius:38px!important;display:flex!important;flex-direction:column!important;overflow:hidden!important;transform:none!important;background:color-mix(in srgb,var(--md-sys-color-surface-container) 96%,transparent)!important}
.logo{padding:18px 10px 13px!important;gap:8px!important;flex-direction:column!important;text-align:center!important}.logo-img{width:44px!important;height:44px!important}.logo-name{font-size:.72rem!important;line-height:1.1!important}.logo-sub{display:none!important}.sb-close{display:none!important}
.nav-wrap{display:flex!important;flex:1!important;min-height:0;flex-direction:column!important;gap:3px!important;padding:8px!important;overflow-y:auto!important;overflow-x:hidden!important;scrollbar-width:none}.nav-wrap::-webkit-scrollbar{display:none}.nav-sec{display:none!important}
.nav-it{position:relative!important;min-height:58px!important;margin:0!important;padding:8px 4px!important;display:flex!important;flex-direction:column!important;justify-content:center!important;gap:5px!important;text-align:center!important;border-radius:18px!important;font-size:.62rem!important;line-height:1.1!important;font-weight:650!important;transform:none!important;flex-shrink:0}.nav-it>i{width:auto!important;font-size:20px!important}.nav-it>span:not(.nav-badge){max-width:86px;overflow:hidden;text-overflow:ellipsis}.nav-it:hover{transform:none!important;background:var(--md-sys-color-surface-container-high)!important}.nav-it.on{border-radius:24px 24px 12px 24px!important;background:var(--md-sys-color-primary-container)!important;color:var(--md-sys-color-on-primary-container)!important}.nav-it.on i{color:var(--md-sys-color-on-primary-container)!important}.nav-badge{position:absolute!important;right:8px!important;top:6px!important;margin:0!important;min-width:18px!important;padding:2px 5px!important;font-size:.55rem!important;background:var(--md-sys-color-tertiary-container)!important;color:var(--md-sys-color-on-tertiary-container)!important}
.sb-foot{padding:9px!important;display:grid!important;grid-template-columns:1fr 1fr!important;gap:6px!important;background:var(--md-sys-color-surface-container-low)!important}.lang-switch,.theme-btn,.logout-btn{width:100%!important;min-width:0!important;min-height:42px!important;margin:0!important;padding:0!important;border:0!important;border-radius:15px!important;display:grid!important;place-items:center!important;cursor:pointer!important}.lang-switch{background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container)}.lang-switch span,.theme-btn span,.logout-btn span{display:none}.logout-btn{grid-column:1/-1!important;background:var(--md-sys-color-error-container)!important;color:var(--md-sys-color-on-error-container)!important}.lang-switch i,.theme-btn i,.logout-btn i{font-size:18px!important}
.main{margin-left:0!important;margin-right:calc(var(--command-rail-w) + 34px)!important;padding:24px 24px 72px!important}.pg{max-width:1380px!important}.topbar{top:16px!important}.tb-title{font-size:1.55rem!important}.tb-title i{border-radius:18px 18px 8px 18px!important}.tb-sub{margin-inline-start:52px!important;margin-left:0!important}
/* Builder composition */
.create-panel{display:grid!important;grid-template-columns:minmax(220px,290px) minmax(0,1fr)!important;align-items:stretch!important;background:var(--md-sys-color-surface-container-lowest)!important;border-radius:36px!important;margin-bottom:26px!important}.cp-head{grid-column:1!important;grid-row:1!important;align-self:stretch!important;flex-direction:column!important;justify-content:flex-start!important;align-items:flex-start!important;gap:20px!important;padding:36px 28px!important;border-radius:36px 0 0 36px!important;background:linear-gradient(155deg,var(--md-sys-color-primary-container),color-mix(in srgb,var(--md-sys-color-tertiary-container) 56%,var(--md-sys-color-primary-container)))!important;position:relative!important;overflow:hidden!important}.cp-head::after{content:'';position:absolute;left:-70px;bottom:-85px;width:240px;height:240px;border-radius:50%;border:36px solid color-mix(in srgb,var(--md-sys-color-primary) 15%,transparent);opacity:.9}.cp-head-icon{width:68px!important;height:68px!important;border-radius:26px 26px 10px 26px!important;font-size:30px!important;box-shadow:0 18px 36px color-mix(in srgb,var(--md-sys-color-on-primary-container) 14%,transparent)!important}.cp-head-title{font-size:1.75rem!important;line-height:1.12!important;letter-spacing:-.045em!important;max-width:8ch}.cp-head-sub{font-size:.82rem!important;line-height:1.75!important;max-width:22ch!important}.cp-head-text{z-index:1!important}.cp-body{grid-column:2!important;display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:14px!important;padding:22px!important}.create-panel .cp-row{display:contents!important}.create-panel .cp-body>.cp-block,.create-panel .endpoint-studio,.create-panel .cp-footer,.create-panel .cp-block:has(#nl-speed){grid-column:1/-1!important}.create-panel .cp-block{margin:0!important;padding:20px!important;border-radius:22px!important;background:var(--md-sys-color-surface-container-low)!important;border:1px solid transparent!important;transition:border-color 180ms,transform 260ms var(--md-sys-motion-easing-emphasized)!important}.create-panel .cp-block:focus-within{border-color:var(--md-sys-color-primary)!important;transform:translateY(-2px)!important}.cp-block-label{font-size:.73rem!important;letter-spacing:.055em!important;text-transform:uppercase!important}.cp-mini-row{margin-top:10px!important}.field-caption{font-size:.7rem;line-height:1.55;color:var(--md-sys-color-on-surface-variant);margin-top:10px}.endpoint-studio{padding:0!important;background:var(--md-sys-color-surface-container)!important;border:0!important}.endpoint-studio-head{padding:22px 24px!important}.endpoint-grid{padding:18px!important}.endpoint-field{background:var(--md-sys-color-surface-container-lowest)!important}.cp-footer{display:grid!important;grid-template-columns:1fr auto!important;align-items:center!important;gap:18px!important;padding:18px 4px 4px!important}.cp-footer-note{font-size:.72rem!important;line-height:1.6!important}.cp-submit-btn{min-width:190px!important;min-height:56px!important;border-radius:20px 20px 8px 20px!important;box-shadow:0 14px 30px color-mix(in srgb,var(--md-sys-color-primary) 18%,transparent)!important}
.config-proxy-studio{grid-column:1/-1!important;background:var(--md-sys-color-surface-container)!important;padding:0!important;overflow:hidden}.config-proxy-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:20px 22px;border-bottom:1px solid var(--md-sys-color-outline-variant)}.config-scope-badge{display:inline-flex;align-items:center;gap:6px;padding:8px 11px;border-radius:999px;background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container);font-size:.68rem;font-weight:750;white-space:nowrap}.config-proxy-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.repository-refresh-btn{min-height:40px;border:0;border-radius:999px;padding:0 13px;align-items:center;gap:6px;background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);font:700 .7rem inherit;cursor:pointer}.repository-refresh-btn:disabled{opacity:.55;cursor:wait}.config-proxy-grid{padding:18px;display:grid;grid-template-columns:minmax(210px,.7fr) 1.3fr;gap:14px}.proxy-mode-card,.config-proxy-fields{padding:16px;border-radius:18px;background:var(--md-sys-color-surface-container-lowest)}.proxy-mode-card label,.config-proxy-fields label{display:block;font-size:.72rem;font-weight:700;margin-bottom:8px}.config-proxy-fields{grid-template-columns:1fr 130px;gap:12px}.config-proxy-fields:not([style*="display: none"]){display:grid!important}.config-proxy-fields textarea{resize:vertical;min-height:70px}.proxy-safe-note{margin:0 18px 18px;padding:13px 15px;display:flex;gap:9px;align-items:flex-start;border-radius:16px;background:color-mix(in srgb,var(--green) 12%,var(--md-sys-color-surface-container-low));color:var(--md-sys-color-on-surface-variant);font-size:.72rem;line-height:1.6}.proxy-safe-note i{color:var(--green);font-size:18px}.route-proxy{margin:10px 18px 0;min-height:38px;padding:8px 11px;border-radius:13px;display:flex;align-items:center;gap:7px;font-size:.68rem;font-weight:700;background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface-variant)}.route-proxy.enabled{background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container)}.route-proxy code{margin-inline-start:auto;max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;direction:ltr}.config-proxy-edit{padding:13px;border-radius:16px;background:var(--md-sys-color-surface-container-low)}@media(max-width:639px){.config-proxy-head{align-items:flex-start;flex-direction:column}.config-proxy-grid{grid-template-columns:1fr}.config-proxy-fields:not([style*="display: none"]){grid-template-columns:1fr!important}}
.managed-safe,.custom-danger{min-height:48px;padding:11px 13px;border-radius:14px;display:flex;align-items:center;gap:7px;font-size:.68rem;font-weight:700;line-height:1.45}.managed-safe{background:color-mix(in srgb,var(--green) 14%,var(--md-sys-color-surface-container));color:var(--green-t)}.custom-danger{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}.route-proxy.custom{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}
/* Configs become a card gallery, not a compressed row/table. */
.cfg-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:var(--v12-card-gap)!important}.route-card{min-width:0;display:flex;flex-direction:column;background:var(--md-sys-color-surface-container-low);border:1px solid var(--md-sys-color-outline-variant);border-radius:30px;overflow:hidden;transition:transform 320ms var(--md-sys-motion-easing-emphasized),box-shadow 320ms,border-color 180ms}.route-card:hover{transform:translateY(-5px);border-color:var(--md-sys-color-outline);box-shadow:var(--shadow)}.route-card.is-off{opacity:.7}.route-card.is-exp{border-color:color-mix(in srgb,var(--md-sys-color-tertiary) 46%,var(--md-sys-color-outline-variant))}.route-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding:22px 22px 16px}.route-title-wrap{display:flex;align-items:flex-start;gap:12px;min-width:0}.route-status-light{width:12px;height:12px;margin-top:6px;border-radius:50%;background:var(--md-sys-color-error);box-shadow:0 0 0 6px color-mix(in srgb,var(--md-sys-color-error) 13%,transparent);flex-shrink:0}.route-status-light.on{background:var(--green);box-shadow:0 0 0 6px color-mix(in srgb,var(--green) 14%,transparent)}.route-label{font:750 1.06rem/1.35 var(--md-ref-typeface-brand);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.route-remark{display:flex;align-items:center;gap:6px;margin-top:5px;color:var(--md-sys-color-on-surface-variant);font-size:.75rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.route-remark i{color:var(--md-sys-color-tertiary)}.route-state{min-height:40px;border:0;border-radius:999px;padding:0 13px;display:flex;align-items:center;gap:6px;background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container);font:700 .7rem inherit;cursor:pointer;flex-shrink:0}.route-state.on{background:var(--green-bg);color:var(--green-t)}.route-network{margin:0 14px;padding:16px;display:grid;grid-template-columns:minmax(0,1fr) 24px minmax(0,1fr) auto;align-items:center;gap:10px;background:var(--md-sys-color-surface-container-high);border-radius:20px}.route-network>div{min-width:0}.route-network span,.route-data span{display:block;font-size:.62rem;letter-spacing:.07em;text-transform:uppercase;color:var(--md-sys-color-on-surface-variant);margin-bottom:4px}.route-network strong{display:block;font:650 .76rem/1.35 ui-monospace,SFMono-Regular,Consolas,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.route-arrow{color:var(--md-sys-color-tertiary);font-size:18px}.route-port{padding-inline-start:10px;border-inline-start:1px solid var(--md-sys-color-outline-variant)}.route-data{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:10px;padding:16px 18px}.route-usage{min-width:0}.route-data-head{display:flex;align-items:center;justify-content:space-between;gap:8px}.route-data-head b{font-size:.7rem}.route-meter{height:6px;margin-top:10px;border-radius:99px;background:var(--md-sys-color-surface-container-highest);overflow:hidden}.route-meter i{height:100%;display:block;background:var(--md-sys-color-primary);border-radius:inherit}.route-fact{padding-inline-start:10px;border-inline-start:1px solid var(--md-sys-color-outline-variant);min-width:0}.route-fact strong{font-size:.77rem;white-space:nowrap}.route-fact .exp-chip{font-size:.64rem!important;padding:5px 7px!important}.route-uuid{margin:0 18px 16px;min-height:42px;border:1px dashed var(--md-sys-color-outline-variant);border-radius:14px;background:transparent;color:var(--md-sys-color-on-surface-variant);display:flex;align-items:center;gap:8px;padding:0 12px;cursor:pointer}.route-uuid code{flex:1;min-width:0;text-align:left;direction:ltr;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.68rem}.route-uuid span{font-size:.66rem;font-weight:700;color:var(--md-sys-color-primary)}.route-actions{display:grid;grid-template-columns:minmax(125px,1.2fr) minmax(145px,1fr) repeat(4,48px);gap:7px;padding:12px;background:var(--md-sys-color-surface-container);border-top:1px solid var(--md-sys-color-outline-variant)}.route-action{min-height:48px;border:0;border-radius:16px;background:var(--md-sys-color-surface-container-highest);color:var(--md-sys-color-on-surface);display:flex;align-items:center;justify-content:center;gap:7px;padding:0 12px;cursor:pointer;font:700 .7rem inherit;transition:transform 160ms var(--md-sys-motion-easing-emphasized),border-radius 160ms,background 160ms}.route-action:hover{transform:translateY(-2px)}.route-action:active{transform:scale(.96);border-radius:10px}.route-action.primary{background:var(--md-sys-color-primary);color:var(--md-sys-color-on-primary);border-radius:18px 18px 7px 18px}.route-action.secondary{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}.route-action.compact{padding:0}.route-action.danger{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}
/* RTL and keyboard */
[dir="rtl"] .cp-head{border-radius:0 36px 36px 0!important}[dir="rtl"] .route-arrow{transform:rotate(180deg)}[dir="rtl"] .route-uuid code{text-align:right;direction:ltr}[dir="rtl"] .endpoint-preview>i{transform:rotate(180deg)}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,.nav-it:focus-visible{outline:3px solid color-mix(in srgb,var(--md-sys-color-primary) 72%,transparent)!important;outline-offset:3px!important}
.pw-eye{width:44px!important;height:44px!important;right:4px!important;top:27px!important;padding:0!important;display:grid!important;place-items:center!important;border-radius:999px!important;background:var(--md-sys-color-surface-container-high)!important}
.ob-check{min-height:48px!important;padding:10px 12px!important;border-radius:14px!important}
.ob-check input{width:20px!important;height:20px!important;flex:0 0 20px!important}
/* adaptive navigation: the right command rail becomes a bottom command dock */
@media(max-width:1199px){.cfg-grid{grid-template-columns:1fr!important}.create-panel{grid-template-columns:230px minmax(0,1fr)!important}.route-actions{grid-template-columns:1fr 1fr repeat(4,48px)}}
@media(max-width:900px){.sidebar{position:fixed!important;left:10px!important;right:10px!important;top:auto!important;bottom:10px!important;width:auto!important;height:84px!important;min-height:0!important;border-radius:28px!important;flex-direction:row!important;z-index:220!important}.logo,.sb-foot{display:none!important}.nav-wrap{width:100%!important;flex-direction:row!important;overflow-x:auto!important;overflow-y:hidden!important;padding:8px!important;gap:4px!important}.nav-it{min-width:82px!important;min-height:66px!important}.nav-it.on{border-radius:20px 20px 8px 20px!important}.main{margin-right:0!important;padding:92px 16px 126px!important}.mob-top{display:flex!important;top:10px!important;left:10px!important;right:10px!important;height:64px!important;border:1px solid var(--md-sys-color-outline-variant)!important;border-radius:24px!important;background:color-mix(in srgb,var(--md-sys-color-surface-container) 92%,transparent)!important;backdrop-filter:blur(20px)!important}.menu-btn{display:none!important}.topbar{position:relative!important;top:auto!important}.create-panel{grid-template-columns:1fr!important}.cp-head{grid-column:1!important;grid-row:auto!important;min-height:220px!important;border-radius:30px 30px 0 0!important}.cp-head-title{max-width:none!important}.cp-body{grid-column:1!important}.tb-sub{margin-inline-start:0!important}}
@media(max-width:639px){.cp-body{grid-template-columns:1fr!important;padding:14px!important}.create-panel .cp-body>.cp-block,.create-panel .cp-block,.create-panel .endpoint-studio,.create-panel .cp-footer{grid-column:1!important}.cp-footer{grid-template-columns:1fr!important}.cp-submit-btn{width:100%!important}.route-network{grid-template-columns:1fr 20px 1fr!important}.route-port{grid-column:1/-1;border-inline-start:0;border-top:1px solid var(--md-sys-color-outline-variant);padding:10px 0 0}.route-data{grid-template-columns:1fr 1fr!important}.route-usage{grid-column:1/-1}.route-fact:nth-child(2){border-inline-start:0;padding-inline-start:0}.route-actions{grid-template-columns:1fr 1fr repeat(2,48px)!important}.route-action.compact:nth-last-child(-n+2){grid-row:2}.route-action span{font-size:.67rem}.route-head{padding:18px}.endpoint-grid{grid-template-columns:1fr!important}.endpoint-preview>i{transform:rotate(90deg)!important}.main{padding-left:10px!important;padding-right:10px!important}.topbar{padding:14px!important}.tb-title{font-size:1.3rem!important}}

</style>
</head>
<body>
<div class="toast" id="toast"></div>
<div class="modal-bg" id="modal-links">
  <div class="modal-v2" style="max-width:500px">
    <div class="lmodal-head">
      <button class="modal-v2-close" onclick="closeModal('modal-links')"><i class="ti ti-x"></i></button>
      <div class="lmodal-icon-row">
        <div class="lmodal-icon"><i class="ti ti-link-plus"></i></div>
        <div>
          <div class="lmodal-title-v2">Manage configs of <span id="modal-sub-name" style="color:var(--accent2)">—</span></div>
          <div class="lmodal-sub-v2">Choose the configs that belong to this group</div>
        </div>
      </div>
      <div class="lmodal-search">
        <i class="ti ti-search"></i>
        <input type="text" id="lmodal-search-inp" placeholder="Search configs..." oninput="filterLmodal(this.value)">
      </div>
      <div class="lmodal-quickbar">
        <button class="lmodal-qbtn" onclick="lmodalSelectAll(true)"><i class="ti ti-checks"></i> Select all</button>
        <button class="lmodal-qbtn" onclick="lmodalSelectAll(false)"><i class="ti ti-x"></i> Clear all</button>
        <span class="lmodal-count" id="lmodal-count">0 selected</span>
      </div>
    </div>
    <div class="lmodal-list" id="modal-links-body"><div class="aspin-box"><span class="aspin aspin-lg"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></span> Loading configs…</div></div>
    <div class="lmodal-footer">
      <div class="lmodal-footer-info"><i class="ti ti-info-circle"></i> Changes are applied instantly</div>
      <div class="lmodal-footer-btns">
        <button class="btn btn-o" onclick="closeModal('modal-links')">Close</button>
        <button class="btn btn-p" id="modal-save-btn" onclick="saveSubLinks()"><i class="ti ti-check"></i> Save</button>
      </div>
    </div>
  </div>
</div>
<div class="modal-bg" id="modal-create-sub">
  <div class="modal-v2">
    <div class="modal-v2-head">
      <button class="modal-v2-close" onclick="closeModal('modal-create-sub')"><i class="ti ti-x"></i></button>
      <div class="modal-v2-icon"><i class="ti ti-folder-plus"></i></div>
      <div class="modal-v2-title">New sub group</div>
      <div class="modal-v2-sub">Create a dedicated public page for a set of configs</div>
    </div>
    <div class="modal-v2-body">
      <div class="modal-v2-field">
        <label><i class="ti ti-tag"></i> Group name</label>
        <input class="modal-v2-input" id="ns-name" placeholder="e.g. Premium users">
      </div>
      <div class="modal-v2-field">
        <label><i class="ti ti-align-left"></i> Description (optional)</label>
        <input class="modal-v2-input" id="ns-desc" placeholder="A short note about this group">
      </div>
      <div class="modal-v2-field" style="margin-bottom:0">
        <label><i class="ti ti-lock"></i> Public page password (optional)</label>
        <input class="modal-v2-input" id="ns-pw" type="password" placeholder="Leave empty = no password">
      </div>
      <div class="cl" style="margin-top:14px"><i class="ti ti-info-circle"></i><span>This group gets its own public page with a unique link.</span></div>
      <div class="modal-v2-footer">
        <button class="btn btn-o" onclick="closeModal('modal-create-sub')" style="flex:.6">Cancel</button>
        <button class="btn btn-pur" onclick="createSub()"><i class="ti ti-folder-plus"></i> Create group</button>
      </div>
    </div>
  </div>
</div>
<div class="modal-bg" id="modal-edit-link">
  <div class="modal">
    <button class="modal-close" onclick="closeModal('modal-edit-link')"><i class="ti ti-x"></i></button>
    <div class="modal-title"><i class="ti ti-edit"></i> Edit config</div>
    <input type="hidden" id="el-uuid">
    <div class="fg" style="margin-bottom:13px"><label>Label</label><input class="fi" id="el-label" style="width:100%"></div>
    <div class="fg" style="margin-bottom:13px"><label>Client remark</label><input class="fi" id="el-remark" maxlength="120" placeholder="Exact name shown in client apps" style="width:100%"></div>
    <div class="form-row" style="margin-bottom:13px">
      <div class="fg" style="flex:1"><label>Quota (0 = unlimited)</label><input class="fi" id="el-val" type="number" min="0" step="0.1" style="width:100%"></div>
      <div class="fg"><label>Unit</label><select class="fs" id="el-unit"><option value="GB">GB</option><option value="MB">MB</option></select></div>
    </div>
    <div class="fg" style="margin-bottom:13px"><label>Expiry (days from now, 0 = keep / unlimited)</label><input class="fi" id="el-exp" type="number" min="0" step="1" style="width:100%"></div>
    <div class="fg" style="margin-bottom:13px"><label>Note</label><input class="fi" id="el-note" style="width:100%"></div>
    <div class="form-row" style="margin-bottom:13px">
      <div class="fg" style="flex:1"><label>Address (IPv4 / IPv6 / domain)</label><input class="fi endpoint-ltr" id="el-address" placeholder="Empty = current service" style="width:100%"></div>
      <div class="fg" style="flex:1"><label>TLS SNI (domain only)</label><input class="fi endpoint-ltr" id="el-sni" placeholder="Empty = automatic" style="width:100%"></div>
    </div>
    <div class="fg config-proxy-edit" style="margin-bottom:13px"><label>Exit IP settings</label><select class="fs" id="el-exit-mode" onchange="syncExitProxy('el')" style="width:100%"><option value="direct">Direct — safest default</option><option value="repository">Managed proxy repository</option><option value="custom">Custom proxy — unsafe</option></select><div id="el-repository-fields" style="display:none;margin-top:9px"><select class="fs" id="el-proxy-id" style="width:100%"></select></div><div id="el-custom-fields" style="display:none;margin-top:9px"><input class="fi endpoint-ltr" id="el-custom-proxy" placeholder="http://user:pass@host:port" style="width:100%"><div class="field-caption" style="color:var(--md-sys-color-error)"><i class="ti ti-alert-triangle"></i> Unsafe custom proxy; configuration may fail or traffic may be exposed.</div></div></div>
    <div class="form-row" style="margin-bottom:13px">
      <div class="fg" style="flex:1"><label>Fingerprint (uTLS)</label>
        <select class="fs" id="el-fp" style="width:100%">
          <option value="chrome">chrome</option>
          <option value="firefox">firefox</option>
          <option value="safari">safari</option>
          <option value="ios">ios</option>
          <option value="android">android</option>
          <option value="edge">edge</option>
          <option value="360">360</option>
          <option value="qq">qq</option>
          <option value="random">random</option>
          <option value="randomized">randomized</option>
        </select>
      </div>
      <div class="fg" style="flex:1"><label>ALPN (empty = default)</label><input class="fi" id="el-alpn" placeholder="e.g. h2,http/1.1" style="width:100%"></div>
    </div>
    <div class="form-row" style="margin-bottom:16px">
      <div class="fg" style="flex:1"><label>Connection port</label><input class="fi" id="el-port" type="number" min="1" max="65535" style="width:100%"></div>
      <div class="fg" style="flex:1"><label>IP limit (0 = unlimited)</label><input class="fi" id="el-iplimit" type="number" min="0" step="1" style="width:100%"></div>
    </div>
    <div class="form-row" style="margin-bottom:16px">
      <div class="fg" style="flex:1"><label>Speed limit (0 = unlimited)</label><input class="fi" id="el-speed" type="number" min="0" step="0.5" style="width:100%"></div>
      <div class="fg"><label>Unit</label><select class="fs" id="el-speed-unit"><option value="MBIT">Mbps</option><option value="KB">KB/s</option><option value="MB">MB/s</option></select></div>
    </div>
    <div class="cl"><i class="ti ti-info-circle"></i><span>Leave the expiry field at 0 to keep the current date.</span></div>
    <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
      <button class="btn btn-o" onclick="closeModal('modal-edit-link')">Cancel</button>
      <button class="btn btn-p" onclick="saveEditLink()"><i class="ti ti-check"></i> Save changes</button>
    </div>
  </div>
</div>
<div class="mob-top">
  <div class="ml">
    <div class="mob-logo"><i class="ti ti-shield-bolt"></i></div>
    <span class="mob-title">Lumen Relay</span>
  </div>
  <div class="mob-right">
    <button class="theme-mob" id="lang-mob-btn" onclick="toggleLanguage()" aria-label="Change language"><i class="ti ti-language"></i></button>
    <button class="theme-mob" id="theme-mob-btn" onclick="toggleTheme()" aria-label="Change theme"><i class="ti ti-sun" id="theme-mob-icon"></i></button>
    <button class="menu-btn" id="open-sb" aria-label="Open navigation"><i class="ti ti-layout-bottombar"></i></button>
  </div>
</div>
<div class="overlay" id="overlay"></div>
<aside class="sidebar" id="sb">
  <button class="sb-close" id="close-sb"><i class="ti ti-x"></i></button>
  <div class="logo">
    <div class="logo-img"><i class="ti ti-shield-bolt"></i></div>
    <div><div class="logo-name">Lumen Relay</div><div class="logo-sub">Command Console · v16</div></div>
  </div>
  <nav class="nav-wrap" aria-label="Workspace navigation">
    <div class="nav-sec">Workspace</div>
    <div class="nav-it on" data-pg="overview" title="Control room"><i class="ti ti-command"></i><span>Control room</span></div>
    <div class="nav-it" data-pg="links" title="Route studio"><i class="ti ti-route-alt-left"></i><span>Route studio</span><span class="nav-badge" id="links-nb">0</span></div>
    <div class="nav-it" data-pg="subscriptions" title="Subscriptions"><i class="ti ti-rss"></i><span>Subscriptions</span></div>
    <div class="nav-it" data-pg="subgroups" title="Sub Groups"><i class="ti ti-folders"></i><span>Sub Groups</span><span class="nav-badge" id="subs-nb">0</span></div>
    <div class="nav-sec">Observe</div>
    <div class="nav-it" data-pg="connections" title="Connections"><i class="ti ti-plug-connected"></i><span>Connections</span><span class="nav-badge" id="conns-nb">0</span></div>
    <div class="nav-it" data-pg="traffic" title="Traffic"><i class="ti ti-chart-area-line"></i><span>Traffic</span></div>
    <div class="nav-it" data-pg="logs" title="Activity Log"><i class="ti ti-timeline-event"></i><span>Activity Log</span></div>
    <div class="nav-it" data-pg="errors" title="Errors"><i class="ti ti-alert-hexagon"></i><span>Errors</span></div>
    <div class="nav-sec">Tools</div>
    <div class="nav-it" data-pg="security" title="Security"><i class="ti ti-shield-lock"></i><span>Security</span></div>
    <div class="nav-it" data-pg="testws" title="WebSocket Test"><i class="ti ti-wave-sine"></i><span>WebSocket Test</span></div>
    <div class="nav-it" data-pg="settings" title="Settings"><i class="ti ti-adjustments-horizontal"></i><span>Settings</span></div>
  </nav>
  <div class="sb-foot">
    <button class="lang-switch" onclick="toggleLanguage()" title="Change language"><i class="ti ti-language"></i><span id="lang-label">فارسی</span></button>
    <button class="theme-btn" onclick="toggleTheme()" title="Change theme"><i class="ti ti-moon" id="theme-icon"></i><span id="theme-label">Light mode</span></button>
    <button class="logout-btn" id="logout-btn" title="Sign out"><i class="ti ti-logout"></i><span>Sign out</span></button>
  </div>
</aside>
<main class="main">
<section class="pg on" id="pg-overview">
  <div class="topbar">
    <div><div class="tb-title"><i class="ti ti-layout-dashboard"></i> Relay overview</div><div class="tb-sub" id="last-upd">Loading...</div></div>
    <div class="tb-right">
      <span class="badge bg-green"><span class="dot dg pulse"></span> Active</span>
      <span class="badge bg-blue" id="uptime-badge">—</span>
      <button class="btn btn-p btn-sm" onclick="refreshAll()"><i class="ti ti-refresh"></i> Refresh</button>
    </div>
  </div>
  <div class="metrics">
    <div class="metric"><div class="m-icon"><i class="ti ti-plug-connected"></i></div><div class="m-label">Active connections</div><div class="m-val" id="m-conns">—</div><div class="m-sub"><span class="dot dg pulse"></span> WebSocket live</div></div>
    <div class="metric"><div class="m-icon"><i class="ti ti-transfer"></i></div><div class="m-label">Total traffic</div><div class="m-val" id="m-traffic">—<span class="m-unit">MB</span></div><div class="m-sub">since start-up</div></div>
    <div class="metric suc"><div class="m-icon suc"><i class="ti ti-link"></i></div><div class="m-label">Active configs</div><div class="m-val" id="m-alinks">—</div><div class="m-sub" id="m-lsub">of total</div></div>
    <div class="metric pur"><div class="m-icon pur"><i class="ti ti-folders"></i></div><div class="m-label">Sub Groups</div><div class="m-val" id="m-subs">—</div><div class="m-sub">Active</div></div>
  </div>
  <div class="vless-box">
    <div class="vl-header">
      <div class="vl-title"><i class="ti ti-link"></i> Default link (no limits)</div>
      <span class="badge bg-blue"><span class="dot db"></span> TLS 443 · WS</span>
    </div>
    <div class="vl-code" id="vless-main">Fetching...</div>
    <div class="vl-actions">
      <button class="btn btn-p" onclick="cpText('vless-main')"><i class="ti ti-copy"></i> Copy</button>
      <button class="btn btn-g" onclick="qrFor('vless-main')"><i class="ti ti-qrcode"></i> QR</button>
      <button class="btn btn-o" onclick="navTo('links')"><i class="ti ti-link-plus"></i> Limited configs</button>
      <button class="btn btn-pur" onclick="navTo('subgroups')"><i class="ti ti-folders"></i> Sub Groups</button>
    </div>
  </div>
  <div class="g3">
    <div class="card"><div class="card-title"><i class="ti ti-chart-area"></i> Hourly traffic (MB)</div><div class="ch"><canvas id="ch1"></canvas></div></div>
    <div class="card"><div class="card-title"><i class="ti ti-chart-donut"></i> Distribution</div><div class="ch-sm"><canvas id="ch2"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="card">
      <div class="card-title"><i class="ti ti-activity"></i> Service status</div>
      <div class="sr"><span class="sr-k"><i class="ti ti-shield-check"></i> UUID Auth</span><span class="sr-v" style="color:var(--green-t)">● Active · strict</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-circle-check"></i> VLESS / WS Tunnel</span><span class="sr-v" style="color:var(--green-t)">● Active</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-folders"></i> Sub Groups</span><span class="sr-v" style="color:var(--green-t)">● Active v16</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-rss"></i> Subscription API</span><span class="sr-v" style="color:var(--green-t)">● Active</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-clock"></i> Uptime</span><span class="sr-v" id="uptime-inline">—</span></div>
      <div class="sr" style="flex-direction:column;align-items:flex-start;gap:4px">
        <div style="width:100%;display:flex;justify-content:space-between"><span class="sr-k"><i class="ti ti-gauge"></i> Relative load</span><span class="sr-v" id="bw-pct">—%</span></div>
        <div class="spbar" style="width:100%"><div class="spfill" id="bw-bar" style="width:0%"></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title"><i class="ti ti-list"></i> Config summary <span class="ml-auto badge bg-blue" id="lsummary-badge">0</span></div>
      <div id="lsummary">—</div>
    </div>
  </div>
  <div class="dash-footer">
    <span class="df-text">Lumen Relay · Version 16.0</span>
    
  </div>
</section>
<section class="pg" id="pg-links">
  <div class="topbar">
    <div><div class="tb-title"><i class="ti ti-route-alt-left"></i> Route studio</div><div class="tb-sub">Compose, inspect, and deliver every connection from one workspace</div></div>
    <div class="tb-right"><span class="badge bg-blue" id="links-pg-cnt">0 config</span></div>
  </div>
  <div class="create-panel">
    <div class="cp-head">
      <div class="cp-head-icon"><i class="ti ti-square-rounded-plus"></i></div>
      <div class="cp-head-text">
        <div class="cp-head-title">Compose a new route</div>
        <div class="cp-head-sub">Identity first, network second, delivery controls last</div>
      </div>
    </div>
    <div class="cp-body">
      <div class="cp-row">
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-id-badge-2"></i> Config identity</div>
          <input class="cp-input-full" id="nl-label" placeholder="Internal label · e.g. Alex Doe">
          <div class="cp-mini-row">
            <input class="cp-input-full" id="nl-remark" maxlength="120" placeholder="Client remark · e.g. Lumen Premium Amsterdam">
          </div>
          <div class="cp-mini-row">
            <input class="cp-input-full" id="nl-note" placeholder="Private note (optional)">
          </div>
          <div class="field-caption">Label is for the panel. Remark is the exact name shown inside the client app.</div>
        </div>
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-folders"></i> Sub group & expiry</div>
          <select class="cp-input-full fs" id="nl-sub"><option value="">— No group —</option></select>
          <div class="cp-mini-row">
            <input class="cp-input-full" id="nl-exp" type="number" min="0" step="1" placeholder="Expiry (days) · 0 = Unlimited">
          </div>
          <div class="chip-row" id="exp-chips">
            <span class="chip" onclick="setExpiry(0,this)">Unlimited</span>
            <span class="chip" onclick="setExpiry(7,this)">7 days</span>
            <span class="chip active" onclick="setExpiry(30,this)">30 days</span>
            <span class="chip" onclick="setExpiry(90,this)">90 days</span>
          </div>
        </div>
      </div>
      <div class="cp-block mb16">
        <div class="cp-block-label"><i class="ti ti-gauge"></i> Traffic quota</div>
        <div class="cp-quota-inputs">
          <input class="cp-input-full" id="nl-val" type="number" min="0" step="0.1" placeholder="0 = Unlimited">
          <select class="cp-input-full fs" id="nl-unit"><option value="GB">GB</option><option value="MB" selected>MB</option></select>
        </div>
        <div class="chip-row" id="quota-chips">
          <span class="chip" onclick="setQuota(0,'GB',this)">Unlimited</span>
          <span class="chip" onclick="setQuota(500,'MB',this)">500 MB</span>
          <span class="chip active" onclick="setQuota(1,'GB',this)">1 GB</span>
          <span class="chip" onclick="setQuota(5,'GB',this)">5 GB</span>
          <span class="chip" onclick="setQuota(10,'GB',this)">10 GB</span>
          <span class="chip" onclick="setQuota(50,'GB',this)">50 GB</span>
        </div>
      </div>
      <div class="cp-block mb16">
        <div class="cp-block-label"><i class="ti ti-plug-connected"></i> Transport protocol</div>
        <select id="nl-proto" style="display: none">
          <option value="vless-ws">VLESS / WebSocket Turbo</option>
        </select>
        <div class="proto-cards">
          <div class="proto-card active" data-val="vless-ws" onclick="selectProto('vless-ws',this)">
            <div class="proto-card-check"><i class="ti ti-check"></i></div>
            <div class="proto-card-icon"><i class="ti ti-link"></i></div>
            <div class="proto-card-title">VLESS / WS</div>
            <div class="proto-card-desc">Turbo · zero-copy · maximum throughput</div>
          </div>
        </div>
      </div>
      <div class="cp-block endpoint-studio mb16" id="endpoint-studio">
        <div class="endpoint-studio-head">
          <div>
            <div class="cp-block-label" style="margin-bottom:0"><i class="ti ti-route-2"></i> Connection identity</div>
            <div class="endpoint-studio-sub">Choose the public dial target and the independent TLS identity.</div>
          </div>
          <span class="endpoint-status" id="endpoint-status"><i class="ti ti-rosette-discount-check"></i> Verified preset</span>
        </div>
        <div class="endpoint-grid">
          <div class="endpoint-field">
            <label for="nl-address"><span class="step-dot">1</span> Address</label>
            <select class="cp-input-full fs endpoint-ltr" id="nl-address" onchange="endpointChoiceChanged('address')">
              <option value="__auto__">Auto — current service</option>
              <option value="__custom__">Custom address…</option>
            </select>
            <div class="endpoint-custom" id="nl-address-custom-row" style="display: none">
              <input class="cp-input-full endpoint-ltr" id="nl-address-custom" autocomplete="off" spellcheck="false" placeholder="IPv4, IPv6 or domain" oninput="updateEndpointPreview()">
            </div>
            <div class="endpoint-help">The address after <code>@</code>. Ports, paths and URL schemes are intentionally separate.</div>
          </div>
          <div class="endpoint-field">
            <label for="nl-sni"><span class="step-dot">2</span> TLS SNI</label>
            <select class="cp-input-full fs endpoint-ltr" id="nl-sni" onchange="endpointChoiceChanged('sni')">
              <option value="__auto__">Auto — safest TLS routing</option>
              <option value="__custom__">Custom SNI…</option>
            </select>
            <div class="endpoint-custom" id="nl-sni-custom-row" style="display: none">
              <input class="cp-input-full endpoint-ltr" id="nl-sni-custom" autocomplete="off" spellcheck="false" placeholder="front.example.com" oninput="updateEndpointPreview()">
            </div>
            <div class="endpoint-help">SNI must be a domain. With a raw IP address, Auto keeps the service domain for TLS.</div>
          </div>
        </div>
        <div class="endpoint-preview" id="endpoint-preview">
          <div><span>Dial</span><code id="endpoint-preview-address">current service</code></div>
          <i class="ti ti-arrow-right"></i>
          <div><span>TLS identity</span><code id="endpoint-preview-sni">current service</code></div>
        </div>
      </div>
      <div class="cp-block config-proxy-studio"><div class="config-proxy-head"><div><div class="cp-block-label"><i class="ti ti-world-cog"></i> Exit IP settings</div><div class="endpoint-studio-sub">Choose a managed HTTP, HTTPS, or SOCKS5 proxy for this config only.</div></div><div class="config-proxy-actions"><span class="config-scope-badge"><i class="ti ti-user-shield"></i> Only this config</span><button class="repository-refresh-btn" id="proxy-recheck-btn" style="display:none" onclick="refreshProxyCatalogNow()"><i class="ti ti-refresh"></i><span>Recheck now</span></button></div></div><div class="config-proxy-grid"><div class="proxy-mode-card"><label>Connection mode</label><select class="cp-input-full fs" id="nl-exit-mode" onchange="syncExitProxy('nl')"><option value="direct">Direct — safest default</option><option value="repository">Managed proxy repository</option><option value="custom">Custom proxy — unsafe</option></select></div><div class="config-proxy-fields" id="nl-repository-fields" style="display: none"><div><label>Managed proxy</label><select class="cp-input-full fs" id="nl-proxy-id"><option value="">Loading managed proxies…</option></select></div><div class="managed-safe"><i class="ti ti-shield-check"></i> Managed and verified</div></div><div class="config-proxy-fields" id="nl-custom-fields" style="display: none"><div><label>Custom proxy URL</label><input class="cp-input-full endpoint-ltr" id="nl-custom-proxy" placeholder="socks5://user:pass@host:port"></div><div class="custom-danger"><i class="ti ti-alert-triangle"></i> Warning: leaving the managed safety boundary. This proxy may expose traffic or stop the config.</div></div></div><div class="proxy-safe-note"><i class="ti ti-eye-off"></i><span>Managed endpoints stay server-side. Only flag, country, protocol, and health are shown.</span></div></div>
      <div class="cp-row">
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-fingerprint"></i> Fingerprint (uTLS)</div>
          <select class="cp-input-full fs" id="nl-fp">
            <option value="chrome" selected>chrome</option>
            <option value="firefox">firefox</option>
            <option value="safari">safari</option>
            <option value="ios">ios</option>
            <option value="android">android</option>
            <option value="edge">edge</option>
            <option value="360">360</option>
            <option value="qq">qq</option>
            <option value="random">random</option>
            <option value="randomized">randomized</option>
          </select>
        </div>
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-antenna-bars-5"></i> ALPN</div>
          <select class="cp-input-full fs" id="nl-alpn-preset" onchange="onAlpnPresetChange()">
            <option value="">WS default (http/1.1)</option>
            <option value="http/1.1">http/1.1</option>
            <option value="__custom__">Custom...</option>
          </select>
          <div class="cp-mini-row">
            <input class="cp-input-full" id="nl-alpn" placeholder="Custom ALPN value" style="display: none">
          </div>
        </div>
      </div>
      <div class="cp-row mb16">
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-route"></i> Connection port</div>
          <input class="cp-input-full" id="nl-port" type="number" min="1" max="65535" placeholder="443" value="443">
        </div>
        <div class="cp-block">
          <div class="cp-block-label"><i class="ti ti-users"></i> IP limit / concurrent users</div>
          <input class="cp-input-full" id="nl-iplimit" type="number" min="0" step="1" placeholder="0 = Unlimited" value="0">
          <div class="chip-row" id="iplimit-chips">
            <span class="chip active" onclick="setIpLimit(0,this)">Unlimited</span>
            <span class="chip" onclick="setIpLimit(1,this)">1 user</span>
            <span class="chip" onclick="setIpLimit(2,this)">2 user</span>
            <span class="chip" onclick="setIpLimit(5,this)">5 user</span>
          </div>
        </div>
      </div>
      <div class="cp-row mb16">
        <div class="cp-block" style="flex:1">
          <div class="cp-block-label"><i class="ti ti-gauge"></i> Speed limit</div>
          <div class="form-row">
            <input class="cp-input-full" id="nl-speed" type="number" min="0" step="0.5" placeholder="0 = Unlimited" value="0" style="flex:1">
            <select class="fs" id="nl-speed-unit" style="flex:0 0 100px">
              <option value="MBIT" selected>Mbps</option>
              <option value="KB">KB/s</option>
              <option value="MB">MB/s</option>
            </select>
          </div>
          <div class="chip-row" id="speed-chips">
            <span class="chip active" onclick="setSpeedLimit(0,this)">Unlimited</span>
            <span class="chip" onclick="setSpeedLimit(1,this)">1 Mbps</span>
            <span class="chip" onclick="setSpeedLimit(5,this)">5 Mbps</span>
            <span class="chip" onclick="setSpeedLimit(10,this)">10 Mbps</span>
            <span class="chip" onclick="setSpeedLimit(25,this)">25 Mbps</span>
          </div>
        </div>
      </div>
      <div class="cp-footer">
        <div class="cp-footer-note"><i class="ti ti-info-circle"></i> Every UUID is fully random · only registered UUIDs may connect · the protocol cannot be changed later.</div>
        <button class="cp-submit-btn" onclick="createLink()"><i class="ti ti-sparkles"></i> Build route</button>
      </div>
    </div>
  </div>
  <div class="cfg-grid" id="links-grid"></div>
  <div class="empty" id="links-empty" style="display: none"><i class="ti ti-link-off"></i><p>No configs yet</p></div>
</section>
<section class="pg" id="pg-subgroups">
  <div class="topbar">
    <div><div class="tb-title"><i class="ti ti-folders"></i> Sub Groups</div><div class="tb-sub">Every group has its own public page with its own configs</div></div>
    <div class="tb-right">
      <span class="badge bg-purple" id="subs-pg-cnt">0 Group</span>
      <button class="btn btn-pur" onclick="openModal('modal-create-sub')"><i class="ti ti-folder-plus"></i> New group</button>
    </div>
  </div>
  <div class="subs-toolbar">
    <div class="subs-search">
      <i class="ti ti-search"></i>
      <input type="text" id="subs-search-inp" placeholder="Search groups..." oninput="filterSubs(this.value)">
    </div>
  </div>
  <div class="sub-grid" id="subs-grid">
    <div class="subs-empty-v2"><div class="subs-empty-v2-icon"><i class="ti ti-folders"></i></div><div class="subs-empty-v2-title">No groups yet</div><div class="subs-empty-v2-sub">Create a group to organise your configs</div></div>
  </div>
</section>
<section class="pg" id="pg-subscriptions">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-rss"></i> Subscriptions</div><div class="tb-sub">Subscription links for apps like v2ray</div></div></div>
  <div class="g2">
    <div class="card">
      <div class="card-title"><i class="ti ti-rss"></i> Per-config subscription</div>
      <p style="font-size:11.5px;color:var(--t3);line-height:1.8;margin-bottom:12px">Each config URL has its own subscription link. On the config card, click the <i class="ti ti-rss"></i> icon.</p>
    </div>
    <div class="card">
      <div class="card-title"><i class="ti ti-database"></i> Full subscription (admin)</div>
      <p style="font-size:11.5px;color:var(--t3);line-height:1.8;margin-bottom:4px">Includes every active config.</p>
      <div class="sub-box"><span class="sub-url" id="sub-all-url">Fetching...</span><div style="display:flex;gap:6px"><button class="btn btn-sm btn-g" onclick="cpSubAll()"><i class="ti ti-copy"></i></button><button class="btn btn-sm btn-g" onclick="window.open(location.protocol+'//'+location.host+'/sub-all')"><i class="ti ti-external-link"></i></button></div></div>
      <div class="cl amber" style="margin-top:11px"><i class="ti ti-alert-triangle"></i><span>This address only works in the browser that is signed in to the panel (session cookie required).</span></div>
    </div>
  </div>
  <div class="card">
    <div class="card-title"><i class="ti ti-folders"></i> Group subscription links</div>
    <div id="sub-groups-list"><div class="aspin-box"><span class="aspin aspin-lg"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></span> Loading groups…</div></div>
  </div>
</section>
<section class="pg" id="pg-traffic">
  <div class="topbar">
    <div><div class="tb-title"><i class="ti ti-chart-area"></i> Traffic</div><div class="tb-sub">Bandwidth usage analytics and monitoring</div></div>
    <div class="tb-right"><button class="btn btn-p btn-sm" onclick="refreshAll()"><i class="ti ti-refresh"></i> Refresh</button></div>
  </div>

  <div class="traf-hero">
    <div class="traf-main-stat">
      <div class="traf-main-label"><i class="ti ti-database"></i> Total traffic used</div>
      <div class="traf-main-val" id="t-traffic">—<span>MB</span></div>
      <div class="traf-trend up" id="t-trend"><i class="ti ti-trending-up"></i> <span id="t-trend-val">—</span></div>
    </div>
    <div class="traf-mini">
      <div class="traf-mini-top"><div class="traf-mini-icon"><i class="ti ti-arrow-up-right"></i></div><span class="traf-mini-label">Hourly average</span></div>
      <div><div class="traf-mini-val" id="t-avg">—</div><div class="traf-mini-sub">MB per hour</div></div>
    </div>
    <div class="traf-mini">
      <div class="traf-mini-top"><div class="traf-mini-icon pk"><i class="ti ti-chart-bar"></i></div><span class="traf-mini-label">Peak usage</span></div>
      <div><div class="traf-mini-val" id="t-peak">—</div><div class="traf-mini-sub" id="t-peak-time">peak hour</div></div>
    </div>
    <div class="traf-mini">
      <div class="traf-mini-top"><div class="traf-mini-icon lo"><i class="ti ti-clock-hour-4"></i></div><span class="traf-mini-label">Lowest usage</span></div>
      <div><div class="traf-mini-val" id="t-low">—</div><div class="traf-mini-sub">MB per hour</div></div>
    </div>
  </div>

  <div class="traf-chart-card">
    <div class="traf-chart-head">
      <div>
        <div class="traf-chart-title"><i class="ti ti-activity"></i> Traffic usage trend</div>
        <div class="traf-chart-sub">Megabytes per hour</div>
      </div>
      <div class="traf-legend">
        <div class="traf-legend-item"><span class="traf-legend-dot" style="background:var(--accent)"></span> Usage</div>
        <div class="traf-legend-item"><span class="traf-legend-dot" style="background:var(--amber)"></span> Average</div>
      </div>
    </div>
    <div class="traf-chart-body"><canvas id="ch3"></canvas></div>
  </div>
</section>
<section class="pg" id="pg-connections">
  <div class="topbar">
    <div><div class="tb-title"><i class="ti ti-plug-connected"></i> Active connections</div><div class="tb-sub">Live monitoring of IP and traffic per connection</div></div>
    <div class="tb-right"><span class="badge bg-green" id="conns-live">—</span><button class="btn btn-p btn-sm" onclick="refreshAll()"><i class="ti ti-refresh"></i> Refresh</button></div>
  </div>

  <div class="conn-hero">
    <div class="conn-hero-tile">
      <div class="conn-hero-icon"><i class="ti ti-plug-connected"></i></div>
      <div class="conn-hero-label">Live connections</div>
      <div class="conn-hero-val" id="ch-count">—</div>
    </div>
    <div class="conn-hero-tile">
      <div class="conn-hero-icon"><i class="ti ti-transfer"></i></div>
      <div class="conn-hero-label">Live traffic total</div>
      <div class="conn-hero-val" id="ch-traffic">—</div>
    </div>
    <div class="conn-hero-tile">
      <div class="conn-hero-icon"><i class="ti ti-clock"></i></div>
      <div class="conn-hero-label">Average session length</div>
      <div class="conn-hero-val" id="ch-avgdur">—</div>
    </div>
    <div class="conn-hero-tile">
      <div class="conn-hero-icon"><i class="ti ti-map-pin"></i></div>
      <div class="conn-hero-label">Unique IPs</div>
      <div class="conn-hero-val" id="ch-uniq">—</div>
    </div>
  </div>

  <div class="conn-toolbar">
    <div class="conn-toolbar-title"><i class="ti ti-list-details"></i> Connection list</div>
    <div class="conn-live-badge"><span class="conn-live-dot"></span> Auto-refresh every 5 seconds</div>
  </div>

  <div class="conn-grid-v2" id="conns-grid"></div>
  <div class="conn-empty-v2" id="conns-empty" style="display: none">
    <div class="conn-empty-v2-icon"><i class="ti ti-plug-off"></i></div>
    <div class="conn-empty-v2-title">No active connections</div>
    <div class="conn-empty-v2-sub">Clients will appear here as soon as they connect</div>
  </div>
</section>
<section class="pg" id="pg-security">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-shield-lock"></i> Security</div></div></div>
  <div class="g2">
    <div class="card">
      <div class="card-title"><i class="ti ti-lock"></i> Encryption</div>
      <div class="sr"><span class="sr-k"><i class="ti ti-certificate"></i> TLS/HTTPS</span><span class="sr-v" style="color:var(--green-t)">● Enabled (443)</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-fingerprint"></i> Fingerprint</span><span class="sr-v">Chrome Spoof</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-network"></i> Protocols</span><span class="sr-v">VLESS / WebSocket Turbo</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-key"></i> Password hash</span><span class="sr-v">SHA-256+Salt</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-cookie"></i> Session</span><span class="sr-v">HttpOnly · 7 days</span></div>
    </div>
    <div class="card">
      <div class="card-title"><i class="ti ti-shield-check"></i> Access control</div>
      <div class="sr"><span class="sr-k"><i class="ti ti-id-badge"></i> UUID Auth strict</span><span class="sr-v" style="color:var(--green-t)">● Active v16</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-toggle-right"></i> Enable / disable config</span><span class="sr-v" style="color:var(--green-t)">● Active</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-gauge"></i> Traffic quota</span><span class="sr-v" style="color:var(--green-t)">● Active</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-calendar-x"></i> Expiry date</span><span class="sr-v" style="color:var(--green-t)">● Active</span></div>
      <div class="sr"><span class="sr-k"><i class="ti ti-lock"></i> Public sub page password</span><span class="sr-v" style="color:var(--green-t)">● optional · SHA-256</span></div>
    </div>
  </div>
</section>
<section class="pg" id="pg-logs">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-history"></i> Activity Log</div><div class="tb-sub">Complete history of panel events</div></div><div class="tb-right"><button class="btn btn-p btn-sm" onclick="loadActivity()"><i class="ti ti-refresh"></i></button></div></div>
  <div class="card"><div class="log-timeline" id="logs-list">—</div><div class="empty" id="logs-empty" style="display: none"><i class="ti ti-history-toggle"></i><p>No log entries yet</p></div></div>
</section>
<section class="pg" id="pg-errors">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-alert-triangle"></i> Errors</div></div><div class="tb-right"><span class="badge bg-red" id="errs-badge">0</span><button class="btn btn-p btn-sm" onclick="refreshAll()"><i class="ti ti-refresh"></i></button></div></div>
  <div class="card"><div class="card-title"><i class="ti ti-bug"></i> Error log</div><div id="errs-full">—</div></div>
</section>
<section class="pg" id="pg-testws">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-wifi"></i> WebSocket Test</div></div></div>
  <div class="card" style="max-width:660px">
    <div class="cl amber" style="margin-top:0;margin-bottom:12px"><i class="ti ti-alert-triangle"></i><span>Only registered and active UUIDs can connect. This build supports VLESS over WebSocket only.</span></div>
    <div class="form-row" style="margin-bottom:12px">
      <div class="fg" style="flex:1"><label>UUID (must already exist in Configs)</label><input class="fi" id="ws-uuid" placeholder="UUID of an active config" style="width:100%"></div>
      <button class="btn btn-p" onclick="wsConn()"><i class="ti ti-plug-connected"></i> connection</button>
      <button class="btn btn-d" onclick="wsDisc()"><i class="ti ti-plug-x"></i> Disconnect</button>
    </div>
    <div class="form-row" style="margin-bottom:12px">
      <input class="fi" id="ws-msg" placeholder="Test message..." style="flex:1">
      <button class="btn btn-o" onclick="wsSend()"><i class="ti ti-send"></i> Send</button>
    </div>
    <div style="background:rgba(0,0,0,.3);border:1px solid var(--card-b);border-radius:10px;padding:14px;height:250px;overflow-y:auto;font-family:ui-monospace,monospace;font-size:10.5px;line-height:1.9" id="ws-log">
      <p style="color:var(--t3)">Waiting for connection...</p>
    </div>
  </div>
</section>
<section class="pg" id="pg-settings">
  <div class="topbar"><div><div class="tb-title"><i class="ti ti-settings"></i> Settings</div></div></div>
  <div class="g2">
    <div class="srv-panel">
      <div class="srv-hero">
        <div class="srv-hero-icon"><i class="ti ti-server-2"></i></div>
        <div class="srv-hero-text">
          <div class="srv-hero-domain" id="set-host">—</div>
          <div class="srv-hero-sub"><span class="dot dg pulse"></span> Online · Railway</div>
        </div>
      </div>
      <div class="srv-tiles">
        <div class="srv-tile"><div class="srv-tile-icon"><i class="ti ti-route"></i></div><div class="srv-tile-text"><div class="srv-tile-label">Default port</div><div class="srv-tile-val">443 (TLS) · can be overridden per config</div></div></div>
        <div class="srv-tile"><div class="srv-tile-icon"><i class="ti ti-versions"></i></div><div class="srv-tile-text"><div class="srv-tile-label">Version</div><div class="srv-tile-val">v16.0</div></div></div>
        <div class="srv-tile"><div class="srv-tile-icon"><i class="ti ti-brand-fastapi"></i></div><div class="srv-tile-text"><div class="srv-tile-label">Framework</div><div class="srv-tile-val">FastAPI + Uvicorn</div></div></div>
        <div class="srv-tile"><div class="srv-tile-icon"><i class="ti ti-cloud"></i></div><div class="srv-tile-text"><div class="srv-tile-label">Platform</div><div class="srv-tile-val">Railway</div></div></div>
        <div class="srv-tile" style="grid-column:1/-1"><div class="srv-tile-icon"><i class="ti ti-device-floppy"></i></div><div class="srv-tile-text"><div class="srv-tile-label">Storage</div><div class="srv-tile-val">JSON File (/data)</div></div></div>
      </div>
    </div>
    <div class="pw-panel">
      <div class="pw-hero">
        <div class="pw-hero-icon"><i class="ti ti-key"></i></div>
        <div class="pw-hero-text">
          <div class="pw-hero-title">Change password</div>
          <div class="pw-hero-sub">Pick a strong password and keep it somewhere safe</div>
        </div>
      </div>
      <div class="pw-body">
        <div class="pw-field">
          <label>Current password</label>
          <input class="pw-input" type="password" id="cp-cur" placeholder="Enter your current password">
          <button class="pw-eye" type="button" onclick="togglePwField('cp-cur',this)"><i class="ti ti-eye"></i></button>
        </div>
        <div class="pw-field" style="margin-bottom:6px">
          <label>New password</label>
          <input class="pw-input" type="password" id="cp-new" placeholder="At least 4 characters" oninput="checkPwStrength(this.value)">
          <button class="pw-eye" type="button" onclick="togglePwField('cp-new',this)"><i class="ti ti-eye"></i></button>
        </div>
        <div class="pw-strength" id="pw-strength-bar">
          <div class="pw-strength-seg"></div><div class="pw-strength-seg"></div><div class="pw-strength-seg"></div><div class="pw-strength-seg"></div>
        </div>
        <div class="pw-strength-label" id="pw-strength-label"><i class="ti ti-shield"></i> Password strength</div>
        <div class="pw-reqs">
          <span class="pw-req" id="req-len"><i class="ti ti-circle-dashed"></i> At least 4 characters</span>
          <span class="pw-req" id="req-num"><i class="ti ti-circle-dashed"></i> Has a number</span>
          <span class="pw-req" id="req-case"><i class="ti ti-circle-dashed"></i> Upper & lower case</span>
        </div>
        <div class="pw-field" style="margin-bottom:18px">
          <label>Repeat new password</label>
          <input class="pw-input" type="password" id="cp-cf" placeholder="Repeat new password">
          <button class="pw-eye" type="button" onclick="togglePwField('cp-cf',this)"><i class="ti ti-eye"></i></button>
        </div>
        <button class="pw-submit" onclick="changePw()"><i class="ti ti-shield-check"></i> Save new password</button>
      </div>
    </div>
  </div>

</section>

</main>
<script type="application/json" id="dashboard-i18n">{
  "Manage configs of": "مدیریت کانفیگ‌های",
  "Choose the configs that belong to this group": "کانفیگ‌های متعلق به این گروه را انتخاب کنید",
  "Select all": "انتخاب همه",
  "Clear all": "پاک کردن انتخاب‌ها",
  "0 selected": "۰ انتخاب",
  "Loading configs…": "در حال بارگذاری کانفیگ‌ها…",
  "Changes are applied instantly": "تغییرات بلافاصله اعمال می‌شوند",
  "Close": "بستن",
  "Save": "ذخیره",
  "New sub group": "گروه اشتراک جدید",
  "Create a dedicated public page for a set of configs": "برای مجموعه‌ای از کانفیگ‌ها یک صفحه عمومی اختصاصی بسازید",
  "Group name": "نام گروه",
  "Description (optional)": "توضیحات (اختیاری)",
  "Public page password (optional)": "رمز صفحه عمومی (اختیاری)",
  "This group gets its own public page with a unique link.": "این گروه یک صفحه عمومی با لینک یکتا دریافت می‌کند.",
  "Cancel": "انصراف",
  "Create group": "ساخت گروه",
  "Edit config": "ویرایش کانفیگ",
  "Label": "برچسب داخلی",
  "Client remark": "نام نمایشی کلاینت",
  "Exact name shown in client apps": "نام دقیق نمایش‌داده‌شده در کلاینت‌ها",
  "Quota (0 = unlimited)": "حجم (۰ = نامحدود)",
  "Unit": "واحد",
  "Expiry (days from now, 0 = keep / unlimited)": "انقضا از امروز (۰ = حفظ مقدار/نامحدود)",
  "Note": "یادداشت",
  "Address (IPv4 / IPv6 / domain)": "آدرس (IPv4 / IPv6 / دامنه)",
  "TLS SNI (domain only)": "TLS SNI (فقط دامنه)",
  "Fingerprint (uTLS)": "اثر انگشت (uTLS)",
  "ALPN (empty = default)": "ALPN (خالی = پیش‌فرض)",
  "Connection port": "پورت اتصال",
  "IP limit (0 = unlimited)": "محدودیت IP (۰ = نامحدود)",
  "Speed limit (0 = unlimited)": "محدودیت سرعت (۰ = نامحدود)",
  "Leave the expiry field at 0 to keep the current date.": "برای حفظ تاریخ فعلی، فیلد انقضا را روی ۰ بگذارید.",
  "Save changes": "ذخیره تغییرات",
  "Workspace": "فضای کار",
  "Observe": "پایش",
  "Tools": "ابزارها",
  "Control room": "اتاق کنترل",
  "Route studio": "استودیوی مسیر",
  "Subscriptions": "اشتراک‌ها",
  "Sub Groups": "گروه‌های اشتراک",
  "Connections": "اتصالات",
  "Traffic": "ترافیک",
  "Activity Log": "گزارش فعالیت",
  "Errors": "خطاها",
  "Security": "امنیت",
  "WebSocket Test": "تست WebSocket",
  "Settings": "تنظیمات",
  "Change language": "تغییر زبان",
  "Change theme": "تغییر پوسته",
  "Light mode": "حالت روشن",
  "Dark mode": "حالت تاریک",
  "Sign out": "خروج",
  "Relay overview": "نمای کلی رله",
  "Loading...": "در حال بارگذاری…",
  "Active": "فعال",
  "Refresh": "تازه‌سازی",
  "Active connections": "اتصالات فعال",
  "WebSocket live": "WebSocket زنده",
  "Total traffic": "کل ترافیک",
  "since start-up": "از زمان راه‌اندازی",
  "Active configs": "کانفیگ‌های فعال",
  "of total": "از کل",
  "Default link (no limits)": "لینک پیش‌فرض (بدون محدودیت)",
  "Limited configs": "کانفیگ‌های محدود",
  "Hourly traffic (MB)": "ترافیک ساعتی (MB)",
  "Distribution": "توزیع",
  "Service status": "وضعیت سرویس",
  "UUID Auth": "احراز هویت UUID",
  "VLESS / WS Tunnel": "تونل VLESS / WS",
  "Subscription API": "API اشتراک",
  "Uptime": "زمان فعالیت",
  "Relative load": "بار نسبی",
  "Config summary": "خلاصه کانفیگ‌ها",
  "Compose, inspect, and deliver every connection from one workspace": "ساخت، بررسی و تحویل همه اتصال‌ها در یک فضای کاری",
  "Compose a new route": "ساخت مسیر جدید",
  "Identity first, network second, delivery controls last": "ابتدا هویت، سپس شبکه و در پایان کنترل‌های تحویل",
  "Config identity": "هویت کانفیگ",
  "Internal label · e.g. Alex Doe": "برچسب داخلی · مثلاً کاربر یک",
  "Client remark · e.g. Lumen Premium Amsterdam": "نام نمایشی کلاینت · مثلاً Lumen Premium Amsterdam",
  "Private note (optional)": "یادداشت خصوصی (اختیاری)",
  "Label is for the panel. Remark is the exact name shown inside the client app.": "برچسب برای پنل است؛ نام نمایشی دقیقاً داخل برنامه کلاینت دیده می‌شود.",
  "Sub group & expiry": "گروه اشتراک و انقضا",
  "— No group —": "— بدون گروه —",
  "Unlimited": "نامحدود",
  "7 days": "۷ روز",
  "30 days": "۳۰ روز",
  "90 days": "۹۰ روز",
  "Traffic quota": "حجم ترافیک",
  "Transport protocol": "پروتکل انتقال",
  "Turbo · zero-copy · maximum throughput": "توربو · کم‌کپی · بیشترین توان عبوری",
  "Connection identity": "هویت اتصال",
  "Choose the public dial target and the independent TLS identity.": "مقصد اتصال عمومی و هویت مستقل TLS را انتخاب کنید.",
  "Verified preset": "گزینه تأییدشده",
  "Custom route": "مسیر سفارشی",
  "Address": "آدرس",
  "Auto — current service": "خودکار — سرویس فعلی",
  "Custom address…": "آدرس سفارشی…",
  "The address after": "آدرس بعد از",
  ". Ports, paths and URL schemes are intentionally separate.": ". پورت، مسیر و scheme عمداً جدا هستند.",
  "TLS SNI": "TLS SNI",
  "Auto — safest TLS routing": "خودکار — امن‌ترین مسیریابی TLS",
  "Custom SNI…": "SNI سفارشی…",
  "SNI must be a domain. With a raw IP address, Auto keeps the service domain for TLS.": "SNI باید دامنه باشد. با Address از نوع IP، حالت خودکار دامنه سرویس را برای TLS نگه می‌دارد.",
  "Dial": "اتصال",
  "current service": "سرویس فعلی",
  "TLS identity": "هویت TLS",
  "WS default (http/1.1)": "پیش‌فرض WS (http/1.1)",
  "Custom...": "سفارشی…",
  "IP limit / concurrent users": "محدودیت IP / کاربران هم‌زمان",
  "1 user": "۱ کاربر",
  "2 user": "۲ کاربر",
  "5 user": "۵ کاربر",
  "Speed limit": "محدودیت سرعت",
  "Every UUID is fully random · only registered UUIDs may connect · the protocol cannot be changed later.": "هر UUID کاملاً تصادفی است؛ فقط UUIDهای ثبت‌شده متصل می‌شوند و پروتکل بعداً تغییر نمی‌کند.",
  "Build route": "ساخت مسیر",
  "No configs yet": "هنوز کانفیگی وجود ندارد",
  "Every group has its own public page with its own configs": "هر گروه صفحه عمومی مستقل و کانفیگ‌های خودش را دارد",
  "New group": "گروه جدید",
  "No groups yet": "هنوز گروهی وجود ندارد",
  "Create a group to organise your configs": "برای مرتب‌سازی کانفیگ‌ها یک گروه بسازید",
  "Subscription links for apps like v2ray": "لینک‌های اشتراک برای برنامه‌هایی مانند v2ray",
  "Per-config subscription": "اشتراک هر کانفیگ",
  "Each config URL has its own subscription link. On the config card, click the": "هر کانفیگ لینک اشتراک خودش را دارد. در کارت کانفیگ روی",
  "icon.": "بزنید.",
  "Full subscription (admin)": "اشتراک کامل (مدیر)",
  "Includes every active config.": "شامل همه کانفیگ‌های فعال است.",
  "This address only works in the browser that is signed in to the panel (session cookie required).": "این آدرس فقط در مرورگری کار می‌کند که وارد پنل شده باشد.",
  "Group subscription links": "لینک‌های اشتراک گروه‌ها",
  "Loading groups…": "در حال بارگذاری گروه‌ها…",
  "Bandwidth usage analytics and monitoring": "تحلیل و پایش مصرف پهنای باند",
  "Total traffic used": "کل ترافیک مصرف‌شده",
  "Hourly average": "میانگین ساعتی",
  "MB per hour": "MB در ساعت",
  "Peak usage": "بیشترین مصرف",
  "peak hour": "ساعت اوج",
  "Lowest usage": "کمترین مصرف",
  "Traffic usage trend": "روند مصرف ترافیک",
  "Megabytes per hour": "مگابایت در ساعت",
  "Usage": "مصرف",
  "Average": "میانگین",
  "Live monitoring of IP and traffic per connection": "پایش زنده IP و ترافیک هر اتصال",
  "Live connections": "اتصالات زنده",
  "Live traffic total": "کل ترافیک زنده",
  "Average session length": "میانگین زمان نشست",
  "Unique IPs": "IPهای یکتا",
  "Connection list": "فهرست اتصالات",
  "Auto-refresh every 5 seconds": "تازه‌سازی خودکار هر ۵ ثانیه",
  "No active connections": "اتصال فعالی وجود ندارد",
  "Clients will appear here as soon as they connect": "کلاینت‌ها پس از اتصال در اینجا نمایش داده می‌شوند",
  "Encryption": "رمزنگاری",
  "TLS/HTTPS": "TLS/HTTPS",
  "Fingerprint": "اثر انگشت",
  "Chrome Spoof": "شبیه‌سازی Chrome",
  "Protocols": "پروتکل‌ها",
  "Password hash": "هش رمز",
  "Session": "نشست",
  "Access control": "کنترل دسترسی",
  "UUID Auth strict": "احراز هویت سخت‌گیرانه UUID",
  "Enable / disable config": "فعال/غیرفعال‌کردن کانفیگ",
  "Expiry date": "تاریخ انقضا",
  "Public sub page password": "رمز صفحه عمومی اشتراک",
  "Complete history of panel events": "تاریخچه کامل رویدادهای پنل",
  "No log entries yet": "هنوز گزارشی ثبت نشده",
  "Error log": "گزارش خطا",
  "Only registered and active UUIDs can connect. This build supports VLESS over WebSocket only.": "فقط UUIDهای ثبت‌شده و فعال متصل می‌شوند. این نسخه فقط VLESS روی WebSocket را پشتیبانی می‌کند.",
  "UUID (must already exist in Configs)": "UUID (باید از قبل در کانفیگ‌ها وجود داشته باشد)",
  "Disconnect": "قطع اتصال",
  "Send": "ارسال",
  "Waiting for connection...": "در انتظار اتصال…",
  "Online · Railway": "آنلاین · Railway",
  "Default port": "پورت پیش‌فرض",
  "443 (TLS) · can be overridden per config": "443 (TLS) · برای هر کانفیگ قابل تغییر",
  "Version": "نسخه",
  "Framework": "فریم‌ورک",
  "Platform": "پلتفرم",
  "Storage": "ذخیره‌سازی",
  "Change password": "تغییر رمز",
  "Pick a strong password and keep it somewhere safe": "یک رمز قوی انتخاب و در جای امن نگهداری کنید",
  "Current password": "رمز فعلی",
  "New password": "رمز جدید",
  "Password strength": "قدرت رمز",
  "At least 4 characters": "حداقل ۴ نویسه",
  "Has a number": "دارای عدد",
  "Upper & lower case": "حروف بزرگ و کوچک",
  "Repeat new password": "تکرار رمز جدید",
  "Save new password": "ذخیره رمز جدید",
  "The IP address seen by destination websites": "IP دیده‌شده توسط سایت‌های مقصد",
  "Outbound mode": "حالت خروجی",
  "Direct — server connection (default)": "مستقیم — اتصال سرور (پیش‌فرض)",
  "SOCKS5 — chained proxy": "SOCKS5 — پروکسی زنجیره‌ای",
  "Default port 443 · supports": "پورت پیش‌فرض ۴۴۳ · پشتیبانی از",
  "and TXT records. Separate with commas or new lines (up to 8 candidates are selected).": "و رکورد TXT. با کاما یا خط جدید جدا کنید (تا ۸ گزینه انتخاب می‌شود).",
  "Chained proxy address": "آدرس پروکسی زنجیره‌ای",
  "The saved password is masked; enter the full value again to change it.": "رمز ذخیره‌شده پنهان است؛ برای تغییر مقدار کامل را دوباره وارد کنید.",
  "Parallel dial (PROXY_CONCURRENT_DIAL)": "اتصال موازی (PROXY_CONCURRENT_DIAL)",
  "Higher values start faster but may rotate the exit IP more often.": "مقادیر بالاتر سریع‌تر شروع می‌شوند اما ممکن است IP خروجی بیشتر تغییر کند.",
  "Forced hosts (GO2SOCKS5)": "میزبان‌های اجباری (GO2SOCKS5)",
  "Only for chained proxy modes.": "فقط برای حالت‌های پروکسی زنجیره‌ای.",
  "= all destinations.": "= همه مقصدها.",
  "Connect directly if every candidate fails (fallback)": "اگر همه گزینه‌ها شکست خوردند مستقیم متصل شو (fallback)",
  "Use chained proxy for every destination (global)": "استفاده از پروکسی زنجیره‌ای برای همه مقصدها (global)",
  "Save settings": "ذخیره تنظیمات",
  "Test connection": "تست اتصال",
  "Port": "پورت",
  "Traffic used": "ترافیک مصرف‌شده",
  "Expiry": "انقضا",
  "Users": "کاربران",
  "Speed": "سرعت",
  "Copy UUID": "کپی UUID",
  "Copy config": "کپی کانفیگ",
  "Copy subscription": "کپی اشتراک",
  "Show QR": "نمایش QR",
  "Reset usage": "ریست مصرف",
  "Delete config": "حذف کانفیگ",
  "Live": "زنده",
  "Paused": "متوقف",
  "Enable or disable config": "فعال یا غیرفعال‌کردن کانفیگ",
  "Config copied": "کانفیگ کپی شد",
  "Subscription copied": "اشتراک کپی شد",
  "UUID copied": "UUID کپی شد",
  "Refreshed": "تازه‌سازی شد",
  "No configs": "بدون کانفیگ",
  "config": "کانفیگ",
  "Group": "گروه",
  "Inactive": "غیرفعال",
  "Copy": "کپی",
  "Open": "بازکردن",
  ",": "،",
  ", suffix": "، پسوند",
  "Optional reverse-SNI exit path, isolated from every other user.": "مسیر خروجی اختیاری مبتنی بر SNI که از تمام کاربران دیگر جداست.",
  "Only this config": "فقط همین کانفیگ",
  "Connection mode": "حالت اتصال",
  "Direct — safest default": "مستقیم — امن‌ترین پیش‌فرض",
  "Parallel checks": "بررسی‌های موازی",
  "Direct fallback is always enabled and cannot be disabled.": "بازگشت مستقیم همیشه فعال است و غیرفعال نمی‌شود.",
  "Direct · fallback ready": "مستقیم · آماده بازگشت",
  "1 parallel check": "۱ بررسی موازی",
  "2 parallel checks": "۲ بررسی موازی",
  "4 parallel checks": "۴ بررسی موازی",
  "6 parallel checks": "۶ بررسی موازی",
  "Exit IP settings": "تنظیم آیپی خروجی",
  "Managed proxy repository": "مخزن پروکسی مدیریت‌شده",
  "Custom proxy — unsafe": "پروکسی دلخواه — ناامن",
  "Managed proxy": "پروکسی مدیریت‌شده",
  "Managed and verified": "مدیریت‌شده و تأییدشده",
  "Custom proxy URL": "آدرس پروکسی دلخواه",
  "Managed endpoints stay server-side. Only flag, country, protocol, and health are shown.": "آدرس‌های مدیریت‌شده فقط در سرور می‌مانند؛ فقط پرچم، کشور، پروتکل و سلامت نمایش داده می‌شود.",
  "Recheck now": "بررسی جدید",
  "Repository checked again": "مخزن دوباره بررسی شد",
  "Refresh failed": "بررسی جدید ناموفق بود"
}</script>
<script>
const I18N_FA=JSON.parse(document.getElementById('dashboard-i18n').textContent);
let uiLang=localStorage.getItem('lumen-ui-lang')||'en';
const _textOrigins=new WeakMap(),_attrOrigins=new WeakMap();
function tr(value){const v=String(value??'');return uiLang==='fa'?(I18N_FA[v]||v):v}
function translateTree(root=document.body){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  let n;while(n=walker.nextNode()){
    if(['SCRIPT','STYLE','CODE'].includes(n.parentElement?.tagName))continue;
    const raw=n.nodeValue,core=raw.trim();if(!core)continue;
    if(!_textOrigins.has(n))_textOrigins.set(n,core);
    const origin=_textOrigins.get(n),target=uiLang==='fa'?(I18N_FA[origin]||origin):origin;
    n.nodeValue=raw.slice(0,raw.indexOf(core))+target+raw.slice(raw.indexOf(core)+core.length);
  }
  root.querySelectorAll?.('[placeholder],[title],[aria-label]').forEach(el=>{
    let origins=_attrOrigins.get(el);if(!origins){origins={};['placeholder','title','aria-label'].forEach(a=>{if(el.hasAttribute(a))origins[a]=el.getAttribute(a)});_attrOrigins.set(el,origins)}
    Object.entries(origins).forEach(([a,v])=>el.setAttribute(a,uiLang==='fa'?(I18N_FA[v]||v):v));
  });
}
function applyLanguage(){
  document.documentElement.lang=uiLang;document.documentElement.dir=uiLang==='fa'?'rtl':'ltr';
  translateTree(document.body);
  const l=document.getElementById('lang-label');if(l)l.textContent=uiLang==='fa'?'English':'فارسی';
  const mob=document.getElementById('lang-mob-btn');if(mob)mob.title=uiLang==='fa'?'English':'فارسی';
}
function toggleLanguage(){uiLang=uiLang==='en'?'fa':'en';localStorage.setItem('lumen-ui-lang',uiLang);applyLanguage();applyTheme(isDark)}
const _i18nObserver=new MutationObserver(entries=>entries.forEach(e=>e.addedNodes.forEach(n=>{if(n.nodeType===1)translateTree(n);else if(n.nodeType===3&&n.parentElement)translateTree(n.parentElement)})));
let isDark=localStorage.getItem('x4g-theme')!=='light';
function applyTheme(dark){
  document.documentElement.setAttribute('data-theme',dark?'dark':'light');
  const icon=dark?'ti-sun':'ti-moon',label=tr(dark?'Light mode':'Dark mode');
  document.getElementById('theme-icon').className='ti '+icon;
  document.getElementById('theme-label').textContent=label;
  const mobI=document.getElementById('theme-mob-icon');if(mobI)mobI.className='ti '+icon;
}
function toggleTheme(){isDark=!isDark;localStorage.setItem('x4g-theme',isDark?'dark':'light');applyTheme(isDark)}
applyTheme(isDark);applyLanguage();_i18nObserver.observe(document.body,{childList:true,subtree:true});
function toast(msg,type=''){
  const t=document.getElementById('toast');
  t.textContent=tr(msg);t.className='toast show'+(type?' '+type:'');
  setTimeout(()=>t.classList.remove('show'),2400);
}
function fmtB(b){if(!b||b===0)return '0 B';if(b<1024)return b+' B';if(b<1024**2)return (b/1024).toFixed(1)+' KB';if(b<1024**3)return (b/1024**2).toFixed(2)+' MB';return (b/1024**3).toFixed(2)+' GB'}
function toFa(n){const v=String(n);return uiLang==='fa'?v.replace(/\d/g,d=>'۰۱۲۳۴۵۶۷۸۹'[d]):v}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function daysLeft(exp){if(!exp)return null;return Math.ceil((new Date(exp)-Date.now())/(864e5))}
function expChip(exp,expired){
  if(expired)return '<span class="exp-chip ec-exp"><i class="ti ti-calendar-x"></i> Expired</span>';
  if(!exp)return '<span class="exp-chip ec-inf"><i class="ti ti-infinity"></i> Unlimited</span>';
  const d=daysLeft(exp);
  if(d<=0)return '<span class="exp-chip ec-exp"><i class="ti ti-calendar-x"></i> Expired</span>';
  if(d<=3)return `<span class="exp-chip ec-warn"><i class="ti ti-alert-triangle"></i> ${toFa(d)} days left</span>`;
  return `<span class="exp-chip ec-ok"><i class="ti ti-calendar-check"></i> ${toFa(d)} days left</span>`;
}
function protoBadge(p){
  const m={'vless-ws':['VLESS · WS Turbo','pc-ws']};
  const v=m[p]||m['vless-ws'];
  return `<span class="proto-chip ${v[1]}">${v[0]}</span>`;
}
async function checkAuth(){try{const r=await fetch('/api/me');const d=await r.json();if(!d.authenticated)location.href='/login';}catch(e){location.href='/login'}}
async function logout(){try{await fetch('/api/logout',{method:'POST'})}catch(e){}location.href='/login'}
document.getElementById('logout-btn').addEventListener('click',logout);
async function authF(url,opts={}){
  const r=await fetch(url,opts);
  if(r.status===401){location.href='/login';throw new Error('unauthorized')}
  return r;
}

/* ===== Managed proxy repository per config ===== */
let managedProxyCatalog=[];
function managedOption(p){return `<option value="${esc(p.id)}">${esc((p.flag||'🌐')+' '+p.country+' · '+p.health+'% · '+p.type.toUpperCase())}</option>`}
async function loadProxyCatalog(){const btn=document.getElementById('proxy-recheck-btn');try{const sr=await authF('/api/proxy-catalog/manual-status');const state=await sr.json();if(btn)btn.style.display=state.enabled?'inline-flex':'none'}catch(e){if(btn)btn.style.display='none'}try{const r=await authF('/api/proxy-catalog');const d=await r.json();managedProxyCatalog=d.proxies||[];if(btn&&d.status?.manual_refresh_enabled)btn.style.display='inline-flex';['nl-proxy-id','el-proxy-id'].forEach(id=>{const e=document.getElementById(id);if(!e)return;const old=e.value;e.innerHTML='<option value="">— Choose managed proxy —</option>'+managedProxyCatalog.map(managedOption).join('');if(managedProxyCatalog.some(p=>p.id===old))e.value=old})}catch(e){toast('Managed proxy repository unavailable','err')}}
async function refreshProxyCatalogNow(){const btn=document.getElementById('proxy-recheck-btn');if(btn)btn.disabled=true;try{const r=await authF('/api/proxy-catalog/refresh',{method:'POST'});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Refresh failed');toast('Repository checked again','ok');await loadProxyCatalog()}catch(e){toast(e.message||'Refresh failed','err')}finally{if(btn)btn.disabled=false}}
function syncExitProxy(prefix){const m=document.getElementById(prefix+'-exit-mode')?.value||'direct';document.getElementById(prefix+'-repository-fields').style.display=m==='repository'?'':'none';document.getElementById(prefix+'-custom-fields').style.display=m==='custom'?'':'none';if(m==='custom')toast('Warning: custom proxy is outside the managed safety boundary','err')}
function exitProxyValues(prefix){return {exit_proxy_mode:document.getElementById(prefix+'-exit-mode')?.value||'direct',proxy_id:document.getElementById(prefix+'-proxy-id')?.value||'',custom_proxy:document.getElementById(prefix+'-custom-proxy')?.value.trim()||''}}
function setQuota(val,unit,el){
  document.getElementById('nl-val').value = val===0?'':val;
  document.getElementById('nl-unit').value = unit;
  document.querySelectorAll('#quota-chips .chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}
function setExpiry(days,el){
  document.getElementById('nl-exp').value = days===0?'':days;
  document.querySelectorAll('#exp-chips .chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}
function selectProto(val,el){
  document.getElementById('nl-proto').value = val;
  document.querySelectorAll('.proto-card').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}
function setIpLimit(n,el){
  document.getElementById('nl-iplimit').value = n;
  document.querySelectorAll('#iplimit-chips .chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}
function setSpeedLimit(n,el){
  document.getElementById('nl-speed').value = n;
  document.getElementById('nl-speed-unit').value = 'MBIT';
  document.querySelectorAll('#speed-chips .chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}
function onAlpnPresetChange(){
  const p=document.getElementById('nl-alpn-preset').value;
  const inp=document.getElementById('nl-alpn');
  if(p==='__custom__'){inp.style.display='block';inp.value='';inp.focus();}
  else{inp.style.display='none';inp.value=p;}
}
const sb=document.getElementById('sb'),overlay=document.getElementById('overlay');
function openSb(){sb.classList.add('open');overlay.classList.add('show')}
function closeSb(){sb.classList.remove('open');overlay.classList.remove('show')}
document.getElementById('open-sb').addEventListener('click',openSb);
document.getElementById('close-sb').addEventListener('click',closeSb);
overlay.addEventListener('click',closeSb);
function navTo(name){
  document.querySelectorAll('.nav-it').forEach(n=>n.classList.toggle('on',n.dataset.pg===name));
  document.querySelectorAll('.pg').forEach(p=>p.classList.toggle('on',p.id==='pg-'+name));
  const loaders={links:loadLinks,connections:loadConns,errors:loadErrs,subscriptions:loadSubsPage,subgroups:loadSubs,logs:loadActivity};
  if(loaders[name])loaders[name]();
  closeSb();window.scrollTo({top:0,behavior:'smooth'});
}
document.querySelectorAll('.nav-it').forEach(el=>el.addEventListener('click',()=>navTo(el.dataset.pg)));
function openModal(id){document.getElementById(id).classList.add('open')}
function closeModal(id){document.getElementById(id).classList.remove('open')}
let prevTraf=0,ch1,ch2,ch3;
async function fetchStats(){
  try{
    const r=await authF('/stats'),d=await r.json();
    document.getElementById('m-conns').textContent=d.active_connections;
    document.getElementById('conns-nb').textContent=d.active_connections;
    document.getElementById('m-traffic').innerHTML=d.total_traffic_mb.toFixed(1)+'<span class="m-unit">MB</span>';
    document.getElementById('m-alinks').textContent=d.active_links??'—';
    document.getElementById('m-lsub').textContent='of '+d.links_count+' config';
    document.getElementById('m-subs').textContent=d.subs_count??'—';
    document.getElementById('errs-badge').textContent=d.total_errors+' Error';
    document.getElementById('uptime-inline').textContent=d.uptime;
    document.getElementById('uptime-badge').textContent='Railway · '+d.uptime;
    document.getElementById('last-upd').textContent='Last update: '+new Date().toLocaleTimeString('en-US');
    document.getElementById('conns-live').innerHTML='<span class="dot dg pulse"></span> '+d.active_connections+' connection';
    document.getElementById('t-traffic').innerHTML=d.total_traffic_mb.toFixed(1)+'<span class="m-unit">MB</span>';
    const delta=d.total_traffic_mb-prevTraf,pct=Math.min(100,Math.round((delta/50)*100));
    document.getElementById('bw-pct').textContent=pct+'%';
    document.getElementById('bw-bar').style.width=pct+'%';
    prevTraf=d.total_traffic_mb;
    if(d.hourly){
      const labels=Object.keys(d.hourly).sort(),vals=labels.map(k=>+(d.hourly[k]/1024**2).toFixed(2));
      [ch1,ch3].forEach(c=>{if(!c)return;c.data.labels=labels;c.data.datasets[0].data=vals;c.update()});
      if(vals.length){const avg=vals.reduce((a,b)=>a+b,0)/vals.length,peak=Math.max(...vals);document.getElementById('t-avg').innerHTML=avg.toFixed(2)+'<span class="m-unit">MB</span>';document.getElementById('t-peak').innerHTML=peak.toFixed(2)+'<span class="m-unit">MB</span>';}
    }
    renderErrs(d.recent_errors||[]);
  }catch(e){console.error(e)}
}
function renderErrs(errs){
  const el=document.getElementById('errs-full');if(!el)return;
  if(!errs.length){el.innerHTML='<div style="color:var(--green-t);padding:10px;font-size:12px;display:flex;align-items:center;gap:5px"><i class="ti ti-circle-check"></i> No errors</div>';return}
  el.innerHTML=errs.slice().reverse().map(e=>`<div class="erow"><div class="etime"><i class="ti ti-clock"></i>${new Date(e.time).toLocaleString('en-US')}</div><div class="emsg">${esc(e.error)}${e.url?' — '+esc(e.url):''}</div></div>`).join('');
}
async function loadActivity(){
  try{
    const r=await authF('/api/activity'),d=await r.json();
    const logs=(d.logs||[]).slice().reverse();
    const el=document.getElementById('logs-list'),em=document.getElementById('logs-empty');
    if(!logs.length){el.innerHTML='';em.style.display='block';return}
    em.style.display='none';
    const icMap={ok:'ti-circle-check',err:'ti-circle-x',warn:'ti-alert-triangle',info:'ti-info-circle'};
    const kindFa={link:'config',sub:'Group',auth:'Sign in',connection:'connection',system:'System'};
    el.innerHTML=logs.map(l=>`
      <div class="log-item">
        <div class="log-ic ${l.level}"><i class="ti ${icMap[l.level]||'ti-info-circle'}"></i></div>
        <div class="log-body">
          <div class="log-msg">${esc(l.message)}</div>
          <div class="log-time"><i class="ti ti-clock"></i> ${new Date(l.time).toLocaleString('en-US')} <span class="log-kind">${kindFa[l.kind]||l.kind}</span></div>
        </div>
      </div>
    `).join('');
  }catch(e){console.error(e)}
}
let endpointCatalog={default_address:location.hostname,default_sni:location.hostname,addresses:[],snis:[]};
function endpointOption(value,label){return `<option value="${esc(value)}">${esc(label||value)}</option>`}
function endpointValue(kind){
  const sel=document.getElementById('nl-'+kind);
  if(!sel)return '';
  if(sel.value==='__custom__')return document.getElementById('nl-'+kind+'-custom').value.trim();
  if(sel.value==='__auto__')return kind==='address'?(endpointCatalog.default_address||location.hostname):'';
  return sel.value;
}
function endpointChoiceChanged(kind){
  const custom=document.getElementById('nl-'+kind).value==='__custom__';
  document.getElementById('nl-'+kind+'-custom-row').style.display=custom?'':'none';
  if(custom)setTimeout(()=>document.getElementById('nl-'+kind+'-custom').focus(),0);
  updateEndpointPreview();
}
function isIpAddressPreview(value){
  const v=String(value||'').trim();
  return v.includes(':')||/^(?:\d{1,3}\.){3}\d{1,3}$/.test(v);
}
function updateEndpointPreview(){
  const address=endpointValue('address')||endpointCatalog.default_address||location.hostname;
  const explicitSni=endpointValue('sni');
  const sni=explicitSni||(isIpAddressPreview(address)?(endpointCatalog.default_sni||location.hostname):address);
  document.getElementById('endpoint-preview-address').textContent=address||'—';
  document.getElementById('endpoint-preview-sni').textContent=sni||'—';
  const custom=['address','sni'].some(k=>document.getElementById('nl-'+k).value==='__custom__');
  const badge=document.getElementById('endpoint-status');
  badge.className='endpoint-status'+(custom?' custom':'');
  badge.innerHTML=custom?'<i class="ti ti-adjustments-horizontal"></i> Custom route':'<i class="ti ti-rosette-discount-check"></i> Verified preset';
}
async function loadEndpointChoices(){
  try{
    const r=await authF('/api/config-endpoints');
    const d=await r.json();
    if(!r.ok)throw new Error(d.detail||'Could not load endpoint choices');
    endpointCatalog=d;
    const a=document.getElementById('nl-address'),sn=document.getElementById('nl-sni');
    const aOld=a.value,sOld=sn.value;
    a.innerHTML=endpointOption('__auto__',`Auto — service · ${d.default_address}`)+(d.addresses||[]).map(x=>endpointOption(x.value,`${x.current?'Service':'Relay'} · ${x.value} · ${x.kind}`)).join('')+endpointOption('__custom__','Custom address…');
    sn.innerHTML=endpointOption('__auto__','Auto — safest TLS routing')+(d.snis||[]).map(x=>endpointOption(x,x===d.default_sni?`Service TLS · ${x}`:x)).join('')+endpointOption('__custom__','Custom SNI…');
    if([...a.options].some(o=>o.value===aOld))a.value=aOld;
    if([...sn.options].some(o=>o.value===sOld))sn.value=sOld;
    endpointChoiceChanged('address');endpointChoiceChanged('sni');
  }catch(e){console.error(e);toast(e.message||'Endpoint list unavailable','err')}
}
function selectedCreateEndpoints(){return {address:endpointValue('address'),sni:endpointValue('sni')}}
let allSubsList=[],allLinksList=[];
async function loadLinks(){
  try{
    const [lr,sr]=await Promise.all([authF('/api/links'),authF('/api/subs')]);
    const {links=[]}=await lr.json();
    const {subs=[]}=await sr.json();
    allSubsList=subs;allLinksList=links;
    const nlSub=document.getElementById('nl-sub');
    const selectedSub=nlSub.value;
    nlSub.innerHTML='<option value="">— No group —</option>'+subs.map(s=>`<option value="${esc(s.sub_id)}">${esc(s.name)}</option>`).join('');
    if(selectedSub&&subs.some(s=>s.sub_id===selectedSub))nlSub.value=selectedSub;
    document.getElementById('links-nb').textContent=links.length;
    document.getElementById('links-pg-cnt').textContent=toFa(links.length)+' '+tr('config');
    document.getElementById('lsummary-badge').textContent=toFa(links.length);
    const grid=document.getElementById('links-grid'),empty=document.getElementById('links-empty');
    if(!links.length){grid.innerHTML='';empty.style.display='block';document.getElementById('lsummary').innerHTML='<div class="empty"><i class="ti ti-link-off"></i><p>No configs</p></div>';return}
    empty.style.display='none';
    const subMap=Object.fromEntries(subs.map(s=>[s.sub_id,s.name]));
    grid.innerHTML=links.map(l=>{
      const lim=l.limit_bytes===0?'∞':fmtB(l.limit_bytes);
      const pct=l.limit_bytes===0?0:Math.min(100,l.used_bytes/l.limit_bytes*100);
      const allowed=l.active&&!l.expired;
      const cardCls=!l.active?'is-off':(l.expired?'is-exp':'');
      const routeAddress=l.address||location.hostname;
      const routeSni=l.sni||((l.address&&!isIpAddressPreview(l.address))?l.address:location.hostname);
      const speed=l.speed_limit_bytes?((l.speed_limit_bytes*8/1024/1024).toFixed(1)+' Mbps'):'Unlimited';
      return `<article class="route-card ${cardCls}">
        <header class="route-head">
          <div class="route-title-wrap">
            <span class="route-status-light ${allowed?'on':''}"></span>
            <div><div class="route-label">${esc(l.label)}</div><div class="route-remark"><i class="ti ti-message-2"></i>${esc(l.remark||l.label)}</div></div>
          </div>
          <button class="route-state ${allowed?'on':''}" onclick="toggleActive('${l.uuid}',${!l.active})" aria-label="Enable or disable config"><i class="ti ${allowed?'ti-player-pause':'ti-player-play'}"></i><span>${allowed?'Live':'Paused'}</span></button>
        </header>
        <div class="route-network">
          <div><span>Address</span><strong>${esc(routeAddress)}</strong></div>
          <i class="ti ti-arrow-right route-arrow"></i>
          <div><span>TLS SNI</span><strong>${esc(routeSni)}</strong></div>
          <div class="route-port"><span>Port</span><strong>${l.port||443}</strong></div>
        </div>
        <div class="route-proxy ${l.exit_proxy_mode==='repository'?'enabled':(l.exit_proxy_mode==='custom'?'custom':'direct')}"><i class="ti ${l.exit_proxy_mode==='repository'?'ti-shield-check':(l.exit_proxy_mode==='custom'?'ti-alert-triangle':'ti-route')}"></i><span>${l.exit_proxy_mode==='repository'&&l.exit_proxy?`${esc(l.exit_proxy.flag||'🌐')} ${esc(l.exit_proxy.country)} · ${l.exit_proxy.health}% · ${esc(l.exit_proxy.type.toUpperCase())}`:(l.exit_proxy_mode==='custom'?'Custom proxy · unsafe':'Direct')}</span></div>
        <div class="route-data">
          <div class="route-usage">
            <div class="route-data-head"><span>Traffic used</span><b>${fmtB(l.used_bytes)} / ${lim}</b></div>
            <div class="route-meter"><i style="width:${pct}%"></i></div>
          </div>
          <div class="route-fact"><span>Expiry</span>${expChip(l.expires_at,l.expired)}</div>
          <div class="route-fact"><span>Users</span><strong>${l.connected_ips||0}${l.ip_limit?('/'+l.ip_limit):' / ∞'}</strong></div>
          <div class="route-fact"><span>Speed</span><strong>${speed}</strong></div>
        </div>
        <button class="route-uuid" onclick="navigator.clipboard.writeText('${l.uuid}').then(()=>toast('UUID copied','ok'))"><i class="ti ti-fingerprint"></i><code>${l.uuid}</code><span>Copy UUID</span></button>
        <footer class="route-actions">
          <button class="route-action primary" onclick="navigator.clipboard.writeText('${esc(l.vless_link)}').then(()=>toast('Config copied','ok'))"><i class="ti ti-copy"></i><span>Copy config</span></button>
          <button class="route-action secondary" onclick="navigator.clipboard.writeText('${esc(l.sub_url)}').then(()=>toast('Subscription copied','ok'))"><i class="ti ti-rss"></i><span>Copy subscription</span></button>
          <button class="route-action compact" onclick="showQR('${esc(l.vless_link)}')" title="Show QR" aria-label="Show QR"><i class="ti ti-qrcode"></i></button>
          <button class="route-action compact" onclick="openEditLink('${l.uuid}')" title="Edit config" aria-label="Edit config"><i class="ti ti-pencil"></i></button>
          <button class="route-action compact" onclick="resetUsage('${l.uuid}')" title="Reset usage" aria-label="Reset usage"><i class="ti ti-rotate"></i></button>
          <button class="route-action compact danger" onclick="deleteLink('${l.uuid}')" title="Delete config" aria-label="Delete config"><i class="ti ti-trash"></i></button>
        </footer>
      </article>`;
    }).join('');
    document.getElementById('lsummary').innerHTML=links.slice(0,6).map(l=>`<div class="sr"><span class="sr-k" style="gap:5px"><i class="ti ${l.expired?'ti-calendar-x':l.active?'ti-circle-check':'ti-circle-x'}" style="color:${l.expired?'var(--amber)':l.active?'var(--green)':'var(--red)'}"></i>${esc(l.label)}</span><span class="sr-v" style="font-size:10px">${fmtB(l.used_bytes)} / ${l.limit_bytes===0?'∞':fmtB(l.limit_bytes)}</span></div>`).join('');
  }catch(e){console.error(e)}
}
async function createLink(){
  const label=document.getElementById('nl-label').value.trim()||'New config';
  const val=document.getElementById('nl-val').value;
  const unit=document.getElementById('nl-unit').value;
  const exp=document.getElementById('nl-exp').value;
  const note=document.getElementById('nl-note').value.trim();
  const remark=document.getElementById('nl-remark').value.trim()||label;
  const sub_id=document.getElementById('nl-sub').value||null;
  const protocol=document.getElementById('nl-proto').value||'vless-ws';
  const fingerprint=document.getElementById('nl-fp').value||'chrome';
  const alpn=document.getElementById('nl-alpn').value.trim();
  const port=Number(document.getElementById('nl-port').value)||443;
  const ip_limit=Number(document.getElementById('nl-iplimit').value)||0;
  const speed_limit_value=Number(document.getElementById('nl-speed').value)||0;
  const speed_limit_unit=document.getElementById('nl-speed-unit').value;
  const {address,sni}=selectedCreateEndpoints();
  const {exit_proxy_mode,proxy_id,custom_proxy}=exitProxyValues('nl');
  try{
    const r=await authF('/api/links',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({label,remark,limit_value:val||0,limit_unit:unit,expires_days:exp||0,note,sub_id,protocol,fingerprint,alpn,port,ip_limit,speed_limit_value,speed_limit_unit,address,sni,exit_proxy_mode,proxy_id,custom_proxy})});
    const d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.detail||'Could not create config');
    ['nl-label','nl-remark','nl-val','nl-exp','nl-note','nl-alpn'].forEach(id=>document.getElementById(id).value='');
    document.getElementById('nl-port').value='443';
    document.getElementById('nl-iplimit').value='0';
    document.getElementById('nl-speed').value='0';
    document.getElementById('nl-alpn-preset').value='';
    document.getElementById('nl-alpn').style.display='none';
    document.getElementById('nl-exit-mode').value='direct';document.getElementById('nl-custom-proxy').value='';syncExitProxy('nl');
    toast('Config created ✓','ok');loadLinks();
  }catch(e){toast(e.message||'Could not create','err')}
}
function openEditLink(uuid){
  const l=allLinksList.find(x=>x.uuid===uuid);
  if(!l)return;
  document.getElementById('el-uuid').value=uuid;
  document.getElementById('el-label').value=l.label;
  document.getElementById('el-remark').value=l.remark||l.label||'';
  document.getElementById('el-note').value=l.note||'';
  if(l.limit_bytes===0){document.getElementById('el-val').value='';document.getElementById('el-unit').value='GB';}
  else{document.getElementById('el-val').value=(l.limit_bytes/1024/1024).toFixed(0);document.getElementById('el-unit').value='MB';}
  document.getElementById('el-exp').value='';
  document.getElementById('el-fp').value=l.fingerprint||'chrome';
  document.getElementById('el-alpn').value=l.alpn||'';
  document.getElementById('el-port').value=l.port||443;
  document.getElementById('el-address').value=l.address||'';
  document.getElementById('el-sni').value=l.sni||'';
  document.getElementById('el-exit-mode').value=l.exit_proxy_mode||'direct';document.getElementById('el-proxy-id').value=l.proxy_id||'';document.getElementById('el-custom-proxy').value=l.custom_proxy||'';syncExitProxy('el');
  document.getElementById('el-iplimit').value=l.ip_limit||0;
  if(!l.speed_limit_bytes){document.getElementById('el-speed').value='0';document.getElementById('el-speed-unit').value='MBIT';}
  else{document.getElementById('el-speed').value=(l.speed_limit_bytes*8/1024/1024).toFixed(2);document.getElementById('el-speed-unit').value='MBIT';}
  openModal('modal-edit-link');
}
async function saveEditLink(){
  const uuid=document.getElementById('el-uuid').value;
  const label=document.getElementById('el-label').value.trim();
  const remark=document.getElementById('el-remark').value.trim()||label;
  const note=document.getElementById('el-note').value.trim();
  const val=document.getElementById('el-val').value;
  const unit=document.getElementById('el-unit').value;
  const exp=document.getElementById('el-exp').value;
  const fingerprint=document.getElementById('el-fp').value||'chrome';
  const alpn=document.getElementById('el-alpn').value.trim();
  const port=Number(document.getElementById('el-port').value)||443;
  const ip_limit=Number(document.getElementById('el-iplimit').value)||0;
  const speed_limit_value=Number(document.getElementById('el-speed').value)||0;
  const speed_limit_unit=document.getElementById('el-speed-unit').value;
  const address=document.getElementById('el-address').value.trim();
  const sni=document.getElementById('el-sni').value.trim();
  const {exit_proxy_mode,proxy_id,custom_proxy}=exitProxyValues('el');
  const body={label,remark,note,limit_value:val||0,limit_unit:unit,fingerprint,alpn,port,ip_limit,speed_limit_value,speed_limit_unit,address,sni,exit_proxy_mode,proxy_id,custom_proxy};
  if(exp&&Number(exp)>0)body.expires_days=Number(exp);
  try{
    const r=await authF('/api/links/'+uuid,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.detail||'Could not update');
    closeModal('modal-edit-link');
    toast('Config updated ✓','ok');loadLinks();
  }catch(e){toast(e.message||'Could not update','err')}
}
async function toggleActive(uuid,newState){
  try{const r=await authF('/api/links/'+uuid,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:newState})});if(!r.ok)throw new Error();toast(newState?'Enabled ✓':'Disabled','ok');loadLinks();}catch(e){toast('Error','err')}
}
async function resetUsage(uuid){
  try{const r=await authF('/api/links/'+uuid,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({reset_usage:true})});if(!r.ok)throw new Error();toast('Usage reset ✓','ok');loadLinks();}catch(e){toast('Error','err')}
}
async function deleteLink(uuid){
  if(!confirm('Delete this config?'))return;
  try{const r=await authF('/api/links/'+uuid,{method:'DELETE'});if(!r.ok)throw new Error();toast('Deleted ✓','ok');loadLinks();}catch(e){toast('Error','err')}
}
function showQR(link){window.open('https://api.qrserver.com/v1/create-qr-code/?size=300x300&data='+encodeURIComponent(link),'_blank')}
let allSubsRaw=[];
async function loadSubs(){
  try{
    const r=await authF('/api/subs'),d=await r.json();
    const subs=d.subs||[];
    allSubsRaw=subs;
    document.getElementById('subs-nb').textContent=subs.length;
    document.getElementById('subs-pg-cnt').textContent=toFa(subs.length)+' '+tr('Group');
    renderSubsGrid(subs);
  }catch(e){console.error(e)}
}
function renderSubsGrid(subs){
  const grid=document.getElementById('subs-grid');
  if(!subs.length){
    grid.innerHTML='<div class="subs-empty-v2"><div class="subs-empty-v2-icon"><i class="ti ti-folders"></i></div><div class="subs-empty-v2-title">No groups yet</div><div class="subs-empty-v2-sub">Create a group to organise your configs</div></div>';
    return;
  }
  grid.innerHTML=subs.map(s=>`
    <div class="sub-card">
      <div class="sub-card-top">
        <div class="sub-card-head-v2">
          <div class="sub-card-icon"><i class="ti ti-folder"></i></div>
          <div class="sub-card-titles">
            <div class="sub-card-name-v2">${esc(s.name)}</div>
            ${s.desc?`<div class="sub-card-desc-v2">${esc(s.desc)}</div>`:'<div class="sub-card-desc-v2" style="opacity:.5">No description</div>'}
          </div>
          <div class="sub-card-lock-badge ${s.has_password?'locked':'open'}" title="${s.has_password?'Password':'Public'}">
            <i class="ti ${s.has_password?'ti-lock':'ti-lock-open'}"></i>
          </div>
        </div>
        <div class="sub-card-stats">
          <div class="sub-card-stat"><div class="sub-card-stat-val">${toFa(s.links_count)}</div><div class="sub-card-stat-label">config</div></div>
          <div class="sub-card-stat"><div class="sub-card-stat-val" style="color:var(--green-t)">${toFa(s.active_count)}</div><div class="sub-card-stat-label">Active</div></div>
          <div class="sub-card-stat"><div class="sub-card-stat-val" style="font-size:12px">${esc(s.total_used_fmt)}</div><div class="sub-card-stat-label">Usage</div></div>
        </div>
      </div>
      <div class="sub-card-url-row">
        <span class="sub-card-url-text">${esc(s.public_url)}</span>
        <button class="sub-card-url-copy" onclick="navigator.clipboard.writeText('${esc(s.public_url)}').then(()=>toast('Public link copied','ok'))" title="Copy"><i class="ti ti-copy"></i></button>
        <button class="sub-card-url-copy" onclick="window.open('${esc(s.public_url)}','_blank')" title="Open"><i class="ti ti-external-link"></i></button>
      </div>
      <div class="sub-card-bottom">
        <button class="btn btn-sm btn-g" onclick="openSubLinks('${esc(s.sub_id)}','${esc(s.name)}')"><i class="ti ti-link-plus"></i> Configs</button>
        <button class="btn btn-sm btn-o" onclick="navigator.clipboard.writeText('${esc(s.sub_url)}').then(()=>toast('Subscription link copied','ok'))"><i class="ti ti-rss"></i> Sub</button>
        <button class="btn btn-sm btn-g btn-icon" onclick="showQR('${esc(s.sub_url)}')" title="QR"><i class="ti ti-qrcode"></i></button>
        <button class="btn btn-sm btn-d btn-icon" onclick="deleteSub('${esc(s.sub_id)}')" title="Delete"><i class="ti ti-trash"></i></button>
      </div>
    </div>
  `).join('');
}
function filterSubs(q){
  q=q.trim().toLowerCase();
  if(!q){renderSubsGrid(allSubsRaw);return}
  renderSubsGrid(allSubsRaw.filter(s=>s.name.toLowerCase().includes(q)||(s.desc||'').toLowerCase().includes(q)));
}
async function createSub(){
  const name=document.getElementById('ns-name').value.trim()||'New group';
  const desc=document.getElementById('ns-desc').value.trim();
  const pw=document.getElementById('ns-pw').value;
  try{
    const r=await authF('/api/subs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,desc,password:pw})});
    if(!r.ok)throw new Error('failed');
    ['ns-name','ns-desc','ns-pw'].forEach(id=>document.getElementById(id).value='');
    closeModal('modal-create-sub');
    toast('Group created ✓','ok');loadSubs();
  }catch(e){toast('Could not create group','err')}
}
async function deleteSub(sub_id){
  if(!confirm('Delete this group? The configs will be kept.'))return;
  try{const r=await authF('/api/subs/'+sub_id,{method:'DELETE'});if(!r.ok)throw new Error();toast('Group deleted ✓','ok');loadSubs();loadLinks();}catch(e){toast('Error','err')}
}
let lmodalLinks=[],lmodalInSub=new Set();
async function openSubLinks(sub_id,name){
  currentSubId=sub_id;
  document.getElementById('modal-sub-name').textContent=name;
  document.getElementById('modal-links-body').innerHTML='<div class="aspin-box"><span class="aspin aspin-lg"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></span> Loading configs…</div>';
  document.getElementById('lmodal-search-inp').value='';
  openModal('modal-links');
  try{
    const [lr,sr]=await Promise.all([authF('/api/links'),authF('/api/subs')]);
    const {links=[]}=await lr.json();
    const {subs=[]}=await sr.json();
    const thisSub=subs.find(s=>s.sub_id===sub_id);
    lmodalInSub=new Set(thisSub?.link_ids||[]);
    lmodalLinks=links;
    renderLmodalList(links);
  }catch(e){toast('Could not load','err')}
}
function renderLmodalList(links){
  const body=document.getElementById('modal-links-body');
  if(!links.length){body.innerHTML='<div class="empty" style="padding:30px"><i class="ti ti-link-off"></i><p>No configs yet</p></div>';updateLmodalCount();return}
  body.innerHTML=links.map(l=>{
    const checked=lmodalInSub.has(l.uuid);
    const on=l.active&&!l.expired;
    return `<div class="lrow-v2 ${checked?'checked':''}" data-uuid="${l.uuid}" data-name="${esc(l.label).toLowerCase()}" onclick="toggleLrow('${l.uuid}',this)">
      <div class="lrow-v2-check"><i class="ti ti-check"></i></div>
      <div class="lrow-v2-avatar"><i class="ti ti-key"></i></div>
      <div class="lrow-v2-info">
        <div class="lrow-v2-name">${esc(l.label)}</div>
        <div class="lrow-v2-meta"><i class="ti ti-database" style="font-size:10px"></i> ${fmtB(l.used_bytes)}</div>
      </div>
      <span class="lrow-v2-status ${on?'on':'off'}">${on?'Active':'Inactive'}</span>
    </div>`;
  }).join('');
  updateLmodalCount();
}
function toggleLrow(uuid,el){
  if(lmodalInSub.has(uuid)){lmodalInSub.delete(uuid);el.classList.remove('checked')}
  else{lmodalInSub.add(uuid);el.classList.add('checked')}
  updateLmodalCount();
}
function lmodalSelectAll(state){
  lmodalLinks.forEach(l=>{if(state)lmodalInSub.add(l.uuid);else lmodalInSub.delete(l.uuid)});
  renderLmodalList(lmodalLinks);
}
function updateLmodalCount(){
  const el=document.getElementById('lmodal-count');
  if(el)el.textContent=toFa(lmodalInSub.size)+' selected';
}
function filterLmodal(q){
  q=q.trim().toLowerCase();
  document.querySelectorAll('#modal-links-body .lrow-v2').forEach(row=>{
    row.style.display = !q || row.dataset.name.includes(q) ? '' : 'none';
  });
}
async function saveSubLinks(){
  if(!currentSubId)return;
  const link_ids=[...lmodalInSub];
  try{
    const r=await authF('/api/subs/'+currentSubId,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({link_ids})});
    if(!r.ok)throw new Error();
    await Promise.all(lmodalLinks.map(l=>
      authF('/api/links/'+l.uuid,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({sub_id:lmodalInSub.has(l.uuid)?currentSubId:null})})
    ));
    closeModal('modal-links');
    toast('Group configs saved ✓','ok');
    loadSubs();loadLinks();
  }catch(e){toast('Could not save','err')}
}
async function loadSubsPage(){
  document.getElementById('sub-all-url').textContent=location.protocol+'//'+location.host+'/sub-all';
  try{
    const r=await authF('/api/subs'),d=await r.json();
    const subs=d.subs||[];
    const el=document.getElementById('sub-groups-list');
    if(!subs.length){el.innerHTML='<div class="empty"><i class="ti ti-rss-off"></i><p>You have no groups yet</p></div>';return}
    el.innerHTML=subs.map(s=>`
      <div style="padding:13px 15px;background:var(--accent-d);border:1px solid var(--card-b);border-radius:10px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div>
          <div style="font-weight:700;font-size:13px;margin-bottom:3px">${esc(s.name)}</div>
          <div style="font-family:ui-monospace,monospace;font-size:10px;color:#D8705A">${esc(s.sub_url)}</div>
          <div style="font-size:10px;color:var(--t3);margin-top:3px">${toFa(s.links_count)} config · ${esc(s.total_used_fmt)} Usage ${s.has_password?'· 🔒 Password':''}</div>
        </div>
        <div style="display:flex;gap:5px;flex-wrap:wrap">
          <button class="btn btn-sm btn-pur" onclick="navigator.clipboard.writeText('${esc(s.sub_url)}').then(()=>toast('Copied','ok'))"><i class="ti ti-copy"></i> Sub</button>
          <button class="btn btn-sm btn-pur" onclick="navigator.clipboard.writeText('${esc(s.public_url)}').then(()=>toast('Copied','ok'))"><i class="ti ti-globe"></i> Public</button>
          <button class="btn btn-sm btn-g" onclick="showQR('${esc(s.sub_url)}')"><i class="ti ti-qrcode"></i></button>
        </div>
      </div>
    `).join('');
  }catch(e){}
}
function cpSubAll(){navigator.clipboard.writeText(location.protocol+'//'+location.host+'/sub-all').then(()=>toast('Copied ✓','ok'))}
function parseBytesFmt(s){
  if(!s)return 0;
  const m=String(s).match(/([\d.]+)\s*([A-Za-z]+)/);
  if(!m)return 0;
  const n=parseFloat(m[1]),u=m[2].toUpperCase();
  const mult={B:1,KB:1024,MB:1024**2,GB:1024**3,TB:1024**4};
  return n*(mult[u]||1);
}
async function loadConns(){
  try{
    const r=await authF('/api/connections'),d=await r.json();
    const grid=document.getElementById('conns-grid'),ce=document.getElementById('conns-empty');
    document.getElementById('conns-live').innerHTML='<span class="dot dg pulse"></span> '+d.count+' connection';
    document.getElementById('ch-count').textContent=toFa(d.count);
    const conns=d.connections||[];
    if(!d.count){
      grid.innerHTML='';ce.style.display='block';
      document.getElementById('ch-traffic').textContent='—';
      document.getElementById('ch-avgdur').textContent='—';
      document.getElementById('ch-uniq').textContent='—';
      return;
    }
    ce.style.display='none';
    const totalBytes=conns.reduce((s,c)=>s+parseBytesFmt(c.bytes_fmt),0);
    document.getElementById('ch-traffic').textContent=fmtB(totalBytes);
    const uniqIps=new Set(conns.map(c=>c.ip)).size;
    document.getElementById('ch-uniq').textContent=toFa(uniqIps);
    const durs=conns.map(c=>c.connected_at?Math.max(0,Math.floor((Date.now()-new Date(c.connected_at).getTime())/1000)):0);
    const avgSec=durs.length?Math.floor(durs.reduce((a,b)=>a+b,0)/durs.length):0;
    document.getElementById('ch-avgdur').textContent=avgSec<60?avgSec+'s':avgSec<3600?Math.floor(avgSec/60)+'m':Math.floor(avgSec/3600)+'h';
    const maxDur=Math.max(...durs,1);
    grid.innerHTML=conns.map(c=>{
      const secs=c.connected_at?Math.max(0,Math.floor((Date.now()-new Date(c.connected_at).getTime())/1000)):0;
      const dur=secs<60?secs+' sec':secs<3600?Math.floor(secs/60)+' min':Math.floor(secs/3600)+' h';
      const durPct=Math.min(100,Math.round((secs/maxDur)*100));
      const protoVal='vless-ws';
      return `<div class="conn-card-v2">
        <div class="conn-card-v2-glow"></div>
        <div class="conn-card-v2-top">
          <div class="conn-avatar"><i class="ti ti-device-desktop"></i></div>
          <div class="conn-card-v2-id">
            <div class="conn-ip-v2">${esc(c.ip)}
              <button class="conn-ip-copy" onclick="navigator.clipboard.writeText('${esc(c.ip)}').then(()=>toast('IP Copied','ok'))" title="Copy IP"><i class="ti ti-copy"></i></button>
            </div>
            <div class="conn-label-v2">${esc(c.label)}</div>
          </div>
          <span class="conn-status-pill"><span class="dot dg pulse"></span> live</span>
        </div>
        <div class="conn-card-v2-divider"></div>
        <div class="conn-card-v2-body">
          <div class="conn-proto-row">${protoBadge(protoVal)}</div>
          <div class="conn-stat-row">
            <div class="conn-stat-box">
              <div class="conn-stat-icon"><i class="ti ti-transfer"></i></div>
              <div>
                <div class="conn-stat-text-label">Traffic</div>
                <div class="conn-stat-text-val">${esc(c.bytes_fmt)}</div>
              </div>
            </div>
            <div class="conn-stat-box">
              <div class="conn-stat-icon time"><i class="ti ti-clock"></i></div>
              <div>
                <div class="conn-stat-text-label">Session length</div>
                <div class="conn-stat-text-val">${dur}</div>
              </div>
            </div>
          </div>
          <div class="conn-duration-track"><div class="conn-duration-fill" style="width:${durPct}%"></div></div>
        </div>
      </div>`;
    }).join('');
  }catch(e){console.error(e)}
}
async function loadErrs(){try{const r=await authF('/stats'),d=await r.json();renderErrs(d.recent_errors||[]);}catch(e){}}
async function fetchDefaultVless(){
  try{const r=await authF('/api/links'),d=await r.json();const links=d.links||[];const def=links.find(l=>l.limit_bytes===0&&l.active&&!l.expired)||links.find(l=>l.active&&!l.expired)||links[0];document.getElementById('vless-main').textContent=def?def.vless_link:'No configs yet';}catch(e){}
}
function cpText(id){navigator.clipboard.writeText(document.getElementById(id).textContent).then(()=>toast('Copied ✓','ok'))}
function qrFor(id){showQR(document.getElementById(id).textContent)}
function refreshAll(){fetchStats();fetchDefaultVless();loadLinks();if(document.getElementById('pg-subgroups').classList.contains('on'))loadSubs();if(document.getElementById('pg-subscriptions').classList.contains('on'))loadSubsPage();if(document.getElementById('pg-connections').classList.contains('on'))loadConns();if(document.getElementById('pg-logs').classList.contains('on'))loadActivity();toast('Refreshed','ok')}
async function changePw(){
  const cur=document.getElementById('cp-cur').value,nw=document.getElementById('cp-new').value,cf=document.getElementById('cp-cf').value;
  if(!cur||!nw||!cf){toast('Please fill in every field','err');return}
  if(nw.length<4){toast('At least 4 characters','err');return}
  if(nw!==cf){toast('Passwords do not match','err');return}
  try{
    const r=await authF('/api/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:cur,new_password:nw})});
    const d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.detail||'Error');
    toast('Password updated ✓','ok');
    ['cp-cur','cp-new','cp-cf'].forEach(id=>document.getElementById(id).value='');
  }catch(e){toast('✗ '+e.message,'err')}
}
function togglePwField(id,btn){
  const inp=document.getElementById(id);
  const icon=btn.querySelector('i');
  const toText=inp.type==='password';
  inp.type=toText?'text':'password';
  icon.className='ti '+(toText?'ti-eye-off':'ti-eye');
}
function checkPwStrength(val){
  const segs=document.querySelectorAll('#pw-strength-bar .pw-strength-seg');
  const label=document.getElementById('pw-strength-label');
  const reqLen=document.getElementById('req-len'),reqNum=document.getElementById('req-num'),reqCase=document.getElementById('req-case');
  const hasLen=val.length>=4,hasNum=/\d/.test(val),hasCase=/[a-z]/.test(val)&&/[A-Z]/.test(val),hasLong=val.length>=8;
  reqLen.classList.toggle('met',hasLen);
  reqNum.classList.toggle('met',hasNum);
  reqCase.classList.toggle('met',hasCase);
  let score=0;if(hasLen)score++;if(hasNum)score++;if(hasCase)score++;if(hasLong)score++;
  const colors=['#B33A22','#C08A2E','#189BAD','#12A08B'],labels=['Very weak','Weak','Medium','Strong'];
  segs.forEach((s,i)=>{s.style.background=i<score?colors[Math.max(0,score-1)]:'rgba(120,124,125,.2)'});
  if(val.length===0){label.innerHTML='<i class="ti ti-shield"></i> Password strength';return}
  label.innerHTML=`<i class="ti ti-shield-check" style="color:${colors[Math.max(0,score-1)]}"></i> ${labels[Math.max(0,score-1)]}`;
}
function makeGradient(ctx,color1,color2){
  const g=ctx.createLinearGradient(0,0,0,260);
  g.addColorStop(0,color1);g.addColorStop(1,color2);
  return g;
}
function initCharts(){
  const c1=document.getElementById('ch1').getContext('2d');
  const grad1=makeGradient(c1,'rgba(24,155,173,.38)','rgba(24,155,173,0)');
  const opts={
    responsive:true,maintainAspectRatio:false,
    interaction:{mode:'index',intersect:false},
    plugins:{
      legend:{display:false},
      tooltip:{
        backgroundColor:'rgba(23,28,29,.96)',borderColor:'rgba(24,155,173,.3)',borderWidth:1,
        titleColor:'#F2F3F3',bodyColor:'#BFBFBF',padding:11,cornerRadius:10,displayColors:false,
        titleFont:{family:'Vazirmatn',size:11,weight:'700'},bodyFont:{family:'Vazirmatn',size:11},
        callbacks:{label:v=>`${v.parsed.y.toFixed(2)} MB`}
      }
    },
    scales:{
      x:{grid:{display:false},border:{display:false},ticks:{color:'#8C9192',font:{size:9,family:'Vazirmatn'}}},
      y:{grid:{color:'rgba(24,155,173,.06)'},border:{display:false},ticks:{color:'#8C9192',font:{size:9,family:'Vazirmatn'},callback:v=>v+' MB'}}
    },
    elements:{line:{capBezierPoints:true}}
  };
  const ds1={label:'MB',data:[],borderColor:'#189BAD',backgroundColor:grad1,fill:true,tension:.42,pointRadius:0,pointHoverRadius:6,pointHoverBackgroundColor:'#189BAD',pointHoverBorderColor:'#fff',pointHoverBorderWidth:2,borderWidth:2.5};
  ch1=new Chart(document.getElementById('ch1'),{type:'line',data:{labels:[],datasets:[ds1]},options:opts});

  function makeGradientV2(ctx,c1,c2,c3){
    const g=ctx.createLinearGradient(0,0,0,320);
    g.addColorStop(0,c1);g.addColorStop(.6,c2);g.addColorStop(1,c3);
    return g;
  }
  const c3ctx=document.getElementById('ch3').getContext('2d');
  const gradFill3=makeGradientV2(c3ctx,'rgba(24,155,173,.45)','rgba(24,155,173,.08)','rgba(24,155,173,0)');
  ch3=new Chart(document.getElementById('ch3'),{
    type:'line',
    data:{labels:[],datasets:[
      {label:'Usage',data:[],borderColor:'#189BAD',backgroundColor:gradFill3,fill:true,tension:.45,pointRadius:0,pointHoverRadius:7,pointHoverBackgroundColor:'#fff',pointHoverBorderColor:'#189BAD',pointHoverBorderWidth:3,borderWidth:3,order:2},
      {label:'Average',data:[],borderColor:'#C08A2E',borderDash:[6,5],borderWidth:1.6,pointRadius:0,fill:false,tension:0,order:1}
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{display:false},
        tooltip:{
          backgroundColor:'rgba(23,28,29,.97)',borderColor:'rgba(24,155,173,.35)',borderWidth:1,
          titleColor:'#F2F3F3',bodyColor:'#A9CBD1',padding:13,cornerRadius:12,displayColors:true,boxPadding:4,
          titleFont:{family:'Vazirmatn',size:11.5,weight:'700'},bodyFont:{family:'Vazirmatn',size:11},
          callbacks:{label:v=>` ${v.dataset.label}: ${v.parsed.y.toFixed(2)} MB`}
        }
      },
      scales:{
        x:{grid:{display:false},border:{display:false},ticks:{color:'#8C9192',font:{size:9.5,family:'Vazirmatn'},maxRotation:0}},
        y:{grid:{color:'rgba(24,155,173,.05)'},border:{display:false},ticks:{color:'#8C9192',font:{size:9.5,family:'Vazirmatn'},callback:v=>v+' MB'}}
      }
    }
  });

  ch2=new Chart(document.getElementById('ch2'),{
    type:'doughnut',
    data:{labels:['VLESS/WS Turbo','HTTP Proxy'],datasets:[{
      data:[90,10],
      backgroundColor:['#189BAD','#A8351C'],
      borderColor:getComputedStyle(document.documentElement).getPropertyValue('--card')||'#171C1D',
      borderWidth:4,hoverOffset:10,borderRadius:6,spacing:3
    }]},
    options:{
      responsive:true,maintainAspectRatio:false,cutout:'72%',
      plugins:{
        legend:{position:'bottom',labels:{color:'var(--t2)',font:{size:10,family:'Vazirmatn'},padding:12,usePointStyle:true,pointStyle:'circle'}},
        tooltip:{backgroundColor:'rgba(23,28,29,.96)',borderColor:'rgba(24,155,173,.3)',borderWidth:1,padding:10,cornerRadius:10,bodyFont:{family:'Vazirmatn'},titleFont:{family:'Vazirmatn'}}
      }
    }
  });
}
let ws;
function wsLog(c,m){const l=document.getElementById('ws-log'),p=document.createElement('p');const colors={ok:'#3EC3AE',err:'#E08167',info:'#BFBFBF',sent:'#E4BE74'};p.style.color=colors[c]||'#fff';p.textContent='['+new Date().toLocaleTimeString('en-US')+'] '+m;l.appendChild(p);l.scrollTop=l.scrollHeight}
function wsConn(){const u=document.getElementById('ws-uuid').value.trim();if(!u){toast('Enter a UUID','err');return}const url=(location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws/'+u;wsLog('info','Connecting: '+url);ws=new WebSocket(url);ws.onopen=()=>wsLog('ok','✓ Connected — UUID valid');ws.onerror=()=>wsLog('err','✗ Failed — UUID invalid or disabled');ws.onmessage=m=>wsLog('info','Received '+(m.data.size||m.data.length)+' byte');ws.onclose=e=>wsLog('err','Closed ('+e.code+')'+(e.code===1008?' — access denied':''))}
function wsSend(){const m=document.getElementById('ws-msg').value;if(!m||!ws||ws.readyState!==1)return;ws.send(m);wsLog('sent','Sent: '+m);document.getElementById('ws-msg').value=''}
function wsDisc(){if(ws)ws.close()}
document.addEventListener('DOMContentLoaded',async()=>{
  await checkAuth();
  initCharts();
  document.getElementById('set-host').textContent=location.host;
  document.getElementById('sub-all-url')&&(document.getElementById('sub-all-url').textContent=location.protocol+'//'+location.host+'/sub-all');
  fetchStats();fetchDefaultVless();loadEndpointChoices();loadProxyCatalog();loadLinks();loadSubs();
  setInterval(fetchStats,4000);
  setInterval(()=>{
    if(document.getElementById('pg-links').classList.contains('on'))loadLinks();
    if(document.getElementById('pg-subgroups').classList.contains('on'))loadSubs();
    if(document.getElementById('pg-subscriptions').classList.contains('on'))loadSubsPage();
    if(document.getElementById('pg-connections').classList.contains('on'))loadConns();
    if(document.getElementById('pg-logs').classList.contains('on'))loadActivity();
  },5000);
});
</script>
</body></html>"""


_PUBLIC_TPL = r"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#f5f5f7">
<title>Subscription</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{
  --font:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Inter','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace;
  --bg:#F5F5F7;--bg-tint:#EDEDF0;--elev:#FFFFFF;--elev-2:#FBFBFD;
  --sep:rgba(0,0,0,.08);--sep-strong:rgba(0,0,0,.14);
  --t1:#1D1D1F;--t2:#6E6E73;--t3:#8E8E93;
  --accent:#0D6A78;--accent-hi:#0F8496;--accent-soft:rgba(13,106,120,.10);--accent-line:rgba(13,106,120,.22);
  --ok:#0D6A78;--warn:#A5701F;--warn-soft:rgba(165,112,31,.12);
  --danger:#791B0D;--danger-soft:rgba(121,27,13,.10);
  --grey:#BFBFBF;
  --r-xl:26px;--r-lg:20px;--r-md:14px;--r-sm:10px;--pill:980px;
  --sh-1:0 1px 2px rgba(0,0,0,.04),0 6px 20px rgba(0,0,0,.05);
  --sh-2:0 2px 6px rgba(0,0,0,.06),0 24px 60px rgba(0,0,0,.12);
  --header-bg:rgba(245,245,247,.72);
}
[data-theme="dark"]{
  --bg:#000000;--bg-tint:#0A0A0C;--elev:#1C1C1E;--elev-2:#232326;
  --sep:rgba(255,255,255,.12);--sep-strong:rgba(255,255,255,.2);
  --t1:#F5F5F7;--t2:#A1A1A6;--t3:#8E8E93;
  --accent:#3FB6C4;--accent-hi:#5FCBD7;--accent-soft:rgba(63,182,196,.14);--accent-line:rgba(63,182,196,.28);
  --ok:#3FB6C4;--warn:#D8A24E;--warn-soft:rgba(216,162,78,.16);
  --danger:#E08167;--danger-soft:rgba(224,129,103,.14);
  --sh-1:0 1px 2px rgba(0,0,0,.5);
  --sh-2:0 24px 60px rgba(0,0,0,.6);
  --header-bg:rgba(10,10,12,.72);
}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--font);background:var(--bg);color:var(--t1);font-size:17px;line-height:1.5;
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;letter-spacing:-.01em;
  transition:background .4s ease,color .4s ease;min-height:100vh}
::selection{background:var(--accent-soft)}

/* ---------- app bar ---------- */
.appbar{position:sticky;top:0;z-index:50;background:var(--header-bg);-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--sep)}
.appbar-in{max-width:820px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.mark{display:flex;align-items:center;gap:11px;min-width:0}
.mark-glyph{width:32px;height:32px;border-radius:10px;flex-shrink:0;display:grid;place-items:center;color:#fff;font-size:17px;
  background:linear-gradient(150deg,#0F8496,#0D6A78 55%,#791B0D);box-shadow:0 3px 10px rgba(13,106,120,.32)}
.mark-text{min-width:0}
.mark-title{font-size:15px;font-weight:600;letter-spacing:-.01em;line-height:1.25}
.mark-sub{font-size:12px;color:var(--t3);line-height:1.3}
.icon-btn{width:34px;height:34px;border-radius:50%;border:1px solid var(--sep);background:var(--elev);color:var(--t2);
  display:grid;place-items:center;font-size:16px;cursor:pointer;transition:transform .18s ease,background .18s ease,color .18s ease}
.icon-btn:hover{color:var(--t1);background:var(--elev-2)}
.icon-btn:active{transform:scale(.94)}

.wrap{max-width:820px;margin:0 auto;padding:28px 20px 72px}

/* ---------- iCloud style activity spinner ---------- */
.spinner{position:relative;width:20px;height:20px;color:var(--t3);flex-shrink:0}
.spinner b{position:absolute;top:0;left:50%;width:2px;height:5.5px;margin-left:-1px;border-radius:2px;
  background:currentColor;transform-origin:1px 10px;animation:sp-fade 1s linear infinite;opacity:.12}
.spinner b:nth-child(1){transform:rotate(0deg);animation-delay:-.917s}
.spinner b:nth-child(2){transform:rotate(30deg);animation-delay:-.833s}
.spinner b:nth-child(3){transform:rotate(60deg);animation-delay:-.75s}
.spinner b:nth-child(4){transform:rotate(90deg);animation-delay:-.667s}
.spinner b:nth-child(5){transform:rotate(120deg);animation-delay:-.583s}
.spinner b:nth-child(6){transform:rotate(150deg);animation-delay:-.5s}
.spinner b:nth-child(7){transform:rotate(180deg);animation-delay:-.417s}
.spinner b:nth-child(8){transform:rotate(210deg);animation-delay:-.333s}
.spinner b:nth-child(9){transform:rotate(240deg);animation-delay:-.25s}
.spinner b:nth-child(10){transform:rotate(270deg);animation-delay:-.167s}
.spinner b:nth-child(11){transform:rotate(300deg);animation-delay:-.083s}
.spinner b:nth-child(12){transform:rotate(330deg);animation-delay:0s}
@keyframes sp-fade{0%{opacity:1}100%{opacity:.12}}
.spinner-lg{width:32px;height:32px}
.spinner-lg b{width:3px;height:9px;margin-left:-1.5px;transform-origin:1.5px 16px}
.spinner-sm{width:16px;height:16px;color:currentColor}
.spinner-sm b{height:4.5px;transform-origin:1px 8px}
.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;padding:96px 20px;text-align:center}
.loading p{font-size:15px;color:var(--t2)}

/* ---------- buttons ---------- */
.btn{font-family:inherit;font-size:14px;font-weight:600;letter-spacing:-.01em;border:1px solid transparent;
  border-radius:var(--pill);padding:9px 18px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;
  transition:transform .16s ease,background .18s ease,color .18s ease,border-color .18s ease;white-space:nowrap}
.btn i{font-size:16px}
.btn:active{transform:scale(.97)}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-hi)}
[data-theme="dark"] .btn-primary{color:#04191C}
.btn-quiet{background:var(--accent-soft);color:var(--accent)}
.btn-quiet:hover{background:var(--accent-line)}
.btn-plain{background:transparent;color:var(--t2);border-color:var(--sep)}
.btn-plain:hover{color:var(--t1);border-color:var(--sep-strong)}
.btn-wide{width:100%;padding:13px 18px;font-size:16px}
.btn[disabled]{opacity:.55;cursor:default;transform:none}

/* ---------- hero ---------- */
.hero{background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-xl);padding:30px 28px 24px;box-shadow:var(--sh-1);margin-bottom:14px}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);display:flex;align-items:center;gap:6px;margin-bottom:10px}
.hero-title{font-size:34px;font-weight:700;letter-spacing:-.03em;line-height:1.12;margin-bottom:8px;word-break:break-word}
.hero-desc{font-size:16px;color:var(--t2);line-height:1.55;margin-bottom:18px;max-width:56ch}
.url-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--bg-tint);border:1px solid var(--sep);border-radius:var(--r-md);padding:12px 14px}
[data-theme="dark"] .url-row{background:var(--elev-2)}
.url-text{flex:1;min-width:180px;font-family:var(--mono);font-size:12.5px;color:var(--t2);word-break:break-all;line-height:1.6}
.url-actions{display:flex;gap:8px;flex-shrink:0}
.hero-meta{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--t3);margin-top:14px}

/* ---------- stats ---------- */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px}
.stat{background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-lg);padding:18px 20px;box-shadow:var(--sh-1)}
.stat-label{font-size:13px;font-weight:500;color:var(--t2);margin-bottom:8px}
.stat-val{font-size:28px;font-weight:700;letter-spacing:-.03em;line-height:1.1}
.stat-sub{font-size:12.5px;color:var(--t3);margin-top:6px;display:flex;align-items:center;gap:6px}

/* ---------- copy all banner ---------- */
.banner{display:flex;align-items:center;gap:16px;background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-lg);
  padding:18px 20px;margin-bottom:30px;box-shadow:var(--sh-1);flex-wrap:wrap}
.banner-glyph{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-size:20px;background:var(--accent-soft);color:var(--accent);flex-shrink:0}
.banner-text{flex:1;min-width:170px}
.banner-title{font-size:16px;font-weight:600;letter-spacing:-.01em}
.banner-sub{font-size:13.5px;color:var(--t2);margin-top:2px}

/* ---------- section title ---------- */
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 4px 12px}
.sec-title{font-size:22px;font-weight:700;letter-spacing:-.02em}
.sec-count{font-size:13.5px;color:var(--t3)}

/* ---------- config cards ---------- */
.cfg-list{display:grid;gap:12px}
.cfg{background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-lg);padding:20px 22px;box-shadow:var(--sh-1);transition:box-shadow .2s ease,border-color .2s ease}
.cfg:hover{border-color:var(--sep-strong);box-shadow:var(--sh-2)}
.cfg.off{opacity:.72}
.cfg-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:16px}
.cfg-name{font-size:18px;font-weight:600;letter-spacing:-.02em;line-height:1.3;word-break:break-word}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.chip{font-size:11.5px;font-weight:600;letter-spacing:.01em;padding:3px 9px;border-radius:var(--pill);background:var(--bg-tint);color:var(--t2)}
[data-theme="dark"] .chip{background:var(--elev-2)}
.chip-proto{background:var(--accent-soft);color:var(--accent)}
.chip-live{background:var(--accent-soft);color:var(--accent);display:inline-flex;align-items:center;gap:5px}
.pill{font-size:12px;font-weight:600;padding:4px 11px;border-radius:var(--pill);display:inline-flex;align-items:center;gap:5px;white-space:nowrap;flex-shrink:0}
.pill-ok{background:var(--accent-soft);color:var(--accent)}
.pill-off{background:var(--danger-soft);color:var(--danger)}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block;animation:breathe 2s ease-in-out infinite}
@keyframes breathe{0%,100%{opacity:1}50%{opacity:.3}}
.meter{height:6px;border-radius:var(--pill);background:var(--bg-tint);overflow:hidden;margin-bottom:8px}
[data-theme="dark"] .meter{background:rgba(255,255,255,.1)}
.meter-fill{height:100%;border-radius:var(--pill);background:var(--accent);transition:width .6s cubic-bezier(.4,0,.2,1)}
.meter-txt{display:flex;justify-content:space-between;gap:10px;font-size:13px;color:var(--t2);margin-bottom:16px}
.disclose{width:100%;display:flex;align-items:center;justify-content:space-between;gap:10px;background:transparent;
  border:1px solid var(--sep);border-radius:var(--r-md);padding:11px 14px;cursor:pointer;font-family:inherit;
  font-size:14px;font-weight:500;color:var(--t2);transition:border-color .18s ease,color .18s ease,background .18s ease}
.disclose:hover{color:var(--t1);border-color:var(--sep-strong);background:var(--bg-tint)}
[data-theme="dark"] .disclose:hover{background:var(--elev-2)}
.disclose .dl{display:flex;align-items:center;gap:8px}
.disclose .ti-chevron-down{transition:transform .25s cubic-bezier(.4,0,.2,1);font-size:17px}
.disclose.open .ti-chevron-down{transform:rotate(180deg)}
.reveal{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s cubic-bezier(.4,0,.2,1)}
.reveal.open{grid-template-rows:1fr}
.reveal-in{overflow:hidden}
.code{display:block;margin-top:10px;background:var(--bg-tint);border:1px solid var(--sep);border-radius:var(--r-md);
  padding:13px 15px;font-family:var(--mono);font-size:12.5px;line-height:1.75;color:var(--t2);word-break:break-all;max-height:132px;overflow:auto}
[data-theme="dark"] .code{background:#0E0E10}
.cfg-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}

/* ---------- lock screen ---------- */
.lock-stage{display:flex;align-items:center;justify-content:center;min-height:62vh;padding:20px 0}
.lock{background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-xl);box-shadow:var(--sh-2);max-width:400px;width:100%;overflow:hidden;
  animation:sheet-in .45s cubic-bezier(.32,.72,0,1)}
.lock-top{padding:36px 32px 26px;text-align:center;border-bottom:1px solid var(--sep)}
.lock-glyph{width:60px;height:60px;border-radius:18px;margin:0 auto 18px;display:grid;place-items:center;font-size:27px;
  color:#fff;background:linear-gradient(150deg,#0F8496,#0D6A78 60%,#791B0D);box-shadow:0 8px 22px rgba(13,106,120,.3)}
.lock-title{font-size:24px;font-weight:700;letter-spacing:-.02em;line-height:1.2;margin-bottom:8px;word-break:break-word}
.lock-sub{font-size:15px;color:var(--t2);line-height:1.5}
.lock-body{padding:24px 32px 28px}
.lock-field{position:relative;margin-bottom:12px}
.lock-inp{width:100%;padding:14px 46px 14px 16px;border-radius:var(--r-md);border:1px solid var(--sep-strong);background:var(--bg-tint);
  color:var(--t1);font-family:inherit;font-size:16px;outline:none;transition:border-color .18s ease,box-shadow .18s ease,background .18s ease}
[data-theme="dark"] .lock-inp{background:#0E0E10}
.lock-inp::placeholder{color:var(--t3);letter-spacing:.16em}
.lock-inp:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft);background:var(--elev)}
.lock-eye{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--t3);cursor:pointer;
  font-size:18px;padding:8px;display:flex;border-radius:50%}
.lock-eye:hover{color:var(--t1)}
.lock-err{min-height:20px;font-size:13.5px;color:var(--danger);display:flex;align-items:center;gap:6px;margin-bottom:10px}
.lock-foot{padding:14px 32px;border-top:1px solid var(--sep);font-size:12.5px;color:var(--t3);display:flex;align-items:center;justify-content:center;gap:7px}

/* ---------- empty / error ---------- */
.state{text-align:center;padding:84px 24px;color:var(--t2)}
.state-glyph{width:56px;height:56px;border-radius:16px;margin:0 auto 16px;display:grid;place-items:center;font-size:26px;background:var(--bg-tint);color:var(--t3)}
[data-theme="dark"] .state-glyph{background:var(--elev-2)}
.state-title{font-size:19px;font-weight:600;color:var(--t1);letter-spacing:-.01em;margin-bottom:6px}
.state-sub{font-size:15px;color:var(--t2)}

/* ---------- toast ---------- */
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,24px) scale(.96);z-index:900;pointer-events:none;opacity:0;
  display:flex;align-items:center;gap:9px;padding:12px 20px;border-radius:var(--pill);font-size:14.5px;font-weight:500;
  background:rgba(28,28,30,.9);color:#fff;-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);box-shadow:var(--sh-2);
  transition:opacity .28s ease,transform .35s cubic-bezier(.32,.72,0,1);max-width:90vw}
[data-theme="dark"] .toast{background:rgba(240,240,245,.92);color:#111}
.toast.show{opacity:1;transform:translate(-50%,0) scale(1)}

/* ---------- QR sheet ---------- */
.qr-modal{position:fixed;inset:0;z-index:800;display:none;align-items:center;justify-content:center;padding:22px;
  background:rgba(0,0,0,.4);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}
.qr-modal.open{display:flex}
.qr-box{background:var(--elev);border:1px solid var(--sep);border-radius:var(--r-xl);padding:26px;max-width:340px;width:100%;
  text-align:center;box-shadow:var(--sh-2);animation:sheet-in .42s cubic-bezier(.32,.72,0,1)}
@keyframes sheet-in{from{opacity:0;transform:translateY(14px) scale(.96)}to{opacity:1;transform:none}}
.qr-title{font-size:17px;font-weight:600;letter-spacing:-.01em;margin-bottom:18px;word-break:break-word}
.qr-img{border-radius:var(--r-lg);overflow:hidden;margin-bottom:18px;background:#fff;padding:12px}
.qr-img img{width:100%;display:block}

.footer{display:flex;align-items:center;justify-content:center;gap:8px;padding-top:34px;font-size:13px;color:var(--t3);text-align:center}

@media(max-width:620px){
  body{font-size:16px}
  .wrap{padding:20px 16px 60px}
  .appbar-in{padding:11px 16px}
  .hero{padding:24px 20px 20px;border-radius:var(--r-lg)}
  .hero-title{font-size:27px}
  .hero-desc{font-size:15px}
  .stats{grid-template-columns:1fr 1fr;gap:10px}
  .stats .stat:nth-child(3){grid-column:1/-1}
  .stat-val{font-size:24px}
  .cfg{padding:18px}
  .sec-title{font-size:19px}
  .url-actions{width:100%}
  .url-actions .btn{flex:1}
}
@media(prefers-reduced-motion:reduce){
  *{animation-duration:.001ms !important;animation-iteration-count:1 !important;transition-duration:.001ms !important}
  .spinner b{animation:none;opacity:.45}
}
button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid var(--accent-line);outline-offset:2px}
*::-webkit-scrollbar{width:9px;height:9px}
*::-webkit-scrollbar-track{background:transparent}
*::-webkit-scrollbar-thumb{background:rgba(142,142,147,.35);border-radius:99px;border:2px solid transparent;background-clip:content-box}
</style>
</head>
<body>
<div class="toast" id="toast"></div>

<div class="qr-modal" id="qr-modal" onclick="this.classList.remove('open')">
  <div class="qr-box" onclick="event.stopPropagation()">
    <div class="qr-title" id="qr-label">QR Code</div>
    <div class="qr-img"><img id="qr-img" src="" alt="QR code"></div>
    <button class="btn btn-quiet btn-wide" onclick="document.getElementById('qr-modal').classList.remove('open')">Done</button>
  </div>
</div>

<header class="appbar">
  <div class="appbar-in">
    <div class="mark">
      <div class="mark-glyph"><i class="ti ti-shield-check"></i></div>
      <div class="mark-text">
        <div class="mark-title">Subscription</div>
        <div class="mark-sub">Your configurations</div>
      </div>
    </div>
    <button class="icon-btn" id="theme-toggle" onclick="toggleTheme()" title="Switch appearance" aria-label="Switch appearance">
      <i class="ti ti-moon" id="theme-icon"></i>
    </button>
  </div>
</header>

<main class="wrap">
  <div id="root">
    <div class="loading">
      <div class="spinner spinner-lg"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></div>
      <p>Loading your configurations…</p>
    </div>
  </div>
  <div class="footer"><i class="ti ti-lock"></i> This page was created just for you</div>
</main>

<script>
const UUID_KEY='__UUID_KEY__';
let savedPw='';

const SPINNER='<span class="spinner spinner-sm"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></span>';

let isDark=localStorage.getItem('sub-appearance')==='dark';
function applyTheme(dark){
  document.documentElement.setAttribute('data-theme',dark?'dark':'light');
  document.getElementById('theme-icon').className='ti '+(dark?'ti-sun':'ti-moon');
  const meta=document.querySelector('meta[name="theme-color"]');
  if(meta)meta.setAttribute('content',dark?'#000000':'#f5f5f7');
}
function toggleTheme(){isDark=!isDark;localStorage.setItem('sub-appearance',isDark?'dark':'light');applyTheme(isDark)}
applyTheme(isDark);

function toast(msg,type=''){
  const t=document.getElementById('toast');
  t.innerHTML=(type==='ok'?'<i class="ti ti-circle-check"></i>':type==='err'?'<i class="ti ti-alert-circle"></i>':'')+'<span></span>';
  t.querySelector('span').textContent=msg;
  t.className='toast show';
  clearTimeout(window._toastT);
  window._toastT=setTimeout(()=>t.classList.remove('show'),2400);
}
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fmtB(b){if(!b||b===0)return '0 B';if(b<1024)return b+' B';if(b<1024**2)return (b/1024).toFixed(1)+' KB';if(b<1024**3)return (b/1024**2).toFixed(2)+' MB';return (b/1024**3).toFixed(2)+' GB'}
function nowTime(){return new Date().toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})}
function protoChip(p){
  return '<span class="chip chip-proto">VLESS · WS Turbo</span>';
}
function copyText(text,msg){
  navigator.clipboard.writeText(text).then(()=>toast(msg,'ok')).catch(()=>toast('Copy failed','err'));
}

function showQR(label,link){
  document.getElementById('qr-label').textContent=label;
  document.getElementById('qr-img').src='https://api.qrserver.com/v1/create-qr-code/?size=260x260&data='+encodeURIComponent(link);
  document.getElementById('qr-modal').classList.add('open');
}

function toggleLink(i){
  const wrap=document.getElementById('vw-'+i);
  const btn=document.getElementById('vt-'+i);
  const open=wrap.classList.toggle('open');
  btn.classList.toggle('open',open);
  btn.querySelector('.dl span').textContent = open ? 'Hide configuration link' : 'Show configuration link';
}

async function loadData(pw=''){
  const url='/api/public/sub/'+UUID_KEY+(pw?'?pw='+encodeURIComponent(pw):'');
  const r=await fetch(url);
  return r.json();
}

function renderLock(name,errMsg=''){
  document.getElementById('root').innerHTML=`
    <div class="lock-stage">
      <div class="lock">
        <div class="lock-top">
          <div class="lock-glyph"><i class="ti ti-lock"></i></div>
          <div class="lock-title">${esc(name)}</div>
          <div class="lock-sub">This group is password protected. Enter the password to see its configurations.</div>
        </div>
        <div class="lock-body">
          <div class="lock-err" id="lock-err">${errMsg ? '<i class="ti ti-alert-circle"></i> '+esc(errMsg) : ''}</div>
          <div class="lock-field">
            <input class="lock-inp" type="password" id="lock-pw" placeholder="••••••••" autocomplete="current-password" autofocus>
            <button class="lock-eye" type="button" onclick="togglePwVis()" aria-label="Show password"><i class="ti ti-eye" id="lock-eye-icon"></i></button>
          </div>
          <button class="btn btn-primary btn-wide" id="lock-submit" onclick="submitLock()">Continue</button>
        </div>
        <div class="lock-foot"><i class="ti ti-shield-lock"></i> Your connection is encrypted</div>
      </div>
    </div>
  `;
  const inp=document.getElementById('lock-pw');
  inp.addEventListener('keydown',e=>{if(e.key==='Enter')submitLock()});
}

function togglePwVis(){
  const inp=document.getElementById('lock-pw');
  const icon=document.getElementById('lock-eye-icon');
  const toText = inp.type==='password';
  inp.type = toText ? 'text' : 'password';
  icon.className = 'ti '+(toText ? 'ti-eye-off' : 'ti-eye');
}

async function submitLock(){
  const pw=document.getElementById('lock-pw').value;
  const btn=document.getElementById('lock-submit');
  btn.disabled=true;btn.innerHTML=SPINNER+' Checking…';
  try{
    const data=await loadData(pw);
    if(data.locked){renderLock(data.name,'Incorrect password');return}
    savedPw=pw;
    renderContent(data);
  }catch(e){
    btn.disabled=false;btn.textContent='Continue';
    toast('Could not connect','err');
  }
}

function renderContent(d){
  const activeCount=d.links.filter(l=>l.active).length;
  const baseSubUrl = d.sub_url || (window.location.protocol + '//' + window.location.host + '/sub-group/' + UUID_KEY);
  const subUrl = baseSubUrl + (savedPw ? '?pw=' + encodeURIComponent(savedPw) : '');

  window._subUrl  = subUrl;
  window._subName = d.name;
  window._cfgLinks = d.links.map(l => ({
    vless : l.vless_link,
    sub   : l.sub_url + (savedPw ? '?pw=' + encodeURIComponent(savedPw) : ''),
    label : l.label,
  }));

  const cards = d.links.length ? d.links.map((l, i) => {
    const pct = l.limit_bytes === 0 ? 0 : Math.min(100, l.used_bytes / l.limit_bytes * 100);
    const col = pct > 90 ? 'var(--danger)' : pct > 70 ? 'var(--warn)' : 'var(--accent)';
    const lim = l.limit_bytes === 0 ? 'Unlimited' : fmtB(l.limit_bytes);
    return `
      <article class="cfg${l.active ? '' : ' off'}">
        <div class="cfg-head">
          <div>
            <div class="cfg-name">${esc(l.label)}</div>
            <div class="chips">
              ${protoChip(l.protocol)}
              ${l.connections > 0 ? `<span class="chip chip-live"><span class="dot"></span> ${l.connections} connected</span>` : ''}
            </div>
          </div>
          <span class="pill ${l.active ? 'pill-ok' : 'pill-off'}">${l.active ? '<i class="ti ti-circle-check"></i> Active' : '<i class="ti ti-circle-x"></i> Inactive'}</span>
        </div>
        <div class="meter"><div class="meter-fill" style="width:${pct}%;background:${col}"></div></div>
        <div class="meter-txt"><span>${esc(l.used_fmt)} used</span><span>${lim === 'Unlimited' ? 'Unlimited data' : 'of ' + lim}</span></div>
        <button class="disclose" id="vt-${i}" onclick="toggleLink(${i})">
          <span class="dl"><i class="ti ti-key"></i> <span>Show configuration link</span></span>
          <i class="ti ti-chevron-down"></i>
        </button>
        <div class="reveal" id="vw-${i}">
          <div class="reveal-in"><code class="code">${esc(l.vless_link)}</code></div>
        </div>
        <div class="cfg-actions">
          <button class="btn btn-primary" onclick="copyText(window._cfgLinks[${i}].vless,'Configuration link copied')">
            <i class="ti ti-copy"></i> Copy link
          </button>
          <button class="btn btn-quiet" onclick="showQR(window._cfgLinks[${i}].label, window._cfgLinks[${i}].vless)">
            <i class="ti ti-qrcode"></i> QR code
          </button>
        </div>
      </article>`;
  }).join('') : `
      <div class="state">
        <div class="state-glyph"><i class="ti ti-inbox"></i></div>
        <div class="state-title">No configurations yet</div>
        <div class="state-sub">Anything added to this group will show up here.</div>
      </div>`;

  document.getElementById('root').innerHTML=`
    <section class="hero">
      <div class="eyebrow"><i class="ti ti-folder"></i> Access group</div>
      <h1 class="hero-title">${esc(d.name)}</h1>
      ${d.desc ? `<p class="hero-desc">${esc(d.desc)}</p>` : ''}
      <div class="url-row">
        <span class="url-text">${esc(subUrl)}</span>
        <div class="url-actions">
          <button class="btn btn-primary" onclick="copyText(window._subUrl,'Subscription link copied')"><i class="ti ti-copy"></i> Copy</button>
          <button class="btn btn-quiet" onclick="showQR(window._subName + ' — full group', window._subUrl)"><i class="ti ti-qrcode"></i> QR</button>
        </div>
      </div>
      <div class="hero-meta"><i class="ti ti-clock"></i> Updated ${nowTime()} · refreshes automatically</div>
    </section>

    <div class="stats">
      <div class="stat">
        <div class="stat-label">Active configurations</div>
        <div class="stat-val">${activeCount}</div>
        <div class="stat-sub">of ${d.links.length} total</div>
      </div>
      <div class="stat">
        <div class="stat-label">Live connections</div>
        <div class="stat-val">${d.active_connections}</div>
        <div class="stat-sub" style="color:var(--accent)"><span class="dot"></span> Online now</div>
      </div>
      <div class="stat">
        <div class="stat-label">Data used</div>
        <div class="stat-val">${esc(d.total_used_fmt)}</div>
        <div class="stat-sub">across all configurations</div>
      </div>
    </div>

    <div class="banner">
      <div class="banner-glyph"><i class="ti ti-clipboard-copy"></i></div>
      <div class="banner-text">
        <div class="banner-title">Copy every configuration</div>
        <div class="banner-sub">Grab all active links at once and paste them into your app.</div>
      </div>
      <button class="btn btn-primary" onclick="copyAllConfigs()"><i class="ti ti-copy"></i> Copy all (${activeCount})</button>
    </div>

    <div class="sec-head">
      <div class="sec-title">Configurations</div>
      <div class="sec-count">${d.links.length} total</div>
    </div>
    <div class="cfg-list">${cards}</div>
  `;
  setTimeout(() => autoRefresh(), 30000);
}

function copyAllConfigs(){
  const links=window._cfgLinks||[];
  if(!links.length){toast('Nothing to copy','err');return}
  copyText(links.map(l=>l.vless).join('\n'), links.length+' configurations copied');
}

async function autoRefresh(){
  try{
    const data = await loadData(savedPw);
    if (!data.locked) renderContent(data);
  } catch(e) {}
}

async function init(){
  try{
    const data = await loadData();
    if (data.locked) { renderLock(data.name); return; }
    renderContent(data);
  } catch(e) {
    document.getElementById('root').innerHTML =
      '<div class="state"><div class="state-glyph" style="color:var(--danger)"><i class="ti ti-cloud-off"></i></div>' +
      '<div class="state-title">Something went wrong</div>' +
      '<div class="state-sub">We could not load this page. Please try again in a moment.</div></div>';
  }
}

init();
</script>
</body></html>"""


def get_public_page_html(uuid_key: str) -> str:
    """Public subscription page (sub group) - Apple inspired light/dark design."""
    return _PUBLIC_TPL.replace("__UUID_KEY__", uuid_key)
