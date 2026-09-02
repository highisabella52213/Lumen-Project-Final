# مخزن خصوصی پروکسی — v16

مخزن با AWS Signature Version 4 مستقیماً از S3-compatible خوانده می‌شود. اطلاعات باکت و endpoint واقعی پروکسی‌های مدیریت‌شده به مرورگر ارسال نمی‌شود.

## تنظیم iDrive E2 در کد

در `proxy_repository.py` بخش `PRIVATE S3 CONFIGURATION` را پیدا کنید. فقط دو placeholder زیر را عوض کنید:

```python
S3_ACCESS_KEY_ID = "KEY_ID"
S3_SECRET_ACCESS_KEY = "SECRET_ACCESS"
```

Endpoint و مسیر از قبل روی این مقادیر است:

```python
S3_ENDPOINT = "https://s3.us-west-2.idrivee2.com"
S3_REGION = "us-west-2"
S3_BUCKET = "bt2"
S3_OBJECT_KEY = "www-32k-ort-org-021/proxy.txt"
```

کلید S3 را read-only و فقط با مجوز `GetObject` برای همین object بسازید.

## قالب `proxy.txt`

```text
http://1.2.3.4:8080#Finland - 75%
socks5://user:pass@1.2.3.4:8181#DE|Germany - 32%
https://proxy.example.com:443#US - 91%
```

بررسی هنگام startup و سپس هر ۲ ساعت انجام می‌شود. اگر دریافت جدید شکست بخورد، آخرین لیست سالم حفظ می‌شود. مسیر اتصال کاربر هیچ‌وقت منتظر S3 نمی‌ماند.

## 
## سازگاری و Fail-open پروکسی

- HTTP CONNECT، SOCKS5 و هر دو برداشت رایج از لیبل HTTPS پشتیبانی می‌شوند.
- TLS-to-proxy با گواهی self-signed/نامنطبق هم برای endpoint مدیریت‌شده قابل استفاده است.
- اگر پروکسی دامنه مقصد را نپذیرد، اتصال با IPهای resolve‌شده دوباره امتحان می‌شود.
- ClientHello تکه‌تکه‌شده برای مدت کوتاه جمع می‌شود و تونل فقط پس از دریافت اولین بایت واقعی مقصد معتبر محسوب می‌شود.
- پروکسی‌ای که CONNECT را قبول کند ولی ترافیک ندهد، با timeout محدود بسته می‌شود و اتصال به Direct برمی‌گردد؛ بنابراین نباید کانفیگ را در حالت بی‌پایان `-1` نگه دارد.

> کلید S3 که برای امضا لازم است، اگر داخل سورس قرار بگیرد از دارنده کامل سورس قابل مخفی‌کردن نیست. محدودکردن دسترسی کلید، کنترل امنیتی اصلی است.
