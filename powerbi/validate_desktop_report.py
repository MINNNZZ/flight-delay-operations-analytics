from pathlib import Path
import json, hashlib, urllib.request, urllib.error
import jsonschema
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'schema'/'cache';CACHE.mkdir(parents=True,exist_ok=True)
memo={}
def fetch(url):
    if url in memo:return memo[url]
    assert urlparse(url).hostname=='developer.microsoft.com',url
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if not path.exists():
        try:b=urllib.request.urlopen(url,timeout=25).read()
        except urllib.error.HTTPError as e:
            if e.code!=404 or 'schema.embedded.json' not in url:raise
            b=urllib.request.urlopen(url.replace('schema.embedded.json','schema-embedded.json'),timeout=25).read()
        path.write_bytes(b)
    memo[url]=json.loads(path.read_text(encoding='utf-8-sig'))
    return memo[url]

errors=[];files=0
for p in (ROOT/'desktop').rglob('*'):
    if not p.is_file() or p.suffix not in ['.json','.pbip','.pbir','.pbism'] or '/StaticResources/' in p.as_posix():continue
    data=json.loads(p.read_text(encoding='utf-8-sig'))
    if '$schema' not in data:continue
    uri=data['$schema'];schema=fetch(uri)
    resolver=jsonschema.RefResolver(uri,schema,handlers={'https':fetch})
    validator=jsonschema.Draft7Validator(schema,resolver=resolver)
    for e in validator.iter_errors(data):errors.append({'path':str(p.relative_to(ROOT)),'location':list(e.path),'message':e.message})
    files+=1
print(json.dumps({'files_checked':files,'errors':errors},ensure_ascii=True,indent=2))
if errors:raise SystemExit(1)
