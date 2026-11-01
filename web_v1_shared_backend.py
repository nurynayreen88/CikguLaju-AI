"""Shared domain interface for CikguLaju Telegram and Web V1.

No storage or generation implementation is duplicated here. Both clients must
use the same server-side services once audited and explicitly enabled.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class AccountContext:
    telegram_user_id: int
    authenticated: bool


@dataclass(frozen=True)
class LessonSelection:
    year: int
    subject_code: str
    unit: str
    lesson_id: str


class SharedCikguLajuBackend(Protocol):
    def list_verified_lessons(self, account: AccountContext, year: int, subject_code: str) -> Sequence[dict]:
        ...

    def list_available_materials(self, account: AccountContext, lesson: LessonSelection) -> Sequence[dict]:
        ...

    def get_account_entitlements(self, account: AccountContext) -> dict:
        ...

    def generate_materials(self, account: AccountContext, lesson: LessonSelection, kinds: Sequence[str], idempotency_key: str) -> dict:
        ...

    def authorize_download(self, account: AccountContext, material_id: str) -> dict:
        ...


class BackendNotConnected(RuntimeError):
    pass


class DisabledSharedBackend:
    """Explicit fail-closed default, never a mock that returns user data."""
    def _disabled(self):
        raise BackendNotConnected("Shared Telegram/Web backend not connected")

    def list_verified_lessons(self, account, year, subject_code):
        self._disabled()

    def list_available_materials(self, account, lesson):
        self._disabled()

    def get_account_entitlements(self, account):
        self._disabled()

    def generate_materials(self, account, lesson, kinds, idempotency_key):
        self._disabled()

    def authorize_download(self, account, material_id):
        self._disabled()
