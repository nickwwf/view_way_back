SQLALCHEMY_DATABASE_URI: str = 'mysql+pymysql://flysee:flysee2021@192.168.10.187:3306/fs_uav_patrol'

SECRET_KEY = 'view_back_secret_key1'
SQLALCHEMY_TRACK_MODIFICATIONS = True

REDIS_HOST = "192.168.10.51"  # redis数据库地址
REDIS_PORT = 6379  # redis 端口号
REDIS_DB = 7  # 数据库名

# RABBITMQ
RABBIT_HOST = '192.168.10.187'
RABBIT_PORT = 5672
RABBIT_USERNAME = 'flysee'
RABBIT_PASSWD = 'flysee'

# MinIO
MINIO_ENDPOINT = '192.168.10.187:39010'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = 'hjqweqwrl'
MINIO_BUCKET = 'viewwaypicture'
MINIO_SECURE = False
