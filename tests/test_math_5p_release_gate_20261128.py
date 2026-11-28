import os
import unittest
from unittest.mock import patch
from web import kp2027_math_5p_release as gate

class TestMathReleaseGate(unittest.TestCase):
    def test_manifest_and_default_deny(self):
        rows=gate.records()
        self.assertEqual(len(rows),249)
        self.assertEqual(sum(r["correction_present"] for r in rows.values()),40)
        for flag in ("0","1"):
            with patch.dict(os.environ,{gate.FIVE_P_FLAG:flag}):
                self.assertEqual(gate.released_groups(),{"A":[],"B":[]})
        approved={k:dict(r) for k,r in rows.items()}
        approved["A",1].update(ready=True,status="APPROVED_FOR_RELEASE")
        approved["B",1].update(ready=True,status="APPROVED_FOR_RELEASE")
        with patch.dict(os.environ,{gate.FIVE_P_FLAG:"1"}),patch.object(gate,"records",return_value=approved):
            self.assertEqual(gate.released_groups({"A":[1,2],"B":[2]}),{"A":[1],"B":[]})
            self.assertTrue(gate.is_released("A",1))
            self.assertFalse(gate.is_released("A",True))
            self.assertFalse(gate.is_released("A",2))
        with patch.dict(os.environ,{gate.FIVE_P_FLAG:"1"}),patch.object(gate,"records",side_effect=ValueError("drift")):
            self.assertEqual(gate.released_groups(),{"A":[],"B":[]})

if __name__=="__main__": unittest.main()
