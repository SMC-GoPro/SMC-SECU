import asyncio
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from database import db, Post, Comment

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/posts')
async def posts():
    search_query = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    def get_pagination():
        query = db.session.query(Post, func.count(Comment.id).label('comment_count')).outerjoin(Comment, Post.id == Comment.post_id).group_by(Post.id)
        if search_query:
            query = query.filter(Post.title.ilike(f'%{search_query}%'))
        return query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    pagination = await asyncio.to_thread(get_pagination)
    
    posts_data = [
        {
            'id': post.id,
            'title': post.title,
            'author': post.author,
            'created_at': post.created_at,
            'comment_count': comment_count
        }
        for post, comment_count in pagination.items
    ]

    return render_template('posts.html', posts=posts_data, page=page, total_pages=pagination.pages, total_posts=pagination.total)

@posts_bp.route('/new_post', methods=['GET', 'POST'])
async def new_post():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']
        
        # 입력값 검증
        if len(title) < 1 or len(title) > 255:
            flash('제목은 1-255자 사이여야 합니다.', 'danger')
            return render_template('new_post.html', username=session['username'], title=title, content=content)
        
        if len(content) < 1 or len(content) > 50000:
            flash('내용은 1-50000자 사이여야 합니다.', 'danger')
            return render_template('new_post.html', username=session['username'], title=title, content=content)

        new_post_obj = Post(title=title, content=content, author=author)
        await asyncio.to_thread(lambda: db.session.add(new_post_obj))
        await asyncio.to_thread(lambda: db.session.commit())
        return redirect(url_for('posts.posts'))

    return render_template('new_post.html', username=session['username'])

@posts_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
async def view_post(post_id):
    post = await asyncio.to_thread(lambda: Post.query.get_or_404(post_id))
    comments = await asyncio.to_thread(lambda: Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.asc()).all())

    if request.method == 'POST':
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('auth.login'))

        author = session['username']
        content = request.form['content']
        parent_id = request.form.get('parent_id')  
        
        # 입력값 검증
        if len(content.strip()) < 1:
            flash('댓글 내용을 입력해주세요.', 'danger')
            return redirect(url_for('posts.view_post', post_id=post_id))
            
        if len(content) > 1000:
            flash('댓글 내용은 1000자를 초과할 수 없습니다.', 'danger')
            return redirect(url_for('posts.view_post', post_id=post_id))

        new_comment = Comment(post_id=post_id, author=author, content=content, parent_id=parent_id if parent_id else None)
        await asyncio.to_thread(lambda: db.session.add(new_comment))
        await asyncio.to_thread(lambda: db.session.commit())
        return redirect(url_for('posts.view_post', post_id=post_id))

    return render_template('view_post.html', post=post, comments=comments, username=session.get('username'))

@posts_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
async def edit_post(post_id):
    post = await asyncio.to_thread(lambda: Post.query.get_or_404(post_id))

    if post.author != session.get('username') and session.get('role') != 'admin':
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        post.title = new_title
        post.content = new_content
        await asyncio.to_thread(lambda: db.session.commit())

        flash('게시물이 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('posts.view_post', post_id=post_id))

    return render_template('edit_post.html', post=post)

@posts_bp.route('/post/<int:post_id>/delete', methods=['POST'])
async def delete_post(post_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('auth.login'))
        
    post = await asyncio.to_thread(lambda: Post.query.get_or_404(post_id))

    if post.author != session.get('username') and session.get('role') != 'admin':
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))

    await asyncio.to_thread(lambda: db.session.delete(post))
    await asyncio.to_thread(lambda: db.session.commit())

    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('posts.posts'))

@posts_bp.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
async def edit_comment(comment_id):
    comment = await asyncio.to_thread(lambda: Comment.query.get_or_404(comment_id))

    if comment.author != session.get('username'):
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    if request.method == 'POST':
        new_content = request.form['content']
        comment.content = new_content
        await asyncio.to_thread(lambda: db.session.commit())
        flash('댓글이 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    return render_template('edit_comment.html', comment=comment)

@posts_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
async def delete_comment(comment_id):
    comment = await asyncio.to_thread(lambda: Comment.query.get_or_404(comment_id))

    if comment.author != session.get('username') and session.get('role') != 'admin':
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    await asyncio.to_thread(lambda: db.session.delete(comment))
    await asyncio.to_thread(lambda: db.session.commit())
    
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('posts.view_post', post_id=comment.post_id)) 