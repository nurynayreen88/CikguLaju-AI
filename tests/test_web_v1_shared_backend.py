"""Prevent accidentally using disconnected web and Telegram data services."""
import unittest
from web_v1_shared_backend import (
    AccountContext, LessonSelection, DisabledSharedBackend, BackendNotConnected,
)


class SharedBackendTests(unittest.TestCase):
    def test_every_operation_is_disabled_until_same_backend_connected(self):
        backend = DisabledSharedBackend()
        account = AccountContext(telegram_user_id=123, authenticated=True)
        lesson = LessonSelection(3, "ENGLISH", "Welcome", "93")
        operations = (
            lambda: backend.list_verified_lessons(account, 3, "ENGLISH"),
            lambda: backend.list_available_materials(account, lesson),
            lambda: backend.get_account_entitlements(account),
            lambda: backend.generate_materials(account, lesson, ("rph",), "request-123"),
            lambda: backend.authorize_download(account, "file-1"),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(BackendNotConnected):
                operation()


if __name__ == "__main__":
    unittest.main()
