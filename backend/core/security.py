# backend/core/security.py
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..config.settings import get_settings

settings = get_settings()


def generate_key(password: str, salt: bytes = None) -> bytes:
    """从密码生成加密密钥"""
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self, master_password: str = None):
        """初始化密钥管理器"""
        self.master_password = master_password or os.getenv(
            "MASTER_PASSWORD", "default_secure_password")
        # 在实际应用中，应该从环境变量或安全存储中获取主密码

        # 生成加密密钥
        self.key, self.salt = generate_key(self.master_password)
        self.cipher = Fernet(self.key)

    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        encrypted_key = self.cipher.encrypt(api_key.encode())
        return encrypted_key.decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        decrypted_key = self.cipher.decrypt(encrypted_key.encode())
        return decrypted_key.decode()

    def hash_api_key(self, api_key: str) -> str:
        """哈希API密钥用于存储或比较"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """验证API密钥"""
        return self.hash_api_key(api_key) == hashed_key
