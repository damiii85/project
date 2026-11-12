import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from server import match_courses,COURSES
class MatchingTests(unittest.TestCase):
 def test_data_loaded(self):self.assertGreater(len(COURSES),0)
 def test_swimming_in_bundang(self):
  rows=match_courses({'sport':'수영','center':'분당스포츠센터'})
  self.assertTrue(rows)
  self.assertTrue(all(r['sport']=='수영' and r['center']=='분당스포츠센터' for r in rows))
 def test_budget(self):
  rows=match_courses({'budget':'50000','min_year':'0'})
  self.assertTrue(all(r['price'] is not None and r['price']<=50000 for r in rows))
 def test_year(self):
  rows=match_courses({'min_year':'2026'})
  self.assertTrue(all(r['month'][:4]>='2026' for r in rows))
 def test_time(self):
  rows=match_courses({'period':'저녁','min_year':'0'})
  self.assertTrue(all(int(r['time'][:2])>=18 for r in rows))
if __name__=='__main__':unittest.main()
