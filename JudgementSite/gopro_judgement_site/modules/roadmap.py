import asyncio
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import db, RoadmapTask, Lecture, UserLectureProgress
from modules.utils import check_roadmap_access, check_admin, subject_slug_map

roadmap_bp = Blueprint('roadmap', __name__)

@roadmap_bp.route('/roadmap')
async def roadmap_overview():
    if not check_roadmap_access():
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    roadmap_data = []

    for slug, subject in subject_slug_map.items():
        total_lectures = await asyncio.to_thread(
            lambda: db.session.query(Lecture)
                    .join(RoadmapTask, RoadmapTask.id == Lecture.task_id)
                    .filter(RoadmapTask.subject == subject)
                    .count()
        )
        completed_lectures = await asyncio.to_thread(
            lambda: db.session.query(UserLectureProgress)
                    .join(Lecture, Lecture.id == UserLectureProgress.lecture_id)
                    .join(RoadmapTask, RoadmapTask.id == Lecture.task_id)
                    .filter(UserLectureProgress.user_id == user_id, RoadmapTask.subject == subject)
                    .count()
        )
        progress = int((completed_lectures / total_lectures * 100)) if total_lectures > 0 else 0
        roadmap_data.append({
            'subject': subject,
            'progress': progress,
            'slug': slug
        })

    return render_template('roadmap_overview.html', roadmap_data=roadmap_data)

@roadmap_bp.route('/roadmap/<slug>')
async def roadmap_subject(slug):
    if not check_roadmap_access():
        return redirect(url_for('auth.login'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    subject = subject_slug_map[slug]
    user_id = session['user_id']
    tasks = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(subject=subject).all())
    return render_template('roadmap_subject.html', subject=subject, tasks=tasks, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>')
async def roadmap_task_detail(slug, task_id):
    if not check_roadmap_access():
        return redirect(url_for('auth.login'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    subject = subject_slug_map[slug]
    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())

    lectures = await asyncio.to_thread(lambda: Lecture.query.filter_by(task_id=task_id).all())

    user_id = session['user_id']
    completed_lectures = await asyncio.to_thread(
        lambda: [lp.lecture_id for lp in UserLectureProgress.query.filter_by(user_id=user_id).all()]
    )
    
    return render_template('roadmap_task_detail.html', subject=subject, task=task, lectures=lectures, completed_lectures=completed_lectures, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>/lecture/<int:lecture_id>/toggle', methods=['POST'])
async def toggle_lecture(slug, task_id, lecture_id):
    if not check_roadmap_access():
        return redirect(url_for('auth.login'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    user_id = session['user_id']

    lecture = await asyncio.to_thread(lambda: Lecture.query.filter_by(id=lecture_id, task_id=task_id).first())
    if not lecture:
        flash('강의를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))
    
    progress = await asyncio.to_thread(lambda: UserLectureProgress.query.filter_by(user_id=user_id, lecture_id=lecture_id).first())
    
    if progress:
        await asyncio.to_thread(lambda: (db.session.delete(progress), db.session.commit()))
        flash(f'"{lecture.title}" 강의의 완료 상태를 취소했습니다.', 'success')
    else:
        await asyncio.to_thread(lambda: (db.session.add(UserLectureProgress(user_id=user_id, lecture_id=lecture_id)), db.session.commit()))
        flash(f'"{lecture.title}" 강의를 완료했습니다.', 'success')
    
    return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>/lecture/new', methods=['GET', 'POST'])
async def new_lecture(slug, task_id):
    if not check_admin():
        flash("관리자 권한이 필요합니다.", "danger")
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))
    subject = subject_slug_map.get(slug)
    if not subject:
        flash("존재하지 않는 과목입니다.", "danger")
        return redirect(url_for('roadmap.roadmap_overview'))
    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash("모든 필드를 입력하세요.", "danger")
            return redirect(url_for('roadmap.new_lecture', slug=slug, task_id=task_id))
        new_lecture = Lecture(task_id=task_id, title=title, content=content)
        await asyncio.to_thread(lambda: db.session.add(new_lecture))
        await asyncio.to_thread(lambda: db.session.commit())
        flash("새 강의가 성공적으로 추가되었습니다.", "success")
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))
    
    return render_template('new_lecture.html', task=task, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>/lecture/<int:lecture_id>/edit', methods=['GET', 'POST'])
async def edit_lecture(slug, task_id, lecture_id):
    if not check_admin():
        flash("관리자 권한이 필요합니다.", "danger")
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))
    subject = subject_slug_map.get(slug)
    if not subject:
        flash("존재하지 않는 과목입니다.", "danger")
        return redirect(url_for('roadmap.roadmap_overview'))

    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())
    lecture = await asyncio.to_thread(lambda: Lecture.query.filter_by(id=lecture_id, task_id=task_id).first_or_404())
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash("모든 필드를 입력하세요.", "danger")
            return redirect(url_for('roadmap.edit_lecture', slug=slug, task_id=task_id, lecture_id=lecture_id))
        lecture.title = title
        lecture.content = content
        await asyncio.to_thread(lambda: db.session.commit())
        flash("강의가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))
    
    return render_template('edit_lecture.html', task=task, lecture=lecture, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>/lecture/<int:lecture_id>/delete', methods=['POST'])
async def delete_lecture(slug, task_id, lecture_id):
    if not check_admin():
        flash('관리자만 접근할 수 있습니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))

    subject = subject_slug_map.get(slug)
    if not subject:
        flash("존재하지 않는 과목입니다.", "danger")
        return redirect(url_for('roadmap.roadmap_overview'))

    lecture = await asyncio.to_thread(lambda: Lecture.query.filter_by(id=lecture_id, task_id=task_id).first())
    if not lecture:
        flash('강의를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))

    await asyncio.to_thread(lambda: db.session.delete(lecture))
    await asyncio.to_thread(lambda: db.session.commit())

    flash("강의가 성공적으로 삭제되었습니다.", "success")
    return redirect(url_for('roadmap.roadmap_task_detail', slug=slug, task_id=task_id))

@roadmap_bp.route('/roadmap/<slug>/task/<int:task_id>/lecture/<int:lecture_id>')
async def lecture_detail(slug, task_id, lecture_id):
    if not check_roadmap_access():
        return redirect(url_for('auth.login'))
    subject = subject_slug_map.get(slug)
    if not subject:
        flash("존재하지 않는 과목입니다.", "danger")
        return redirect(url_for('roadmap.roadmap_overview'))
    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())
    lecture = await asyncio.to_thread(lambda: Lecture.query.filter_by(id=lecture_id, task_id=task_id).first_or_404())
    return render_template('lecture_detail.html', task=task, lecture=lecture, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/new', methods=['GET', 'POST'])
async def new_roadmap_task(slug):
    if not check_admin():
        return redirect(url_for('roadmap.roadmap_overview'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    subject = subject_slug_map[slug]
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if not title or not description:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('roadmap.new_roadmap_task', slug=slug))
        new_task = RoadmapTask(subject=subject, title=title, description=description)
        await asyncio.to_thread(lambda: db.session.add(new_task))
        await asyncio.to_thread(lambda: db.session.commit())
        flash('새 로드맵 항목이 생성되었습니다.', 'success')
        return redirect(url_for('roadmap.roadmap_subject', slug=slug))
    return render_template('new_roadmap_task.html', subject=subject, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/edit/<int:task_id>', methods=['GET', 'POST'])
async def edit_roadmap_task(slug, task_id):
    if not check_admin():
        return redirect(url_for('roadmap.roadmap_overview'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    subject = subject_slug_map[slug]
    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if not title or not description:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('roadmap.edit_roadmap_task', slug=slug, task_id=task_id))
        task.title = title
        task.description = description
        await asyncio.to_thread(lambda: db.session.commit())
        flash('로드맵 항목이 수정되었습니다.', 'success')
        return redirect(url_for('roadmap.roadmap_subject', slug=slug))
    return render_template('edit_roadmap_task.html', task=task, subject=subject, slug=slug)

@roadmap_bp.route('/roadmap/<slug>/delete/<int:task_id>', methods=['POST'])
async def delete_roadmap_task(slug, task_id):
    if not check_admin():
        return redirect(url_for('roadmap.roadmap_overview'))
    if slug not in subject_slug_map:
        flash('존재하지 않는 과목입니다.', 'danger')
        return redirect(url_for('roadmap.roadmap_overview'))
    subject = subject_slug_map[slug]
    task = await asyncio.to_thread(lambda: RoadmapTask.query.filter_by(id=task_id, subject=subject).first_or_404())
    await asyncio.to_thread(lambda: db.session.delete(task))
    await asyncio.to_thread(lambda: db.session.commit())
    flash('로드맵 항목이 삭제되었습니다.', 'success')
    return redirect(url_for('roadmap.roadmap_subject', slug=slug)) 