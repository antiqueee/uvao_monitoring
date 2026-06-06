from app.routes.reports import parse_source_posts


def test_parse_source_posts_uses_line_titles_and_fallback_title() -> None:
    posts = parse_source_posts(
        "",
        "\nhttps://vk.com/wall-1_2 | Первый пост\nhttps://vk.com/wall-3_4\n",
        "Общий заголовок",
    )

    assert posts == [
        {"url": "https://vk.com/wall-1_2", "title": "Первый пост"},
        {"url": "https://vk.com/wall-3_4", "title": "Общий заголовок"},
    ]
