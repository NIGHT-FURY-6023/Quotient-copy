from typing import Any
import json
from tortoise.fields.base import Field


class ArrayField(Field, list):
    def __init__(self, field: Field, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sub_field = field
        self.SQL_TYPE = "TEXT"  # Store as JSON string in SQLite

    def to_python_value(self, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []
        return list(map(self.sub_field.to_python_value, value))

    def to_db_value(self, value: Any, instance: Any) -> Any:
        if value is None:
            return "[]"
        db_values = [self.sub_field.to_db_value(val, instance) for val in value]
        return json.dumps(db_values)
