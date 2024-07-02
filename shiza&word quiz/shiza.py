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

# 낱말을 무작위로 섞어주는 함수
def shuffle_word(word):
    # 낱말을 리스트로 분리
    chars = list(word)
    
    # 낱말을 무작위로 섞음
    random.shuffle(chars)
    
    # 섞인 낱말을 다시 문자열로 반환
    return ''.join(chars)

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
            align-items: flex-start; /* 단어와 뜻을 왼쪽 아래 정렬 */
          }
          .word {
            font-weight: bold;
            margin-right: 5px;
            cursor: pointer;
            user-select: none; /* 드래그 방지 */
          }
          .definition {
            margin-top: 20px;
            font-style: italic; /* 뜻을 기울임체로 표시 */
          }
          .drop-container {
            border: 2px dashed #ccc;
            padding: 10px;
            margin-top: 10px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div id="words-container">
            {% if word_data_list %}
              {% for word_data in word_data_list %}
                <span class="word" id="word-{{ loop.index }}" draggable="true" ondragstart="drag(event)">
                  {% for char in shuffle_word(word_data.word) %}
                    {{ char }}
                  {% endfor %}
                </span>
              {% endfor %}
            {% else %}
              <p>No word information found.</p>
            {% endif %}
          </div>
          <div class="definition-container drop-container" ondrop="drop(event)" ondragover="allowDrop(event)">
            {% if word_data_list %}
              {% for word_data in word_data_list %}
              <div class="definition">
                {{ word_data.definition | safe }}
              </div>
              {% endfor %}
            {% endif %}
          </div>
        </div>
        
        <script>
          var draggedWord = null;
          
          function allowDrop(event) {
            event.preventDefault();
          }
          
          function drag(event) {
            draggedWord = event.target;
            event.dataTransfer.setData("text", draggedWord.textContent.trim());
          }
          
          function drop(event) {
            event.preventDefault();
            var data = event.dataTransfer.getData("text");
            var droppedWord = event.target;
            
            // 드래그한 단어를 새로운 span으로 감싸기
            var draggedElement = document.createElement('span');
            draggedElement.textContent = data;
            draggedElement.className = 'word';
            draggedElement.draggable = true;
            draggedElement.ondragstart = drag;
            
            // 단어가 합쳐진 경우 분리하기
            if (droppedWord.textContent.trim().length > 1) {
              var droppedText = droppedWord.textContent.trim();
              var droppedFirstChar = droppedText.charAt(0);
              var droppedRestChars = droppedText.substring(1);
              
              // 기존 단어에서 첫 글자 제거
              droppedWord.textContent = droppedRestChars;
              
              // 드래그한 단어의 첫 글자 추가
              draggedElement.textContent = droppedFirstChar + draggedElement.textContent;
            }
            
            // 드래그한 단어 추가
            droppedWord.appendChild(draggedElement);
          }
        </script>
        
      </body>
    </html>
    ''', word_data_list=word_data_list, shuffle_word=shuffle_word)

if __name__ == '__main__':
    app.run(debug=False)
