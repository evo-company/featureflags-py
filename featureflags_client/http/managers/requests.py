import logging
from enum import EnumMeta
from typing import Any, Dict, List, Optional, Type, Union

from featureflags_client.http.constants import Endpoints
from featureflags_client.http.managers.base import (
    BaseManager,
)
from featureflags_client.http.types import (
    Variable,
)

try:
    from urllib.parse import urljoin

    import requests
except ImportError:
    raise ImportError(
        "`requests` is not installed, please install it to use RequestsManager "
        "like this `pip install 'featureflags-client[requests]'`"
    ) from None

log = logging.getLogger(__name__)


class RequestsManager(BaseManager):
    """Feature flags and values manager for sync apps with `requests` client."""

    def __init__(  # noqa: PLR0913
        self,
        url: str,
        project: str,
        variables: List[Variable],
        defaults: Union[EnumMeta, Type, Dict[str, bool]],
        values_defaults: Optional[
            Union[EnumMeta, Type, Dict[str, Union[int, str]]]
        ] = None,
        request_timeout: int = 5,
        refresh_interval: int = 10,
    ) -> None:
        super().__init__(
            url,
            project,
            variables,
            defaults,
            values_defaults,
            request_timeout,
            refresh_interval,
        )
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _post(
        self,
        url: Endpoints,
        payload: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        response = self._session.post(
            url=urljoin(self.url, url.value),
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data
