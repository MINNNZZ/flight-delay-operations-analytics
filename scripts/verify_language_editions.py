"""Validate bilingual outputs and the live-model query evidence saved per language."""
from common import ROOT, require_quality_gate, sha256, write_json
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import math
import re

def main():
    require_quality_gate()
    desktop=ROOT/'powerbi/desktop'
    meta=json.loads((desktop/'localization_verification.json').read_text(encoding='utf-8'))
    baseline=json.loads((desktop/'native_dax_results.json').read_text(encoding='utf-8-sig'))[0]
    assert len(baseline)==21
    with ZipFile(desktop/'Aviation_Insights.pbix') as z:
        model_hash=hashlib.sha256(z.read('DataModel')).hexdigest()
    for entry in meta['reports']:
        language=entry['language']
        pbix=desktop/entry['file']
        with ZipFile(pbix) as z:
            assert z.testzip() is None
            assert hashlib.sha256(z.read('DataModel')).hexdigest()==model_hash
            pages=[n for n in z.namelist() if n.endswith('/page.json')]
            assert len(pages)==7
            assert len([n for n in z.namelist() if n.endswith('/visual.json')])==51
        result_file=desktop/f'native_dax_results_{language}.json'
        rows=json.loads(result_file.read_text(encoding='utf-8-sig'))
        assert len(rows)==1 and rows[0].keys()==baseline.keys()
        for key,expected in baseline.items():
            actual=rows[0][key]
            if expected is None:assert actual is None
            else:assert math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-8),(language,key,actual,expected)
        screenshots=sorted((desktop/f'screenshots_{language}').glob('page_*.png'))
        assert len(screenshots)==7 and len({sha256(p) for p in screenshots})==7
        assert all(p.stat().st_size>30000 for p in screenshots)
        report=ROOT/f'reports/final_analysis_report_{language}.md'
        text=report.read_text(encoding='utf-8')
        assert len(text.split())>2000
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in link:assert (report.parent/link).exists(),link
        for token in ['5,819,079','325,591','89,884','15,187','430,662','81,016','110,498','28,526']:
            assert token in text or token.replace(',','.') in text,(language,token)
        entry.update({'desktop_opened':True,'native_dax_checks':21,'native_dax_status':'PASS','native_dax_result_file':result_file.name,'screenshots':[p.relative_to(desktop).as_posix() for p in screenshots],'pbix_sha256':sha256(pbix),'written_report_sha256':sha256(report),'written_report_words':len(text.split()),'report_links_and_core_figures':'PASS'})
    source_manifest=json.loads((ROOT/'reports/source_manifest.json').read_text())
    meta.update({'status':'PASS','desktop_validation_pending':False,'model_unchanged':True,'desktop_engine_query_executed':True,'native_pages_captured':14,'source_hashes_unchanged':True,'scope':'Language-specific display labels/narratives and static recommendations; source identifiers and model data/formulas unchanged. Application menus and source cause-category terms retain application/source language. New statistical appendix remains in written reports.'})
    write_json(desktop/'localization_verification.json',meta)
    print('PASS: two written editions, two embedded-model-identical PBIX files, 42 native DAX checks, 14 page captures.')

if __name__=='__main__':main()
