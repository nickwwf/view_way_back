#!/usr/bin/env python
import logging
import threading
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.env import load_conf


class DBSessionFactory:
    """
    定时任务专用数据库连接管理器
    使用连接池和线程局部会话，避免频繁创建连接
    """

    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        """线程安全的单例模式"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_url=None, pool_size=20, max_overflow=80, pool_recycle=1800, echo=False):
        """
        初始化连接池

        :param db_url: 数据库连接URL
        :param pool_size: 连接池大小(建议5-10)
        :param max_overflow: 最大溢出连接数(建议10-20)
        :param pool_recycle: 连接回收时间(秒，建议300-600)
        :param echo: 是否输出SQL日志
        """
        if self._initialized or not db_url:
            return

        self._engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # 自动检查连接是否有效
            echo=echo,
            connect_args={
                "connect_timeout": 5,
                "read_timeout": 30,
                "write_timeout": 30,
            }
        )

        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False
        )

        self._Session = scoped_session(self._session_factory)
        self._initialized = True
        logging.info("DBTaskManager initialized with pool_size=%d, max_overflow=%d", pool_size, max_overflow)

    @contextmanager
    def session_scope(self):
        """
        获取数据库会话的上下文管理器
        自动处理提交/回滚和资源清理

        用法:
        with db.session_scope() as session:
            session.query(...)
        """
        session = self._Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"数据库操作失败: {str(e)}", exc_info=True)
            raise
        finally:
            self._Session.remove()

    def get_session(self) -> scoped_session:
        """
        手动获取会话(需要手动关闭)

        用法:
        session = db.get_session()
        try:
            # 操作数据库
        finally:
            db.close_session(session)
        """
        return self._Session()

    def close_session(self, session: Optional[scoped_session] = None):
        """
        手动关闭会话

        :param session: 要关闭的会话，如果为None则关闭当前线程的会话
        """
        sess = session or (self._Session() if self._Session.registry.has() else None)
        if sess:
            try:
                sess.close()
            except Exception as e:
                logging.warning(f"关闭会话时出错: {str(e)}")
            finally:
                self._Session.remove()

    def shutdown(self):
        """关闭引擎，释放所有连接"""
        if hasattr(self, '_engine') and self._engine:
            self._engine.dispose()
            logging.info("数据库连接池已关闭")

    @property
    def engine(self):
        """获取SQLAlchemy引擎实例"""
        return self._engine


# 全局单例实例
db_factory = DBSessionFactory(db_url=load_conf.get('SQLALCHEMY_DATABASE_URI'))
