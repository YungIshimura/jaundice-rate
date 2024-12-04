import asyncio
import enum
import time

import aiofiles
import aiohttp
import anyio
import pymorphy2
from async_timeout import timeout

from adapters.exceptions import ArticleNotFound
from adapters.inosmi_ru import sanitize
from tools.text_tools import calculate_jaundice_rate, split_by_words

# TODO продумать возможность для использования контекстного менеджера


class ProcessingStatus(str, enum.Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


async def get_charged_words(filepaths):
    charged_words = []
    for filepath in filepaths:
        async with aiofiles.open(filepath, mode="r") as file:
            words = await file.read()
            splited_words = words.split("\n")
            charged_words.extend(splited_words)

    return charged_words


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(
    articles,
    processed_articles=[],
    charged_word_filepaths=[
        "charged_dict/negative_words.txt",
        "charged_dict/positive_words.txt",
    ],
):
    morph = pymorphy2.MorphAnalyzer()
    charged_words = await get_charged_words(charged_word_filepaths)

    async with aiohttp.ClientSession() as session:
        for article in articles:
            try:
                async with timeout(5):
                    html = await fetch(session, article)

                start_time = time.monotonic()
                clean_text = sanitize(html, plaintext=True)
                splited_clean_text = await split_by_words(morph, clean_text)
                jaundice_rate = await calculate_jaundice_rate(
                    splited_clean_text, charged_words
                )

                processed_articles.append(
                    {
                        "URL": article,
                        "Статус": ProcessingStatus.OK,
                        "Рейтинг": jaundice_rate,
                        "Слов в статье": len(splited_clean_text),
                        "INFO:root": f"Анализ закончен за {time.monotonic() - start_time:.2f} сек",
                    }
                )
            except aiohttp.ClientError:
                processed_articles.append(
                    {
                        "URL": article,
                        "Статус": ProcessingStatus.FETCH_ERROR,
                        "Рейтинг": None,
                        "Слов в статье": None,
                    }
                )
            except ArticleNotFound:
                processed_articles.append(
                    {
                        "URL": article,
                        "Статус": ProcessingStatus.PARSING_ERROR,
                        "Рейтинг": None,
                        "Слов в статье": None,
                    }
                )
            except asyncio.TimeoutError:
                processed_articles.append(
                    {
                        "URL": article,
                        "Статус": ProcessingStatus.TIMEOUT,
                        "Рейтинг": None,
                        "Слов в статье": None,
                    }
                )
                


async def analyze(article_urls):
    processed_articles = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(process_article, article_urls, processed_articles)

    return processed_articles
