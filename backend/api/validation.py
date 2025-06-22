# backend/api/validation.py
import json
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError


class SchemaValidator:
    def __init__(self, schema_path: str = None, schema: Dict = None):
        if schema:
            self.schema = schema
        elif schema_path:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        else:
            raise ValueError("Either schema or schema_path must be provided")

    def validate_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """验证输出是否符合JSON Schema"""
        try:
            validate(instance=output, schema=self.schema)
            return {"valid": True, "data": output}
        except ValidationError as e:
            return {"valid": False, "error": str(e)}
