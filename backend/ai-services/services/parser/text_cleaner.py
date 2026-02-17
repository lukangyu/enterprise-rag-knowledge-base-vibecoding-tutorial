import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """清洗文本"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:\'"()-]', '', text)
        return text.strip()

    @staticmethod
    def normalize(text: str) -> str:
        """规范化文本"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
