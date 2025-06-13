from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    score = db.Column(db.Integer, default=0)
    force_password_reset = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False, default='공지')

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
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    author = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade="all, delete-orphan")

class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    required_vars = db.Column(db.Text, nullable=True)

class UserProblemAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('attempts', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('attempts', lazy=True))

class RoadmapTask(db.Model):
    __tablename__ = 'roadmap_task'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class ProblemSolveLog(db.Model):
    __tablename__ = 'problem_solve_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    language = db.Column(db.String(20), nullable=False)
    code = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=True)
    result_message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('problem_logs', lazy=True))

class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('roadmap_task.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    task = db.relationship('RoadmapTask', backref=db.backref('lectures', lazy=True))

class UserLectureProgress(db.Model):
    __tablename__ = 'user_lecture_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)

# ----------------------------------------------------------
# 정보처리기능사 전용 문제 모델
class JeongchgiProblem(db.Model):
    __tablename__ = 'jeongchgi_problems'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)          # 예: 2011
    session = db.Column(db.String(10), nullable=False)      # 예: "1회", "2회"
    subject = db.Column(db.String(50), nullable=False)      # 예: "전자계산기일반"
    question_text = db.Column(db.Text, nullable=False)      # 문제 내용
    option_1 = db.Column(db.String(255), nullable=False)
    option_2 = db.Column(db.String(255), nullable=False)
    option_3 = db.Column(db.String(255), nullable=False)
    option_4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 정답 번호 (1~4)
    answer_explanation = db.Column(db.Text, nullable=True)  # 해설(답안지도)

class JeongchgiAttempt(db.Model):
    __tablename__ = 'jeongchgi_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('jeongchgi_problems.id'), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('jeongchgi_attempts', lazy=True))
    problem = db.relationship('JeongchgiProblem', backref=db.backref('attempts', lazy=True))

class JeongchgiQuizResult(db.Model):
    __tablename__ = 'jeongchgi_quiz_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    exam_session = db.Column(db.String(10), nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.Column(db.Text, nullable=False)  # JSON 형식으로 저장 (각 문제의 결과)
    correct_count = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref=db.backref('jeongchgi_quiz_results', lazy=True))
