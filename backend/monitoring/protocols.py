from typing import Protocol

import requests


class HTTPSession(Protocol):
    def get(
        self,
        url: str,
        *,
        timeout: float,
        allow_redirects: bool = True,
    ) -> requests.Response: ...
