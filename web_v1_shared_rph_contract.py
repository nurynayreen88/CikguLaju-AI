"""Shared RPH service contract for future Telegram and web integration.

No production imports, DB connections, quota mutations or file generation.
Both frontends must eventually call the same audited implementation.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RphRequest:
    account_id: str
    lesson_id: str
    output_format: str
    idempotency_key: str


@dataclass(frozen=True)
class RphResult:
    document_id: str
    output_format: str
    download_token: str


class SharedRphService(Protocol):
    def generate(self, request: RphRequest) -> RphResult:
        ...


class UnconfiguredRphService:
    def generate(self, request: RphRequest) -> RphResult:
        raise RuntimeError("Shared RPH generator not connected; generation is disabled")


def validate_rph_request(request: RphRequest) -> None:
    if not isinstance(request, RphRequest):
        raise ValueError("invalid RPH request")
    for value in (request.account_id, request.lesson_id, request.idempotency_key):
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ValueError("invalid RPH request identifier")
    if request.output_format not in ("pdf", "docx"):
        raise ValueError("unsupported output format")
