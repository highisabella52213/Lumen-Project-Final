# WS + XHTTP Hyper v5

این نسخه هر دو مسیر WS و XHTTP را ارتقا می‌دهد. اعداد تست loopback هستند و تضمین سرعت اینترنت نیستند.

## XHTTP Hyper

### اصلاح سازگاری و پایداری

- `stream-one` اکنون مطابق Xray روی base path و بدون session-id کار می‌کند: `POST /configured/path/`.
- `stream-up` و `stream-one` از پاسخ full-duplex اختصاصی استفاده می‌کنند تا listener داخلی Starlette با `request.stream()` رقابت نکند و چانک‌های آپلود گم نشوند.
- هدر VLESS می‌تواند بین چند HTTP chunk یا چند packet-up POST شکسته شود.
- packet-up دارای reorder buffer قفل‌شده، retry idempotent و سقف تعداد/حجم است.
- دانلینک با `text/event-stream`، `X-Accel-Buffering: no` و `Cache-Control: no-store, no-transform` زودتر از CDN flush می‌شود.
- پاسخ packet-up فقط HTTP 200 خالی است و دیگر JSON اضافه تولید نمی‌کند.

### افزایش سرعت

- لینک‌های packet-up/auto دارای `scMaxEachPostBytes=4000000` و `scMinPostsIntervalMs=1` هستند. پیش‌فرض Xray حدود 1 MB و 30 ms است؛ این تغییر سقف مصنوعی آپلود packet-up را حذف می‌کند.
- XMUX روی `maxConcurrency=8-16` و `maxConnections=4-8` تنظیم شده؛ چند carrier واقعی حفظ می‌شود، بدون انفجار RAM/CPU پروفایل قبلی.
- `hKeepAlivePeriod=0`، عمر reusable برابر 1800-3600 ثانیه و reuse برابر 256-512 است.
- XHTTP همان Happy-Eyeballs و route cache مسیر WS را استفاده می‌کند؛ IPv6 و IPv4 هم‌زمان مسابقه می‌دهند و IPv4 delay اجباری ندارد.
- write window آپلینک از 8 تا 64 MiB تطبیق پیدا می‌کند و read chunk دانلینک تا 2 MiB است.
- VLESS response prefix جداگانه ارسال می‌شود تا اولین payload کپی نشود و first-byte زودتر برسد.
- stream-up هر 25 ثانیه روی پاسخ upload پدینگ بی‌ضرر می‌فرستد تا CDN اتصال طولانی را قطع نکند.

## WS Hyper

- مسیر zero-copy دانلود و framing مستقیم نسخه قبل حفظ شده است.
- آپلود تا 32 فریم یا 4 MiB را با `turbo_receive_nowait` در هر burst تخلیه می‌کند؛ await اضافه بین فریم‌های صف‌شده حذف شده است.
- queue محدود، adaptive write window، Early Data 4096 و dual-stack route memory حفظ شده‌اند.

## انتخاب پروفایل

1. **دانلود/آپلود پایدار و سازگاری زیاد:** WS با Mux عمومی خاموش.
2. **بهترین XHTTP روی TLS/H2 و CDN سازگار:** `xhttp-stream-up`.
3. **بیشترین سازگاری XHTTP:** `xhttp-auto` یا `xhttp-packet-up`. در Xray فعلی، auto روی TLS معمولی غالباً packet-up انتخاب می‌کند.
4. **کمترین RTT نظری:** `xhttp-stream-one`، فقط اگر CDN/reverse-proxy واقعاً full-duplex را عبور دهد.

XMUX داخلی XHTTP با Mux عمومی Xray یکی نیست. پروفایل XMUX تولیدشده را نگه دارید؛ برای WS همچنان Mux عمومی را برای دانلود خاموش بگذارید.

## نتایج مقایسه کنترل‌شده

- packet-up، 8×16 MiB: میانه **308.9 MiB/s** در هر جهت؛ نسخه قبل **215.9 MiB/s**.
- stream-up، 8×16 MiB: میانه **277.0 MiB/s** در هر جهت؛ نسخه قبل **246.5 MiB/s**.
- stream-one، 8×16 MiB: میانه **254.3 MiB/s**؛ نسخه قبل در exact-byte خراب بود و اکنون پاس می‌شود.
- WS، 16×8 MiB: میانه **307.6 MiB/s** در هر جهت.
- 60 تونل کوتاه XHTTP با payload شانزده KiB: حدود **750 session/s** در loopback.
- شش چرخه هر سه مد XHTTP: active=0، errors=0، FD برابر 8→8، task باقی‌مانده=0.
- هشت چرخه WS × 24 اتصال: active=0، errors=0، FD برابر 9→9، task باقی‌مانده=0.
- IPv6 واقعی، IPv4 fallback، startup، split header، packet reorder، duplicate retry و base-path رسمی stream-one همگی پاس شدند.

## استقرار

- پورت عمومی TLS: `443`
- پورت داخلی: `$PORT`، پیش‌فرض `8000`
- Uvicorn مستقیماً HTTP/2 ارائه نمی‌کند؛ CDN یا reverse proxy لایه H2/H3 را terminate می‌کند. پشتیبانی آن واسط از streaming روی نتیجه stream-up/one اثر مستقیم دارد.
