from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class AuthHandler:
    """معالج المصادقة"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر تسجيل الدخول"""
        user = update.effective_user
        
        # محاولة مصادقة المستخدم
        try:
            auth_result = await self.api_client.authenticate_user(
                telegram_id=user.id,
                username=user.username or user.first_name
            )
            
            if auth_result and auth_result.get('token'):
                # حفظ التوكن في context
                context.user_data['token'] = auth_result['token']
                context.user_data['user_info'] = auth_result.get('user', {})
                
                await update.message.reply_text(
                    f"✅ تم تسجيل الدخول بنجاح!\n"
                    f"مرحباً {auth_result.get('user', {}).get('full_name', user.first_name)}"
                )
            else:
                # إرسال رابط للربط اليدوي
                keyboard = [
                    [InlineKeyboardButton("🔗 ربط الحساب", url=f"{self.api_client.base_url}/auth/telegram-link/?telegram_id={user.id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "🔐 لم يتم العثور على حسابك.\n"
                    "يرجى ربط حسابك أولاً:",
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            await update.message.reply_text("❌ خطأ في تسجيل الدخول. يرجى المحاولة لاحقاً")
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الملف الشخصي"""
        if not context.user_data.get('token'):
            await update.message.reply_text("🔐 يرجى تسجيل الدخول أولاً: /login")
            return
        
        user_info = context.user_data.get('user_info', {})
        
        profile_text = f"""
👤 **ملفك الشخصي:**

📛 الاسم: {user_info.get('full_name', 'غير محدد')}
🎓 الشعبة: {user_info.get('section', 'غير محدد')}
📧 البريد: {user_info.get('email', 'غير محدد')}
🎯 النقاط: {user_info.get('total_points', 0)}
📈 الترتيب: #{user_info.get('rank', 'غير محدد')}
        """
        
        await update.message.reply_text(profile_text, parse_mode='Markdown')