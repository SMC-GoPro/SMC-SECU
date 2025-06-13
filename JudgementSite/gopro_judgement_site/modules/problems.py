import asyncio
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from database import db, Problem, UserProblemAttempt, ProblemSolveLog, User
from modules.utils import check_admin, normalize_output, calculate_score
from judge0 import run_judge0_code

problems_bp = Blueprint('problems', __name__)

@problems_bp.route('/problem')
async def problem_list():
    user_id = session.get('user_id')
    difficulty = request.args.get('difficulty')
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    def fetch_problems():
        query = db.session.query(
            Problem,
            func.count(UserProblemAttempt.id).label('total_attempts'),
            func.sum(UserProblemAttempt.is_correct.cast(db.Integer)).label('correct_attempts')
        ).outerjoin(
            UserProblemAttempt, Problem.id == UserProblemAttempt.problem_id
        ).group_by(Problem.id)

        if difficulty:
            query = query.filter(Problem.difficulty == difficulty)
        if search_query:
            query = query.filter(Problem.title.ilike(f'%{search_query}%'))

        paginated_problems = query.order_by(Problem.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        problem_data = []
        for problem, total_attempts, correct_attempts in paginated_problems.items:
            correct_rate = int((correct_attempts / total_attempts * 100)) if total_attempts > 0 else 0
            user_attempt = None
            if user_id:
                user_attempt = UserProblemAttempt.query.filter_by(user_id=user_id, problem_id=problem.id).first()
            if user_attempt:
                status_icon = "fa-check-circle" if user_attempt.is_correct else "fa-times-circle"
            else:
                status_icon = "fa-question-circle"
            problem_data.append({
                'id': problem.id,
                'title': problem.title,
                'author': problem.author,
                'difficulty': problem.difficulty,
                'correct_rate': correct_rate,
                'status_icon': status_icon
            })
        return problem_data, paginated_problems.pages

    problem_data, total_pages = await asyncio.to_thread(fetch_problems)

    return render_template('problem_list.html',
                           problems=problem_data,
                           selected_difficulty=difficulty,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query)

@problems_bp.route('/problem/new', methods=['GET', 'POST'])
async def problem_new():
    if not check_admin():
        flash('접근 권한이 없습니다.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        difficulty = request.form['difficulty']
        answer = request.form['answer']
        required_vars = request.form.get('required_vars', '').strip()

        new_problem = Problem(
            title=title,
            description=description,
            author=session['username'],
            difficulty=difficulty,
            answer=answer,
            required_vars=required_vars
        )
        await asyncio.to_thread(lambda: db.session.add(new_problem))
        await asyncio.to_thread(lambda: db.session.commit())
        return redirect(url_for('problems.problem_list'))
    return render_template('problem_new.html')

@problems_bp.route('/problem/<int:id>')
async def problem_detail(id):
    def fetch_detail():
        problem = Problem.query.get_or_404(id)
        total_attempts = UserProblemAttempt.query.filter_by(problem_id=id).count()
        correct_attempts = UserProblemAttempt.query.filter_by(problem_id=id, is_correct=True).count()
        correct_rate = int((correct_attempts / total_attempts * 100)) if total_attempts > 0 else 0
        return problem, correct_rate

    problem, correct_rate = await asyncio.to_thread(fetch_detail)
    problem_dict = {
        'id': problem.id,
        'title': problem.title,
        'author': problem.author,
        'difficulty': problem.difficulty,
        'description': problem.description,
        'correct_rate': correct_rate
    }
    return render_template('problem_detail.html', problem=problem_dict)

@problems_bp.route('/problem/<int:id>/edit', methods=['GET', 'POST'])
async def edit_problem(id):
    if not check_admin():
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('problems.problem_detail', id=id))
    
    problem = await asyncio.to_thread(lambda: Problem.query.get_or_404(id))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        difficulty = request.form['difficulty']
        answer = request.form['answer']
        required_vars = request.form.get('required_vars', '').strip()

        problem.title = title
        problem.description = description
        problem.difficulty = difficulty
        problem.answer = answer
        problem.required_vars = required_vars
        await asyncio.to_thread(lambda: db.session.commit())
        flash('문제가 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('problems.problem_detail', id=id))
    
    return render_template('edit_problem.html', problem=problem)

@problems_bp.route('/problem/<int:id>/delete', methods=['POST'])
async def delete_problem(id):
    if not check_admin():
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('problems.problem_detail', id=id))
    
    problem = await asyncio.to_thread(lambda: Problem.query.get_or_404(id))
    await asyncio.to_thread(lambda: UserProblemAttempt.query.filter_by(problem_id=id).delete())
    await asyncio.to_thread(lambda: ProblemSolveLog.query.filter_by(problem_id=id).delete())
    await asyncio.to_thread(lambda: db.session.delete(problem))
    await asyncio.to_thread(lambda: db.session.commit())
    
    flash('문제가 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('problems.problem_list'))

@problems_bp.route('/problem/<int:id>/solve', methods=['GET', 'POST'])
async def problem_solve(id):
    if 'logged_in' not in session:
        flash('문제를 풀기 위해서는 로그인이 필요합니다.')
        return redirect(url_for('auth.login'))

    problem = await asyncio.to_thread(lambda: Problem.query.get_or_404(id))
    user_id = session['user_id']
    user = await asyncio.to_thread(lambda: db.session.get(User, user_id))
    if not user:
        flash('사용자 정보를 불러올 수 없습니다.')
        return redirect(url_for('auth.login'))

    # 문제 작성자가 자기 자신이면 풀 수 없게
    if problem.author == user.username:
        flash('자신이 만든 문제는 풀 수 없습니다.')
        return redirect(url_for('problems.problem_list'))

    # 이미 정답 맞힌 문제는 다시 맞힐 수 없게
    existing_correct_attempt = await asyncio.to_thread(
        lambda: UserProblemAttempt.query.filter_by(user_id=user_id, problem_id=id, is_correct=True).first()
    )
    if existing_correct_attempt:
        flash('이미 이 문제를 맞추셨습니다.')
        return redirect(url_for('problems.problem_list'))
    
    code = ""
    user_output = ""
    result_message = ""
    language = "python"
    action = ""

    if request.method == 'POST':
        code = request.form['code']
        language = request.form['language']
        action = request.form.get('action', 'run')
        stdin = request.form.get('stdin', '')  # 사용자 입력값 받기

        # stdin 파라미터 추가하여 Judge0 코드 실행
        execution_result, error = await run_judge0_code(code, language, stdin)
        user_output = error if error else execution_result

        if action == 'submit':
            correct_answer = problem.answer.strip()
            if normalize_output(user_output) == normalize_output(correct_answer):
                result_message = "정답입니다!"
                is_correct = True
                # 점수 증가
                score_to_add = calculate_score(problem.difficulty)
                user.score += score_to_add
                await asyncio.to_thread(lambda: db.session.add(user))
                await asyncio.to_thread(lambda: db.session.commit())
            else:
                result_message = "틀렸습니다."
                is_correct = False

            new_attempt = UserProblemAttempt(
                user_id=user_id,
                problem_id=problem.id,
                is_correct=is_correct
            )
            await asyncio.to_thread(lambda: db.session.add(new_attempt))
            await asyncio.to_thread(lambda: db.session.commit())

            new_log = ProblemSolveLog(
                user_id=user_id,
                problem_id=problem.id,
                language=language,
                code=code,
                output=user_output,
                result_message=result_message
            )
            await asyncio.to_thread(lambda: db.session.add(new_log))
            await asyncio.to_thread(lambda: db.session.commit())

        return render_template('problem_solve.html',
                               problem=problem,
                               code=code,
                               language=language,
                               user_output=user_output,
                               result_message=result_message,
                               action=action)

    return render_template('problem_solve.html',
                           problem=problem,
                           code=code,
                           language=language,
                           user_output=user_output,
                           result_message=result_message,
                           action=action) 