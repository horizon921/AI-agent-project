"""
数据验证模块
处理JSON Schema验证和输入输出验证
"""

import jsonschema
from jsonschema import validate, ValidationError
from typing import Dict, Tuple, Any
import json
import re

# JSON Schema 定义
PAPER_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "minLength": 10},
        "main_contributions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "methodology": {"type": "string", "minLength": 10},
        "key_findings": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3
        },
        "significance": {"type": "string", "minLength": 10}
    },
    "required": ["summary", "main_contributions", "methodology", "key_findings", "limitations", "significance"],
    "additionalProperties": False
}

EDUCATION_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "concept_explanation": {"type": "string", "minLength": 20},
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 6
        },
        "examples": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "exercises": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "minLength": 5},
                    "answer": {"type": "string", "minLength": 5},
                    "difficulty": {
                        "type": "string",
                        "enum": ["基础", "中级", "高级", "中等", "简单", "困难", "容易", "难"]
                    }
                },
                "required": ["question", "answer", "difficulty"]
            },
            "minItems": 1,
            "maxItems": 5
        },
        "further_reading": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3
        }
    },
    "required": ["concept_explanation", "key_points", "examples", "exercises", "further_reading"],
    "additionalProperties": False
}

CHAT_MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["user", "assistant", "system"]},
        "content": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["text", "image_url"]},
                            "text": {"type": "string"},
                            "image_url": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string"}
                                }
                            }
                        },
                        "required": ["type"]
                    }
                }
            ]
        }
    },
    "required": ["role", "content"]
}


class DataValidator:
    """数据验证器类"""

    @staticmethod
    def normalize_difficulty(data):
        """标准化难度级别"""
        difficulty_mapping = {
            "中等": "中级",
            "简单": "基础",
            "困难": "高级",
            "容易": "基础",
            "难": "高级"
        }

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "difficulty" and isinstance(value, str):
                    data[key] = difficulty_mapping.get(value, value)
                elif isinstance(value, (dict, list)):
                    DataValidator.normalize_difficulty(value)
        elif isinstance(data, list):
            for item in data:
                DataValidator.normalize_difficulty(item)
        return data

    @staticmethod
    def validate_json_response(data: Dict, schema: Dict, response_type: str) -> Tuple[bool, str]:
        """验证JSON响应是否符合Schema"""
        try:
            # 先标准化数据
            normalized_data = DataValidator.normalize_difficulty(data.copy())
            validate(instance=normalized_data, schema=schema)
            return True, ""
        except ValidationError as e:
            error_msg = f"{response_type}格式验证失败: {e.message}"
            return False, error_msg
        except Exception as e:
            error_msg = f"{response_type}验证出错: {str(e)}"
            return False, error_msg

    @staticmethod
    def validate_input_data(data: Dict, data_type: str) -> Tuple[bool, str]:
        """验证输入数据"""
        if data_type == "paper_text":
            if not isinstance(data.get("text"), str):
                return False, "论文文本必须是字符串"
            if len(data["text"].strip()) < 50:
                return False, "论文文本长度不能少于50个字符"
            return True, ""

        elif data_type == "education_request":
            if not isinstance(data.get("topic"), str):
                return False, "主题必须是字符串"
            if len(data["topic"].strip()) < 2:
                return False, "主题长度不能少于2个字符"
            if data.get("level") not in ["小学", "初中", "高中", "大学", "研究生"]:
                return False, "教育级别必须是：小学、初中、高中、大学、研究生之一"
            return True, ""

        return True, ""

    @staticmethod
    def parse_json_response(response: str) -> Any:
        """解析JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(
                r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试查找大括号内容
            brace_match = re.search(r'\{.*\}', response, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group())
                except json.JSONDecodeError:
                    pass

            return None

    def safe_parse_json_response(self, response: str, expected_schema: Dict, response_type: str) -> Tuple[Any, bool, str]:
        """安全解析并验证JSON响应"""
        parsed_data = self.parse_json_response(response)

        if parsed_data is None:
            return None, False, f"{response_type}响应不是有效的JSON格式"

        is_valid, error_msg = self.validate_json_response(
            parsed_data, expected_schema, response_type)
        return parsed_data, is_valid, error_msg


# 全局验证器实例
validator = DataValidator()
