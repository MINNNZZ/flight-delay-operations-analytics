"""Shared readers; all source files remain read-only."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
TABLES = REPORTS / 'tables'
PROCESSED = ROOT / 'data' / 'processed'
CODES = ['AIRLINE', 'TAIL_NUMBER', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'CANCELLATION_REASON']
CAUSES = ['AIR_SYSTEM_DELAY', 'SECURITY_DELAY', 'AIRLINE_DELAY', 'LATE_AIRCRAFT_DELAY', 'WEATHER_DELAY']
TIMES = ['SCHEDULED_DEPARTURE', 'DEPARTURE_TIME', 'WHEELS_OFF', 'WHEELS_ON', 'SCHEDULED_ARRIVAL', 'ARRIVAL_TIME']
KEY = ['YEAR', 'MONTH', 'DAY', 'AIRLINE', 'FLIGHT_NUMBER', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'SCHEDULED_DEPARTURE']

def setup():
    for p in [REPORTS, TABLES, PROCESSED]:
        p.mkdir(parents=True, exist_ok=True)

def read_flights():
    columns = pd.read_csv(ROOT / 'flights.csv', nrows=0).columns
    # Float32 represents these integer-valued fields exactly; verify integrality in profiling.
    dtypes = {c: ('category' if c in CODES else 'float32') for c in columns}
    return pd.read_csv(ROOT / 'flights.csv', dtype=dtypes, low_memory=False)

def read_dimensions():
    return pd.read_csv(ROOT / 'airports.csv'), pd.read_csv(ROOT / 'airlines.csv')

def dates(df):
    # pandas assembles YYYYMMDD arithmetically: float32 cannot represent every
    # eight-digit calendar value, even though each input component is exact.
    parts = df[['YEAR', 'MONTH', 'DAY']].astype('float64').rename(columns=str.lower)
    return pd.to_datetime(parts, errors='coerce')

def valid_time(s):
    return s.isna() | ((s >= 0) & (s < 2400) & (s % 100 < 60) & (s % 1 == 0)) | s.eq(2400)

def minutes(s):
    return (s // 100 * 60 + s % 100) % 1440

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def require_current_profile(root=None):
    """Reject a partial or stale DQA before using its conclusions."""
    base = Path(root) if root is not None else ROOT
    profile = json.loads((base / 'reports' / 'data_profile.json').read_text(encoding='utf-8'))
    manifest = json.loads((base / 'reports' / 'source_manifest.json').read_text(encoding='utf-8'))
    fingerprint = profile.get('source_sha256', {})
    names = ['flights.csv', 'airports.csv', 'airlines.csv']
    if not profile.get('profile_run_id') or profile['profile_run_id'] != manifest.get('profile_run_id'):
        raise RuntimeError('Incomplete or legacy quality profile; rerun scripts/profile_data.py.')
    for name in names:
        if not fingerprint.get(name) or fingerprint[name] != manifest.get('sha256', {}).get(name):
            raise RuntimeError(f'Quality profile has inconsistent source identity: {name}.')
        if sha256(base / name) != fingerprint[name]:
            raise RuntimeError(f'Source changed after quality assessment: {name}. Rerun profiling and review cleaning.')
    return profile

def require_quality_gate(root=None):
    base = Path(root) if root is not None else ROOT
    profile = require_current_profile(base)
    gate = json.loads((base / 'reports' / 'quality_gate.json').read_text(encoding='utf-8'))
    status = str(gate.get('quality_status', '')).upper().replace(' ', '_')
    if status not in {'READY', 'READY_WITH_WARNINGS'}:
        raise RuntimeError(f'Quality gate blocks analysis: {status or "missing status"}.')
    if gate.get('source_sha256') != profile['source_sha256']:
        raise RuntimeError('Quality gate belongs to different or unidentified sources; review cleaning and rerun analysis.')
    return gate

def write_json(path, obj):
    def convert(value):
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, (pd.Timestamp, Path)):
            return str(value)
        raise TypeError(type(value).__name__)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=convert, allow_nan=False), encoding='utf-8')

def csv(df, name):
    df.to_csv(TABLES / f'{name}.csv', index=False, encoding='utf-8-sig')
