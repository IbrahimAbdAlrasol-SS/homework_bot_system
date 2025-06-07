#!/usr/bin/env python3
"""
سكريبت تشغيل بوت التليجرام
"""

import asyncio
import logging
import sys
import os

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import HomeworkBot
from config import BotConfig

def main():
    """الدالة الرئيسية"""
    # إعداد التسجيل
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # التحقق من وجود التوكن
    config = BotConfig.from_env()
    if not config.token:
        logger.error("❌ لم يتم العثور على TELEGRAM_BOT_TOKEN في متغيرات البيئة")
        sys.exit(1)
    
    # تشغيل البوت
    try:
        logger.info("🚀 بدء تشغيل بوت الواجبات...")
        bot = HomeworkBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()