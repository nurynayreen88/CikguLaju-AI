"""Durable RPH trial reservation client (staging; not wired into production).

Call reserve before generation, commit after confirmed Telegram delivery, and
release on generation/delivery failure. All calls require server-side Supabase
service credentials through the existing _sb_request function.
"""
from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class ReservationResult:
    ok: bool
    remaining: int | None
    status: str


def _rpc_row(request: Callable[..., Any], function: str, user_id: int, request_id: str) -> dict:
    if not isinstance(request_id, str) or not 8 <= len(request_id) <= 200:
        raise ValueError("request_id must be a stable 8–200 character string")
    result = request(
        "POST",
        "rpc/" + function,
        json={"p_telegram_user_id": int(user_id), "p_request_id": request_id},
    )
    if isinstance(result, list):
        if len(result) != 1:
            raise RuntimeError("Unexpected Supabase RPC response length")
        result = result[0]
    if not isinstance(result, dict) or "ok" not in result:
        raise RuntimeError("Invalid Supabase RPC response")
    return result


def reserve(request: Callable[..., Any], user_id: int, request_id: str) -> ReservationResult:
    row = _rpc_row(request, "cikgulaju_reserve_rph_trial", user_id, request_id)
    return ReservationResult(bool(row["ok"]), row.get("remaining"), str(row.get("reservation_status", "")))


def commit(request: Callable[..., Any], user_id: int, request_id: str) -> ReservationResult:
    row = _rpc_row(request, "cikgulaju_commit_rph_trial", user_id, request_id)
    return ReservationResult(bool(row["ok"]), row.get("remaining"), str(row.get("reservation_status", "")))


def release(request: Callable[..., Any], user_id: int, request_id: str) -> ReservationResult:
    row = _rpc_row(request, "cikgulaju_release_rph_trial", user_id, request_id)
    return ReservationResult(bool(row["ok"]), row.get("remaining"), str(row.get("reservation_status", "")))
