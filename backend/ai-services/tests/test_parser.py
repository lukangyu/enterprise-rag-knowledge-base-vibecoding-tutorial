import pytest
from services.parser.markdown_parser import MarkdownParser
from services.parser.text_cleaner import TextCleaner


class TestMarkdownParser:
    def test_parse_basic_markdown(self):
        parser = MarkdownParser()
        content = "# 标题\n\n这是内容"
        result = parser.parse(content)

        assert result.content == content
        assert len(result.structure) == 1
        assert result.structure[0]["type"] == "heading"
        assert result.structure[0]["text"] == "标题"

    def test_parse_multiple_headings(self):
        parser = MarkdownParser()
        content = "# 一级\n## 二级\n### 三级"
        result = parser.parse(content)

        assert len(result.structure) == 3
        assert result.structure[0]["level"] == 1
        assert result.structure[1]["level"] == 2
        assert result.structure[2]["level"] == 3

    def test_parse_frontmatter(self):
        parser = MarkdownParser()
        content = "---\ntitle: 测试\nauthor: 作者\n---\n# 内容"
        result = parser.parse(content)

        assert "title" in result.metadata
        assert result.metadata["title"] == "测试"

    def test_parse_returns_parsed_document(self):
        parser = MarkdownParser()
        content = "# 测试标题\n\n测试内容"
        result = parser.parse(content)

        assert hasattr(result, 'content')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'structure')
        assert hasattr(result, 'content_hash')

    def test_content_hash_generated(self):
        parser = MarkdownParser()
        content = "# 测试"
        result = parser.parse(content)

        assert result.content_hash is not None
        assert len(result.content_hash) == 64


class TestTextCleaner:
    def test_clean_whitespace(self):
        text = "  多余  空格  "
        result = TextCleaner.clean(text)

        assert result == "多余 空格"

    def test_normalize_newlines(self):
        text = "第一行\r\n\r\n\r\n第二行"
        result = TextCleaner.normalize(text)

        assert "\r\n" not in result
        assert "\n\n\n" not in result

    def test_clean_removes_special_chars(self):
        text = "测试内容@#$%^&*特殊字符"
        result = TextCleaner.clean(text)

        assert "@#$%^&*" not in result

    def test_normalize_strips_whitespace(self):
        text = "  前后空格  "
        result = TextCleaner.normalize(text)

        assert result == "前后空格"

    def test_clean_preserves_chinese(self):
        text = "这是中文测试内容"
        result = TextCleaner.clean(text)

        assert "中文" in result
        assert "测试" in result
