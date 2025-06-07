import json
import time
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware لتحديد معدل الطلبات"""
    
    def process_request(self, request):
        # تجاهل طلبات الأدمن والملفات الثابتة
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        # الحصول على IP العميل
        client_ip = self.get_client_ip(request)
        
        # مفتاح التخزين المؤقت
        cache_key = f"rate_limit_{client_ip}"
        
        # الحصول على عدد الطلبات الحالي
        current_requests = cache.get(cache_key, 0)
        
        # التحقق من تجاوز الحد المسموح
        if current_requests >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse({
                'error': 'تم تجاوز الحد المسموح من الطلبات',
                'message': 'يرجى المحاولة لاحقاً',
                'retry_after': settings.RATE_LIMIT_WINDOW
            }, status=429)
        
        # زيادة عداد الطلبات
        cache.set(cache_key, current_requests + 1, settings.RATE_LIMIT_WINDOW)
        
        return None
    
    def get_client_ip(self, request):
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware لإضافة رؤوس الأمان"""
    
    def process_response(self, request, response):
        # إضافة رؤوس الأمان
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware لتسجيل الطلبات"""
    
    def process_request(self, request):
        request.start_time = time.time()
        
        # تسجيل الطلب
        logger.info(f"Request: {request.method} {request.path} from {self.get_client_ip(request)}")
        
        return None
    
    def process_response(self, request, response):
        # حساب وقت الاستجابة
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Response: {response.status_code} in {duration:.2f}s")
        
        return response
    
    def get_client_ip(self, request):
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TelegramAuthMiddleware(MiddlewareMixin):
    """Middleware للتحقق من مصادقة التلكرام"""
    
    def process_request(self, request):
        # تجاهل بعض المسارات
        excluded_paths = ['/admin/', '/api/docs/', '/api/auth/login/']
        if any(request.path.startswith(path) for path in excluded_paths):
            return None
        
        # التحقق من وجود رمز المصادقة
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'error': 'مطلوب رمز المصادقة',
                'message': 'يرجى تسجيل الدخول أولاً'
            }, status=401)
        
        # استخراج الرمز
        token = auth_header.split(' ')[1]
        
        try:
            # التحقق من صحة الرمز (سيتم تنفيذه لاحقاً)
            user = self.verify_token(token)
            if not user:
                return JsonResponse({
                    'error': 'رمز مصادقة غير صحيح',
                    'message': 'يرجى تسجيل الدخول مرة أخرى'
                }, status=401)
            
            # إضافة المستخدم للطلب
            request.user = user
            
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return JsonResponse({
                'error': 'خطأ في التحقق من المصادقة',
                'message': 'يرجى المحاولة لاحقاً'
            }, status=500)
        
        return None
    
    def verify_token(self, token):
        """التحقق من صحة الرمز المميز"""
        # سيتم تنفيذ هذه الوظيفة مع JWT لاحقاً
        return None