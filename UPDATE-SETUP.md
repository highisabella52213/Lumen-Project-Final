# Lumen Railway installer — v28

نصاب Cloudflare حذف شده است. کل برنامه قابل‌دیپلوی داخل پوشه `railway-installer/` قرار دارد و به متغیر محیطی یا ذخیره‌سازی توکن روی خود نصب‌کننده نیاز ندارد.

## 1. ساخت توکن‌ها

1. GitHub classic token با دسترسی `public_repo`:
   <https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Railway%20Installer>
2. Railway Account Token:
   <https://railway.com/account/tokens>
3. اتصال GitHub به Railway و دادن دسترسی به فورک:
   <https://railway.com/account/integrations>

Project Token کافی نیست، چون نصاب باید پروژه جدید ایجاد کند.

## 2. دیپلوی خود نصب‌کننده روی Railway

1. در Railway گزینه **New Project → Deploy from GitHub repo** را انتخاب کنید.
2. همین مخزن را انتخاب کنید.
3. در تنظیمات سرویس، **Root Directory** را روی `/railway-installer` بگذارید.
4. Railway فایل `railway.json` و `Dockerfile` داخل همان پوشه را تشخیص می‌دهد؛ متغیر محیطی لازم نیست.
5. Health Check روی `/health` اجرا می‌شود و تا تمام‌شدن بررسی شبکه منتظر می‌ماند.
6. بعد از سالم‌شدن Deployment، از بخش Networking یک دامنه عمومی بسازید و صفحه نصب را باز کنید.

## 3. بررسی مسیرها هنگام Deployment

این شش پروکسی HTTP CONNECT داخل کد باقی مانده‌اند:

```text
http://176.111.37.216:39811
http://107.167.18.122:443
http://130.110.103.245:3128
http://176.111.37.5:39811
http://94.249.197.220:40001
http://13.203.138.32:3001
```

هنگام بالا آمدن سرویس، همه پروکسی‌ها از همان Railway Deployment روی هر دو مقصد زیر آزمایش می‌شوند:

```text
GET  https://api.github.com/meta
POST https://backboard.railway.com/graphql/v2
```

هر مسیر فقط وقتی سالم است که هر دو بررسی را پاس کند. سریع‌ترین پروکسی سالم انتخاب می‌شود. اگر هر شش پروکسی شکست بخورند، مسیر مستقیم Railway روی هر دو مقصد آزمایش می‌شود. اگر مسیر مستقیم هم شکست بخورد، `/health` کد 503 می‌دهد و نصب جدید آغاز نمی‌شود.

نتیجه بدون اطلاعات محرمانه از این مسیرها قابل مشاهده است:

```text
GET  /health
GET  /api/network
POST /api/network/refresh
```

بررسی شبکه هر پنج دقیقه تکرار می‌شود و ابتدای هر نصب نیز تمام مسیرها دوباره آزمایش می‌شوند. مسیر انتخاب‌شده برای کل همان نصب ثابت می‌ماند.

## 4. اجرای نصب Lumen

1. دامنه عمومی نصب‌کننده را باز کنید.
2. GitHub token و Railway Account Token را وارد کنید.
3. نصب را شروع کنید.
4. نصاب سورس رسمی `highisabella52213/Lumen-Project-Final` را Star/Fork می‌کند.
5. پروژه مقصد، سرویس، متغیرهای محافظت‌شده، Volume الزامی `/data`، دامنه و Deployment ساخته می‌شوند.
6. لینک پنل، رمز ادمین یک‌بارمصرف و مسیر شبکه انتخاب‌شده نمایش داده می‌شوند.

## امنیت

- توکن‌های واردشده فقط در حافظه همان درخواست نگه‌داری می‌شوند و در فایل یا لاگ نصب‌کننده نوشته نمی‌شوند.
- درخواست‌های probe هیچ هدر Authorization ندارند.
- تونل پروکسی پس از HTTP CONNECT، TLS مقصد را با SNI و `rejectUnauthorized: true` اعتبارسنجی می‌کند.
- مقصدهای شبکه به `api.github.com:443` و `backboard.railway.com:443` محدود شده‌اند.
- نصب‌کننده را در حساب Railway خودتان دیپلوی کنید و توکن‌ها را داخل نمونه متعلق به فرد دیگری وارد نکنید.
