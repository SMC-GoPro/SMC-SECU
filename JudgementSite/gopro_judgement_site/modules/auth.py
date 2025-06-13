import re
import asyncio
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from argon2 import PasswordHasher
from database import db, User

# Blueprint initialization
auth_bp = Blueprint('auth', __name__)

# PasswordHasher instance
ph = PasswordHasher()

# Login attempts tracking
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT = timedelta(minutes=15)

@auth_bp.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        # 로그인 시도 제한 확인
        client_ip = request.remote_addr
        if client_ip in login_attempts:
            attempts, last_attempt_time = login_attempts[client_ip]
            if attempts >= MAX_LOGIN_ATTEMPTS:
                if datetime.now() - last_attempt_time < LOGIN_TIMEOUT:
                    error = f'로그인 시도 횟수를 초과했습니다. {LOGIN_TIMEOUT.seconds // 60}분 후에 다시 시도해주세요.'
                    return render_template('login.html', error=error)
                else:
                    # 타임아웃 지남, 초기화
                    login_attempts[client_ip] = (0, datetime.now())

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        username_pattern = r'^[a-zA-Z0-9]{3,20}$'

        if re.match(email_pattern, identifier):
            identifier_type = 'email'
        elif re.match(username_pattern, identifier):
            identifier_type = 'username'
        else:
            # 로그인 실패 시 시도 횟수 증가
            if client_ip not in login_attempts:
                login_attempts[client_ip] = (1, datetime.now())
            else:
                attempts, _ = login_attempts[client_ip]
                login_attempts[client_ip] = (attempts + 1, datetime.now())
            
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
            return render_template('login.html', error=error)

        if identifier_type == 'email':
            user = await asyncio.to_thread(lambda: User.query.filter_by(email=identifier).first())
        else:
            user = await asyncio.to_thread(lambda: User.query.filter_by(username=identifier).first())

        if user:
            if user.is_suspended:
                error = '계정이 정지되어 있습니다.'
                return render_template('login.html', error=error)

            if user.force_password_reset:
                if password == user.username:
                    # 성공하면 로그인 시도 카운터 초기화
                    if client_ip in login_attempts:
                        del login_attempts[client_ip]
                        
                    # 세션 재설정
                    session.clear()
                    
                    # 사용자 세션 생성
                    session['logged_in'] = True
                    session['username'] = user.username
                    session['role'] = user.role
                    session['user_id'] = user.id
                    session['csrf_token'] = request.form.get('csrf_token', '')
                    session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.permanent = True
                    
                    flash("비밀번호 초기화가 필요합니다. 새로운 비밀번호를 입력해주세요.", "info")
                    return redirect(url_for('auth.force_change_password'))
                else:
                    # 로그인 실패 시 시도 횟수 증가
                    if client_ip not in login_attempts:
                        login_attempts[client_ip] = (1, datetime.now())
                    else:
                        attempts, _ = login_attempts[client_ip]
                        login_attempts[client_ip] = (attempts + 1, datetime.now())
                    
                    error = '아이디 또는 비밀번호가 잘못되었습니다.'
                    return render_template('login.html', error=error)
            else:
                try:
                    ph.verify(user.password, password)
                    # 성공하면 로그인 시도 카운터 초기화
                    if client_ip in login_attempts:
                        del login_attempts[client_ip]
                        
                    # 세션 재설정
                    session.clear()
                    
                    # 사용자 세션 생성
                    session['logged_in'] = True
                    session['username'] = user.username
                    session['role'] = user.role
                    session['user_id'] = user.id
                    session['csrf_token'] = request.form.get('csrf_token', '')
                    session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.permanent = True
                    
                    return redirect(url_for('index'))
                except Exception:
                    # 로그인 실패 시 시도 횟수 증가
                    if client_ip not in login_attempts:
                        login_attempts[client_ip] = (1, datetime.now())
                    else:
                        attempts, _ = login_attempts[client_ip]
                        login_attempts[client_ip] = (attempts + 1, datetime.now())
                    
                    error = '아이디 또는 비밀번호가 잘못되었습니다.'
                    return render_template('login.html', error=error)
        else:
            # 로그인 실패 시 시도 횟수 증가
            if client_ip not in login_attempts:
                login_attempts[client_ip] = (1, datetime.now())
            else:
                attempts, _ = login_attempts[client_ip]
                login_attempts[client_ip] = (attempts + 1, datetime.now())
                
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
            return render_template('login.html', error=error)

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
async def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        username_pattern = r'^[a-zA-Z0-9]{3,20}$'
        password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'

        if not re.match(username_pattern, username):
            error = '유효한 사용자 이름을 입력하세요. (3~20자의 영문자, 숫자만 사용 가능)'
            return render_template('signup.html', error=error)

        if not re.match(email_pattern, email):
            error = '유효한 이메일 주소를 입력하세요.'
            return render_template('signup.html', error=error)
            
        if not re.match(password_pattern, password):
            error = '비밀번호는 최소 8자 이상이며, 문자, 숫자, 특수문자를 포함해야 합니다.'
            return render_template('signup.html', error=error)

        if password != confirm_password:
            error = '비밀번호가 일치하지 않습니다.'
            return render_template('signup.html', error=error)

        hashed_password = ph.hash(password)

        existing_user_username = await asyncio.to_thread(lambda: User.query.filter_by(username=username).first())
        existing_user_email = await asyncio.to_thread(lambda: User.query.filter_by(email=email).first())

        if existing_user_username or existing_user_email:
            error = '이미 존재하는 사용자 이름 또는 이메일입니다.'
            return render_template('signup.html', error=error)
        else:
            role = 'user'
            new_user = User(username=username, email=email, password=hashed_password, role=role)
            await asyncio.to_thread(lambda: db.session.add(new_user))
            await asyncio.to_thread(lambda: db.session.commit())
            return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth_bp.route('/force_change_password', methods=['GET', 'POST'])
async def force_change_password():
    if 'logged_in' not in session or not session['logged_in']:
        flash("로그인이 필요합니다.", "danger")
        return redirect(url_for('auth.login'))
    
    user = await asyncio.to_thread(lambda: db.session.get(User, session['user_id']))

    if not user.force_password_reset:
        flash("비밀번호 초기화가 필요하지 않습니다.", "info")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        if new_password != confirm_new_password:
            flash("비밀번호가 일치하지 않습니다.", "danger")
            return render_template('force_change_password.html')
        user.password = ph.hash(new_password)
        user.force_password_reset = False
        await asyncio.to_thread(lambda: db.session.commit())
        flash("비밀번호가 성공적으로 변경되었습니다.", "success")
        return redirect(url_for('index'))
    return render_template('force_change_password.html')

@auth_bp.route('/change_password', methods=['POST'])
async def change_password():
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = await asyncio.to_thread(lambda: User.query.get(user_id))

    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']

    try:
        ph.verify(user.password, current_password)
    except Exception:
        password_error = '현재 비밀번호가 일치하지 않습니다.'
        return redirect(url_for('user.mypage', password_error=password_error))

    if new_password != confirm_new_password:
        password_error = '새 비밀번호가 일치하지 않습니다.'
        return redirect(url_for('user.mypage', password_error=password_error))

    user.password = ph.hash(new_password)
    await asyncio.to_thread(lambda: db.session.commit())

    password_success = '비밀번호가 성공적으로 변경되었습니다.'
    return redirect(url_for('user.mypage', password_success=password_success))

@auth_bp.route('/delete_account', methods=['POST'])
async def delete_account():
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = await asyncio.to_thread(lambda: User.query.get(user_id))
    
    password = request.form['delete_password']
    
    try:
        # 비밀번호 확인
        ph.verify(user.password, password)
        
        # 사용자 계정에 연결된 모든 데이터 삭제
        # 필요한 연관 테이블에서 데이터 삭제 (cascade 옵션으로 자동 처리되는 것 외에 필요한 것이 있다면 여기서 처리)
        
        # 사용자 데이터 삭제
        await asyncio.to_thread(lambda: db.session.delete(user))
        await asyncio.to_thread(lambda: db.session.commit())
        
        # 세션 정리
        session.clear()
        flash('계정이 성공적으로 삭제되었습니다.', 'success')
        return redirect(url_for('index'))
    
    except Exception:
        # 비밀번호 불일치 시
        flash('비밀번호가 일치하지 않습니다.', 'danger')
        return redirect(url_for('user.mypage', account_delete_error='비밀번호가 일치하지 않습니다.'))

@auth_bp.route('/logout')
async def logout():
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route('/terms')
async def terms():
    return render_template('terms.html')

@auth_bp.route('/privacy')
async def privacy():
    return render_template('privacy.html') 