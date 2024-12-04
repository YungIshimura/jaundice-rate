import asyncio
import string

import pymorphy2
from async_timeout import timeout


async def _clean_word(word):
    word = word.replace('«', '').replace('»', '').replace('…', '')
    # FIXME какие еще знаки пунктуации часто встречаются ?
    word = word.strip(string.punctuation)
    return word


async def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги."""
    words = []
    async with timeout(3):
        for word in text.split():
            cleaned_word = await _clean_word(word)
            normalized_word = morph.parse(cleaned_word)[0].normal_form
            if len(normalized_word) > 2 or normalized_word == 'не':
                words.append(normalized_word)
        return words


def test_split_by_words():
    morph = pymorphy2.MorphAnalyzer()

    result = asyncio.run(split_by_words(morph, 'Во-первых, он хочет, чтобы'))
    assert result == ['во-первых', 'хотеть', 'чтобы']

    result = asyncio.run(split_by_words(morph, '«Удивительно, но это стало началом!»'))
    assert result == ['удивительно', 'это', 'стать', 'начало']



async def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста, принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = [word for word in article_words if word in set(charged_words)]

    score = len(found_charged_words) / len(article_words) * 100

    return round(score, 2)


def test_calculate_jaundice_rate():
    result = asyncio.run(calculate_jaundice_rate([], []))
    assert -0.01 < result < 0.01

    result = asyncio.run(calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']))
    assert 33.0 < result < 34.0
