# Lumen · WS-only v14

- حذف کامل قابلیت قدیمی آیپی معکوس از backend، پنل، ربات، state و تست‌ها.
- مخزن مدیریت‌شده HTTP/HTTPS/SOCKS5 با fetch از فایل TXT در S3-compatible روی HTTPS.
- کش ۵ دقیقه‌ای، refresh امن، محدودیت ۵۱۲ KiB و حداکثر ۱۰۰۰ رکورد.
- انتخاب مستقل خروجی برای هر کانفیگ: Direct، Managed repository یا Custom.
- API مدیریت‌شده هرگز endpoint، نام کاربری یا رمز را به پنل نمی‌دهد؛ فقط شناسه هش‌شده، پرچم، کشور، نوع و سلامت برمی‌گردد.
- هشدار واضح برای پروکسی دلخواه و fallback مستقیم در خرابی پروکسی.
- طراحی Material 3 Expressive، چینش، ناوبری و breakpointهای قبلی بدون تغییر حفظ شدند.

قالب TXT: `scheme://host:port#Country - 75%` یا `#FI|Finland - 75%`.
