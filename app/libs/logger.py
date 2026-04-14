# utf-8 -*-
import logging
import os
import re

from concurrent_log import ConcurrentTimedRotatingFileHandler

dir = os.path.dirname(os.path.dirname(__file__))


class Logger:
    def __init__(self, logger_name, folder_name, file_name, level=logging.INFO):

        # 创建一个logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)

        # 创建一个handler，用于写入日志文件
        path = os.path.join(dir, 'logs')
        if not os.path.exists(path):
            os.mkdir(path)
        log_path = os.path.join(path, folder_name)  # 指定文件输出路径
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        file_name = file_name.replace('.log', '')
        log_name = os.path.join(log_path, file_name + '.log')  # 指定输出的日志文件名

        # interval 滚动周期，
        # when="MIDNIGHT", interval=1 表示每天0点为更新点，每天生成一个文件
        # backupCount  表示日志保存个数
        file_handler = ConcurrentTimedRotatingFileHandler(
            filename=log_name, when='MIDNIGHT', interval=1, backupCount=31
        )
        file_handler.suffix = "%Y-%m-%d.log"
        # extMatch是编译好正则表达式，用于匹配日志文件名后缀
        # 需要注意的是suffix和extMatch一定要匹配的上，如果不匹配，过期日志不会被删除。
        file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
        # 定义日志输出格式
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(process)d] [%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s"
            )
        )
        self.logger.addHandler(file_handler)
        fh = logging.FileHandler(log_name, encoding='utf-8')  # 指定utf-8格式编码，避免输出的日志文本乱码
        fh.setLevel(logging.INFO)

        # 创建一个handler，用于将日志输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 定义handler的输出格式
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def get_log(self):
        """定义一个函数，回调logger实例"""
        return self.logger

logger = Logger(logger_name='view_back_api', folder_name='view_back_api_v1', file_name='api.log', level=logging.DEBUG).get_log()
logger_mq = Logger(logger_name='logger_mq', folder_name='logger_mq', file_name='logger_mq.log', level=logging.INFO).get_log()
logger_rabbit = Logger(logger_name='rabbit', folder_name='rabbit', file_name='rabbit.log', level=logging.DEBUG).get_log()
