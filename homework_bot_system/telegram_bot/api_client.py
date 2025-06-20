import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from config import BotConfig, API_ENDPOINTS

logger = logging.getLogger(__name__)

class APIClient:
    """عميل API للتواصل مع خادم Django"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = None
        self.base_url = config.api_base_url
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """إجراء طلب HTTP"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API Error: {response.status} - {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    async def authenticate_user(self, telegram_id: int, username: str) -> Optional[Dict]:
        """مصادقة المستخدم"""
        data = {
            'telegram_id': telegram_id,
            'username': username
        }
        return await self._make_request('POST', API_ENDPOINTS['auth'], json=data)
    
    async def get_user_assignments(self, user_token: str) -> List[Dict]:
        """جلب واجبات المستخدم"""
        headers = {'Authorization': f'Bearer {user_token}'}
        result = await self._make_request('GET', API_ENDPOINTS['assignments'], headers=headers)
        return result.get('results', []) if result else []
    
    async def get_active_competitions(self) -> List[Dict]:
        """جلب المسابقات النشطة"""
        result = await self._make_request('GET', f"{API_ENDPOINTS['competitions']}active/")
        return result.get('results', []) if result else []
    
    async def get_user_stats(self, user_token: str) -> Optional[Dict]:
        """جلب إحصائيات المستخدم"""
        headers = {'Authorization': f'Bearer {user_token}'}
        return await self._make_request('GET', API_ENDPOINTS['stats'], headers=headers)
    
    async def submit_assignment(self, user_token: str, assignment_id: int, file_url: str) -> Optional[Dict]:
        """تسليم واجب"""
        headers = {'Authorization': f'Bearer {user_token}'}
        data = {
            'assignment': assignment_id,
            'file_url': file_url
        }
        return await self._make_request('POST', API_ENDPOINTS['submissions'], headers=headers, json=data)

    async def get_assignment_details(self, assignment_id: int) -> Optional[Dict]:
        """جلب تفاصيل واجب محدد"""
        return await self._make_request('GET', f"{API_ENDPOINTS['assignments']}{assignment_id}/")
    
    async def get_competition_details(self, competition_id: int) -> Optional[Dict]:
        """جلب تفاصيل مسابقة محددة"""
        return await self._make_request('GET', f"{API_ENDPOINTS['competitions']}{competition_id}/")
    
    async def join_competition(self, user_token: str, competition_id: int) -> Optional[Dict]:
        """الانضمام لمسابقة"""
        headers = {'Authorization': f'Bearer {user_token}'}
        data = {'competition': competition_id}
        return await self._make_request('POST', f"{API_ENDPOINTS['competitions']}{competition_id}/join/", headers=headers, json=data)
    
    async def get_leaderboard(self, competition_id: int = None) -> List[Dict]:
        """جلب لوحة المتصدرين"""
        endpoint = API_ENDPOINTS['leaderboard']
        if competition_id:
            endpoint += f"?competition={competition_id}"
        
        result = await self._make_request('GET', endpoint)
        return result.get('results', []) if result else []
    
    async def get_user_badges(self, user_token: str) -> List[Dict]:
        """جلب شارات المستخدم"""
        headers = {'Authorization': f'Bearer {user_token}'}
        result = await self._make_request('GET', API_ENDPOINTS['badges'], headers=headers)
        return result.get('results', []) if result else []
    
    async def get_assignments(self, section_id=None):
        """الحصول على الواجبات"""
        params = {}
        if section_id:
            params['section'] = section_id
            
        response = await self._make_request('GET', 'assignments/', params=params)
        return response
    
    async def submit_assignment(self, assignment_id, content, files=None):
        """تسليم واجب"""
        data = {
            'assignment': assignment_id,
            'content': content
        }
        
        response = await self._make_request('POST', 'submissions/', data=data)
        
        # رفع الملفات إذا وجدت
        if files and response.get('id'):
            await self._upload_files(response['id'], files)
            
        return response
    
    async def get_notifications(self, user_id):
        """الحصول على الإشعارات"""
        response = await self._make_request('GET', f'notifications/?user={user_id}')
        return response
    
    async def make_request(self, endpoint, method='GET', data=None, retries=3):
        """إجراء طلب API مع إعادة المحاولة ومعالجة الأخطاء"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method, url, 
                        json=data, 
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:
                            logger.error("Unauthorized - Token may be expired")
                            return None
                        elif response.status >= 500:
                            # خطأ خادم - إعادة المحاولة
                            if attempt < retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        
                        logger.error(f"API Error: {response.status} - {await response.text()}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"Request timeout (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        return None