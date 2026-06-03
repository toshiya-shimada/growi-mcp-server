from __future__ import annotations

from dataclasses import dataclass

from growi_mcp_server.domain.services import GrowiService
from growi_mcp_server.settings import Settings


@dataclass(slots=True)
class AppContext:
    settings: Settings
    service: GrowiService
