# Lumen · WS-only v15

- دریافت خصوصی فایل مخزن از iDrive E2 با AWS Signature Version 4.
- Endpoint: `https://s3.us-west-2.idrivee2.com`، Region: `us-west-2`، Bucket: `bt2`، Key: `www-32k-ort-org-021/proxy.txt`.
- Access Key ID و Secret Access Key مستقیماً در بخش مشخص‌شده‌ی `proxy_repository.py` قرار می‌گیرند.
- بررسی در startup و سپس هر ۲ ساعت با background task کنترل‌شده.
- دکمه‌ی Material 3 «بررسی جدید» فقط در صورت تطابق SHA-256 مقدار Variable محرمانه‌ی Railway ظاهر می‌شود.
- endpoint بررسی دستی نیز مستقل از UI با پاسخ 403 محافظت می‌شود.
- لیست سالم قبلی در خطای S3 حفظ می‌شود و endpoint/credentials پروکسی‌ها به مرورگر داده نمی‌شود.
