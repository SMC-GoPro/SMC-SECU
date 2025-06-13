import asyncio
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import db, Announcement
from modules.utils import check_admin

news_bp = Blueprint('news', __name__)

@news_bp.route('/news')
async def news():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    def get_pagination():
        if search_query:
            return Announcement.query.filter(Announcement.title.ilike(f'%{search_query}%'))\
                                       .order_by(Announcement.id.desc())\
                                       .paginate(page=page, per_page=per_page, error_out=False)
        else:
            return Announcement.query.order_by(Announcement.id.desc())\
                                       .paginate(page=page, per_page=per_page, error_out=False)

    pagination = await asyncio.to_thread(get_pagination)
    posts = pagination.items
    total_pages = pagination.pages

    return render_template('news.html', posts=posts, page=page, total_pages=total_pages)

@news_bp.route('/news/new', methods=['GET', 'POST'])
async def new_news():
    if 'logged_in' not in session or session.get('role') != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('news.news'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        author = '운영자'
        date = datetime.now().date()

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('news.new_news'))

        new_announcement = Announcement(title=title, author=author, content=content, date=date, category=category)
        await asyncio.to_thread(lambda: db.session.add(new_announcement))
        await asyncio.to_thread(lambda: db.session.commit())

        flash('새 공지가 성공적으로 등록되었습니다!', 'success')
        return redirect(url_for('news.news'))

    return render_template('new_news.html')

@news_bp.route('/news/<int:id>')
async def view_news(id):
    post = await asyncio.to_thread(lambda: Announcement.query.get_or_404(id))
    return render_template('view_news.html', post=post)

@news_bp.route('/news/<int:id>/edit', methods=['GET', 'POST'])
async def edit_news(id):
    if not check_admin():
        return redirect(url_for('news.news'))

    post = await asyncio.to_thread(lambda: Announcement.query.get_or_404(id))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date = datetime.now().date()

        if not title or not content:
            flash('모든 필드를 입력하세요.', 'danger')
            return redirect(url_for('news.edit_news', id=id))

        post.title = title
        post.content = content
        post.date = date

        await asyncio.to_thread(lambda: db.session.add(post))
        await asyncio.to_thread(lambda: db.session.commit())

        flash('공지사항이 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('news.view_news', id=id))

    return render_template('edit_news.html', post=post)

@news_bp.route('/news/<int:id>/delete', methods=['POST'])
async def delete_news(id):
    if not check_admin():
        return redirect(url_for('news.news'))

    post = await asyncio.to_thread(lambda: Announcement.query.get_or_404(id))
    await asyncio.to_thread(lambda: db.session.delete(post))
    await asyncio.to_thread(lambda: db.session.commit())

    flash('공지사항이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('news.news')) 