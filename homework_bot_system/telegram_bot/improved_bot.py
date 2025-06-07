

# ===== 3. إصلاح معالجة الأخطاء في البوت =====
# homework_bot_system/telegram_bot/improved_bot.py

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import aiohttp
from datetime import datetime

# إعداد التسجيل المتقدم
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ImprovedHomeworkBot:
    """بوت محسن مع معالجة أخطاء شاملة"""
    
    def __init__(self, token, api_base_url):
        self.token = token
        self.api_base_url = api_base_url
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.setup_error_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("login", self.login_command))
        
        # أوامر الطلاب
        self.application.add_handler(CommandHandler("assignments", self.assignments_command))
        self.application.add_handler(CommandHandler("submit", self.submit_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # أوامر الأدمن
        self.application.add_handler(CommandHandler("approve", self.approve_command))
        self.application.add_handler(CommandHandler("reject", self.reject_command))
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # معالج الرسائل
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def setup_error_handlers(self):
        """إعداد معالجات الأخطاء المحسنة"""
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء المحسن"""
        logger.error(f"Exception while handling update: {context.error}")
        
        # تحديد نوع الخطأ وإرسال رسالة مناسبة
        error_message = "❌ حدث خطأ غير متوقع. يرجى المحاولة لاحقاً."
        
        if "Network" in str(context.error):
            error_message = "🌐 مشكلة في الاتصال. يرجى التحقق من الإنترنت."
        elif "Timeout" in str(context.error):
            error_message = "⏱️ انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى."
        elif "Unauthorized" in str(context.error):
            error_message = "🔐 يرجى تسجيل الدخول أولاً باستخدام /login"
        
        try:
            if update.effective_message:
                await update.effective_message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def api_call_with_error_handling(self, endpoint, method='GET', data=None):
        """استدعاء API مع معالجة أخطاء محسنة"""
        try:
            return await self.api_client.make_request(endpoint, method, data)
        except aiohttp.ClientError as e:
            logger.error(f"API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية المحسن"""
        try:
            user = update.effective_user
            welcome_text = f"""
🎓 مرحباً {user.first_name}!

أهلاً بك في بوت إدارة الواجبات التنافسي 🚀

📚 يمكنني مساعدتك في:
• متابعة واجباتك
• تسليم الواجبات
• المشاركة في المسابقات
• مراقبة ترتيبك

🔐 للبدء، يرجى تسجيل الدخول: /login
❓ للمساعدة: /help
            """
            
            keyboard = [
                [InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="login")],
                [
                    InlineKeyboardButton("📚 الواجبات", callback_data="assignments"),
                    InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")
                ],
                [InlineKeyboardButton("❓ مساعدة", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await self.send_error_message(update, "خطأ في تحميل الصفحة الرئيسية")
    
    async def assignments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الواجبات مع معالجة أخطاء محسنة"""
        try:
            # التحقق من تسجيل الدخول
            if not self.is_user_logged_in(context):
                await update.message.reply_text("🔐 يرجى تسجيل الدخول أولاً: /login")
                return
            
            # جلب الواجبات
            assignments = await self.safe_api_call(self.get_user_assignments, context.user_data.get('token'))
            
            if assignments is None:
                await update.message.reply_text("❌ فشل في جلب الواجبات. يرجى المحاولة لاحقاً.")
                return
            
            if not assignments:
                await update.message.reply_text("📚 لا توجد واجبات متاحة حالياً")
                return
            
            # عرض الواجبات
            text = "📚 **واجباتك:**\n\n"
            keyboard = []
            
            for assignment in assignments[:5]:  # أول 5 واجبات
                # تحديد حالة التسليم
                is_submitted = assignment.get('is_submitted', False)
                status_emoji = "✅" if is_submitted else "⏳"
                
                # تحديد الأولوية
                priority = assignment.get('priority', 'medium')
                priority_emoji = self.get_priority_emoji(priority)
                
                # تنسيق التاريخ
                due_date = self.format_date(assignment.get('due_date'))
                
                text += f"{status_emoji} {priority_emoji} **{assignment.get('title', 'بدون عنوان')}**\n"
                text += f"📅 الموعد: {due_date}\n"
                text += f"📊 النقاط: {assignment.get('points_value', 0)}\n\n"
                
                # إضافة زر للواجب
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {assignment.get('title', '')[:25]}...",
                        callback_data=f"assignment_{assignment.get('id')}"
                    )
                ])
            
            # أزرار إضافية
            keyboard.extend([
                [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_assignments")],
                [InlineKeyboardButton("📝 تسليم جديد", callback_data="new_submission")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in assignments_command: {e}")
            await self.send_error_message(update, "خطأ في جلب الواجبات")
    
    def is_user_logged_in(self, context):
        """فحص تسجيل دخول المستخدم"""
        return context.user_data.get('token') is not None
    
    def get_priority_emoji(self, priority):
        """الحصول على رمز الأولوية"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'urgent': '🚨'
        }
        return emojis.get(priority, '⚪')
    
    def format_date(self, date_string):
        """تنسيق التاريخ"""
        try:
            if not date_string:
                return "غير محدد"
            
            # تحويل التاريخ
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return "تاريخ غير صحيح"
    
    async def send_error_message(self, update, message):
        """إرسال رسالة خطأ"""
        try:
            await update.message.reply_text(f"❌ {message}")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def get_user_assignments(self, token):
        """جلب واجبات المستخدم من API"""
        # سيتم تنفيذها مع API client محسن
        # placeholder للمثال
        return []
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🚀 بدء تشغيل البوت المحسن...")
        try:
            self.application.run_polling()
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
