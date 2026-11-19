import unittest

from web.rph_phase_display import activity_without_schedule, phase_heading


class RphPhaseDisplayTests(unittest.TestCase):
    def test_removes_phase_metadata_and_preserves_activity_and_time_questions(self):
        source = (
            "5 minit\n"
            "Aktiviti 1 (10 minit) – Baca Waktu\n"
            "Guru meminta murid menetapkan pemasa selama 10 minit.\n\n"
            "2. Activity 2 – Guided Practice (10–15 minutes)\n"
            "Pupils compare 15 min and 20 min.\n"
            "Reinforcement / PBD (8 minutes):\n"
            "5 minutes\n"
            "Find the duration from 08:00 to 08:30.\n"
            "Aktiviti 3: Murid catat tempoh perjalanan (30 minit)"
        )
        expected = (
            "Aktiviti 1 – Baca Waktu\n"
            "Guru meminta murid menetapkan pemasa selama 10 minit.\n\n"
            "2. Activity 2 – Guided Practice\n"
            "Pupils compare 15 min and 20 min.\n"
            "Reinforcement / PBD:\n"
            "Find the duration from 08:00 to 08:30.\n"
            "Aktiviti 3: Murid catat tempoh perjalanan (30 minit)"
        )
        self.assertEqual(activity_without_schedule(source), expected)

    def test_keeps_a_timed_answer_inside_an_activity(self):
        value = "Teacher asks for the time elapsed.\n15 minutes\nPupils share how they know."
        self.assertEqual(activity_without_schedule(value), value)

    def test_strips_only_the_planned_duration_from_localized_headings(self):
        self.assertEqual(phase_heading("ڤنوتوڤ (٥ مينيت)"), "ڤنوتوڤ")
        self.assertEqual(phase_heading("التمهيد (٥ دقائق)"), "التمهيد")
        self.assertEqual(phase_heading("Set Induction (5 min)"), "Set Induction")
