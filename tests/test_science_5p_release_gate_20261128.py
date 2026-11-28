import os
import unittest
from unittest.mock import patch
from web import science_5p_release as gate

class ScienceReleaseGate(unittest.TestCase):
    def test_source_inventory_and_default_deny(self):
        rows=gate.records()
        self.assertEqual(len(rows),205)
        self.assertEqual(sum(y==5 for y,_ in rows),116)
        self.assertEqual(sum(y==6 for y,_ in rows),89)
        self.assertEqual(sum(r["correction_present"] for r in rows.values()),82)
        with patch.dict(os.environ,{gate.FLAG:"0"}):
            for y,cid in rows:
                self.assertFalse(gate.is_released(y,cid))
        with patch.dict(os.environ,{gate.FLAG:"1"}):
            for y,cid in rows:
                self.assertTrue(gate.is_released(y,cid))
        approved={k:dict(v,ready=False,status="PENDING_INTERNAL_PUBLICATION_APPROVAL") for k,v in rows.items()}
        key=5,"SK27-SCI-Y5-PDP-001"
        approved[key].update(ready=True,status="APPROVED_FOR_RELEASE")
        with patch.object(gate,"records",return_value=approved):
            with patch.dict(os.environ,{gate.FLAG:"0"}):
                self.assertFalse(gate.is_released(*key))
            with patch.dict(os.environ,{gate.FLAG:"1"}):
                self.assertTrue(gate.is_released(*key))
                self.assertFalse(gate.is_released(6,key[1]))
                self.assertFalse(gate.is_released(5,"SK27-SCI-Y5-PDP-002"))
                self.assertFalse(gate.is_released("5",key[1]))
        with patch.dict(os.environ,{gate.FLAG:"1"}),patch.object(gate,"records",side_effect=ValueError("drift")):
            self.assertFalse(gate.is_released(*key))

if __name__=="__main__": unittest.main()
