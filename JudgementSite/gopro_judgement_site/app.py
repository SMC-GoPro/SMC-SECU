from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
import secrets
import re
from datetime import datetime
from judgement import execute_code
from datetime import datetime
from sqlalchemy import *


app = Flask(__name__)
app.secret_key = "rnai_st5151sfga"

# SQLAlchemy 설정
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 모델 정의
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    score = db.Column(db.Integer, default=0)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProblemAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 'users' 테이블의 id를 참조하도록 수정
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)  # 'problems' 테이블의 id를 참조하도록 수정
    is_correct = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('attempts', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('attempts', lazy=True))


def nl2br(value):
    return Markup(re.sub(r'\n', '<br>\n', Markup.escape(value)))

app.jinja_env.filters['nl2br'] = nl2br

# 에러 핸들러
@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', title="Error - 400", error_code=400, message="잘못된 요청입니다."), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title="Error - 404", error_code=404, message="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title="Error - 500", error_code=500, message="내부 서버 오류가 발생했습니다."), 500

# 라우트 정의
@app.route('/')
def index():
    posts = Announcement.query.order_by(Announcement.id.desc()).limit(3).all()
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

        if identifier_type == 'email':
            user = User.query.filter_by(email=identifier).first()
        else:
            user = User.query.filter_by(username=identifier).first()

        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.id
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

        existing_user_username = User.query.filter_by(username=username).first()
        existing_user_email = User.query.filter_by(email=email).first()

        if existing_user_username or existing_user_email:
            error = '이미 존재하는 사용자 이름 또는 이메일입니다.'
            return render_template('signup.html', error=error)
        else:
            role = 'user'
            new_user = User(username=username, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/posts')
def posts():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # 기본값 1
    per_page = 10

    query = db.session.query(
        Post,
        func.count(Comment.id).label('comment_count')
    ).outerjoin(Comment, Post.id == Comment.post_id).group_by(Post.id)

    if search_query:
        query = query.filter(Post.title.like(f'%{search_query}%'))
    
    pagination = query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Post 객체와 comment_count를 템플릿에 전달
    posts_data = [{'id': post.id, 'title': post.title, 'author': post.author, 'created_at': post.created_at, 'comment_count': comment_count} for post, comment_count in pagination.items]

    return render_template('posts.html', posts=posts_data, page=page, total_pages=pagination.pages)

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']

        new_post = Post(title=title, content=content, author=author)
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for('posts'))

    return render_template('new_post.html', username=session['username'])

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()

    if request.method == 'POST':
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))

        author = session['username']
        content = request.form['content']

        new_comment = Comment(post_id=post_id, author=author, content=content)
        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for('view_post', post_id=post_id))

    return render_template('view_post.html', post=post, comments=comments, username=session.get('username'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != session.get('username') and session.get('role') != 'admin':
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        post.title = new_title
        post.content = new_content
        db.session.commit()

        flash('게시물이 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('view_post', post_id=post_id))

    return render_template('edit_post.html', post=post)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != session.get('username') and session.get('role') != 'admin':
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    db.session.delete(post)
    db.session.commit()

    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('posts'))

@app.route('/news')
def news():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)  # 기본값 1
    per_page = 10

    if search_query:
        pagination = Announcement.query.filter(Announcement.title.like(f'%{search_query}%')).order_by(Announcement.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = Announcement.query.order_by(Announcement.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    posts = pagination.items
    total_pages = pagination.pages

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
        date = datetime.now().date()

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('new_news'))

        new_announcement = Announcement(title=title, author=author, content=content, date=date)
        db.session.add(new_announcement)
        db.session.commit()

        flash('새 공지가 성공적으로 등록되었습니다!', 'success')
        return redirect(url_for('news'))

    return render_template('new_news.html')

@app.route('/news/<int:id>')
def view_news(id):
    post = Announcement.query.get_or_404(id)
    return render_template('view_news.html', post=post)

@app.route('/news/<int:id>/edit', methods=['GET', 'POST'])
def edit_news(id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news'))

    post = Announcement.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date = datetime.now().date()

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('edit_news', id=id))

        post.title = title
        post.content = content
        post.date = date
        db.session.commit()

        flash('공지사항이 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('view_news', id=id))

    return render_template('edit_news.html', post=post)

@app.route('/news/<int:id>/delete', methods=['POST'])
def delete_news(id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news'))

    post = Announcement.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()

    flash('공지사항이 성공적으로 삭제되었습니다!', 'success')
    return redirect(url_for('news'))

@app.route('/rank')
def rank():
    users = User.query.order_by(User.score.desc()).limit(100).all()
    return render_template('rank.html', users=users)

@app.route('/problem')
def problem_list():
    problems = Problem.query.order_by(Problem.created_at.desc()).all()
    return render_template('problem_list.html', problems=problems)

@app.route('/problem/<int:id>')
def problem_detail(id):
    problem = Problem.query.get_or_404(id)
    return render_template('problem_detail.html', problem=problem)

@app.route('/problem/new', methods=['GET', 'POST'])
def problem_new():
    if 'logged_in' in session and session.get('role') == 'admin':
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            difficulty = request.form['difficulty']
            answer = request.form['answer']
            author = session['username']

            new_problem = Problem(
                title=title,
                description=description,
                author=author,
                difficulty=difficulty,
                answer=answer
            )
            db.session.add(new_problem)
            db.session.commit()
            return redirect(url_for('problem_list'))
        return render_template('problem_new.html')
    else:
        flash('접근 권한이 없습니다.')
        return redirect(url_for('login'))

def normalize_output(output):
    output = re.sub(r'\s+', '', output)
    return output.lower()

def calculate_score(difficulty):
    base_score_dict = {
        1: 50,
        2: 65,
        3: 80,
        4: 95,
        5: 105
    }
    return base_score_dict.get(difficulty, 0)

@app.route('/problem/<int:id>/solve', methods=['GET', 'POST'])
def problem_solve(id):
    if 'logged_in' not in session:
        flash('문제를 풀기 위해서는 로그인이 필요합니다.')
        return redirect(url_for('login'))

    problem = Problem.query.get_or_404(id)
    user_id = session['user_id']

    user = User.query.get(user_id)
    if not user:
        flash('사용자 정보를 불러올 수 없습니다.')
        return redirect(url_for('login'))

    existing_attempt = UserProblemAttempt.query.filter_by(user_id=user_id, problem_id=id).first()
    if existing_attempt:
        flash('이미 이 문제를 풀었습니다.')
        return redirect(url_for('problem_list'))

    if request.method == 'POST':
        code = request.form['code']
        language = request.form['language']
        submit_action = request.form.get('submit_action')

        user_output = None
        result_message = None

        execution_result, error = execute_code(code, language)

        if error:
            user_output = error
        else:
            user_output = execution_result

            if submit_action == 'run':
                result_message = "(실행 결과)"
            elif submit_action == 'submit':
                correct_answer = problem.answer.strip()
                if normalize_output(execution_result) == normalize_output(correct_answer):
                    result_message = "정답입니다!"
                    is_correct = True

                    try:
                        score_to_add = calculate_score(problem.difficulty)
                        user.score += score_to_add
                        
                        db.session.add(user)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()

                    new_attempt = UserProblemAttempt(
                        user_id=user_id,
                        problem_id=id,
                        is_correct=is_correct
                    )
                    db.session.add(new_attempt)
                    db.session.commit()
                else:
                    result_message = "틀렸습니다."
                    is_correct = False

                    new_attempt = UserProblemAttempt(
                        user_id=user_id,
                        problem_id=id,
                        is_correct=is_correct
                    )
                    db.session.add(new_attempt)
                    db.session.commit()

        return render_template(
            'problem_solve.html',
            problem=problem,
            code=code,
            user_output=user_output,
            result_message=result_message,
            action=submit_action
        )

    return render_template('problem_solve.html', problem=problem)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
