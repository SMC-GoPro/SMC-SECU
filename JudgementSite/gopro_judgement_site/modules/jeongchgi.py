import asyncio
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import db, JeongchgiProblem, JeongchgiAttempt, JeongchgiQuizResult

jeongchgi_bp = Blueprint('jeongchgi', __name__)

@jeongchgi_bp.route('/jeongchgi')
async def jeongchgi_index():
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
    # 연도만 distinct하게 추출
    years = await asyncio.to_thread(lambda: db.session.query(JeongchgiProblem.year)
                                      .distinct().order_by(JeongchgiProblem.year.desc()).all())
    years = [year for (year,) in years]
    return render_template('jeongchgi_index.html', years=years)

@jeongchgi_bp.route('/jeongchgi/<int:year>')
async def jeongchgi_year(year):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
    # 회차만 추출
    sessions = await asyncio.to_thread(lambda: db.session.query(JeongchgiProblem.session)
                                         .filter_by(year=year)
                                         .distinct().order_by(JeongchgiProblem.session).all())
    sessions = [s for (s,) in sessions]
    return render_template('jeongchgi_year.html', year=year, sessions=sessions)

@jeongchgi_bp.route('/jeongchgi/quiz/<int:year>/<exam_session>', methods=['GET', 'POST'])
async def jeongchgi_quiz_paginated(year, exam_session):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = await asyncio.to_thread(lambda: JeongchgiProblem.query.filter_by(year=year, session=exam_session)
                                         .order_by(JeongchgiProblem.id.asc())
                                         .paginate(page=page, per_page=per_page, error_out=False))
    problems = pagination.items

    # 전체 문제 목록과 subject_pages 계산
    all_problems = await asyncio.to_thread(lambda: JeongchgiProblem.query.filter_by(year=year, session=exam_session)
                                             .order_by(JeongchgiProblem.id.asc()).all())
    subject_pages = {}
    for i, p in enumerate(all_problems):
        if p.subject not in subject_pages:
            subject_pages[p.subject] = {
                'page': (i // per_page) + 1,
                'problem_id': p.id
            }

    # session에 저장된 답안 불러오기
    if 'jeongchgi_answers' not in session:
        session['jeongchgi_answers'] = {}
    answers = session.get('jeongchgi_answers')

    if request.method == 'POST':
        # 현재 페이지의 답안을 업데이트
        for p in problems:
            selected = request.form.get(f'selected_option_{p.id}')
            if selected:
                answers[str(p.id)] = int(selected)
        # 만약 최종 제출 시 hidden 입력(all_answers)에 값이 있다면 localStorage의 전체 답안을 사용
        if request.form.get('all_answers'):
            answers = json.loads(request.form.get('all_answers'))
        session['jeongchgi_answers'] = answers

        if page < pagination.pages:
            return redirect(url_for('jeongchgi.jeongchgi_quiz_paginated', year=year, exam_session=exam_session, page=page+1))
        else:
            # 마지막 페이지 – 채점 진행
            correct_count = 0
            overall_results = {}
            for idx, p in enumerate(all_problems, start=1):
                user_answer = answers.get(str(p.id))
                if user_answer == p.correct_option:
                    correct_count += 1
                    overall_results[p.id] = {
                        'result': '정답',
                        'correct_answer': getattr(p, f'option_{p.correct_option}'),
                        'user_answer': user_answer,
                        'global_index': idx
                    }
                else:
                    overall_results[p.id] = {
                        'result': '오답',
                        'correct_answer': getattr(p, f'option_{p.correct_option}'),
                        'user_answer': user_answer,
                        'global_index': idx
                    }
            total = len(all_problems)
            # 결과를 JSON으로 저장하고 DB에 기록
            result_json = json.dumps(overall_results)
            new_result = JeongchgiQuizResult(
                user_id=session['user_id'],
                year=year,
                exam_session=exam_session,
                results=result_json,
                correct_count=correct_count,
                total=total
            )
            await asyncio.to_thread(lambda: (db.session.add(new_result), db.session.commit()))
            session.pop('jeongchgi_answers', None)
            # 최종 결과 페이지로 리디렉션 (mypage 내 기록 상세 페이지)
            return redirect(url_for('user.mypage_jeongchgi_result', result_id=new_result.id))
    return render_template('jeongchgi_quiz_paginated.html',
                           year=year,
                           exam_session=exam_session,
                           problems=problems,
                           pagination=pagination,
                           answers=answers,
                           subject_pages=subject_pages)

@jeongchgi_bp.route('/jeongchgi/problem/<int:problem_id>', methods=['GET'])
async def jeongchgi_problem_detail(problem_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
    problem = await asyncio.to_thread(lambda: JeongchgiProblem.query.get_or_404(problem_id))
    user_answer = request.args.get('user_answer', type=int)
    correct_answer = getattr(problem, f'option_{problem.correct_option}')
    return render_template('jeongchgi_problem_detail.html',
                           problem=problem,
                           user_answer=user_answer,
                           correct_answer=correct_answer) 