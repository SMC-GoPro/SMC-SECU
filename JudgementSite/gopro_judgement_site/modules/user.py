import asyncio
import math
import json
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from database import db, User, UserProblemAttempt, Problem, ProblemSolveLog, JeongchgiQuizResult

user_bp = Blueprint('user', __name__)

@user_bp.route('/rank')
async def rank():
    users = await asyncio.to_thread(lambda: User.query.order_by(User.score.desc()).limit(100).all())
    users_list = [{"username": user.username, "score": user.score} for user in users]
    return render_template('rank.html', users=users_list)

@user_bp.route('/mypage')
async def mypage():
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = await asyncio.to_thread(lambda: User.query.get(user_id))
    if not user:
        flash('사용자 정보를 불러올 수 없습니다.', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    per_page = 10

    attempts_query = db.session.query(
        UserProblemAttempt, Problem.title
    ).join(Problem, UserProblemAttempt.problem_id == Problem.id).filter(UserProblemAttempt.user_id == user_id)

    total_attempts = await asyncio.to_thread(lambda: attempts_query.count())
    attempts = await asyncio.to_thread(
        lambda: attempts_query.order_by(UserProblemAttempt.id.desc()).limit(per_page).offset((page - 1) * per_page).all()
    )
    total_pages = math.ceil(total_attempts / per_page)

    # Get Jeongchgi quiz results
    quiz_results = await asyncio.to_thread(
        lambda: JeongchgiQuizResult.query.filter_by(user_id=user_id).order_by(JeongchgiQuizResult.attempted_at.desc()).all()
    )

    # Get any flash messages
    password_error = request.args.get('password_error')
    password_success = request.args.get('password_success')
    account_delete_error = request.args.get('account_delete_error')

    return render_template('mypage.html',
                           username=user.username,
                           user_score=user.score,
                           attempts=attempts,
                           quiz_results=quiz_results,
                           page=page,
                           total_pages=total_pages,
                           password_error=password_error,
                           password_success=password_success,
                           account_delete_error=account_delete_error)

@user_bp.route('/mypage/attempt/<int:attempt_id>')
async def mypage_attempt_detail(attempt_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))

    attempt = await asyncio.to_thread(lambda: UserProblemAttempt.query.get_or_404(attempt_id))
    if attempt.user_id != session.get('user_id'):
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('user.mypage'))

    problem = await asyncio.to_thread(lambda: Problem.query.get_or_404(attempt.problem_id))
    logs = await asyncio.to_thread(
        lambda: ProblemSolveLog.query.filter_by(user_id=attempt.user_id, problem_id=attempt.problem_id)
                                     .order_by(ProblemSolveLog.timestamp.desc())
                                     .all()
    )
    return render_template('mypage_attempt_detail.html', attempt=attempt, problem=problem, logs=logs)

@user_bp.route('/mypage/jeongchgi_result/<int:result_id>')
async def mypage_jeongchgi_result(result_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
    
    result = await asyncio.to_thread(lambda: JeongchgiQuizResult.query.get_or_404(result_id))
    if result.user_id != session.get('user_id'):
         flash('접근 권한이 없습니다.', 'danger')
         return redirect(url_for('user.mypage'))
    
    overall_results = json.loads(result.results)
    return render_template('mypage_jeongchgi_result.html',
                           result=result,
                           overall_results=overall_results) 