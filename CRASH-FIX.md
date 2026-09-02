# رفع کرش startup

## علت

در اجرای `python main.py`، فایل اصلی با نام `__main__` بارگذاری می‌شد. سپس `relay_vless.py` عبارت `from main import ...` را اجرا می‌کرد و پایتون همان فایل را بار دوم با نام `main` اجرا می‌کرد. اجرای دوم هنگام `from relay_vless import RELAY_BUF` به ماژول نیمه‌بارگذاری‌شده برمی‌گشت و با خطای زیر متوقف می‌شد:

```text
ImportError: cannot import name 'RELAY_BUF' from 'relay_vless'
```

## اصلاح

در ابتدای `main.py`، هنگام اجرای مستقیم، ماژول `__main__` با نام canonical یعنی `main` در `sys.modules` ثبت می‌شود. بنابراین relay و speed-limit همان نمونه‌ی اصلی را می‌بینند و فایل دوباره اجرا نمی‌شود.

هشدار `on_event is deprecated` فقط هشدار FastAPI است و عامل کرش نبود.

## تست پس از اصلاح

- بازتولید دقیق سناریوی `python main.py`: پاس؛ `RELAY_BUF=1048576` و `server.run=True`.
- کامپایل تمام فایل‌ها: پاس.
- هدر WS عادی، تکه‌تکه و Early Data: هر سه پاس.
- 16 اتصال موازی × 8MiB: پاس؛ خطا و نشت اتصال صفر.
