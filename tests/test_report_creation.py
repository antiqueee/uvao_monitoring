import pytest

from app.routes.reports import build_source_posts, zip_post_entries
from app.services.url_parser import InvalidVkPostUrl


def test_zip_post_entries_pairs_fields_and_drops_empty_blocks() -> None:
    entries = zip_post_entries(
        ["https://vk.com/wall-1_2", "", "https://vk.com/wall-3_4"],
        ["Первый", "", "Второй"],
    )

    assert entries == [
        {"url": "https://vk.com/wall-1_2", "title": "Первый"},
        {"url": "https://vk.com/wall-3_4", "title": "Второй"},
    ]


def test_build_source_posts_parses_each_post() -> None:
    posts = build_source_posts(
        ["https://vk.com/wall-1_2", "https://vk.com/wall-3_4"],
        ["Первый пост", "Второй пост"],
    )

    assert posts == [
        {"url": "https://vk.com/wall-1_2", "title": "Первый пост", "owner_id": "-1", "post_id": "2"},
        {"url": "https://vk.com/wall-3_4", "title": "Второй пост", "owner_id": "-3", "post_id": "4"},
    ]


def test_build_source_posts_requires_title_for_filled_link() -> None:
    with pytest.raises(InvalidVkPostUrl):
        build_source_posts(["https://vk.com/wall-1_2"], [""])


def test_build_source_posts_requires_at_least_one_post() -> None:
    with pytest.raises(InvalidVkPostUrl):
        build_source_posts(["", ""], ["", ""])
