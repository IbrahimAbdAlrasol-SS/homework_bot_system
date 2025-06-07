from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class CompetitionsHandler:
    """معالج المسابقات"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def list_competitions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض قائمة المسابقات"""
        try:
            competitions = await self.api_client.get_active_competitions()
            
            if not competitions:
                await update.message.reply_text("🏆 لا توجد مسابقات نشطة حالياً")
                return
            
            text = "🏆 **المسابقات المتاحة:**\n\n"
            keyboard = []
            
            for comp in competitions:
                text += f"🎯 **{comp.get('title')}**\n"
                text += f"👥 المشاركين: {comp.get('participants_count', 0)}\n"
                text += f"🏅 النقاط: {comp.get('points_reward', 0)}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎯 {comp.get('title')}",
                        callback_data=f"competition_{comp.get('id')}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🏆 لوحة المتصدرين", callback_data="leaderboard")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error listing competitions: {e}")
            await update.message.reply_text("❌ خطأ في جلب المسابقات")
    
    async def show_competition_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, competition_id: int):
        """عرض تفاصيل مسابقة محددة"""
        try:
            competition = await self.api_client.get_competition_details(competition_id)
            
            if not competition:
                await update.callback_query.message.reply_text("❌ لم يتم العثور على المسابقة")
                return
            
            text = f"""
🏆 **{competition.get('title')}**

📝 **الوصف:**
{competition.get('description', 'لا يوجد وصف')}

📅 **تاريخ البداية:** {competition.get('start_date')}
📅 **تاريخ النهاية:** {competition.get('end_date')}
👥 **المشاركين:** {competition.get('participants_count', 0)}
🏅 **جوائز النقاط:** {competition.get('points_reward', 0)}

📊 **حالة المسابقة:** {competition.get('status', 'نشطة')}
            """
            
            keyboard = []
            if not competition.get('is_participant'):
                keyboard.append([InlineKeyboardButton("🎯 الانضمام للمسابقة", callback_data=f"join_{competition_id}")])
            else:
                keyboard.append([InlineKeyboardButton("📊 عرض ترتيبي", callback_data=f"my_rank_{competition_id}")])
            
            keyboard.append([InlineKeyboardButton("🏆 لوحة المتصدرين", callback_data=f"leaderboard_{competition_id}")])
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_competitions")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing competition details: {e}")
            await update.callback_query.message.reply_text("❌ خطأ في جلب تفاصيل المسابقة")
    
    async def join_competition(self, update: Update, context: ContextTypes.DEFAULT_TYPE, competition_id: int):
        """الانضمام لمسابقة"""
        if not context.user_data.get('token'):
            await update.callback_query.message.reply_text("🔐 يرجى تسجيل الدخول أولاً: /login")
            return
        
        try:
            result = await self.api_client.join_competition(
                context.user_data['token'],
                competition_id
            )
            
            if result:
                await update.callback_query.message.reply_text(
                    "🎉 تم الانضمام للمسابقة بنجاح!\n"
                    "🚀 حظاً موفقاً في المنافسة!"
                )
            else:
                await update.callback_query.message.reply_text(
                    "❌ فشل في الانضمام للمسابقة\n"
                    "تأكد من أنك مؤهل للمشاركة"
                )
                
        except Exception as e:
            logger.error(f"Error joining competition: {e}")
            await update.callback_query.message.reply_text("❌ خطأ في الانضمام للمسابقة")