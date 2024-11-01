from flask import *
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
import secrets
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(128)

app.config['MYSQL_HOST'] = '103.244.116.23'
app.config['MYSQL_USER'] = 'rani'
app.config['MYSQL_PASSWORD'] = 'RrT$^L[MdYs1h[T#,}+.&$m6*,nAM)X$'
app.config['MYSQL_DB'] = 'go_pro'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def nl2br(value):
    return Markup(re.sub(r'\n', '<br>\n', Markup.escape(value)))

app.jinja_env.filters['nl2br'] = nl2br

@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', title="Error - 400", error_code=400, message="잘못된 요청입니다."), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title="Error - 404", error_code=404, message="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title="Error - 500", error_code=500, message="내부 서버 오류가 발생했습니다."), 500

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, date, content FROM announcements ORDER BY id DESC LIMIT 3")
    posts = cur.fetchall()
    cur.close()
    
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        username_pattern = r'^[a-zA-Z0-9]{3,20}$'

        if re.match(email_pattern, identifier):
            identifier_type = 'email'
        elif re.match(username_pattern, identifier):
            identifier_type = 'username'
        else:
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
            return render_template('login.html', error=error)

        cur = mysql.connection.cursor()
        if identifier_type == 'email':
            cur.execute("SELECT * FROM users WHERE email = %s", (identifier,))
        else:
            cur.execute("SELECT * FROM users WHERE username = %s", (identifier,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']  # 사용자 역할 저장
            return redirect(url_for('index'))
        else:
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        username_pattern = r'^[a-zA-Z0-9]{3,20}$'

        if not re.match(username_pattern, username):
            error = '유효한 사용자 이름을 입력하세요. (3~20자의 영문자, 숫자만 사용 가능)'
            return render_template('signup.html', error=error)

        if not re.match(email_pattern, email):
            error = '유효한 이메일 주소를 입력하세요.'
            return render_template('signup.html', error=error)

        if password != confirm_password:
            error = '비밀번호가 일치하지 않습니다.'
            return render_template('signup.html', error=error)

        hashed_password = generate_password_hash(password, method='pbkdf2:sha512')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_username = cur.fetchone()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_email = cur.fetchone()

        if user_username or user_email:
            error = '이미 존재하는 사용자 이름 또는 이메일입니다.'
            cur.close()
            return render_template('signup.html', error=error)
        else:
            role = 'user'
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                        (username, email, hashed_password, role))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/posts')
def posts():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # 기본값 1
    per_page = 10
    offset = (page - 1) * per_page  # 페이지에 따른 오프셋 계산
    
    cur = mysql.connection.cursor()

    if search_query:
        cur.execute("""
            SELECT p.id, p.title, p.author, p.created_at, 
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            WHERE p.title LIKE %s
            ORDER BY p.id DESC
            LIMIT %s OFFSET %s
        """, ('%' + search_query + '%', per_page, offset))
    else:
        cur.execute("""
            SELECT p.id, p.title, p.author, p.created_at, 
                   (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count
            FROM posts p
            ORDER BY p.id DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
    
    posts = cur.fetchall()
    
    # 총 게시물 수를 알아내 페이지 계산
    cur.execute("SELECT COUNT(*) FROM posts")
    total_posts = cur.fetchone()['COUNT(*)']
    total_pages = (total_posts + per_page - 1) // per_page  # 전체 페이지 수 계산

    cur.close()

    return render_template('posts.html', posts=posts, page=page, total_pages=total_pages)


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO posts (title, author, content) VALUES (%s, %s, %s)", (title, author, content))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('posts'))

    return render_template('new_post.html', username=session['username'])

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM posts WHERE id = %s", [post_id])
    post = cur.fetchone()

    cur.execute("SELECT * FROM comments WHERE post_id = %s ORDER BY created_at ASC", [post_id])
    comments = cur.fetchall()

    if request.method == 'POST':
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))

        author = session['username']
        content = request.form['content']

        cur.execute("INSERT INTO comments (post_id, author, content) VALUES (%s, %s, %s)", (post_id, author, content))
        mysql.connection.commit()

        return redirect(url_for('view_post', post_id=post_id))

    cur.close()

    return render_template('view_post.html', post=post, comments=comments, username=session.get('username'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM posts WHERE id = %s", [post_id])
    post = cur.fetchone()

    if post['author'] != session.get('username') and session.get('role') != 'admin':
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        cur.execute("""
            UPDATE posts SET title = %s, content = %s WHERE id = %s
        """, (new_title, new_content, post_id))
        mysql.connection.commit()
        cur.close()

        flash('게시물이 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('view_post', post_id=post_id))

    cur.close()
    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM posts WHERE id = %s", [post_id])
    post = cur.fetchone()

    if post['author'] != session.get('username') and session.get('role') != 'admin':
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    cur.execute("DELETE FROM posts WHERE id = %s", [post_id])
    mysql.connection.commit()
    cur.close()

    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('posts'))


@app.route('/news')
def news():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # 기본값 1
    per_page = 10
    offset = (page - 1) * per_page  # 페이지에 따른 오프셋 계산
    
    cur = mysql.connection.cursor()

    if search_query:
        cur.execute("""
            SELECT * FROM announcements 
            WHERE title LIKE %s 
            ORDER BY id DESC 
            LIMIT %s OFFSET %s
        """, ('%' + search_query + '%', per_page, offset))
    else:
        cur.execute("""
            SELECT * FROM announcements 
            ORDER BY id DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
    
    posts = cur.fetchall()

    # 총 공지사항 수를 알아내 페이지 계산
    cur.execute("SELECT COUNT(*) FROM announcements")
    total_posts = cur.fetchone()['COUNT(*)']
    total_pages = (total_posts + per_page - 1) // per_page  # 전체 페이지 수 계산

    cur.close()

    return render_template('news.html', posts=posts, page=page, total_pages=total_pages)



@app.route('/news/new', methods=['GET', 'POST'])
def new_news():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = '운영자'

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('new_news'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO announcements (title, author, date, content) VALUES (%s, %s, %s, %s)",
                    (title, author, datetime.now().strftime('%Y-%m-%d'), content))
        mysql.connection.commit()
        cur.close()

        flash('새 공지가 성공적으로 등록되었습니다!', 'success')
        return redirect(url_for('news'))

    return render_template('new_news.html')

@app.route('/news/<int:id>')
def view_news(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements WHERE id = %s", [id])
    post = cur.fetchone()
    cur.close()

    if post:
        return render_template('view_news.html', post=post)
    else:
        flash('해당 공지를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('news'))
    
@app.route('/news/<int:id>/edit', methods=['GET', 'POST'])
def edit_news(id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements WHERE id = %s", [id])
    post = cur.fetchone()

    if not post:
        flash('해당 공지를 찾을 수 없습니다.', 'danger')
        cur.close()
        return redirect(url_for('news'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date = datetime.now().strftime('%Y-%m-%d')

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('edit_news', id=id))

        cur.execute("UPDATE announcements SET title = %s, content = %s, date = %s WHERE id = %s",
                    (title, content, date, id))
        mysql.connection.commit()
        cur.close()
        flash('공지사항이 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('view_news', id=id))

    cur.close()
    return render_template('edit_news.html', post=post)


@app.route('/news/<int:id>/delete', methods=['POST'])
def delete_news(id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements WHERE id = %s", [id])
    post = cur.fetchone()

    if not post:
        flash('해당 공지를 찾을 수 없습니다.', 'danger')
        cur.close()
        return redirect(url_for('news'))

    cur.execute("DELETE FROM announcements WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('공지사항이 성공적으로 삭제되었습니다!', 'success')
    return redirect(url_for('news'))

@app.route('/rank')
def rank():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT username, score, profile_img 
        FROM users 
        ORDER BY score DESC 
        LIMIT 100
    """)
    users = cur.fetchall()
    cur.close()

    return render_template('rank.html', users=users)

@app.route('/problem')
def problem():
    return render_template('problem.html')

@app.route('/problem_solving')
def problem_solving():
    return render_template('problem_solving.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
