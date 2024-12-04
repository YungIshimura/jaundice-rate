import asyncio
from unittest.mock import patch

import pymorphy2
import pytest
import requests

from adapters.exceptions import ArticleNotFound
from adapters.inosmi_ru import sanitize
from main import ProcessingStatus, analyze, process_article
from tools.mock_tools import mock_fetch_timeout
from tools.text_tools import calculate_jaundice_rate, split_by_words


def test_all_keys_in_error_response():
    articles = ["http://example.com/article1"]

    processed_articles = asyncio.run(analyze(articles))

    assert processed_articles[0].get("Статус", None)
    assert processed_articles[0].get("URL", None)
    assert processed_articles[0].get("Рейтинг", None) == None
    assert processed_articles[0].get("Слов в статье", None) == None


def test_all_keys_in_ok_response():
    articles = ["https://inosmi.ru/20241203/pandemiya-271003793.html"]

    processed_articles = asyncio.run(analyze(articles))

    assert processed_articles[0].get("Статус", None)
    assert processed_articles[0].get("URL", None)
    assert processed_articles[0].get("Рейтинг", None)
    assert processed_articles[0].get("Слов в статье", None)
    assert processed_articles[0].get("INFO:root", None)


def test_process_article_fetch_error():
    articles = ["http://example.com/article1"]

    processed_articles = asyncio.run(analyze(articles))

    assert len(processed_articles) == 1
    assert processed_articles[0]["Статус"] == ProcessingStatus.FETCH_ERROR


def test_process_article_parsing_error():
    articles = ["https://lenta.ru/brief/2021/08/26/afg_terror/"]

    processed_articles = asyncio.run(analyze(articles))

    assert len(processed_articles) == 1
    assert processed_articles[0]["Статус"] == ProcessingStatus.PARSING_ERROR


@pytest.mark.asyncio
async def test_process_article_timeout_error():
    articles = ["https://inosmi.ru/20241203/pandemiya-271003793.html"]
    processed_articles = []

    with patch("main.fetch", mock_fetch_timeout):
        await process_article(articles, processed_articles)

    assert len(processed_articles) == 1
    assert processed_articles[0]["Статус"] == ProcessingStatus.TIMEOUT


def test_split_by_words():
    morph = pymorphy2.MorphAnalyzer()

    result = asyncio.run(split_by_words(morph, "Во-первых, он хочет, чтобы"))
    assert result == ["во-первых", "хотеть", "чтобы"]

    result = asyncio.run(split_by_words(morph, "«Удивительно, но это стало началом!»"))
    assert result == ["удивительно", "это", "стать", "начало"]


def test_calculate_jaundice_rate():
    result = asyncio.run(calculate_jaundice_rate([], []))
    assert -0.01 < result < 0.01

    result = asyncio.run(
        calculate_jaundice_rate(
            ["все", "аутсайдер", "побег"], ["аутсайдер", "банкротство"]
        )
    )
    assert 33.0 < result < 34.0


def test_sanitize():
    resp = requests.get("https://inosmi.ru/economic/20190629/245384784.html")
    resp.raise_for_status()
    clean_text = sanitize(resp.text)

    assert "В субботу, 29 июня, президент США Дональд Трамп" in clean_text
    assert "За несколько часов до встречи с Си" in clean_text

    assert '<img src="' in clean_text
    assert "<h1>" in clean_text

    clean_plaintext = sanitize(resp.text, plaintext=True)

    assert "В субботу, 29 июня, президент США Дональд Трамп" in clean_plaintext
    assert "За несколько часов до встречи с Си" in clean_plaintext

    assert '<img src="' not in clean_plaintext
    assert '<a href="' not in clean_plaintext
    assert "<h1>" not in clean_plaintext
    assert "</article>" not in clean_plaintext
    assert "<h1>" not in clean_plaintext


def test_sanitize_wrong_url():
    resp = requests.get("http://example.com")
    resp.raise_for_status()
    with pytest.raises(ArticleNotFound):
        sanitize(resp.text)
