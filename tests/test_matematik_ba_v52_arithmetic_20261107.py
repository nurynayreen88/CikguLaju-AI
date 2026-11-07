"""Arithmetic regression for the source-scoped v52 classroom examples."""
from fractions import Fraction as F
import unittest

class V52ArithmeticExamples(unittest.TestCase):
    def test_fraction_and_decimal_unit_results(self):
        self.assertEqual(F(1,2)*100+25+F(1,10)*100,85) # cm
        self.assertEqual(F(5,2)-F(3,4)-F(1,4),F(3,2)) # m
        self.assertEqual(F(3,4)/3*100,25) # cm
        self.assertEqual((1+F(3,8))*1000,1375) # g
        self.assertEqual(5-F(12,10)-F(8,10),3) # kg
        self.assertEqual(F(5,2)-F(3,4)-F(25,100),F(3,2)) # kg
        self.assertEqual(F(1209,100)-F(780,1000),F(1131,100)) # L
        self.assertEqual(F(3,2)-F(1,4),F(5,4)) # L
        self.assertEqual(F(84,10)-F(136,100)-F(491,100),F(213,100)) # L
        self.assertEqual(F(7,2)-F(1,2)-F(250,1000),F(11,4)) # L
        self.assertEqual(48*F(23,100),F(1104,100)) # L
        self.assertEqual(F(3,4)*4,3) # L
        self.assertEqual(F(3,4)/3*1000,250) # mL
        self.assertEqual(F(693,100)/15*1000,462) # mL
        self.assertEqual(F(48,1000),F(48,1000)) # L
        self.assertEqual(F(74,10)/50,F(148,1000)) # L
        self.assertEqual(F(3,2)/3*1000,500) # mL

    def test_ratio_numerator_denominator_consistency(self):
        self.assertEqual(F(6,9),F(2,3))
        self.assertEqual(F(6,15),F(2,5))
        self.assertEqual(F(15,9),F(5,3))
        self.assertEqual(F(8,12),F(2,3))
        self.assertEqual(F(8,20),F(2,5))
        self.assertEqual(F(20,12),F(5,3))
        self.assertEqual(F(4,6),F(2,3))
        self.assertEqual(F(4,10),F(2,5))
        self.assertEqual(F(10,6),F(5,3))

if __name__=="__main__":
    unittest.main()
