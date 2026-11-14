"""Behavioral checks for source freshness and the new statistical estimands."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import sha256, require_current_profile, require_quality_gate
from review_analysis import contrasts, month_block_bootstrap, carrier_comparison

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'reports').mkdir()
        names=['flights.csv','airports.csv','airlines.csv']
        for name in names:(self.root/name).write_text('id,value\n1,10\n',encoding='utf-8')
        self.hashes={name:sha256(self.root/name) for name in names}
        self.write('data_profile.json',{'profile_run_id':'completed-run','source_sha256':self.hashes})
        self.write('source_manifest.json',{'profile_run_id':'completed-run','sha256':self.hashes})
        self.write('quality_gate.json',{'quality_status':'READY','source_sha256':self.hashes})
    def tearDown(self):self.temp.cleanup()
    def write(self,name,value):(self.root/'reports'/name).write_text(json.dumps(value),encoding='utf-8')
    def test_ready_and_warning_statuses_are_supported(self):
        for status in ['READY','READY_WITH_WARNINGS','READY WITH WARNINGS']:
            self.write('quality_gate.json',{'quality_status':status,'source_sha256':self.hashes})
            self.assertEqual(require_quality_gate(self.root)['quality_status'],status)
    def test_modified_source_blocks_reuse(self):
        (self.root/'flights.csv').write_text('id,value\n1,999\n',encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError,'Source changed'):require_current_profile(self.root)
    def test_interrupted_profile_publication_blocks_reuse(self):
        self.write('source_manifest.json',{'profile_run_id':'different-run','sha256':self.hashes})
        with self.assertRaisesRegex(RuntimeError,'Incomplete'):require_current_profile(self.root)
    def test_unidentified_or_stale_gate_blocks_analysis(self):
        self.write('quality_gate.json',{'quality_status':'READY'})
        with self.assertRaisesRegex(RuntimeError,'different or unidentified'):require_quality_gate(self.root)
    def test_not_ready_blocks_analysis(self):
        self.write('quality_gate.json',{'quality_status':'NOT_READY','source_sha256':self.hashes})
        with self.assertRaisesRegex(RuntimeError,'blocks analysis'):require_quality_gate(self.root)

class StatisticalReviewTests(unittest.TestCase):
    def test_mean_uses_flight_exposure_not_equal_day_weights(self):
        days=np.array([[[10,0,1,10,1],[10,100,2,10,2]],[[90,900,9,90,9],[10,100,2,10,2]]],dtype=float)
        self.assertAlmostEqual(contrasts(days.sum(axis=0))[0],1.0)
    def test_paired_blocks_preserve_constant_effects(self):
        values=np.tile(np.array([[100,0,10,110,15],[100,1000,20,120,25]],dtype=float),(56,1,1))
        months=np.repeat([1,2],28)
        expected=contrasts(values.sum(axis=0))
        for block in [1,7,14]:
            samples=month_block_bootstrap(values,months,block,repetitions=100,seed=42)
            np.testing.assert_allclose(samples,np.tile(expected,(100,1)),atol=1e-12)
    def test_bootstrap_is_reproducible_without_global_rng_state(self):
        values=np.tile(np.array([[100,0,10,110,15],[100,1000,20,120,25]],dtype=float),(28,1,1))
        values[:,1,1]+=np.arange(28)*5
        first=month_block_bootstrap(values,np.ones(28),7,100,123)
        np.random.seed(999)
        second=month_block_bootstrap(values,np.ones(28),7,100,123)
        np.testing.assert_array_equal(first,second)
    def test_empty_denominators_and_oversized_blocks_are_rejected(self):
        with self.assertRaises(ValueError):contrasts(np.zeros((2,5)))
        values=np.tile(np.array([[10,0,1,10,1],[10,100,2,10,2]]),(7,1,1))
        with self.assertRaises(ValueError):month_block_bootstrap(values,np.ones(7),14,100,1)
    def test_selection_and_standardization_are_separate(self):
        rows=[]
        for route,carrier,n,events in [('A','NK',80,64),('A','ZZ',20,16),('B','NK',20,4),('B','ZZ',80,16),('C','NK',100,100)]:
            for i in range(n):
                rows.append({'AIRLINE':carrier,'ORIGIN_AIRPORT':route,'DESTINATION_AIRPORT':'D','MONTH':1,'BAND':'EARLY','ARR':60 if i<events else 0,'SEVERE':i<events})
        result=carrier_comparison(pd.DataFrame(rows),'NK','BAND',10)
        self.assertAlmostEqual(result['geographic_raw_severe_gap_pp'],52)
        self.assertAlmostEqual(result['retained_raw_severe_gap_pp'],36)
        self.assertAlmostEqual(result['standardized_severe_gap_pp'],0)
        self.assertEqual(result['retained_carrier_n'],100)
        self.assertAlmostEqual(result['carrier_common_support_share'],.5)

if __name__=='__main__':unittest.main()
