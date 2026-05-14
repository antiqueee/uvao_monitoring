import pytest

from app.services.url_parser import InvalidVkPostUrl, parse_vk_post_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://vk.com/wall-12345_67890", (-12345, 67890)),
        ("https://vk.com/wall12345_67890", (12345, 67890)),
        ("https://vk.com/somegroup?w=wall-12345_67890", (-12345, 67890)),
        ("https://m.vk.com/wall-12345_67890", (-12345, 67890)),
    ],
)
def test_parse_vk_post_url(url: str, expected: tuple[int, int]) -> None:
    assert parse_vk_post_url(url) == expected


def test_parse_vk_post_url_rejects_non_wall_url() -> None:
    with pytest.raises(InvalidVkPostUrl):
        parse_vk_post_url("https://vk.com/feed")
