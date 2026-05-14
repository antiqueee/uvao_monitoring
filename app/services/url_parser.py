import re

WALL_RE = re.compile(r"wall(-?\d+)_(\d+)")


class InvalidVkPostUrl(ValueError):
    pass


def parse_vk_post_url(url: str) -> tuple[int, int]:
    match = WALL_RE.search(url.strip())
    if not match:
        raise InvalidVkPostUrl("не похоже на ссылку на пост ВК")
    return int(match.group(1)), int(match.group(2))
