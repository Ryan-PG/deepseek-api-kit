from curl_cffi import requests
from typing import Optional, Dict, Any, Generator, Literal
import json
from .pow import DeepSeekPOW
import pkg_resources
import sys
from pathlib import Path
import subprocess
import time

ThinkingMode = Literal['detailed', 'simple', 'disabled']
SearchMode = Literal['enabled', 'disabled']

class DeepSeekError(Exception):
    """Base exception for all DeepSeek API errors"""
    pass

class AuthenticationError(DeepSeekError):
    """Raised when authentication fails"""
    pass

class RateLimitError(DeepSeekError):
    """Raised when API rate limit is exceeded"""
    pass

class NetworkError(DeepSeekError):
    """Raised when network communication fails"""
    pass

class CloudflareError(DeepSeekError):
    """Raised when Cloudflare blocks the request"""
    pass

class APIError(DeepSeekError):
    """Raised when API returns an error response"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class SSEMessageParser:
        def __init__(self):
            self.thinking_content = ""
            self.content = ""
            self.finished_status = None
            self.current_section = None   # 'thinking' یا 'content'
            self.response_message_id=None

        def parse_sse(self, chunk):
            """
            یک خط (bytes) از iter_lines() می‌گیرد.
            در طول جمع‌آوری، None برمی‌گرداند.
            فقط وقتی وضعیت FINISHED را ببیند، دیکشنری نهایی را برمی‌گرداند.
            """
            if isinstance(chunk, bytes):
                chunk = chunk.decode('utf-8')

            # حذف پیشوندهای رایج SSE
            json_str = chunk
            if chunk.startswith('data: '):
                json_str = chunk[6:]
            # اگر خط خالی یا نامربوط بود، رد شو
            if not json_str.strip():
                return None

            try:
                obj = json.loads(json_str)
            except json.JSONDecodeError:
                return None   # خطی که JSON نیست را نادیده بگیر
            
            if 'response_message_id' in obj:
                self.response_message_id=obj['response_message_id']
                return None
            
            p = obj.get('p')
            v = obj.get('v', '')
            o = obj.get('o')

            if p:   # شروع یک بخش جدید
                # بخش قبلی را کامل کن (اگر بافر خالی بود کاری نکن)
                # اما در طراحی ما، بافر به‌صورت پیوسته ساخته می‌شود.

                if p == 'response/thinking_content':
                    self.current_section = 'thinking'
                    self.thinking_content = str(v) if v else ""
                elif p == 'response/content':
                    self.current_section = 'content'
                    self.content = str(v) if v else ""
                elif p == 'response/status':
                    self.finished_status = v
                    self.current_section = None
                    # به محض دریافت پایان، دیکشنری نهایی را برگردان
                    return {
                        'response_message_id':self.response_message_id,
                        'thinking_content': self.thinking_content,
                        'content': self.content,
                        'finished_status': self.finished_status
                    }
                else:
                    # سایر p ها (مثل elapsed_secs) – بخش جاری را باطل کن ولی محتوا حفظ شود
                    self.current_section = None
            else:
                # خط الحاقی (APPEND) بدون p
                if self.current_section == 'thinking':
                    self.thinking_content += str(v)
                elif self.current_section == 'content':
                    self.content += str(v)

            return None   # هنوز کار تمام نشده

        def parse_sse_streaming(self, chunk):
            """
            نسخه streaming parse_sse.
            هر chunk را پردازش می‌کند و در صورت اضافه شدن متن (delta)، آن را yield می‌کند.
            در پایان، دیکشنری نهایی را yield کرده و متوقف می‌شود.
            """
            if isinstance(chunk, bytes):
                chunk = chunk.decode('utf-8')

            # حذف پیشوندهای رایج SSE
            json_str = chunk
            if chunk.startswith('data: '):
                json_str = chunk[6:]
            elif chunk.startswith('S.m: '):
                json_str = chunk[5:]

            if not json_str.strip():
                return  # nothing to yield

            try:
                obj = json.loads(json_str)
            except json.JSONDecodeError:
                return

            if 'response_message_id' in obj:
                self.response_message_id = obj['response_message_id']
                # در streaming، id را هم می‌توان yield کرد اما فعلاً نیازی نیست
                return

            p = obj.get('p')
            v = str(obj.get('v', ''))
            o = obj.get('o')

            if p:
                if p == 'response/thinking_content':
                    # شروع بخش thinking
                    self.current_section = 'thinking'
                    # مقدار قبلی را با v جدید جایگزین کن (طبق منطق اصلی)
                    # اما در streaming، ممکن است بخواهیم کل محتوا را بفرستیم
                    old_len = len(self.thinking_content)
                    self.thinking_content = v
                    # اگر مقدار جدیدی اضافه شده (نه فقط جایگزینی)، ولی در اینجا v کل محتواست
                    # بنابراین بهتر است کل accumulated را yield کنیم
                    yield {
                        'type': 'thinking',
                        'delta': v,
                        'accumulated': self.thinking_content,
                        'finished': False,
                        'response_message_id': self.response_message_id
                    }
                elif p == 'response/content':
                    self.current_section = 'content'
                    old_len = len(self.content)
                    self.content = v
                    yield {
                        'type': 'content',
                        'delta': v,
                        'accumulated': self.content,
                        'finished': False,
                        'response_message_id': self.response_message_id
                    }
                elif p == 'response/status':
                    self.finished_status = v
                    self.current_section = None
                    yield {
                        'type': 'finished',
                        'finished_status': self.finished_status,
                        'response_message_id': self.response_message_id,
                        'thinking_content': self.thinking_content,
                        'content': self.content
                    }
                    # بعد از finish، مولد پایان می‌یابد (اما نیازی به return صریح نیست چون function تمام می‌شود)
                else:
                    # سایر p ها (مثل elapsed_secs) – بخش جاری را باطل کن ولی محتوا حفظ شود
                    self.current_section = None
            else:
                # خط الحاقی (APPEND) بدون p
                if self.current_section == 'thinking':
                    self.thinking_content += v
                    yield {
                        'type': 'thinking',
                        'delta': v,
                        'accumulated': self.thinking_content,
                        'finished': False,
                        'response_message_id': self.response_message_id
                    }
                elif self.current_section == 'content':
                    self.content += v
                    yield {
                        'type': 'content',
                        'delta': v,
                        'accumulated': self.content,
                        'finished': False,
                        'response_message_id': self.response_message_id
                    }
                # در غیر این صورت چیزی yield نمی‌شود

class DeepSeekAPI:
    BASE_URL = "https://chat.deepseek.com/api/v0"

    def __init__(self, auth_token: str):
        self.sse_parser=SSEMessageParser()
        if not auth_token or not isinstance(auth_token, str):
            raise AuthenticationError("Invalid auth token provided")

        try:
            curl_cffi_version = pkg_resources.get_distribution('curl-cffi').version
        except pkg_resources.DistributionNotFound:
            print("\033[93mWarning: curl-cffi not found. Please install the lastest version", file=sys.stderr)
            print("pip install curl-cffi\033[0m", file=sys.stderr)

        self.auth_token = auth_token
        self.pow_solver = DeepSeekPOW()

        # Load cookies from JSON file
        cookies_path = Path(__file__).parent / 'cookies.json'
        try:
            with open(cookies_path, 'r') as f:
                cookie_data = json.load(f)
                self.cookies = cookie_data.get('cookies', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"\033[93mWarning: Could not load cookies from {cookies_path}: {e}\033[0m", file=sys.stderr)
            self.cookies = {}

    def _get_headers(self, pow_response: Optional[str] = None) -> Dict[str, str]:
        headers = {
            'accept': '*/*',
            'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'authorization': f'Bearer {self.auth_token}',
            'content-type': 'application/json',
            'origin': 'https://chat.deepseek.com',
            'referer': 'https://chat.deepseek.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'x-app-version': '20241129.1',
            'x-client-locale': 'en_US',
            'x-client-platform': 'web',
            'x-client-version': '1.0.0-always',
        }

        if pow_response:
            headers['x-ds-pow-response'] = pow_response

        return headers

    def _refresh_cookies(self) -> None:
        """Run the cookie refresh script and reload cookies"""
        try:
            # Get path to bypass.py
            script_path = Path(__file__).parent / 'bypass.py'

            # Run the script
            subprocess.run([sys.executable, script_path], check=True)

            # Wait briefly for cookies file to be written
            time.sleep(2)

            # Reload cookies
            cookies_path = Path(__file__).parent / 'cookies.json'
            with open(cookies_path, 'r') as f:
                cookie_data = json.load(f)
                self.cookies = cookie_data.get('cookies', {})

        except Exception as e:
            print(f"\033[93mWarning: Failed to refresh cookies: {e}\033[0m", file=sys.stderr)

    def _make_request(self, method: str, endpoint: str, json_data: Dict[str, Any], pow_required: bool = False) -> Any:
        url = f"{self.BASE_URL}{endpoint}"

        retry_count = 0
        max_retries = 2

        while retry_count < max_retries:
            try:
                headers = self._get_headers()
                if pow_required:
                    challenge = self._get_pow_challenge()
                    pow_response = self.pow_solver.solve_challenge(challenge)
                    headers = self._get_headers(pow_response)

                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    cookies=self.cookies,
                    impersonate='chrome120',
                    timeout=None
                )

                # Check if we hit Cloudflare protection
                if "<!DOCTYPE html>" in response.text and "Just a moment" in response.text:
                    print("\033[93mWarning: Cloudflare protection detected. Bypassing...\033[0m", file=sys.stderr)
                    if retry_count < max_retries - 1:
                        self._refresh_cookies()  # Refresh cookies
                        retry_count += 1
                        continue

                # Handle other response codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired authentication token")
                elif response.status_code == 429:
                    raise RateLimitError("API rate limit exceeded")
                elif response.status_code >= 500:
                    raise APIError(f"Server error occurred: {response.text}", response.status_code)
                elif response.status_code != 200:
                    raise APIError(f"API request failed: {response.text}", response.status_code)

                return response.json()

            except requests.exceptions.RequestException as e:
                raise NetworkError(f"Network error occurred: {str(e)}")
            except json.JSONDecodeError:
                raise APIError("Invalid JSON response from server")

        raise APIError("Failed to bypass Cloudflare protection after multiple attempts")

    def _get_pow_challenge(self) -> Dict[str, Any]:
        try:
            response = self._make_request(
                'POST',
                '/chat/create_pow_challenge',
                {'target_path': '/api/v0/chat/completion'}
            )
            return response['data']['biz_data']['challenge']
        except KeyError:
            raise APIError("Invalid challenge response format from server")

    def create_chat_session(self) -> str:
        """Creates a new chat session and returns the session ID"""
        try:
            response = self._make_request(
                'POST',
                '/chat_session/create',
                {'character_id': None}
            )
            return response['data']['biz_data']['id']
        except KeyError:
            raise APIError("Invalid session creation response format from server")

    def chat_completion(self,
                    chat_session_id: str,
                    prompt: str,
                    parent_message_id: Optional[str] = None,
                    thinking_enabled: bool = True,
                    search_enabled: bool = True) -> Generator[Dict[str, Any], None, None]:
        """
        Send a message and get streaming response

        Args:
            chat_session_id (str): The ID of the chat session
            prompt (str): The message to send
            parent_message_id (Optional[str]): ID of the parent message for threading
            thinking_enabled (bool): Whether to show the thinking process
            search_enabled (bool): Whether to enable web search for up-to-date information

        Returns:
            Generator[Dict[str, Any], None, None]: Yields message chunks with content and type

        Raises:
            AuthenticationError: If the authentication token is invalid
            RateLimitError: If the API rate limit is exceeded
            NetworkError: If a network error occurs
            APIError: If any other API error occurs
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
        if not chat_session_id or not isinstance(chat_session_id, str):
            raise ValueError("Chat session ID must be a non-empty string")

        json_data = {
            'chat_session_id': chat_session_id,
            'parent_message_id': parent_message_id,
            'prompt': prompt,
            'ref_file_ids': [],
            'thinking_enabled': thinking_enabled,
            'search_enabled': search_enabled,
        }

        try:
            headers = self._get_headers(
                pow_response=self.pow_solver.solve_challenge(
                    self._get_pow_challenge()
                )
            )

            response = requests.post(
                f"{self.BASE_URL}/chat/completion",
                headers=headers,
                json=json_data,
                cookies=self.cookies,  # Add cookies
                impersonate='chrome120',
                stream=True,
                timeout=None
            )

            if response.status_code != 200:
                error_text = next(response.iter_lines(), b'').decode('utf-8', 'ignore')
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired authentication token")
                elif response.status_code == 429:
                    raise RateLimitError("API rate limit exceeded")
                else:
                    raise APIError(f"API request failed: {error_text}", response.status_code)

            # ایجاد یک parser جدید برای این درخواست (برای جلوگیری از تداخل وضعیت بین درخواست‌ها)
            parser = SSEMessageParser()
            for chunk in response.iter_lines():
                try:
                    # استفاده از نسخه streaming
                    for partial in parser.parse_sse_streaming(chunk):
                        yield partial
                        if partial.get('type') == 'finished' and partial.get('finished_status') == 'FINISHED':
                            return  # پایان مولد
                except Exception as e:
                    raise APIError(f"Error parsing response chunk: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error occurred during streaming: {str(e)}")