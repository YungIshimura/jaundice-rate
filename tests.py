import pytest
from main import analyze, process_article, ProcessingStatus
import asyncio
from unittest.mock import patch


def test_all_keys_in_error_response():
    articles = ["http://example.com/article1"]

    processed_articles = asyncio.run(analyze(articles))

    assert processed_articles[0].get('Статус', None) 
    assert processed_articles[0].get('URL', None) 
    assert processed_articles[0].get('Рейтинг', None)  == None
    assert processed_articles[0].get('Слов в статье', None) == None


def test_all_keys_in_ok_response():
    articles = ["https://inosmi.ru/20241203/pandemiya-271003793.html"]

    processed_articles = asyncio.run(analyze(articles))

    assert processed_articles[0].get('Статус', None) 
    assert processed_articles[0].get('URL', None) 
    assert processed_articles[0].get('Рейтинг', None)
    assert processed_articles[0].get('Слов в статье', None)
    assert processed_articles[0].get('INFO:root', None)


def test_process_article_fetch_error():
    articles = ["http://example.com/article1"]

    processed_articles = asyncio.run(analyze(articles))
    
    assert len(processed_articles) == 1
    assert processed_articles[0]['Статус'] == ProcessingStatus.FETCH_ERROR


def test_process_article_parsing_error():
    articles = ["https://lenta.ru/brief/2021/08/26/afg_terror/"]

    processed_articles = asyncio.run(analyze(articles))
    
    assert len(processed_articles) == 1
    assert processed_articles[0]['Статус'] == ProcessingStatus.PARSING_ERROR


async def mock_fetch_timeout(*args, **kwargs):
    raise asyncio.TimeoutError("Timeout error")


@pytest.mark.asyncio
async def test_process_article_timeout_error():
    articles = ["https://inosmi.ru/20241203/pandemiya-271003793.html"]
    processed_articles = []

    with patch("main.fetch", mock_fetch_timeout):
        await process_article(articles, processed_articles)

    assert len(processed_articles) == 1
    assert processed_articles[0]['Статус'] == ProcessingStatus.TIMEOUT