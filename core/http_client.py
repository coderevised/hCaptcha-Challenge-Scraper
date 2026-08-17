from __future__ import annotations
from typing import Any, Optional, Union
import requests

class HttpClient:
    def __init__(
        self,
        *,
        base_url: str = "",
        proxy: Optional[str] = None,
        timeout: float = 30.0,
        emulation: str = "Chrome147",
        follow_redirects: bool = True,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.timeout = timeout
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers or {})
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def get(self, url: str, *, headers: Optional[dict[str, str]] = None) -> requests.Response:
        return self.session.get(url, headers=headers, timeout=self.timeout)

    def post(
        self,
        url: str,
        *,
        data: Optional[Union[dict, bytes, str]] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> requests.Response:
        if json_data is not None:
            return self.session.post(url, json=json_data, headers=headers, timeout=self.timeout)
        return self.session.post(url, data=data, headers=headers, timeout=self.timeout)