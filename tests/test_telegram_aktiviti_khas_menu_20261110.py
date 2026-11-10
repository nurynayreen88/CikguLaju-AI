"""Focused, no-network parity tests for Telegram Special Activity RPH menu."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from rph_standalone.aktiviti_khas import engine
from web.telegram_special_activity_menu import install, PREFIX


class DummyResponse:
    ok = True
    def __init__(self, success=True):
        self.ok = success

    def json(self):
        return {"ok": self.ok, "result": {"message_id": 4}}


class FakeTelegram:
    API = "https://example.invalid"
    def __init__(self, *, allow=True, delivered=True):
        self.state = {}
        self.messages = []
        self.docs = []
        self.charges = 0
        self.gate_checks = 0
        self.menu_calls = 0
        self.fallback_calls = []
        self.allow = allow
        self.delivered = delivered

    def menu(self, cid, show_persistent=False):
        self.menu_calls += 1
        return {"original": True, "persistent": show_persistent}

    def callback(self, cid, data):
        self.fallback_calls.append(data)
        return "ordinary route"

    def send(self, cid, text, kb=None):
        self.messages.append((cid, text, kb))
        return DummyResponse()

    def send_document(self, cid, path, caption=""):
        content = Path(path).read_bytes()
        self.docs.append((content, caption, Path(path).name))
        return DummyResponse(success=self.delivered)

    def _credit_gate(self, cid, ss):
        self.gate_checks += 1
        if not self.allow:
            self.send(cid, "No free trial remaining")
            return False
        self.state.setdefault(cid, {})["_free_generation_pending_v25282"] = True
        return True

    def _consume_free_after_success_v25282(self, cid, reason):
        if self.state.setdefault(cid, {}).pop("_free_generation_pending_v25282", False):
            self.charges += 1
        return 9

    def _telegram_delivery_ok_v25279(self, response):
        return bool(response.ok and response.json()["ok"])

    def _profile_class_records(self, cid):
        return [{"name": "1 Bestari", "students": 30},
                {"name": "6 Cekal", "students": 28}]


def _act(bot, code):
    return bot.callback(123, PREFIX + code)


def _transisi_until_preview(bot):
    _act(bot, "home")
    _act(bot, "t")
    _act(bot, "tf:0")
    ss = bot.state[123]["_aktiviti_khas_20261110"]
    assert ss["kind"] == engine.TRANSISI
    assert ss["year"] == 1
    assert len(ss["options"]) == 10
    assert len(ss["digest"]) == 64
    _act(bot, "a:" + ss["options"][0])
    _act(bot, "c:0")
    _act(bot, "d:t")
    assert ss["class"] == "1 Bestari"
    assert ss["students"] == "30"
    assert ss["date"] == datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date().isoformat()
    return ss


def test_menu_is_additive_and_existing_callbacks_are_unchanged():
    bot = FakeTelegram()
    assert install(bot) is True
    assert install(bot) is True
    result = bot.menu(123, show_persistent=True)
    assert result == {"original": True, "persistent": True}
    assert bot.menu_calls == 1
    assert bot.messages == []  # no extra message on the main menu
    _act(bot, "home")
    assert any(PREFIX + "home" not in str(keyboard)
               for _, _, keyboard in bot.messages)
    assert any("RPH Aktiviti Khas" in text for _, text, _ in bot.messages)
    assert bot.callback(123, "rpt2027_home") == "ordinary route"
    assert bot.fallback_calls == ["rpt2027_home"]


def test_year1_transisi_same_catalog_word_and_pdf_only_one_trial():
    bot = FakeTelegram()
    assert install(bot)
    ss = _transisi_until_preview(bot)
    assert bot.charges == 0
    assert any("DRAF" in text for _, text, _ in bot.messages)
    _act(bot, "w")
    assert len(bot.docs) == 1
    assert bot.docs[0][0][:2] == b"PK"
    assert bot.docs[0][2].endswith("DRAF.docx")
    assert bot.charges == 1
    assert bot.gate_checks == 1
    _act(bot, "f")
    assert len(bot.docs) == 2
    assert bot.docs[1][0][:5] == b"%PDF-"
    assert bot.charges == 1
    assert bot.gate_checks == 1
    # Old Telegram inline keyboards can be pressed again; no double charge.
    _act(bot, "d:t")
    _act(bot, "f")
    assert len(bot.docs) == 3
    assert bot.charges == 1
    assert ss["_confirmed_delivery_key"]


def test_post_syllabus_year6_subject_and_activity_match():
    bot = FakeTelegram()
    assert install(bot)
    _act(bot, "p")
    _act(bot, "py:6")
    _act(bot, "ps:3")  # Sains, index derived from shared engine.SPECIAL_SUBJECTS
    ss = bot.state[123]["_aktiviti_khas_20261110"]
    assert ss["year"] == 6
    assert ss["subject"] == "Sains"
    assert len(ss["options"]) == 1
    chosen = ss["options"][0]
    row = engine.select(engine.SELEPAS, 6, chosen, ss["digest"])
    assert row["subject_options"] == ["Sains"]
    _act(bot, "a:" + chosen)
    _act(bot, "c:x")
    _act(bot, "d:x")
    _act(bot, "f")
    assert bot.docs and bot.docs[0][0].startswith(b"%PDF-")
    assert bot.charges == 1
    assert ss["date"] == "" and ss["class"] == ""


def test_unrelated_or_forged_old_selection_fails_closed():
    bot = FakeTelegram()
    assert install(bot)
    _act(bot, "py:6")
    _act(bot, "ps:3")
    _act(bot, "a:K01")  # Transition ID, not in chosen subject's options.
    assert bot.docs == []
    assert bot.charges == 0
    ss = bot.state[123]["_aktiviti_khas_20261110"]
    _act(bot, "a:" + ss["options"][0])
    ss["digest"] = "0" * 64
    _act(bot, "review")
    assert bot.docs == []
    assert any("Pilihan atau sumber" in text for _, text, _ in bot.messages)


def test_trial_gate_denial_never_renders_or_spends():
    bot = FakeTelegram(allow=False)
    assert install(bot)
    _transisi_until_preview(bot)
    _act(bot, "w")
    assert bot.gate_checks == 1
    assert bot.charges == 0
    assert bot.docs == []


def test_failed_telegram_send_does_not_debit():
    bot = FakeTelegram(delivered=False)
    assert install(bot)
    _transisi_until_preview(bot)
    _act(bot, "w")
    assert len(bot.docs) == 1
    assert bot.charges == 0
    assert bot.state[123].get("_free_generation_pending_v25282") is None
    assert bot.state[123]["_aktiviti_khas_20261110"]["delivered"] is False


def test_transition_does_not_offer_year2():
    bot = FakeTelegram()
    assert install(bot)
    _act(bot, "t")
    ss = bot.state[123]["_aktiviti_khas_20261110"]
    assert ss["year"] == 1
    _act(bot, "py:2")  # Year 2 is post-syllabus only.
    ss = bot.state[123]["_aktiviti_khas_20261110"]
    assert ss["kind"] == engine.SELEPAS
    assert ss["year"] == 2
