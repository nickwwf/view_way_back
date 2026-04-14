# coding: utf-8
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image

from flask import current_app
from minio import Minio
from werkzeug.datastructures import FileStorage

from app.libs.error_code import ServerError


class FileHelper:

    @staticmethod
    def _get_client():
        cfg = current_app.config
        return Minio(
            cfg['MINIO_ENDPOINT'],
            access_key=cfg['MINIO_ACCESS_KEY'],
            secret_key=cfg['MINIO_SECRET_KEY'],
            secure=cfg.get('MINIO_SECURE', False)
        )

    @staticmethod
    def upload_file(file: FileStorage, sub_folder: str = 'uploads', make_thumbnail: bool = False) -> dict:
        if not file or not isinstance(file, FileStorage):
            raise ServerError(msg='Invalid file')

        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

        if file_ext not in allowed_extensions:
            raise ServerError(msg=f'File type not allowed. Allowed: {", ".join(allowed_extensions)}')

        data = file.read()
        return FileHelper.upload_bytes(data, file_ext, sub_folder, make_thumbnail, original_filename=file.filename, content_type=file.content_type)

    @staticmethod
    def upload_bytes(data: bytes, file_ext: str, sub_folder: str = 'uploads', make_thumbnail: bool = False, original_filename: str = None, content_type: str = None) -> dict:
        if not data:
            raise ServerError(msg='Empty data')

        file_id = str(uuid.uuid4().hex)
        date_path = datetime.now().strftime('%Y%m%d')
        object_name = f"{sub_folder}/{date_path}/{file_id}.{file_ext}"

        file_size = len(data)

        client = FileHelper._get_client()
        bucket = current_app.config['MINIO_BUCKET']

        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        client.put_object(bucket, object_name, BytesIO(data), file_size,
                          content_type=content_type or 'application/octet-stream')

        endpoint = current_app.config['MINIO_ENDPOINT']
        secure = current_app.config.get('MINIO_SECURE', False)
        scheme = 'https' if secure else 'http'
        file_url = f"{scheme}://{endpoint}/{bucket}/{object_name}"

        result = {
            'file_id': file_id,
            'file_path': object_name,
            'file_url': file_url,
            'original_filename': original_filename,
            'file_size': file_size,
            'file_ext': file_ext
        }

        if make_thumbnail:
            try:
                thumbnail_data = FileHelper.generate_thumbnail(data, file_ext)
                thumb_object_name = f"{sub_folder}/{date_path}/{file_id}_thumb.{file_ext}"
                client.put_object(bucket, thumb_object_name, BytesIO(thumbnail_data), len(thumbnail_data),
                                  content_type=content_type or 'application/octet-stream')
                result['thumbnail_url'] = f"{scheme}://{endpoint}/{bucket}/{thumb_object_name}"
                result['thumbnail_path'] = thumb_object_name
            except Exception as e:
                current_app.logger.error(f"Generate thumbnail error: {str(e)}")
                result['thumbnail_url'] = None

        return result

    @staticmethod
    def generate_thumbnail(image_data: bytes, file_ext: str, size=(200, 200)) -> bytes:
        img = Image.open(BytesIO(image_data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        img.thumbnail(size)
        thumb_io = BytesIO()
        
        save_format = 'JPEG' if file_ext.lower() in ['jpg', 'jpeg'] else file_ext.upper()
        if save_format == 'JPG': save_format = 'JPEG'
        
        img.save(thumb_io, format=save_format)
        return thumb_io.getvalue()

    @staticmethod
    def delete_file(file_path: str) -> bool:
        try:
            client = FileHelper._get_client()
            bucket = current_app.config['MINIO_BUCKET']
            client.remove_object(bucket, file_path)
            return True
        except Exception as e:
            current_app.logger.exception(str(e))
            return False
