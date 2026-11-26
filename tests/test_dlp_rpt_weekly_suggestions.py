"""Exercise the real ten DLP published RPTs and the day/week suggestion route."""
import os
import unittest
from datetime import date
from unittest.mock import patch
from web.dlp_rpt_weekly_suggestions import COUNTS,published_weeks,suggestion
from web.rph_hari_ini_web import weekly_rpt_suggestion

class WeeklyDLP(unittest.TestCase):
    def test_all_source_rows(self):
        for (code,year),(n,m) in COUNTS.items():
            weeks=published_weeks(code,year)
            labels=[label for row in weeks.values() for label in row["labels"]]
            self.assertEqual(len(labels),n+m,(code,year))
            self.assertEqual([l for l in labels if l.startswith("Lesson")],[f"Lesson {i:02d}" for i in range(1,n+1)])
            self.assertEqual([l for l in labels if l.startswith("Review")],[f"Review {i:02d}" for i in range(1,m+1)])
            self.assertLessEqual(max(weeks),38)
            for week,row in weeks.items():
                for a in (True,False):
                    start=date.fromisoformat(row["dates"][0 if a else 1][0])
                    self.assertEqual(suggestion(code,year,start,a)["dlp_labels"],row["labels"])
            with patch.dict(os.environ,{"CIKGULAJU_DLP_WEEKLY_SUGGESTIONS":"1"}):
                self.assertEqual(weekly_rpt_suggestion("Pahang",date(2027,1,11),code,year)["dlp_labels"],weeks[2]["labels"])
            print("DLP_WEEKLY_OK",code,year,len(labels),len(weeks),flush=True)

if __name__=="__main__":unittest.main()
