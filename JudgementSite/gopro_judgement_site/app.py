from flask import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', notices=[['새로운 업데이트', '2024년 09월 10일', '대규모 사이트 업데이트'],['서버 점검 실시', '2024년 09월 10일', 'GoPro 사이트 점검합니다.'],['새로운 업데이트', '2024년 09월 10일', '대규모 사이트 업데이트']])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)