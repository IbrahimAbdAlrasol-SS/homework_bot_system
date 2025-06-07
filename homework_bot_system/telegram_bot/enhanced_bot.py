# homework_bot_system/telegram_bot/enhanced_bot.py
# بوت تلجرام محسن مع جميع الوظائف المطلوبة

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.error import TelegramError, NetworkError, TimedOut

from api_client import APIClient
from config import BotConfig, MESSAGES

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# حالات المحادثة
(WAITING_FOR_ASSIGNMENT_CONTENT, WAITING_FOR_FILE, 
 WAITING_FOR_REVIEW_DECISION, WAITING_FOR_FEEDBACK) = range(4)


class EnhancedHomeworkBot:
    """بوت إدارة الواجبات المحسن والمكتمل"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.application = Application.builder().token(config.token).build()
        self.api_client = APIClient(config)
        self.user_sessions = {}  # تخزين جلسات المستخدمين
        
        self.setup_handlers()
        self.setup_error_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر والمحادثات"""
        
        # ===== الأوامر الأساسية =====
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("login", self.login_command))
        self.application.add_handler(CommandHandler("logout", self.logout_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        
        # ===== أوامر الطلاب =====
        self.application.add_handler(CommandHandler("assignments", self.assignments_command))
        self.application.add_handler(CommandHandler("submit", self.submit_command))
        self.application.add_handler(CommandHandler("mystats", self.my_stats_command))
        self.application.add_handler(CommandHandler("mybadges", self.my_badges_command))
        self.application.add_handler(CommandHandler("competitions", self.competitions_command))
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        
        # ===== أوامر الأدمن =====
        self.application.add_handler(CommandHandler("pending", self.pending_submissions_command))
        self.application.add_handler(CommandHandler("approve", self.approve_command))
        self.application.add_handler(CommandHandler("reject", self.reject_command))
        self.application.add_handler(CommandHandler("create", self.create_assignment_command))
        self.application.add_handler(CommandHandler("stats", self.admin_stats_command))
        
        # ===== محادثات التسليم =====
        submission_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_submission, pattern=r'^submit_\d+$')],
            states={
                WAITING_FOR_ASSIGNMENT_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_assignment_content)
                ],
                WAITING_FOR_FILE: [
                    MessageHandler(filters.Document.ALL | filters.PHOTO, self.receive_assignment_file),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.skip_file)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_submission)]
        )
        self.application.add_handler(submission_conv)
        
        # ===== محادثات المراجعة =====
        review_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_review, pattern=r'^review_\d+$')],
            states={
                WAITING_FOR_REVIEW_DECISION: [
                    CallbackQueryHandler(self.review_decision, pattern=r'^(approve|reject)_\d+$')
                ],
                WAITING_FOR_FEEDBACK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_feedback)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_review)]
        )
        self.application.add_handler(review_conv)
        
        # ===== معالج الأزرار العام =====
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # ===== معالج الرسائل العام =====
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    def setup_error_handlers(self):
        """إعداد معالجات الأخطاء"""
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء المتقدم"""
        error = context.error
        logger.error(f"Exception while handling update: {error}")
        
        error_message = "❌ حدث خطأ غير متوقع."
        
        # تحديد نوع الخطأ
        if isinstance(error, NetworkError):
            error_message = "🌐 مشكلة في الاتصال. يرجى المحاولة لاحقاً."
        elif isinstance(error, TimedOut):
            error_message = "⏱️ انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى."
        elif "Unauthorized" in str(error):
            error_message = "🔐 انتهت صلاحية تسجيل الدخول. يرجى استخدام /login"
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    # ===== الأوامر الأساسية =====
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية مع واجهة تفاعلية"""
        try:
            user = update.effective_user
            
            # فحص تسجيل الدخول
            is_logged_in = await self.check_login_status(context)
            
            if is_logged_in:
                user_info = context.user_data.get('user_info', {})
                welcome_text = f"""
🎓 مرحباً مرة أخرى {user_info.get('full_name', user.first_name)}!

📊 إحصائياتك السريعة:
🏆 النقاط: {user_info.get('points', 0)}
📚 الواجبات المكتملة: {user_info.get('completed_assignments', 0)}
🥇 ترتيبك: #{user_info.get('rank', 'غير محدد')}

🔥 استخدم الأزرار للتنقل السريع:
                """
                
                keyboard = [
                    [
                        InlineKeyboardButton("📚 واجباتي", callback_data="my_assignments"),
                        InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")
                    ],
                    [
                        InlineKeyboardButton("🏆 المسابقات", callback_data="competitions"),
                        InlineKeyboardButton("🏅 شاراتي", callback_data="my_badges")
                    ],
                    [
                        InlineKeyboardButton("📈 لوحة المتصدرين", callback_data="leaderboard"),
                        InlineKeyboardButton("⚙️ إعداداتي", callback_data="settings")
                    ]
                ]
                
                # إضافة أزرار الأدمن
                if user_info.get('is_admin'):
                    keyboard.append([
                        InlineKeyboardButton("👩‍💼 لوحة الأدمن", callback_data="admin_panel")
                    ])
            
            else:
                welcome_text = f"""
🎓 مرحباً {user.first_name}!

أهلاً بك في **بوت إدارة الواجبات التنافسي** 🚀

✨ **ماذا يمكنني فعله؟**
📚 إدارة واجباتك وتسليمها
🏆 المشاركة في المسابقات
📊 متابعة إحصائياتك وترتيبك
🏅 جمع الشارات والنقاط
💬 تلقي إشعارات ذكية

🔐 **للبدء، سجل دخولك أولاً:**
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="login")],
                    [InlineKeyboardButton("❓ مساعدة", callback_data="help")],
                    [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await self.send_error_message(update, "خطأ في تحميل الصفحة الرئيسية")
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تسجيل الدخول مع معالجة أخطاء محسنة"""
        try:
            user = update.effective_user
            
            # محاولة المصادقة التلقائية
            auth_result = await self.api_client.authenticate_user(
                telegram_id=user.id,
                username=user.username or user.first_name
            )
            
            if auth_result and auth_result.get('token'):
                # نجح تسجيل الدخول
                context.user_data['token'] = auth_result['token']
                context.user_data['user_info'] = auth_result.get('user', {})
                
                user_info = auth_result.get('user', {})
                success_text = f"""
✅ **تم تسجيل الدخول بنجاح!**

👤 مرحباً {user_info.get('full_name', user.first_name)}
🎓 الشعبة: {user_info.get('section_name', 'غير محدد')}
🏆 النقاط: {user_info.get('points', 0)}
📊 الترتيب: #{user_info.get('rank', 'غير محدد')}

🚀 يمكنك الآن استخدام جميع وظائف البوت!
                """
                
                keyboard = [
                    [
                        InlineKeyboardButton("📚 واجباتي", callback_data="my_assignments"),
                        InlineKeyboardButton("🏆 المسابقات", callback_data="competitions")
                    ],
                    [InlineKeyboardButton("🏠 الصفحة الرئيسية", callback_data="home")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    success_text, 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
            
            else:
                # فشل تسجيل الدخول
                error_text = """
❌ **لم يتم العثور على حسابك**

🔗 يرجى التأكد من ربط حسابك بالتلكرام أولاً:

1️⃣ اذهب إلى موقع النظام
2️⃣ سجل دخولك
3️⃣ اربط حسابك بالتلكرام
4️⃣ عد وجرب /login مرة أخرى

💬 أو تواصل مع الدعم للمساعدة
                """
                
                keyboard = [
                    [InlineKeyboardButton("🌐 فتح الموقع", url=f"{self.config.api_base_url}/auth/telegram-link/")],
                    [InlineKeyboardButton("💬 تواصل مع الدعم", callback_data="contact_support")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    error_text, 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error in login_command: {e}")
            await self.send_error_message(update, "خطأ في تسجيل الدخول")
    
    # ===== أوامر الطلاب =====
    
    async def assignments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الواجبات مع تصفية وتنظيم محسن"""
        try:
            if not await self.check_login_status(context):
                await self.send_login_required_message(update)
                return
            
            # جلب الواجبات
            assignments = await self.api_client.get_user_assignments(
                context.user_data.get('token')
            )
            
            if not assignments:
                await update.message.reply_text(
                    "📚 لا توجد واجبات متاحة حالياً\n\n"
                    "✨ ستصلك إشعارات عند إضافة واجبات جديدة!"
                )
                return
            
            # تصنيف الواجبات
            pending_assignments = [a for a in assignments if not a.get('is_submitted')]
            completed_assignments = [a for a in assignments if a.get('is_submitted')]
            overdue_assignments = [a for a in pending_assignments if self.is_overdue(a)]
            
            text = "📚 **واجباتك:**\n\n"
            
            # الواجبات المتأخرة (أولوية عالية)
            if overdue_assignments:
                text += "🚨 **متأخرة:**\n"
                for assignment in overdue_assignments[:3]:
                    text += f"🔴 {assignment.get('title', 'بدون عنوان')}\n"
                    text += f"   📅 انتهى: {self.format_date(assignment.get('due_date'))}\n\n"
            
            # الواجبات المعلقة
            if pending_assignments:
                text += "⏳ **معلقة:**\n"
                for assignment in [a for a in pending_assignments if not self.is_overdue(a)][:3]:
                    emoji = self.get_priority_emoji(assignment.get('priority'))
                    text += f"{emoji} {assignment.get('title', 'بدون عنوان')}\n"
                    text += f"   📅 موعد: {self.format_date(assignment.get('due_date'))}\n"
                    text += f"   📊 نقاط: {assignment.get('points_value', 0)}\n\n"
            
            # الواجبات المكتملة
            if completed_assignments:
                text += f"✅ **مكتملة:** {len(completed_assignments)}\n\n"
            
            # إنشاء الأزرار
            keyboard = []
            
            # أزرار الواجبات المعلقة
            for assignment in pending_assignments[:5]:
                status_emoji = "🚨" if self.is_overdue(assignment) else "⏳"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {assignment.get('title', '')[:30]}...",
                        callback_data=f"assignment_details_{assignment.get('id')}"
                    )
                ])
            
            # أزرار التنقل
            keyboard.extend([
                [
                    InlineKeyboardButton("📝 تسليم سريع", callback_data="quick_submit"),
                    InlineKeyboardButton("🔄 تحديث", callback_data="refresh_assignments")
                ],
                [
                    InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
                    InlineKeyboardButton("🏠 الرئيسية", callback_data="home")
                ]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in assignments_command: {e}")
            await self.send_error_message(update, "خطأ في جلب الواجبات")
    
    async def submit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية تسليم واجب"""
        try:
            if not await self.check_login_status(context):
                await self.send_login_required_message(update)
                return
            
            # جلب الواجبات المعلقة
            assignments = await self.api_client.get_user_assignments(
                context.user_data.get('token')
            )
            
            pending_assignments = [
                a for a in assignments 
                if not a.get('is_submitted') and not self.is_overdue(a)
            ]
            
            if not pending_assignments:
                await update.message.reply_text(
                    "📚 لا توجد واجبات معلقة للتسليم حالياً\n\n"
                    "✅ إما أنك أكملت جميع واجباتك أو لا توجد واجبات جديدة"
                )
                return
            
            text = "📝 **اختر الواجب للتسليم:**\n\n"
            keyboard = []
            
            for assignment in pending_assignments:
                priority_emoji = self.get_priority_emoji(assignment.get('priority'))
                days_left = self.get_days_until_due(assignment.get('due_date'))
                
                button_text = f"{priority_emoji} {assignment.get('title', '')[:25]}"
                if days_left <= 1:
                    button_text += " ⚡"
                
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"submit_{assignment.get('id')}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in submit_command: {e}")
            await self.send_error_message(update, "خطأ في عرض واجبات التسليم")
    
    # ===== وظائف مساعدة =====
    
    async def check_login_status(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """فحص حالة تسجيل الدخول"""
        token = context.user_data.get('token')
        if not token:
            return False
        
        # يمكن إضافة التحقق من صحة التوكن هنا
        return True
    
    async def send_login_required_message(self, update: Update):
        """إرسال رسالة تطلب تسجيل الدخول"""
        keyboard = [[InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="login")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔐 يرجى تسجيل الدخول أولاً للوصول لهذه الخدمة",
            reply_markup=reply_markup
        )
    
    async def send_error_message(self, update: Update, message: str):
        """إرسال رسالة خطأ مع خيارات مساعدة"""
        keyboard = [
            [InlineKeyboardButton("🔄 إعادة المحاولة", callback_data="retry")],
            [InlineKeyboardButton("💬 تواصل مع الدعم", callback_data="contact_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def is_overdue(self, assignment: Dict) -> bool:
        """فحص انتهاء موعد الواجب"""
        try:
            due_date_str = assignment.get('due_date')
            if not due_date_str:
                return False
            
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            return datetime.now(due_date.tzinfo) > due_date
        except Exception:
            return False
    
    def get_days_until_due(self, due_date_str: str) -> int:
        """حساب الأيام المتبقية للموعد النهائي"""
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            days = (due_date - datetime.now(due_date.tzinfo)).days
            return max(0, days)
        except Exception:
            return 0
    
    def get_priority_emoji(self, priority: str) -> str:
        """الحصول على رمز الأولوية"""
        emojis = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴',
            'urgent': '🚨'
        }
        return emojis.get(priority, '⚪')
    
    def format_date(self, date_string: str) -> str:
        """تنسيق التاريخ للعرض"""
        try:
            if not date_string:
                return "غير محدد"
            
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_obj.strftime('%m/%d %H:%M')
        except Exception:
            return "تاريخ غير صحيح"
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار العام"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # توجيه الأزرار لمعالجاتها
        if data == "login":
            await self.login_command(update, context)
        elif data == "home":
            await self.start_command(update, context)
        elif data == "my_assignments":
            await self.assignments_command(update, context)
        elif data.startswith("assignment_details_"):
            assignment_id = data.split("_")[-1]
            await self.show_assignment_details(update, context, assignment_id)
        # إضافة المزيد من معالجات الأزرار...
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل النصية العام"""
        if not await self.check_login_status(context):
            await self.send_login_required_message(update)
            return
        
        # يمكن إضافة معالجة للرسائل التلقائية هنا
        await update.message.reply_text(
            "💡 استخدم الأوامر أو الأزرار للتنقل\n"
            "اكتب /help لعرض جميع الأوامر المتاحة"
        )
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🚀 بدء تشغيل البوت المحسن...")
        try:
            self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")


if __name__ == '__main__':
    config = BotConfig.from_env()
    bot = EnhancedHomeworkBot(config)
    bot.run()