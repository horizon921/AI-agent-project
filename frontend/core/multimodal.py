import streamlit as st
import tempfile
import os
import base64
import io
import speech_recognition as sr
from PIL import Image


def encode_image_to_base64(image):
    """将图片编码为base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def process_audio_to_text(audio_bytes):
    """处理音频转文本"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(tmp_file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language='zh-CN')
        except:
            try:
                with sr.AudioFile(tmp_file_path) as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language='zh-CN')
            except Exception as e:
                raise e

        os.unlink(tmp_file_path)
        return text
    except Exception as e:
        return f"语音识别失败: {str(e)}"


def create_multimodal_message(text, image=None, audio_text=None):
    """创建多模态消息"""
    content = []

    if text:
        content.append({"type": "text", "text": text})

    if audio_text and not audio_text.startswith("语音识别失败"):
        content.append({"type": "text", "text": f"[语音输入]: {audio_text}"})

    if image:
        image_base64 = encode_image_to_base64(image)
        content.append({
            "type": "image_url",
            "image_url": {"url": image_base64}
        })

    return content if len(content) > 0 else [{"type": "text", "text": ""}]
