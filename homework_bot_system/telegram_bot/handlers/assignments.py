from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class AssignmentsHandler:
    """معالج الواجبات"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def list_assignments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة الواجبات"""
        if not context.user_data.get('token'):
            await update.message.reply_text("🔐 يرجى تسجيل الدخول أولاً: /login")
            return
        
        try:
            assignments = await self.api_client.get_user_assignments(context.user_data['token'])
            
            if not assignments:
                await update.message.reply_text("📚 لا توجد واجبات متاحة حالياً")
                return
            
            # إنشاء أزرار للواجبات
            keyboard = []
            for assignment in assignments[:10]:  # أول 10 واجبات
                status = "✅" if assignment.get('is_submitted') else "⏳"
                button_text = f"{status} {assignment.get('title')[:30]}..."
                keyboard.append([
                    InlineKeyboardButton(
                        button_text, 
                        callback_data=f"assignment_{assignment.get('id')}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📚 **اختر واجباً لعرض التفاصيل:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error listing assignments: {e}")
            await update.message.reply_text("❌ خطأ في جلب الواجبات")
    
    async def show_assignment_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, assignment_id: int):
        """عرض تفاصيل واجب محدد"""
        try:
            # جلب تفاصيل الواجب من API
            assignment = await self.api_client.get_assignment_details(assignment_id)
            
            if not assignment:
                await update.callback_query.message.reply_text("❌ لم يتم العثور على الواجب")
                return
            
            status_emoji = "✅" if assignment.get('is_submitted') else "⏳"
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(assignment.get('priority'), "⚪")
            
            text = f"""
{status_emoji} **{assignment.get('title')}**

📝 **الوصف:**
{assignment.get('description', 'لا يوجد وصف')}

📅 **موعد التسليم:** {assignment.get('deadline')}
{priority_emoji} **الأولوية:** {assignment.get('priority', 'عادية')}
📊 **النقاط:** {assignment.get('points_reward', 0)}
⭐ **نقاط التميز:** {assignment.get('excellence_points', 0)}

📎 **الحد الأقصى للتسليمات:** {assignment.get('max_submissions', 'غير محدود')}
            """
            
            keyboard = []
            if not assignment.get('is_submitted'):
                keyboard.append([InlineKeyboardButton("📤 تسليم الواجب", callback_data=f"submit_{assignment_id}")])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_assignments")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing assignment details: {e}")
            await update.callback_query.message.reply_text("❌ خطأ في جلب تفاصيل الواجب")