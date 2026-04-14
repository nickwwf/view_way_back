# coding: utf-8
from flask import request

from app.libs.define_print import DefinePrint
from app.libs.error_code import Success, ServerError
from app.libs.file_helper import FileHelper
from app.libs.token_auth import login_required

api = DefinePrint('task_image')

@api.route('/upload_multiple', methods=['POST'])
@login_required
def upload_multiple_images():
    files = request.files.getlist('files')
    sub_folder = request.form.get('sub_folder', 'uploads')

    if not files or len(files) == 0:
        return ServerError(msg='No files provided')

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    uploaded_files = []
    failed_files = []

    for file in files:
        if not file.filename:
            continue
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            failed_files.append({
                'filename': file.filename,
                'error': f'File type not allowed: {file_ext}'
            })
            continue

        try:
            result = FileHelper.upload_file(file, sub_folder, make_thumbnail=True)
            uploaded_files.append({
                'filename': file.filename,
                'file_id': result['file_id'],
                'file_path': result['file_path'],
                'file_url': result['file_url'],
                'thumbnail_url': result.get('thumbnail_url'),
                'file_size': result['file_size']
            })
        except Exception as e:
            failed_files.append({
                'filename': file.filename,
                'error': str(e)
            })

    return Success(data={
        'total': len(files),
        'success_count': len(uploaded_files),
        'failed_count': len(failed_files),
        'uploaded_files': uploaded_files,
        'failed_files': failed_files
    })