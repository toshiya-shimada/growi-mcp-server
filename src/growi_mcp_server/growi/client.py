from __future__ import annotations

import logging
from collections.abc import Mapping
from time import perf_counter
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from growi_mcp_server.growi.errors import (
    GrowiAuthError,
    GrowiConflictError,
    GrowiNotFoundError,
    GrowiPermissionError,
    GrowiTransportError,
    GrowiValidationError,
)
from growi_mcp_server.settings import Settings
from growi_mcp_server.utils.sanitize import redact_mapping

LOGGER = logging.getLogger(__name__)


class GrowiClient:
    """Thin async HTTP client for the GROWI REST API v3.

    Authentication is performed by appending ``access_token`` to every
    request's query string, which is the method GROWI supports natively.
    """

    def __init__(self, settings: Settings) -> None:
        self._access_token = settings.growi_access_token
        self._client = httpx.AsyncClient(
            base_url=str(settings.growi_base_url).rstrip("/"),
            headers={
                "Accept": "application/json",
                "User-Agent": settings.growi_user_agent,
            },
            timeout=settings.growi_timeout_ms / 1000,
            verify=settings.growi_verify_tls,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        form_data: Mapping[str, Any] | None = None,
        accepted_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        """Execute an authenticated request and return the parsed JSON body.

        ``access_token`` is always appended to the URL query string.
        Write operations pass their payload as ``application/x-www-form-urlencoded``
        body via ``form_data``.
        """
        accepted = accepted_statuses or {200, 201, 204}

        # Always include token in query params
        all_params: dict[str, Any] = {"access_token": self._access_token}
        if params:
            all_params.update(params)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.25, min=0.25, max=1.5),
            retry=retry_if_exception_type((httpx.TransportError, GrowiTransportError)),
            reraise=True,
        ):
            with attempt:
                started = perf_counter()
                try:
                    response = await self._client.request(
                        method,
                        path,
                        params=all_params,
                        data=form_data,
                    )
                except httpx.TransportError as exc:
                    raise GrowiTransportError(str(exc)) from exc
                duration_ms = round((perf_counter() - started) * 1000, 2)
                LOGGER.info(
                    "growi_request method=%s path=%s status=%s duration_ms=%s params=%s",
                    method,
                    path,
                    response.status_code,
                    duration_ms,
                    redact_mapping(dict(all_params)),
                )
                if response.status_code not in accepted:
                    self._raise_for_status(response)
                if response.status_code == 204 or not response.content:
                    return {}
                return response.json()  # type: ignore[no-any-return]

        raise GrowiTransportError("GROWI request failed after retries.")

    def _raise_for_status(self, response: httpx.Response) -> None:
        payload: dict[str, Any] = {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        message = self._build_error_message(response, payload)
        if response.status_code == 401:
            raise GrowiAuthError(message)
        if response.status_code == 403:
            raise GrowiPermissionError(message)
        if response.status_code == 404:
            raise GrowiNotFoundError(message)
        if response.status_code == 409:
            raise GrowiConflictError(message)
        if response.status_code in {400, 412, 422}:
            raise GrowiValidationError(message)
        if response.status_code >= 500:
            raise GrowiTransportError(message)
        raise GrowiValidationError(message)

    @staticmethod
    def _build_error_message(response: httpx.Response, payload: dict[str, Any]) -> str:
        # GROWI error responses may use "errors" list or a top-level "error" string
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            return f"GROWI returned {response.status_code}: {'; '.join(map(str, errors))}"
        error_msg = payload.get("error") or payload.get("message")
        if error_msg:
            return f"GROWI returned {response.status_code}: {error_msg}"
        return (
            f"GROWI returned {response.status_code} for "
            f"{response.request.method} {response.request.url.path}"
        )
