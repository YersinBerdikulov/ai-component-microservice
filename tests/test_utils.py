"""Tests for shared utilities."""
import pytest

from app.services.json_utils import extract_json


def test_plain_json():
    data = extract_json('{"key": "value"}')
    assert data == {"key": "value"}


def test_markdown_json_fence():
    raw = '```json\n{"key": "value"}\n```'
    assert extract_json(raw) == {"key": "value"}


def test_markdown_plain_fence():
    raw = '```\n{"key": "value"}\n```'
    assert extract_json(raw) == {"key": "value"}


def test_whitespace_around_json():
    raw = '  \n  {"key": "value"}  \n  '
    assert extract_json(raw) == {"key": "value"}


def test_invalid_json_raises():
    with pytest.raises(ValueError):  # json.JSONDecodeError subclasses ValueError
        extract_json("this is not json")
