import requests
import time
import logging

# 환경 변수에서 API 키 가져오기
JUDGE0_API_KEY = ''
JUDGE0_API_URL = 'https://judge029.p.rapidapi.com/submissions'

headers = {
    'Content-Type': 'application/json',
    'X-RapidAPI-Host': 'judge029.p.rapidapi.com',
    'X-RapidAPI-Key': JUDGE0_API_KEY
}

# 지원하는 언어 목록 (Judge0에서 사용하는 language_id)
LANGUAGES = {
    'python': 71,  # Python 3
    'c': 75,       # C (GCC 9.2.0)
    'cpp': 76,     # C++ (G++ 9.2.0)
    'java': 62     # Java (OpenJDK 13.0.1)
}

def execute_code(code, language, stdin=''):
    language_id = LANGUAGES.get(language.lower())
    if not language_id:
        return None, '지원하지 않는 언어입니다.'

    payload = {
        'source_code': code,
        'language_id': language_id,
        'stdin': stdin,
        'redirect_stderr_to_stdout': True
    }

    try:
        response = requests.post(JUDGE0_API_URL, json=payload, headers=headers)
        if not response.ok:
            return None, '코드 제출에 실패했습니다.'

        token = response.json().get('token')
        if not token:
            return None, '코드 제출 후 토큰을 받을 수 없습니다.'

        while True:
            result_response = requests.get(f"{JUDGE0_API_URL}/{token}?base64_encoded=false", headers=headers)
            if result_response.status_code != 200:
                return None, '코드 실행 결과를 가져오는 중 오류가 발생했습니다.'

            result_json = result_response.json()
            status_id = result_json.get('status', {}).get('id')

            if status_id in [1, 2]:  # In Queue, Processing
                time.sleep(1)
                continue
            else:
                break

        if 'stdout' in result_json and result_json['stdout']:
            output = result_json['stdout']
        elif 'stderr' in result_json and result_json['stderr']:
            output = result_json['stderr']
        elif 'compile_output' in result_json and result_json['compile_output']:
            output = result_json['compile_output']
        else:
            output = '실행 결과가 없습니다.'

        return output, None

    except Exception as e:
        logging.error(f"Judge0 연동 오류: {str(e)}")
        return None, '코드 실행 중 오류가 발생했습니다.'
