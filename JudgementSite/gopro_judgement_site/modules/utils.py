import os
import re
import imghdr
import mimetypes
from flask import flash, session, redirect, url_for
from werkzeug.utils import secure_filename
import uuid

# Constants
UPLOAD_FOLDER = None  # Will be set in app.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = None  # Will be set in app.py

# Subject mapping
subject_slug_map = {
    "c": "C언어",
    "python": "파이썬",
    "js": "자바스크립트",
    "html": "HTML",
    "css": "CSS",
    "nodejs": "Node JS"
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not '.' in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    return True

def validate_image(stream):
    """Validate image file content"""
    try:
        header = stream.read(512)
        stream.seek(0)
        format = imghdr.what(None, header)
        if not format:
            return None
        
        # 추가적인 MIME 타입 검증
        mime_type = mimetypes.guess_type(f'image.{format}')[0]
        allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if mime_type not in allowed_mime_types:
            return None
            
        return '.' + (format if format != 'jpeg' else 'jpg')
    except Exception:
        return None

def check_admin():
    """Check if current user is admin"""
    if 'logged_in' not in session or not session['logged_in'] or session.get('role') != 'admin':
        flash('관리자만 접근할 수 있습니다.', 'danger')
        return False
    return True

def check_roadmap_access():
    """Check if user has access to roadmap feature"""
    if 'logged_in' not in session or not session['logged_in'] or session.get('role') not in ['gopro', 'admin']:
        flash('로드맵 기능은 gopro 또는 admin 사용자만 이용할 수 있습니다.', 'danger')
        return False
    return True

def normalize_output(output):
    """Normalize output for comparison"""
    # 출력에서 공백/개행 제거 후 소문자로 통일
    output = re.sub(r'\s+', '', output)
    return output.lower()

def calculate_score(difficulty):
    """Calculate score based on problem difficulty"""
    base_score_dict = {
        1: 10,
        2: 20,
        3: 30,
        4: 40,
        5: 50
    }
    return base_score_dict.get(int(difficulty), 0)

def save_uploaded_image(file):
    """Save uploaded image and return the URL"""
    original_filename = secure_filename(file.filename)
    unique_filename = str(uuid.uuid4()) + "_" + original_filename
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    return unique_filename 