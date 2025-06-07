import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import aiohttp
import os
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

class HomeworkBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("login", self.login_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        
        # أوامر الواجبات
        self.application.add_handler(CommandHandler("assignments", self.assignments_command))
        self.application.add_handler(CommandHandler("submit", self.submit_command))
        self.application.add_handler(CommandHandler("pending", self.pending_assignments))
        
        # أوامر المسابقات
        self.application.add_handler(CommandHandler("competitions", self.competitions_command))
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        self.application.add_handler(CommandHandler("join_competition", self.join_competition))
        
        # أوامر الإحصائيات
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("badges", self.badges_command))
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # معالج الرسائل النصية
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        user = update.effective_user
        welcome_text = f"""
🎓 مرحباً {user.first_name}!

أهلاً بك في بوت إدارة الواجبات التنافسي 🚀

📚 يمكنني مساعدتك في:
• متابعة واجباتك
• المشاركة في المسابقات
• مراقبة ترتيبك
• الحصول على الشارات

🔐 للبدء، يرجى تسجيل الدخول باستخدام:
/login

❓ للمساعدة اكتب: /help
        """
        
        keyboard = [
            [InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="login")],
            [InlineKeyboardButton("📚 الواجبات", callback_data="assignments"),
             InlineKeyboardButton("🏆 المسابقات", callback_data="competitions")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
             InlineKeyboardButton("🏅 الشارات", callback_data="badges")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """
🤖 أوامر البوت المتاحة:

🔐 **المصادقة:**
/login - تسجيل الدخول
/profile - عرض الملف الشخصي

📚 **الواجبات:**
/assignments - عرض جميع الواجبات
/pending - الواجبات المعلقة
/submit - تسليم واجب

🏆 **المسابقات:**
/competitions - المسابقات المتاحة
/join_competition - الانضمام لمسابقة
/leaderboard - لوحة المتصدرين

📊 **الإحصائيات:**
/stats - إحصائياتك
/badges - شاراتك

❓ /help - عرض هذه المساعدة
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر تسجيل الدخول"""
        keyboard = [
            [InlineKeyboardButton("🔗 ربط الحساب", url=f"{API_BASE_URL}/auth/telegram-link/")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        login_text = """
🔐 **تسجيل الدخول**

لربط حسابك مع البوت:
1. اضغط على الزر أدناه
2. سجل دخولك في الموقع
3. اتبع التعليمات لربط حسابك

🔒 بياناتك محمية ومشفرة
        """
        
        await update.message.reply_text(login_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def assignments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الواجبات"""
        user_id = update.effective_user.id
        
        # محاولة جلب الواجبات من API
        try:
            assignments = await self.get_user_assignments(user_id)
            if not assignments:
                await update.message.reply_text("📚 لا توجد واجبات متاحة حالياً")
                return
            
            text = "📚 **واجباتك:**\n\n"
            for assignment in assignments[:5]:  # عرض أول 5 واجبات
                status_emoji = "✅" if assignment.get('is_submitted') else "⏳"
                due_date = assignment.get('due_date', 'غير محدد')
                text += f"{status_emoji} **{assignment.get('title')}**\n"
                text += f"📅 موعد التسليم: {due_date}\n"
                text += f"📊 النقاط: {assignment.get('points_reward', 0)}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("📝 تسليم واجب", callback_data="submit_assignment")],
                [InlineKeyboardButton("⏳ الواجبات المعلقة", callback_data="pending_assignments")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching assignments: {e}")
            await update.message.reply_text("❌ خطأ في جلب الواجبات. يرجى المحاولة لاحقاً")
    
    async def competitions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المسابقات"""
        try:
            competitions = await self.get_active_competitions()
            if not competitions:
                await update.message.reply_text("🏆 لا توجد مسابقات نشطة حالياً")
                return
            
            text = "🏆 **المسابقات النشطة:**\n\n"
            for comp in competitions[:3]:  # عرض أول 3 مسابقات
                text += f"🎯 **{comp.get('title')}**\n"
                text += f"📝 {comp.get('description', '')}\n"
                text += f"👥 المشاركين: {comp.get('participant_count', 0)}\n"
                text += f"🏅 الجوائز: {comp.get('prize_structure', {})}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🎯 الانضمام لمسابقة", callback_data="join_competition")],
                [InlineKeyboardButton("🏆 لوحة المتصدرين", callback_data="leaderboard")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching competitions: {e}")
            await update.message.reply_text("❌ خطأ في جلب المسابقات. يرجى المحاولة لاحقاً")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الإحصائيات"""
        user_id = update.effective_user.id
        
        try:
            stats = await self.get_user_stats(user_id)
            if not stats:
                await update.message.reply_text("📊 لا توجد إحصائيات متاحة")
                return
            
            text = f"""
📊 **إحصائياتك:**

🎯 النقاط الإجمالية: {stats.get('total_points', 0)}
📚 الواجبات المكتملة: {stats.get('completed_assignments', 0)}
🏆 المسابقات: {stats.get('competitions_joined', 0)}
🏅 الشارات: {stats.get('badges_count', 0)}
📈 الترتيب: #{stats.get('rank', 'غير محدد')}

⭐ مستوى النشاط: {stats.get('activity_level', 'مبتدئ')}
            """
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            await update.message.reply_text("❌ خطأ في جلب الإحصائيات")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "login":
            await self.login_command(update, context)
        elif query.data == "assignments":
            await self.assignments_command(update, context)
        elif query.data == "competitions":
            await self.competitions_command(update, context)
        elif query.data == "stats":
            await self.stats_command(update, context)
        # يمكن إضافة المزيد من معالجات الأزرار هنا
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل النصية"""
        text = update.message.text
        
        # يمكن إضافة منطق معالجة الرسائل هنا
        await update.message.reply_text(
            "🤖 أهلاً! استخدم /help لرؤية الأوامر المتاحة"
        )
    
    # دوال مساعدة للتواصل مع API
    async def get_user_assignments(self, user_id):
        """جلب واجبات المستخدم"""
        # سيتم تنفيذها لاحقاً مع ربط API
        return []
    
    async def get_active_competitions(self):
        """جلب المسابقات النشطة"""
        # سيتم تنفيذها لاحقاً مع ربط API
        return []
    
    async def get_user_stats(self, user_id):
        """جلب إحصائيات المستخدم"""
        # سيتم تنفيذها لاحقاً مع ربط API
        return {}
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🚀 بدء تشغيل بوت الواجبات...")
        self.application.run_polling()

if __name__ == '__main__':
    bot = HomeworkBot()
    bot.run()