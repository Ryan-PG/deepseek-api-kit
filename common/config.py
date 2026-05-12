import os
from pathlib import Path

# ریشهٔ پروژه (همانجایی که .env هست)
ROOT_DIR = Path(__file__).resolve().parent.parent

def load_api_key():
    """بارگذاری کلید API از متغیر محیطی یا فایل .env"""
    # اول چک کن شاید کاربر ترجیح داده با متغیر محیطی تنظیم کنه
    key = os.getenv("DEEPSEEK_API_KEY")
    if key:
        return key

    # در غیر این صورت، فایل .env را بخون
    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        raise RuntimeError(
            "کلید API دیپ‌سیک پیدا نشد.\n"
            "لطفاً یک فایل .env در ریشهٔ پروژه بسازید و این خط را در آن بنویسید:\n"
            "DEEPSEEK_API_KEY=your_api_key_here\n"
            "یا اینکه متغیر محیطی DEEPSEEK_API_KEY را تنظیم کنید."
        )

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
                else:
                    raise RuntimeError("فایل .env پیدا شد ولی مقدار کلید خالی است.")

    raise RuntimeError("فایل .env پیدا شد ولی خط DEEPSEEK_API_KEY در آن نیست.")

# متغیر قابل استفاده در سایر فایل‌ها
DEEPSEEK_API_KEY = load_api_key()