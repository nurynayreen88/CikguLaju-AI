"""Supabase-backed RPH trial reservation client (staging, not yet wired into app.py).

Only a confirmed Telegram sendDocument response authorizes commit.
Never silently downgrade to legacy post-delivery debit on RPC failure.
"""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Reservation:
    request_id: str
    remaining: int
    status: str


class TrialReservationError(RuntimeError):
    pass


def _row(response):
    if isinstance(response, list):
        return response[0] if response else {}
    return response or {}


class TrialReservationClient:
    def __init__(self, rpc: Callable):
        """rpc(name, payload) -> Supabase JSON response; inject for tests."""
        self.rpc = rpc

    def _call(self, action: str, user_id: int, request_id: str):
        if not request_id or len(request_id) < 8 or len(request_id) > 200:
            raise ValueError("Invalid request_id")
        result = _row(self.rpc(
            "cikgulaju_" + action + "_rph_trial",
            {"p_telegram_user_id": int(user_id), "p_request_id": request_id},
        ))
        if not isinstance(result, dict) or "ok" not in result:
            raise TrialReservationError("Unexpected reservation RPC response")
        return result

    def reserve(self, user_id: int, request_id: str) -> Reservation:
        row = self._call("reserve", user_id, request_id)
        if not row["ok"] or row.get("reservation_status") != "reserved":
            raise TrialReservationError("Trial unavailable or request already finalized")
        return Reservation(request_id, int(row["remaining"]), "reserved")

    def commit(self, user_id: int, request_id: str) -> int:
        row = self._call("commit", user_id, request_id)
        if not row["ok"] or row.get("reservation_status") != "committed":
            raise TrialReservationError("Trial commit not confirmed")
        return int(row["remaining"])

    def release(self, user_id: int, request_id: str):
        row = self._call("release", user_id, request_id)
        if not row["ok"] and row.get("reservation_status") != "committed":
            raise TrialReservationError("Trial release not confirmed")
        return row.get("reservation_status")


def telegram_document_confirmed(response) -> bool:
    try:
        return bool(response.ok and response.json().get("ok") is True
                    and response.json().get("result", {}).get("message_id"))
    except (AttributeError, TypeError, ValueError):
        return False


def deliver_with_trial(client: TrialReservationClient, user_id: int,
                       request_id: str, render: Callable, send: Callable):
    """Reserve -> render -> send -> commit. No resend on uncertain commit.

    On a failed delivery, release. If commit fails AFTER Telegram confirms
    delivery, keep the reservation for reconciliation; do NOT release it.
    """
    client.reserve(user_id, request_id)
    delivered = False
    try:
        document = render()
        response = send(document)
        if not telegram_document_confirmed(response):
            raise TrialReservationError("Telegram document delivery not confirmed")
        delivered = True
        remaining = client.commit(user_id, request_id)
        return response, remaining
    except Exception:
        if not delivered:
            client.release(user_id, request_id)
        raise
