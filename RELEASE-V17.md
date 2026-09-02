# Lumen · WS-only v17

- TLS SNI از WebSocket Transport Host کاملاً جدا شد؛ تغییر SNI فقط پارامتر `sni=` را تغییر می‌دهد و `host=` روی دامنه سرویس ثابت می‌ماند.
- برای فرم ساخت کانفیگ فیلد UUID اختیاری اضافه شد؛ مقدار خالی UUID v4 امن می‌سازد، مقدار دستی canonical می‌شود و UUID تکراری/نامعتبر رد می‌شود.
- سیستم نسخه مبتنی بر GitHub Releases اضافه شد و هنگام ورود به پنل آخرین Release را بررسی می‌کند.
- اگر نسخه جدید وجود داشته باشد دکمه «آپدیت به نسخه جدید» ظاهر می‌شود.
- Setup یک‌باره پس از اولین ورود، Railway account token و GitHub fine-grained token را دریافت و با Fernet رمزگذاری می‌کند.
- Upstream از parent فورک به‌صورت خودکار تشخیص داده می‌شود؛ مقدار دستی نیز پشتیبانی می‌شود.
- Update ابتدا رابطه Fork/Upstream را دوباره اعتبارسنجی می‌کند، سپس `merge-upstream` را اجرا می‌کند و در Conflict بدون Force متوقف می‌شود.
- پس از Sync، همان commit فورک متصل با `serviceInstanceDeployV2` روی Railway دیپلوی می‌شود؛ Redeploy ساده که همان کد قبلی را اجرا کند استفاده نشده است.
- Tokenها هرگز به Browser برگردانده یا Log نمی‌شوند و فایل رمز‌شده به Volume محدود است.
- مسیرهای Proxy و WS Turbo نسخه v16 بدون تغییر عملکردی حفظ شدند.
