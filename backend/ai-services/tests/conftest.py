import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_pdf_content():
    return b"%PDF-1.4\n%fake pdf content"


@pytest.fixture
def sample_text():
    return """
# 标题一

这是第一段内容，包含一些测试文本。

## 标题二

这是第二段内容，用于测试分块功能。
包含多行文本，用于验证分块算法的正确性。

### 标题三

最后一段内容。
"""


@pytest.fixture
def sample_chunks():
    return [
        {"content": "这是第一个分块", "position": 0},
        {"content": "这是第二个分块", "position": 1},
        {"content": "这是第三个分块", "position": 2}
    ]
