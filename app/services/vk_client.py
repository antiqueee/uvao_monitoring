import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings


class VkApiError(RuntimeError):
    def __init__(self, code: int, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.payload = payload or {}


class VkClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = "https://api.vk.com/method"

    async def call(self, method: str, params: dict[str, Any]) -> Any:
        if not self.settings.vk_service_token:
            raise VkApiError(5, "VK_SERVICE_TOKEN не задан")

        request_params = {
            **params,
            "access_token": self.settings.vk_service_token,
            "v": self.settings.vk_api_version,
            "lang": "ru",
        }
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.get(f"{self.base_url}/{method}", params=request_params)
                response.raise_for_status()
                data = response.json()
                if "error" in data:
                    error = data["error"]
                    code = int(error.get("error_code", 0))
                    if code == 6 and attempt < 2:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise VkApiError(code, error.get("error_msg", "Ошибка VK API"), error)
                return data["response"]
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
        raise VkApiError(0, f"VK API недоступен: {last_error}")

    async def resolve_screen_name(self, screen_name: str) -> dict[str, Any]:
        return await self.call("utils.resolveScreenName", {"screen_name": screen_name})

    async def wall_get_by_id(self, owner_id: int, post_id: int) -> dict[str, Any]:
        response = await self.call("wall.getById", {"posts": f"{owner_id}_{post_id}"})
        if isinstance(response, dict):
            items = response.get("items", [])
        else:
            items = response
        if not items:
            raise VkApiError(15, "Пост первоисточника не найден или недоступен")
        return items[0]

    async def wall_get(self, owner_id: int, count: int = 100) -> list[dict[str, Any]]:
        response = await self.call("wall.get", {"owner_id": owner_id, "count": count})
        return response.get("items", [])

    async def group_info(self, owner_id: int) -> dict[str, Any]:
        response = await self.call(
            "groups.getById", {"group_id": abs(owner_id), "fields": "members_count"}
        )
        if isinstance(response, dict) and "groups" in response:
            groups = response["groups"]
        else:
            groups = response
        return groups[0] if groups else {}

    async def user_info(self, owner_id: int) -> dict[str, Any]:
        response = await self.call("users.get", {"user_ids": owner_id, "fields": "followers_count"})
        return response[0] if response else {}


def vk_ts_to_dt(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)
