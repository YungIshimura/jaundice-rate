from typing import List

from bs4 import BeautifulSoup

DEFAULT_BLACKLIST_TAGS = ["script", "time"]
DEFAULT_UNWRAPLIST_TAGS = ["div", "p", "span", "address", "article", "header", "footer"]


def remove_buzz_attrs(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove all attributes except some special tags."""
    for tag in soup.find_all(True):
        if tag.name == "a":
            tag.attrs = {
                "href": tag.attrs.get("href"),
            }
        elif tag.name == "img":
            tag.attrs = {
                "src": tag.attrs.get("src"),
            }
        else:
            tag.attrs = {}

    return soup


def remove_buzz_tags(
    soup: BeautifulSoup,
    blacklist: List[str] = DEFAULT_BLACKLIST_TAGS,
    unwraplist: List[str] = DEFAULT_UNWRAPLIST_TAGS,
) -> None:
    """Remove most of tags, leaves only tags significant for text analysis."""
    for tag in soup.find_all(True):
        if tag.name in blacklist:
            tag.decompose()
        elif tag.name in unwraplist:
            tag.unwrap()


def remove_all_tags(soup: BeautifulSoup) -> None:
    """Unwrap all tags."""
    for tag in soup.find_all(True):
        tag.unwrap()
