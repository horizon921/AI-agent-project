# frontend/core/multimodal.py
import base64
import io
import streamlit as st
from PIL import Image
import tempfile
import os


def encode_image_to_base64(uploaded_file):
    """将上传的图片编码为base64"""
    try:
        # 读取图片数据
        image_data = uploaded_file.read()

        # 编码为base64
        base64_encoded = base64.b64encode(image_data).decode('utf-8')

        return base64_encoded
    except Exception as e:
        raise Exception(f"图片编码失败: {str(e)}")


def process_audio_to_text(uploaded_audio):
    """将音频转换为文字 - 简化版本"""
    try:
        # 这里暂时返回占位符文本
        # 实际项目中可以集成语音识别服务
        return f"音频文件已上传: {uploaded_audio.name}"
    except Exception as e:
        raise Exception(f"音频处理失败: {str(e)}")


def create_multimodal_message(text=None, image_base64=None, audio_text=None):
    """创建多模态消息"""
    content = []

    if text:
        content.append({
            "type": "text",
            "text": text
        })

    if image_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

    if audio_text:
        content.append({
            "type": "text",
            "text": f"[语音转文字]: {audio_text}"
        })

    return content
