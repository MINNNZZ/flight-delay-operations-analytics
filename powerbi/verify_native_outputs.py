from pathlib import Path
from zipfile import ZipFile
import json, hashlib, math

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'/'desktop'
raw=json.loads((OUT/'native_dax_results.json').read_text(encoding='utf-8-sig'))
assert len(raw)==1
row={k.strip('[]'):v for k,v in raw[0].items()}
summary=json.loads((ROOT/'reports'/'analysis_summary.json').read_text(encoding='utf-8'))['overall']
expected={
    'Total Flights':summary['flights'],'Completed Flights':summary['completed'],
    'Severe Flights':summary['severe'],'Cancelled Flights':summary['cancelled'],
    'Diverted Flights':summary['diverted'],'Disrupted Flights':summary['disrupted'],
    'On-Time Flights':summary['on_time'],'Severe Delay Rate':summary['severe_rate'],
    'Cancellation Rate':summary['cancel_rate'],'On-Time Scheduled Rate':summary['on_time_scheduled_rate'],
    'Average Arrival Delay':summary['avg_arr'],'Median Arrival Delay':summary['median_arr'],
    'P95 Arrival Delay':66,'Positive Arrival Minutes':summary['positive_arr_minutes'],
    'Reported Cause Minutes':62651867,'Geographically Resolved Flights':5332914,
    'October Flights':486165,'October Resolved Flights':0,
    'Airline Dimension Rows':14,'Airport Dimension Rows':323,'Date Dimension Rows':365,
}
for k,v in expected.items():
    actual=row[k]
    if k=='October Resolved Flights' and actual is None:actual=0 # DAX COUNTROWS(empty) is BLANK.
    assert actual is not None and math.isclose(actual,v,rel_tol=1e-10,abs_tol=1e-8),(k,actual,v)
screens=sorted((OUT/'screenshots').glob('page_*.png'))
assert len(screens)==7
hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in screens]
assert len(set(hashes))==7,'Page screenshots are not unique'
assert all(p.stat().st_size>30000 for p in screens)
pbix=OUT/'Aviation_Insights.pbix'
with ZipFile(pbix) as z:
    assert z.getinfo('DataModel').file_size>1000000,'Embedded data model missing'
    if 'Report/Layout' in z.namelist():
        layout=json.loads(z.read('Report/Layout').decode('utf-16-le'))
        assert len(layout['sections'])==7
        visuals=sum(len(p['visualContainers']) for p in layout['sections'])
        assert visuals>=51
    else:
        assert len([n for n in z.namelist() if n.endswith('/page.json')])==7
        visuals=len([n for n in z.namelist() if n.endswith('/visual.json')])
manifest=json.loads((ROOT/'reports'/'source_manifest.json').read_text(encoding='utf-8'))
result={'status':'PASS','desktop_version':'2.148.878.0','native_model_refresh':'Analysis Services TOM inside running Power BI Desktop','native_dax_checks':len(expected),'native_dax_results':row,'report_pages':7,'native_visuals_and_text':visuals,'page_screenshots':[str(p.relative_to(OUT)) for p in screens],'saved_pbix':str(pbix.relative_to(ROOT)),'pbix_bytes':pbix.stat().st_size,'source_instruction_check':'Not applicable to standalone public repository','limitations':['Historical 2015 data','Airport/route pages exclude unresolved October codes','Top airport/route lists fixed from baseline rankings','No cloud publishing']}
(OUT/'desktop_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','native_dax_checks':len(expected),'pages':7,'visuals':visuals,'pbix_bytes':pbix.stat().st_size},indent=2))
