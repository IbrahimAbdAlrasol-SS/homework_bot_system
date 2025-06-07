import jwt
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthentication:
    """نظام مصادقة JWT مخصص"""
    
    @staticmethod
    def generate_tokens(user):
        """إنشاء رموز الوصول والتحديث"""
        now = datetime.datetime.utcnow()
        
        # رمز الوصول (مدة قصيرة)
        access_payload = {
            'user_id': user.id,
            'telegram_id': user.telegram_id,
            'role': user.role,
            'exp': now + datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'iat': now,
            'type': 'access'
        }
        
        # رمز التحديث (مدة طويلة)
        refresh_payload = {
            'user_id': user.id,
            'exp': now + datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return access_token, refresh_token
    
    @staticmethod
    def verify_token(token, token_type='access'):
        """التحقق من صحة الرمز"""
        try:
            # فك تشفير الرمز
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # التحقق من نوع الرمز
            if payload.get('type') != token_type:
                return None
            
            # التحقق من وجود المستخدم
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            # التحقق من القائمة السوداء
            if JWTAuthentication.is_token_blacklisted(token):
                return None
            
            # الحصول على المستخدم
            try:
                user = User.objects.get(id=user_id, status='active')
                return user
            except User.DoesNotExist:
                return None
                
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """تحديث رمز الوصول باستخدام رمز التحديث"""
        user = JWTAuthentication.verify_token(refresh_token, 'refresh')
        if not user:
            return None, None
        
        # إنشاء رمز وصول جديد
        access_token, _ = JWTAuthentication.generate_tokens(user)
        return access_token, user
    
    @staticmethod
    def blacklist_token(token):
        """إضافة رمز للقائمة السوداء"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False}
            )
            
            # حساب وقت انتهاء الصلاحية
            exp = payload.get('exp')
            if exp:
                exp_datetime = datetime.datetime.fromtimestamp(exp)
                ttl = (exp_datetime - datetime.datetime.utcnow()).total_seconds()
                
                if ttl > 0:
                    cache.set(f"blacklisted_token_{token}", True, timeout=int(ttl))
                    
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
    
    @staticmethod
    def is_token_blacklisted(token):
        """التحقق من وجود الرمز في القائمة السوداء"""
        return cache.get(f"blacklisted_token_{token}", False)
    
    @staticmethod
    def logout_user(user):
        """تسجيل خروج المستخدم من جميع الأجهزة"""
        # إضافة جميع الرموز النشطة للقائمة السوداء
        # هذا يتطلب تتبع الرموز النشطة (يمكن تنفيذه لاحقاً)
        pass