import random
import requests
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 발급받은 API 키
API_KEY = '64604C58CE0FA8B73E43B74D35A19B1D'

# API 요청 URL
BASE_URL = 'https://stdict.korean.go.kr/api/search.do'

# 한국어 단어 리스트를 위한 함수
def make_korean_words():
    WORDS = []
    url = "https://ko.wiktionary.org/wiki/부록:자주_쓰이는_한국어_낱말_5800"
    r = requests.get(url)
    
    # BeautifulSoup 초기화 시에 lxml 파서 사용 설정
    bs = BeautifulSoup(r.text, "html.parser")
    
    table = bs.select_one("table.prettytable")
    dds = table.select("tr > td > dl > dd")
    
    for dd in dds:
        txt = dd.text.replace(" ", "").strip()
        if len(txt) > 1:
            WORDS.append(txt)
            
    return list(set(WORDS))

# 랜덤한 한국어 단어 선택
def get_random_korean_words(num_words):
    korean_words = make_korean_words()
    return random.sample(korean_words, num_words)

# API를 호출하여 단어 정보를 가져오는 함수
def fetch_word_info(word):
    params = {
        'key': API_KEY,
        'q': word,
        'type_search': 'search',
        'req_type': 'json',
        'num': 1,
        'start': 1,
        'advanced': 'n'
    }
    
    response = requests.get('https://stdict.korean.go.kr/api/search.do?certkey_no=6684&key=64604C58CE0FA8B73E43B74D35A19B1D&type_search=search&req_type=json&q='+word)
    
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Response is not in JSON format")
            return None
    else:
        print(f"API request failed with status code {response.status_code}")
        return None

@app.route('/')
def index():
    num_words = 5  # 출력할 단어 개수
    random_words = get_random_korean_words(num_words)
    word_data_list = []
    
    for word in random_words:
        word_info = fetch_word_info(word)
        
        if word_info and 'channel' in word_info and 'item' in word_info['channel']:
            item = word_info['channel']['item'][0]
            word_data = {
                'word': re.sub(r'[-]', '', item['word']),  # 단어에서 하이픈 제거
                'definition': item['sense']['definition']
            }
            word_data_list.append(word_data)
        else:
            print(f"No word information found for {word}")
    
    return render_template_string(''' 
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Random Korean Words</title>
        <style>
          .container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start; /* 정렬 방향을 위로 맞추기 */
          }
          .definition {
            font-weight: bold;
            margin-right: 10px;
            cursor: pointer;
            text-decoration: underline;
          }
          .word {
            display: none; /* 초기에는 단어를 숨김 */
            margin-left: 20px;
          }
        </style>
        <script>
          function toggleWord(index) {
            const word = document.getElementById('word-' + index);
            word.style.display = word.style.display === 'block' ? 'none' : 'block';
          }
        </script>
      </head>
      <body>
        <div class="container">
          <div>
            <h1>Random Korean Words</h1>
            {% if word_data_list %}
              {% for word_data in word_data_list %}
              <div class="definition" onclick="toggleWord({{ loop.index0 }})">
                {{ word_data.definition }}
              </div>
              {% endfor %}
            {% else %}
              <p>No word information found.</p>
            {% endif %}
          </div>
          <div>
            {% if word_data_list %}
              {% for word_data in word_data_list %}
              <div class="word" id="word-{{ loop.index0 }}">
                {{ word_data.word }}
              </div>
              {% endfor %}
            {% endif %}
          </div>
        </div>
      </body>
    </html>
    ''', word_data_list=word_data_list)

if __name__ == '__main__':
    app.run(debug=False)
