#!/bin/bash
# homework_bot_system/setup_and_run.sh
# سكريبت إعداد وتشغيل المشروع الكامل

echo "🚀 بدء إعداد نظام إدارة الواجبات التنافسي..."

# ===== 1. إعداد البيئة =====
echo "📦 إعداد البيئة الافتراضية..."

# إنشاء البيئة الافتراضية
python3 -m venv homework_bot_env
source homework_bot_env/bin/activate

# تحديث pip
pip install --upgrade pip

# ===== 2. تثبيت المتطلبات =====
echo "📚 تثبيت المكتبات المطلوبة..."

cd homework_bot_system/api_service
pip install -r requirements.txt

# إضافة مكتبات البوت
pip install python-telegram-bot[ext] aiohttp python-decouple

# ===== 3. إعداد قاعدة البيانات =====
echo "🗄️ إعداد قاعدة البيانات..."

# تشغيل سكريبت إنشاء قاعدة البيانات
mysql -u root -p < ../database/schema.sql

# تطبيق الإصلاحات
mysql -u root -p < ../database/fix_migration.sql

# ===== 4. إعداد Django =====
echo "⚙️ إعداد Django..."

# إنشاء ملف .env
cat > .env << EOL
# Django Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=homework_bot_db
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token-here
API_BASE_URL=http://localhost:8000/api/v1

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (اختياري)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EOL

echo "📝 تم إنشاء ملف .env - يرجى تحديث القيم المطلوبة"

# تطبيق migrations
echo "🔄 تطبيق migrations..."
python manage.py makemigrations
python manage.py migrate

# إنشاء مستخدم أدمن
echo "👤 إنشاء مستخدم المدير..."
python manage.py createsuperuser

# ===== 5. إعداد البوت =====
echo "🤖 إعداد بوت التلكرام..."

cd ../telegram_bot

# إنشاء ملف .env للبوت
cat > .env << EOL
TELEGRAM_BOT_TOKEN=your-bot-token-here
API_BASE_URL=http://localhost:8000/api/v1
DEBUG=True
EOL

echo "📝 تم إنشاء ملف .env للبوت - يرجى تحديث التوكن"

# ===== 6. إنشاء سكريبت التشغيل =====
echo "🚀 إنشاء سكريبت التشغيل..."

cat > ../run_all.sh << 'EOL'
#!/bin/bash
# سكريبت تشغيل النظام الكامل

# تشغيل Redis (إذا لم يكن يعمل)
redis-server --daemonize yes

# تشغيل Django API
echo "🌐 تشغيل خادم Django..."
cd api_service
source ../homework_bot_env/bin/activate
python manage.py runserver &
DJANGO_PID=$!

# انتظار تشغيل Django
sleep 5

# تشغيل Celery Worker
echo "⚙️ تشغيل Celery Worker..."
celery -A config worker --loglevel=info &
CELERY_PID=$!

# تشغيل Celery Beat
echo "⏰ تشغيل Celery Beat..."
celery -A config beat --loglevel=info &
BEAT_PID=$!

# تشغيل بوت التلكرام
echo "🤖 تشغيل بوت التلكرام..."
cd ../telegram_bot
python enhanced_bot.py &
BOT_PID=$!

echo "✅ تم تشغيل جميع الخدمات!"
echo "📱 Django Admin: http://localhost:8000/admin/"
echo "📖 API Docs: http://localhost:8000/api/docs/"

# معالج إيقاف الخدمات
cleanup() {
    echo "🛑 إيقاف الخدمات..."
    kill $DJANGO_PID $CELERY_PID $BEAT_PID $BOT_PID 2>/dev/null
    redis-cli shutdown 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# انتظار
wait
EOL

chmod +x ../run_all.sh

# ===== 7. إنشاء سكريبت الاختبار =====
echo "🧪 إنشاء سكريبت الاختبار..."

cd ../api_service

cat > test_system.py << 'EOL'
#!/usr/bin/env python
"""
اختبار سريع للنظام
"""
import os
import django
import requests
from django.test import TestCase

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_api_endpoints():
    """اختبار API endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    endpoints = [
        "/users/",
        "/sections/", 
        "/assignments/",
        "/submissions/",
        "/competitions/competitions/",
        "/badges/",
        "/analytics/dashboard/"
    ]
    
    print("🔍 اختبار API endpoints...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅" if response.status_code in [200, 401] else "❌"
            print(f"{status} {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - خطأ: {e}")

def test_database_connection():
    """اختبار اتصال قاعدة البيانات"""
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ اتصال قاعدة البيانات يعمل")
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")

def test_models():
    """اختبار النماذج"""
    from apps.users.models import User
    from apps.sections.models import Section
    from apps.assignments.models import Assignment
    
    try:
        # اختبار النماذج
        user_count = User.objects.count()
        section_count = Section.objects.count()
        assignment_count = Assignment.objects.count()
        
        print(f"✅ النماذج تعمل:")
        print(f"   👥 المستخدمون: {user_count}")
        print(f"   🎓 الشعب: {section_count}")
        print(f"   📚 الواجبات: {assignment_count}")
        
    except Exception as e:
        print(f"❌ خطأ في النماذج: {e}")

if __name__ == "__main__":
    print("🧪 بدء اختبار النظام...\n")
    
    test_database_connection()
    test_models()
    
    print("\n⏳ تأكد من تشغيل الخادم ثم اختبر API...")
    print("python test_system.py")
EOL

# ===== 8. الإرشادات النهائية =====
echo ""
echo "✅ تم الانتهاء من الإعداد!"
echo ""
echo "🔧 خطوات ما بعد الإعداد:"
echo "1. حدث ملف api_service/.env بالقيم الصحيحة"
echo "2. حدث ملف telegram_bot/.env بتوكن البوت"
echo "3. تأكد من تشغيل MySQL و Redis"
echo "4. شغل النظام: ./run_all.sh"
echo ""
echo "📚 ملفات مهمة:"
echo "- api_service/.env (إعدادات Django)"
echo "- telegram_bot/.env (إعدادات البوت)"
echo "- run_all.sh (تشغيل النظام)"
echo "- api_service/test_system.py (اختبار النظام)"
echo ""
echo "🌐 روابط مفيدة:"
echo "- Django Admin: http://localhost:8000/admin/"
echo "- API Documentation: http://localhost:8000/api/docs/"
echo "- Redoc: http://localhost:8000/api/redoc/"
echo ""
echo "🆘 للمساعدة:"
echo "- تحقق من ملفات اللوج في logs/"
echo "- اختبر النظام: cd api_service && python test_system.py"
echo "- تأكد من الاتصال: curl http://localhost:8000/api/v1/users/"