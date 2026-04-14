import uuid
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery
from sqlalchemy import Column, Integer, SmallInteger, orm, inspect, TIMESTAMP, String
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from contextlib import contextmanager

from app.libs.error_code import NotFound


# 继承 flask_sqlalchemy 的 SQLAlchemy 类, 扩展了auto_commit方法
# 将 session.commit() 包装了事务异常捕捉的能力
class SQLAlchemy(_SQLAlchemy):
    # @contextmanager 装饰器实现了将 yield 前后包装, 可实现我们自己想要加入的逻辑
    @contextmanager
    def auto_commit(self, throw=True):
        try:
            # 实际的业务逻辑执行的位置
            yield
            # 最后做批量提交
            self.session.commit()
        except Exception as e:  # 如果提交发生异常
            # 先将事务进行回滚
            self.session.rollback()
            # 记录错误日志
            current_app.logger.exception('%r' % e)
            if throw:
                raise e     # 抛出异常信息


# 继承 flask_sqlalchemy 的 BaseQuery 类, 重载一些方法, 来满足自由框架逻辑
class Query(BaseQuery):
    def get_or_404(self, ident, description=None):
        rv = self.get(ident)
        if not rv:
            raise NotFound()
        return rv

    def first_or_404(self, description=None):
        print(str(self))
        rv = self.first()

        if not rv:
            raise NotFound()
        return rv


# 参数 query_class=Query 实现了使用我们自定义的 Query 类, 替换 flask_sqlalchemy 中的 Query 类
db = SQLAlchemy(query_class=Query)


class Base(db.Model):
    __abstract__ = True  # 指定该基类是不需要映射到数据库中的一张表的, 而是一个抽象类
    # create_time 在更新数据时也会改变是因为数据库中create_time字段设置了<根据当前时间戳更新>
    create_time = Column(TIMESTAMP, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now, comment='最后修改时间')

    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())

    def set_attrs(self, attrs_dict):
        """
        对传入的字典进行遍历, 动态赋值到当前对象对应的属性中
        该方法解决了接收一个字典对象, 且该字典对象中的属性与需要构造的模型对象属性一致时的快速赋值
        而不需要一个个的从字典中取值出来再赋值给对象
        :param attrs_dict: 接收一个字典对象{key1:value1,key2:value2,...}
        """
        for key, value in attrs_dict.items():
            if value is None:
                continue
            # 判断传入的字典的 key 是否属于当前的实例化对象的某个属性, 且该属性不能是 id(因为 id 字段是所有数据模板的主键, 不应该被改写)
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    def delete(self):
        self.is_del = 1


# 自定义对象序列化器
class MixinJSONSerializer:

    @orm.reconstructor
    def init_on_load(self):
        self._exclude = []
        self._fields = []
        # self._include = []
        self._set_fields()
        self.__prune_fields()

    def _set_fields(self):
        columns = inspect(self.__class__).columns

        try:
            self._fields
        except Exception as e:
            self._fields = []
            self._exclude = []

        if not self._fields:
            all_columns = set(columns.keys())
            self._fields = list(all_columns - set(self._exclude))


    def __prune_fields(self):
        columns = inspect(self.__class__).columns
        if not self._fields:
            all_columns = set(columns.keys())
            self._fields = list(all_columns - set(self._exclude))

    # 隐藏字段
    def hide(self, *args):
        for key in args:
            self._fields.remove(key)
        return self

    # 追加字段
    def append(self, *args):
        for key in args:
            self._fields.append(key)
        return self

    # 显示的字段
    def keys(self):
        return self._fields

    def __getitem__(self, key):
        return getattr(self, key)
