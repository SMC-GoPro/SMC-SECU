import asyncio
import aiohttp
import logging
import re
import os
import html

# Get API URL from environment variable or use default
DEFAULT_API_URL = os.environ.get('JUDGE0_API_URL')
DEFAULT_HEADERS = {
    'Content-Type': 'application/json'
}
LANGUAGES = {
    'python': 71,  # Python 3
    'c': 75,       # C (GCC 9.2.0)
    'cpp': 76,     # C++ (G++ 9.2.0)
    'java': 62     # Java (OpenJDK 13.0.1)
}

# Security limits
MAX_CODE_LENGTH = 65536  # 64KB
MAX_STDIN_LENGTH = 1024  # 1KB
MAX_EXECUTION_TIME = 10  # seconds
MAX_MEMORY_LIMIT = 512000  # KB (512MB)

class Judge0Client:
    def __init__(self, api_url=DEFAULT_API_URL, headers=DEFAULT_HEADERS):
        self.api_url = api_url
        self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        await self.session.close()

    async def execute_code(self, code, language, stdin=''):
        language_id = LANGUAGES.get(language.lower())
        if not language_id:
            return None, '지원하지 않는 언어입니다.'
            
        # Security checks
        if len(code) > MAX_CODE_LENGTH:
            return None, f'코드 길이가 제한({MAX_CODE_LENGTH/1024}KB)을 초과했습니다.'
            
        if len(stdin) > MAX_STDIN_LENGTH:
            return None, f'입력값 길이가 제한({MAX_STDIN_LENGTH}B)을 초과했습니다.'

        # Sanitize inputs
        code = html.escape(code)
        stdin = html.escape(stdin)

        payload = {
            'source_code': code,
            'language_id': language_id,
            'stdin': stdin,
            'redirect_stderr_to_stdout': True,
            'cpu_time_limit': MAX_EXECUTION_TIME,
            'memory_limit': MAX_MEMORY_LIMIT,
            'max_processes_and_or_threads': 10,
            'enable_network': False
        }

        try:
            async with self.session.post(self.api_url, json=payload) as response:
                if not (200 <= response.status < 300):
                    return None, '코드 제출에 실패했습니다.'
                data = await response.json()
                token = data.get('token')
                if not token:
                    return None, '코드 제출 후 토큰을 받을 수 없습니다.'

            max_check_attempts = 10
            check_attempts = 0
            
            while check_attempts < max_check_attempts:
                async with self.session.get(f"{self.api_url}/{token}?base64_encoded=false") as result_response:
                    if result_response.status != 200:
                        return None, '코드 실행 결과를 가져오는 중 오류가 발생했습니다.'
                    result_json = await result_response.json()
                    status_id = result_json.get('status', {}).get('id')
                    if status_id in [1, 2]:
                        await asyncio.sleep(1)
                        check_attempts += 1
                        continue
                    else:
                        break
                        
            if check_attempts >= max_check_attempts:
                return None, '코드 실행 시간이 너무 깁니다. 실행이 중단되었습니다.'

            # 실행 결과 파싱
            if result_json.get('stdout'):
                output = result_json['stdout']
            elif result_json.get('stderr'):
                output = result_json['stderr']
            elif result_json.get('compile_output'):
                output = result_json['compile_output']
            else:
                output = '실행 결과가 없습니다.'

            # 출력 정리
            if language.lower() == 'python' and stdin and 'input(' in code:
                output = self.clean_python_output(output, stdin, code)

            return output, None

        except Exception as e:
            logging.error(f"Judge0 연동 오류: {str(e)}")
            return None, '코드 실행 중 오류가 발생했습니다.'

    def clean_python_output(self, output, stdin, code):
        """
        Python 코드 실행 결과에서 입력 프롬프트와 입력값을 함께 표시한다

        - 간단히 '1:' → '1: <첫 번째 입력값>' 
                    '2:' → '2: <두 번째 입력값>' 
          식으로 치환하는 예시.
        - 만약 input() 호출이 여러 개일 경우, 필요에 따라 확장 가능
        """
        stdin_lines = stdin.split('\n')
        output_lines = output.split('\n')
        cleaned_lines = []
        
        # 사용자 입력들을 배열로 보관
        # (1번째 input()에 stdin_lines[0], 2번째 input()에 stdin_lines[1] ...)
        # 여기서는 max 2개만 처리한다고 가정
        user_inputs = stdin_lines

        for line in output_lines:
            # C:\Users\PC\Desktop\gopro> 부분은 그대로 둔다면 유지 또는 제거
            # 여기서는 유지하되, 사용자 입력을 치환
            if '1:' in line and len(user_inputs) > 0:
                line = line.replace('1:', f'1: {user_inputs[0]}')
            if '2:' in line and len(user_inputs) > 1:
                line = line.replace('2:', f'2: {user_inputs[1]}')
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

async def run_judge0_code(code, language, stdin=''):
    client = Judge0Client()
    try:
        result, error = await client.execute_code(code, language, stdin)
        return result, error
    finally:
        await client.close()
