# WS Hyper — بازطراحی نهایی مسیر دانلود

## تغییر معماری

- ارتقا از `uvicorn 0.24 + websockets 12` به `uvicorn 0.52.4 + websockets 17` و Sans-I/O.
- افزوده شدن `turbo_ws_protocol.py`:
  - مسیر دانلود، فریم استاندارد WS را به صورت **header + payload جدا** روی transport می‌نویسد؛ دیگر BytesIO یک کپی کامل از هر payload چندمگابایتی نمی‌سازد.
  - رفت‌وبرگشت Starlette/ASGI برای تک‌تک فریم‌های binary حذف شده است.
  - صف ورودی 128/32: به جای pause/resume سوکت بعد از هر پیام، burst محدود و کنترل‌شده دریافت می‌شود.
  - تمام control frameها، masking ورودی و close-handshake همچنان توسط Sans-I/O رسمی پردازش می‌شوند.
- استخراج کم‌کپی از `StreamReader`: وقتی کل burst در یک فریم جا می‌شود، bytearray داخلی detach می‌شود.
- `TCP_NOTSENT_LOWAT=512KB` حذف شد؛ روی مسیرهای high-BDP می‌توانست سرعت را محدود کند.
- بافرهای 16MB، high-water تطبیقی تا 32MB، BBR با fallback به CUBIC، TCP Fast Open و Deferred Accept.
- DNS هم‌زمان deduplicate می‌شود و مسیر برنده 15 دقیقه در route cache می‌ماند.
- حسابداری حجم برای لینک نامحدود تا 8MB batch می‌شود؛ hot path هر فریم دیگر coroutine حسابداری نمی‌سازد.
- شمارنده‌ی `total_requests` اصلاح شد: اکنون اتصال VLESS را می‌شمارد، نه هر فریم WS را.
- باگ بررسی محدودیت سرعت اصلاح شد (`speed_limit_bytes`).
- Early Data از 2048 به **4096** افزایش یافت؛ برای اعمال آن لینک WS را دوباره import کنید.

## تست‌ها

- `python -m py_compile` برای تمام فایل‌ها: پاس.
- contract test پروتکل: queue high/low، resume/pause و حفظ object payload بدون full-copy: پاس.
- RFC 6455 واقعی روی TCP loopback، نه FakeWS:
  - هدر یک‌فریمی: پاس
  - هدر سه‌تکه: پاس
  - Early Data: پاس
  - 16 اتصال موازی × 8MiB با بررسی دقیق تمام بایت‌ها: پاس
  - connection leak: صفر
  - error: صفر
  - توان عبوری تست خالص پایتون: حدود 125MiB/s در هر جهت (عدد اینترنت واقعی نیست).

## نکته‌ی مهم

برای فعال شدن پروتکل Hyper باید سرویس با `python main.py` اجرا شود؛ `Procfile` اضافه شده است. اجرای مستقیم `uvicorn main:app` از تنظیمات سفارشی data-plane عبور می‌کند.

WS استاندارد نمی‌تواند یک جریان TCP واحد را بدون پشتیبانی کلاینت روی چند WS تقسیم کند. اما دانلود منیجر/مرورگری که چند Range connection باز کند، هر اتصال را روی WS جدا می‌فرستد و سرور همه را موازی پردازش می‌کند.
