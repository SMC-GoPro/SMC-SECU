import asyncio
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_
from database import db, User, ProblemSolveLog, Problem
from modules.utils import check_admin

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users')
async def admin_users():
    if not check_admin():
        return redirect(url_for('index'))
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Search query
    search_query = request.args.get('search', '')
    
    # Get total users count first
    if search_query:
        total_users = await asyncio.to_thread(lambda: User.query.filter(
            or_(User.username.ilike(f'%{search_query}%'), User.email.ilike(f'%{search_query}%'))
        ).count())
    else:
        total_users = await asyncio.to_thread(lambda: User.query.count())
    
    # Calculate total pages
    total_pages = (total_users + per_page - 1) // per_page
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    # Get paginated users
    if search_query:
        users = await asyncio.to_thread(lambda: User.query.filter(
            or_(User.username.ilike(f'%{search_query}%'), User.email.ilike(f'%{search_query}%'))
        ).limit(per_page).offset((page - 1) * per_page).all())
    else:
        users = await asyncio.to_thread(lambda: User.query.limit(per_page).offset((page - 1) * per_page).all())
    
    # Calculate display range for pagination info
    start_idx = (page - 1) * per_page + 1 if total_users > 0 else 0
    end_idx = min(page * per_page, total_users)
    
    return render_template('admin_users.html', 
                           users=users, 
                           search_query=search_query,
                           page=page, 
                           per_page=per_page,
                           total_users=total_users,
                           total_pages=total_pages,
                           start_idx=start_idx,
                           end_idx=end_idx)

@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
async def admin_delete_user(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    await asyncio.to_thread(lambda: ProblemSolveLog.query.filter_by(user_id=user_id).delete())
    if user.id == session.get('user_id'):
        flash('자신의 계정을 삭제할 수 없습니다.', 'danger')
        return redirect(url_for('admin.admin_users'))
    await asyncio.to_thread(lambda: db.session.delete(user))
    await asyncio.to_thread(lambda: db.session.commit())
    flash('회원이 삭제되었습니다.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/role/<int:user_id>', methods=['POST'])
async def admin_update_role(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    new_role = request.form.get('new_role')
    if new_role not in ['user', 'gopro', 'admin']:
        flash('유효한 역할이 아닙니다.', 'danger')
        return redirect(url_for('admin.admin_users'))

    user.role = new_role
    await asyncio.to_thread(lambda: db.session.commit())

    if user.id == session.get('user_id'):
        session['role'] = new_role

    flash('회원 역할이 업데이트되었습니다.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/score/<int:user_id>', methods=['POST'])
async def admin_update_score(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    new_score = request.form.get('new_score')
    try:
        new_score = int(new_score)
    except (ValueError, TypeError):
        flash('유효한 점수를 입력하세요.', 'danger')
        return redirect(url_for('admin.admin_users'))
    user.score = new_score
    await asyncio.to_thread(lambda: db.session.commit())
    flash('회원 점수가 업데이트되었습니다.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/reset/<int:user_id>', methods=['POST'])
async def admin_reset_password(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    user.force_password_reset = True
    await asyncio.to_thread(lambda: db.session.commit())
    flash(f'{user.username}님의 비밀번호 초기화가 설정되었습니다. 다음 로그인 시 비밀번호를 변경해주세요.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/suspend/<int:user_id>', methods=['POST'])
async def admin_suspend_user(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    if user.id == session.get('user_id'):
        flash('자신의 계정을 정지할 수 없습니다.', 'danger')
        return redirect(url_for('admin.admin_users'))
    user.is_suspended = True
    await asyncio.to_thread(lambda: db.session.commit())
    flash(f'{user.username}님의 계정이 정지되었습니다.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/unsuspend/<int:user_id>', methods=['POST'])
async def admin_unsuspend_user(user_id):
    if not check_admin():
        return redirect(url_for('index'))
    user = await asyncio.to_thread(lambda: User.query.get_or_404(user_id))
    user.is_suspended = False
    await asyncio.to_thread(lambda: db.session.commit())
    flash(f'{user.username}님의 계정 정지가 해제되었습니다.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/logs')
async def admin_logs():
    if not check_admin():
        return redirect(url_for('index'))
    search_username = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)

    def get_pagination():
        query = ProblemSolveLog.query
        if search_username:
            query = query.join(User).filter(User.username.ilike(f"%{search_username}%"))
        query = query.order_by(ProblemSolveLog.timestamp.desc())
        return query.paginate(page=page, per_page=10, error_out=False)

    pagination = await asyncio.to_thread(get_pagination)
    logs = pagination.items

    def is_suspicious(code):
        lines = code.splitlines()
        found_print = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 간단 예시: 모두 print()만 있으면 의심 없음
            if not re.match(r'^print\(.*\)$', line):
                return False
            else:
                found_print = True
        return found_print

    for log in logs:
        log.is_suspicious = is_suspicious(log.code)
    return render_template('admin_logs.html', logs=logs, pagination=pagination)

@admin_bp.route('/admin/logs/<int:log_id>')
async def admin_log_detail(log_id):
    if not check_admin():
        return redirect(url_for('index'))
    log = await asyncio.to_thread(lambda: ProblemSolveLog.query.get_or_404(log_id))
    problem = await asyncio.to_thread(lambda: Problem.query.get(log.problem_id))
    return render_template('log_detail.html', log=log, problem=problem) 