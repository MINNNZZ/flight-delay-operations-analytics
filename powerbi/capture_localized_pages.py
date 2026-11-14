"""Capture all localized native pages in task-selected Desktop instances."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import base64
import json
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--vi-pid',type=int,required=True)
parser.add_argument('--en-pid',type=int,required=True)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
helper=ROOT/'powerbi/desktop_control.ps1'
def quote(s):return "'"+str(s).replace("'","''")+"'"
for language,pid in [('en',args.en_pid),('vi',args.vi_pid)]:
    folder=ROOT/f'powerbi/desktop/screenshots_{language}'
    folder.mkdir(exist_ok=True)
    with ZipFile(ROOT/f'powerbi/desktop/Aviation_Insights_{language}.pbix') as z:
        page_names={}
        for name in z.namelist():
            if name.endswith('/page.json'):
                obj=json.loads(z.read(name));page_names[obj['name']]=obj['displayName']
        order=json.loads(z.read('Report/definition/pages/pages.json'))['pageOrder']
    commands=["$ErrorActionPreference='Stop'"]
    for index,name in enumerate(order,1):
        commands.append(f'& {quote(helper)} -ProcessId {pid} -Action Invoke -Name {quote(page_names[name])}')
        commands.append(f'& {quote(helper)} -ProcessId {pid} -Action Screenshot -OutputPath {quote(folder/f"page_{index}.png")}')
    encoded=base64.b64encode('\n'.join(commands).encode('utf-16-le')).decode('ascii')
    result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',encoded],capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))
    assert len(list(folder.glob('page_*.png')))==7
    print(language,': 7 native page screenshots saved.',flush=True)
