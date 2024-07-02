import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션용 시크릿 키 설정

# MySQL 설정
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'ec2-3-36-189-79.ap-northeast-2.compute.amazonaws.com')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'combo')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'combo12345')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'daero')

# MySQL 객체 생성
mysql = MySQL(app)

# Bcrypt 객체 생성
bcrypt = Bcrypt(app)

@app.route('/main')
def main():
    # # 세션에 username이 없으면 로그인 페이지로 리다이렉트
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/')
def login():
    # 이미 로그인된 상태면 메인 페이지로 리다이렉트
    if 'username' in session:
        return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # POST 요청 시 회원가입 처리
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']

        # 비밀번호 해시화
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 데이터베이스에 사용자 정보 저장
        conn = mysql.connection
        cursor = conn.cursor()
        sql = "INSERT INTO register (username, fullname, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, fullname, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/findid')
def findid():
    return render_template('findid.html')

@app.route('/findpassword')
def findpassword():
    return render_template('findpassword.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    # 데이터베이스에서 사용자 정보 조회
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM register WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.check_password_hash(user[0], password):
        # 로그인 성공 시 세션에 username 저장
        session['username'] = username
        return redirect(url_for('main'))
    else:
        # 로그인 실패 시 에러 메시지 전달
        error = 'Invalid username or password'
        return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # 세션에서 username 제거 후 로그인 페이지로 리다이렉트
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run('0.0.0.0', port=6500, debug=True)
