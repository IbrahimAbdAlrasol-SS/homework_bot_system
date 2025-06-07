import os
from dataclasses import dataclass

@dataclass
class BotConfig:
    """إعدادات البوت"""
    token: str
    api_base_url: str
    webhook_url: str = None
    debug: bool = False
    
    @classmethod
    def from_env(cls):
        return cls(
            token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            api_base_url=os.getenv('API_BASE_URL', 'http://localhost:8000/api'),
            webhook_url=os.getenv('WEBHOOK_URL'),
            debug=os.getenv('DEBUG', 'False').lower() == 'true'
        )

# إعدادات الرسائل
MESSAGES = {
    'welcome': '🎓 مرحباً بك في بوت إدارة الواجبات!',
    'login_required': '🔐 يرجى تسجيل الدخول أولاً',
    'error': '❌ حدث خطأ، يرجى المحاولة لاحقاً',
    'success': '✅ تم بنجاح!',
    'no_data': '📭 لا توجد بيانات متاحة'
}

# إعدادات API
API_ENDPOINTS = {
    'auth': '/auth/telegram/',
    'assignments': '/assignments/',
    'submissions': '/submissions/',
    'competitions': '/competitions/',
    'stats': '/analytics/user-stats/',
    'badges': '/badges/',
    'leaderboard': '/analytics/leaderboard/',
    'notifications': '/notifications/'
}