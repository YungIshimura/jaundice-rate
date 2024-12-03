import aiohttp
import asyncio
from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate
import pymorphy2
import aiofiles
import anyio
import enum
from adapters.exceptions import ArticleNotFound
from async_timeout import timeout
from contextlib import asynccontextmanager
import time


@asynccontextmanager
async def start_analyze():
    yield time.monotonic()


class ProcessingStatus(enum.Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def get_charged_words(filepaths):
    charged_words = []
    for filepath in filepaths:
        async with aiofiles.open(filepath, mode='r') as file:
            words = await file.read()
            splited_words = words.split('\n')
            charged_words.extend(splited_words)
    
    return charged_words


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(articles, processed_articles=[]):
    morph = pymorphy2.MorphAnalyzer()
    charged_words = await get_charged_words(['charged_dict/negative_words.txt', 'charged_dict/positive_words.txt'])
    
    async with aiohttp.ClientSession() as session:
        for article in articles:
            try:
                async with timeout(5):
                    html = await fetch(session, article)
                
                async with start_analyze() as (start_time):
                    clean_text = sanitize(html, plaintext=True)
                    splited_clean_text = split_by_words(morph, clean_text)
                    jaundice_rate = calculate_jaundice_rate(splited_clean_text, charged_words)

                end_time = time.monotonic()

                processed_articles.append([
                    f'URL: {article}',
                    f'Статус: {ProcessingStatus.OK}',
                    f'Рейтинг: {jaundice_rate}',
                    f'Слов в статье: {len(splited_clean_text)}',
                    f'INFO:root:Анализ закончен за {end_time - start_time:.2f} сек'
                ])

            except aiohttp.ClientError:
                processed_articles.append([
                    f'URL - {article}',
                    f'Статус: {ProcessingStatus.FETCH_ERROR}'
                ])
            except ArticleNotFound:
                processed_articles.append([
                    f'URL - {article}',
                    f'Статус: {ProcessingStatus.PARSING_ERROR}'
                ])
            except asyncio.TimeoutError:
                processed_articles.append([
                    f'URL - {article}',
                    f'Статус: {ProcessingStatus.TIMEOUT}'
                ])
        

async def main():
    TEST_ARTICLES = [
        'https://chototam.ru/ladgf',
        'https://lenta.ru/brief/2021/08/26/afg_terror/',
        'https://inosmi.ru/20241203/pandemiya-271003793.html',
        'https://inosmi.ru/20241203/yuzhnaya_koreya-271008691.html',
        'https://inosmi.ru/20241203/nato-271007956.html',
        'https://inosmi.ru/20241203/gruziya-271001446.html',
        'https://inosmi.ru/20241203/su-57-271003013.html'
    ]
    processed_articles = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(process_article, TEST_ARTICLES, processed_articles)

    for article in processed_articles:
        print('\n'.join(article), '\n')


asyncio.run(main())
