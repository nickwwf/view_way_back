


from marshmallow import Schema,fields,ValidationError,validates_schema
from marshmallow.fields import String, Integer, List, Float, Boolean, Dict
from app.libs.error_code import ParameterException, Success

__all__ = [
    "String", "Integer", "List", "Float", "Boolean", "Dict",
]

def check_req(schema,data):
    try:
        return schema().load(data)
    except ValidationError as e:
        return ParameterException(msg=e.messages_dict)

