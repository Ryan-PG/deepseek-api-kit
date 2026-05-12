# 🚀 DeepSeek Tools

دو برنامهٔ سبک و کاربردی برای اتصال به API دیپ‌سیک، یکی به‌عنوان پروکسی سازگار با OpenAI و دیگری به‌عنوان سرور چت با مدیریت نشست و پنل تنظیمات.

---

## 📁 ساختار پروژه

```
deepseek-tools/
├── common/
│   ├── __init__.py
│   ├── api.py              # کلاینت اتصال به API دیپ‌سیک
│   ├── config.py           # بارگذاری کلید API از فایل .env
│   └── pow.py              # حل چالش Proof-of-Work
├── openai_proxy/
│   ├── __init__.py
│   └── main.py             # برنامهٔ اول: پروکسی سازگار با OpenAI
├── deepseek_chat/
│   ├── __init__.py
│   ├── main.py             # برنامهٔ دوم: سرور چت با مدیریت نشست
│   ├── session_store.py    # مدیریت ذخیره و بازیابی نشست‌ها
│   └── panel.html          # پنل مدیریت نشست‌ها (در مرورگر باز شود)
├── example.py              # نمونه کد استفاده از API
├── requirements.txt
└── README.md
```

---

## ✨ ویژگی‌ها

### 🔹 مشترک در هر دو برنامه

- **🧠 Deep Thinking**: فعال/غیرفعال کردن حالت تفکر عمیق
- **🔍 Web Search**: فعال/غیرفعال کردن جستجوی وب
- **📡 Streaming**: دریافت پاسخ‌ها به‌صورت زنده و لحظه‌ای
- **🛡️ Error Handling**: مدیریت خطاهای API و چالش‌های Cloudflare

### 🔸 برنامهٔ اول: OpenAI Proxy

- **🔄 سازگاری کامل با OpenAI API**: به‌عنوان یک دراپ‌این جایگزین برای کلاینت‌های سازگار با OpenAI (کتابخانه‌ها، افزونه‌ها و اپلیکیشن‌ها)

### 🔹 برنامهٔ دوم: DeepSeek Chat

- **💾 مدیریت نشست سرور-ساید**: ذخیره و بازیابی نشست‌ها به‌صورت پایدار در فایل JSON
- **🖥️ پنل مدیریت**: پنل HTML تحت وب برای مشاهده، حذف و تغییر تنظیمات نشست‌ها (Thinking/Search)
- **🌐 CORS فعال**: امکان اتصال از دامنه‌ها و پورت‌های مختلف

---

## ✨ تفاوت دو برنامه

| ویژگی | OpenAI Proxy | DeepSeek Chat |
|--------|--------------|---------------|
| سازگاری با OpenAI API | ✅ کامل | ❌ |
| مدیریت نشست | توسط کلاینت | سرور-ساید (پایدار در JSON) |
| پنل مدیریت | ❌ | ✅ (فایل HTML جداگانه) |
| کنترل Thinking | با انتخاب مدل | داینامیک از پنل |
| کنترل Search | با انتخاب مدل | داینامیک از پنل |
| CORS | ❌ | ✅ |
| اجرا | `uvicorn openai_proxy.main:app` | `uvicorn deepseek_chat.main:app` |

---

## 🤖 مدل‌های پروکسی OpenAI

چهار مدل مختلف تعریف شده که کاربر از طریق کلاینت خود انتخاب می‌کند:

| مدل | Thinking | Search |
|-----|:--------:|:------:|
| `not_thinking_not_search` | ❌ | ❌ |
| `thinking_not_search` | ✅ | ❌ |
| `thinking_search` | ✅ | ✅ |
| `not_thinking_search` | ❌ | ✅ |

---

## 🛠️ پیش‌نیازها

- Python 3.8+
- pip

---

## 📦 نصب

۱. مخزن را کلون کنید:

```bash
git clone https://github.com/YOUR_USERNAME/deepseek-tools.git
cd deepseek-tools
```

۲. وابستگی‌ها را نصب کنید:

```bash
pip install -r requirements.txt
```

---

## 🔑 دریافت توکن احراز هویت DeepSeek

برای استفاده از این پکیج به یک توکن احراز هویت DeepSeek نیاز دارید. در ادامه روش‌های دریافت آن توضیح داده شده است.

> 💡 اگر با **Chrome DevTools** آشنا هستید، کافیست این دستور را در کنسول مرورگر اجرا کنید:
> ```js
> JSON.parse(localStorage.getItem("userToken")).value
> ```

### روش ۱: از طریق LocalStorage (پیشنهادی)

1. به [chat.deepseek.com](https://chat.deepseek.com) بروید.
2. وارد حساب کاربری خود شوید.
3. ابزار توسعه‌دهندهٔ مرورگر را باز کنید (کلید **F12** یا **راست‌کلیک → Inspect**).
4. به تب **Application** بروید (اگر تب دیده نمی‌شود، روی `>>` کلیک کنید تا تب‌های بیشتر نمایش داده شوند).
5. در نوار کناری سمت چپ، بخش **Local Storage** را باز کنید.
6. روی `https://chat.deepseek.com` کلیک کنید.
7. کلیدی با نام **`userToken`** را پیدا کنید.
8. مقدار `value` آن را کپی کنید — این توکن احراز هویت شماست.

### روش ۲: از طریق تب Network

1. به [chat.deepseek.com](https://chat.deepseek.com) بروید.
2. وارد حساب کاربری خود شوید.
3. ابزار توسعه‌دهندهٔ مرورگر را باز کنید (کلید **F12**).
4. به تب **Network** بروید.
5. یک درخواست در چت ارسال کنید.
6. درخواست ارسال شده را در لیست پیدا کنید و روی آن کلیک کنید.
7. به بخش **Request Headers** بروید.
8. توکن `authorization` را کپی کنید (بدون پیشوند `Bearer `).

### ⚠️ تنظیم فایل `.env`

پس از دریافت توکن، یک فایل `.env` در ریشهٔ پروژه بسازید:

```
DEEPSEEK_API_KEY=توکن_دریافتی_شما
```

> ⚠️ فایل `.env` در `.gitignore` قرار دارد و هرگز روی گیت‌هاب آپلود نمی‌شود.

فایل `common/config.py` کلید را از این فایل می‌خواند.

---

## 🛡️ مدیریت چالش‌های Cloudflare

اگر با چالش Cloudflare مواجه شدید (صفحهٔ **"Just a moment..."**) یا خطای **"Please wait a few minutes before trying again"** را دریافت کردید، باید یک کوکی `cf_clearance` دریافت کنید.

دستور زیر را اجرا کنید:

```bash
python -m common.bypass
```

این دستور:

- یک مرورگر **undetected** باز می‌کند.
- به DeepSeek مراجعه می‌کند و چالش Cloudflare را به‌صورت خودکار حل می‌کند.
- کوکی `cf_clearance` را دریافت و ذخیره می‌کند.
- در درخواست‌های بعدی به‌طور خودکار از آن استفاده می‌شود.

### چه زمانی باید این دستور را اجرا کنید:

- زمانی که در درخواست‌های خود با چالش Cloudflare مواجه می‌شوید.
- زمانی که کوکی `cf_clearance` موجود منقضی شده باشد.
- زمانی که خطای **"Please wait a few minutes before trying again"** را مشاهده می‌کنید.

کوکی دریافت شده در فایل `common/cookies.json` ذخیره می‌شود و به‌طور خودکار توسط API استفاده خواهد شد.

---

## 🚀 برنامهٔ اول: پروکسی OpenAI

```bash
uvicorn openai_proxy.main:app --host 127.0.0.1 --port 8000
```

### 🌐 استفاده در برنامه‌های دیگر

برای اتصال از هر کلاینت سازگار با OpenAI (مانند **BetterChatGPT**، **ChatBox**، **OpenCat** و کتابخانه‌های برنامه‌نویسی):

- **URL / Base URL**: `http://127.0.0.1:8000/v1`
- **مدل**: یکی از مدل‌های [جدول بالا](#-مدل‌های-پروکسی-openai) را انتخاب کنید.
- **API Key**: **نیازی نیست**. چون روی لوکال‌هاست اجرا می‌شود، می‌توانید این فیلد را خالی بگذارید یا یک مقدار دلخواه (مثلاً `sk-local`) وارد کنید.

### مثال استفاده در پایتون با پکیج `openai`

```python
import openai

openai.api_base = "http://127.0.0.1:8000/v1"
openai.api_key = "doesnt-matter"

# حالت غیر-استریم
response = openai.ChatCompletion.create(
    model="thinking_search",
    messages=[{"role": "user", "content": "آخرین اخبار هوش مصنوعی"}]
)
print(response.choices[0].message.content)
```

### مثال با `curl`

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "thinking_search",
    "messages": [{"role": "user", "content": "سلام"}]
  }'
```

---

## 🚀 برنامهٔ دوم: DeepSeek Chat

```bash
uvicorn deepseek_chat.main:app --host 127.0.0.1 --port 8000
```

### پنل مدیریت نشست‌ها

پس از اجرا، مرورگر را باز کنید و به آدرس [http://127.0.0.1:8000](http://127.0.0.1:8000) بروید. از طریق پنل می‌توانید:

- لیست نشست‌ها را ببینید
- هر نشست را حذف کنید
- برای هر نشست، **Web Search** و **Deep Thinking** را فعال/غیرفعال کنید

### Endpoint چت

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session",
    "messages": [{"content": "سلام، چطوری؟"}],
    "stream": true
  }'
```

| پارامتر | نوع | توضیح |
|---------|-----|-------|
| `session_id` | `string` (اختیاری) | شناسهٔ نشست. اگر ارسال نشود `default_local_user` استفاده می‌شود |
| `messages` | `array` | آرایهٔ پیام‌ها (فقط آخرین پیام کاربر ارسال می‌شود) |
| `stream` | `boolean` (اختیاری) | حالت استریم (پیش‌فرض `false`) |

> مدیریت تنظیمات Thinking/Search، لیست و حذف نشست‌ها از طریق پنل HTML انجام می‌شود.

---

## 📄 نمونه کد کامل

فایل [`example.py`](example.py) شامل ۴ حالت مختلف (استریم/غیراستریم × نمایش تفکر/عدم نمایش تفکر) است که می‌توانید اجرا کنید:

```bash
python example.py
```

---

## 🧰 تکنولوژی‌ها

- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)
- [wasmtime](https://wasmtime.dev/)
