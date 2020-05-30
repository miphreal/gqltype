import json
import pathlib
from typing import List, Literal, Optional

import aiohttp


ObjectTypeName = Literal[
    "people", "films", "planets", "species", "starships", "vehicles"
]


class Storage:
    """Simple caching proxy to the RESTful swapi.dev"""

    api_url = "http://swapi.dev/api"
    local_cache_file = pathlib.Path("/tmp/sw.json")
    loaded_cache = None

    def cache_set(self, key: str, val: List[dict]):
        cache = self.loaded_cache or {}
        cache[key] = val
        self.loaded_cache = cache
        with self.local_cache_file.open("w") as f:
            f.write(json.dumps(cache))

    def cache_get(self, key: str, *default) -> List[dict]:
        if self.loaded_cache is None and self.local_cache_file.exists():
            with self.local_cache_file.open("r") as f:
                self.loaded_cache = json.loads(f.read())
        cache = self.loaded_cache or {}
        if not default:
            return cache[key]
        return cache.get(key, default[0])

    def url_to_id(self, url: str) -> str:
        if url.startswith(self.api_url):
            return url.replace(self.api_url, "").strip("/").replace("/", ":")
        return url

    async def get_objects(
        self, objects_type: ObjectTypeName, ids: Optional[str] = None
    ) -> List[dict]:
        data = self.cache_get(objects_type, None)

        if not data:
            url = f"{self.api_url}/{objects_type}"
            data = []
            async with aiohttp.ClientSession() as session:
                while url:
                    async with session.get(url) as response:
                        resp = await response.json()
                        data.extend(resp["results"])
                        url = resp.get("next")

            for item in data:
                item["id"] = self.url_to_id(item["url"])
            self.cache_set(objects_type, data)

        if ids is not None:
            ids = set(map(self.url_to_id, ids))
            return [item for item in data if item["id"] in ids]
        return data

    async def get_object(
        self, objects_type: ObjectTypeName, object_id: str
    ) -> Optional[dict]:
        items = await self.get_objects(objects_type, ids=[object_id])
        return next(iter(items))


storage = Storage()
