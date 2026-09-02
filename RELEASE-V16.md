# Lumen · WS-only v16

- بازسازی مسیر خروجی HTTP/HTTPS/SOCKS5 با handshakeهای محدود و Fail-open قطعی به Direct.
- رفع `ping=-1` ناشی از پروکسی‌هایی که CONNECT را قبول می‌کنند ولی هیچ داده‌ای عبور نمی‌دهند، با first-byte watchdog.
- جمع‌کردن ClientHello تکه‌تکه‌شده قبل از اتصال پروکسی و جلوگیری از معطل‌شدن مسیرهای غیرقابل‌اعتبارسنجی.
- پشتیبانی از هر دو نوع رایج HTTPS proxy: HTTP CONNECT معمولی برای لیست‌های عمومی و TLS-to-proxy واقعی.
- سازگاری با certificateهای self-signed و hostname-mismatch در TLS-to-proxy مدیریت‌شده.
- retry مقصد domain با IPv4/IPv6 resolve‌شده برای پروکسی‌های محدودکننده.
- lookup پروکسی در data plane کاملاً cache-only است؛ S3 کند یا قطع دیگر اتصال کاربر را متوقف نمی‌کند.
- دکمه «بررسی جدید» با endpoint سبک وضعیت، دو نام Variable، پاک‌سازی کوتیشن/فاصله و پذیرش raw secret یا SHA-256 پایدار شده است.
- بخش Support، تمام لینک‌ها/کانال‌های خارجی و `support-url` از پنل، footer و خروجی subscription حذف شد.
- طراحی Material 3 Expressive، دو زبان، تم روشن/تاریک و WS Turbo بدون تغییر ساختاری حفظ شد.
