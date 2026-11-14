"""Create two localized PBIX reports without changing embedded model bytes."""
from pathlib import Path
from zipfile import ZipFile
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / 'powerbi/desktop'
CATALOG = json.loads((ROOT/'powerbi/localization.json').read_text(encoding='utf-8'))
for key, value in list(CATALOG.items()):
    CATALOG.setdefault(key.upper(), value.upper())
    for n in range(1, 8):
        CATALOG.setdefault(f'{n}. {key}', f'{n}. {value}')

ALIASES_VI = {
    'Total Flights':'Số chuyến theo lịch', 'Arrival Eligible Flights':'Số chuyến đủ điều kiện đến',
    'Average Arrival Delay':'Chậm đến trung bình', 'Median Arrival Delay':'Trung vị chậm đến',
    'Severe Delay Rate':'Tỷ lệ chậm nặng', 'Cancellation Rate':'Tỷ lệ hủy',
    'On-Time Rate':'Tỷ lệ đúng giờ', 'P95 Arrival Delay':'Phân vị 95 chậm đến',
    'Disruption Rate':'Tỷ lệ gián đoạn', 'Positive Arrival Minutes':'Phút chậm dương',
    'Reported Cause Minutes':'Phút nguyên nhân ghi nhận', 'Cause Minutes':'Phút nguyên nhân',
    'Late Aircraft Share of Reported Minutes':'Tỷ trọng phút do tàu bay đến muộn',
    'Airport Rate With Sample Threshold':'Tỷ lệ chậm nặng đủ cỡ mẫu',
    'Route Rate With Sample Threshold':'Tỷ lệ chậm nặng đủ cỡ mẫu',
    'DEP_HOUR':'Giờ khởi hành dự kiến', 'MONTH':'Tháng', 'Cause':'Nhóm nguyên nhân',
    'IATA_CODE':'Mã sân bay', 'ROUTE':'Tuyến bay',
}
ALIASES_EN = {'DEP_HOUR':'Scheduled departure hour','MONTH':'Month','IATA_CODE':'Airport code','ROUTE':'Route'}

ACTIONS = {
    'vi': [
        'ƯU TIÊN CAO — Xác minh lại trên dữ liệu mới trước khi thử nghiệm.',
        'Cuối ngày: rà soát vòng quay tàu bay và năng lực phục hồi tại ORD/LGA. Phụ trách đề xuất: vận hành mạng.',
        'Bằng chứng lịch sử: rủi ro chậm nặng 17–21h là 8,49%, so với 3,61% lúc 06–11h.',
        'TRUNG HẠN — Điều tra phân khúc NK có chênh lệch và hủy chuyến MQ. Phụ trách: nhóm hiệu suất hãng.',
        'KHÔI PHỤC PHẠM VI — Xác minh mã sân bay tháng 10; không tự suy mã. Phụ trách: chủ dữ liệu.',
        'ĐO THÀNH CÔNG — Chậm nặng, gián đoạn, hủy, p95 và cỡ mẫu trên tập so sánh ổn định.',
        'TRẠNG THÁI: ĐỀ XUẤT. Chưa có kết quả can thiệp hoặc bằng chứng tiết kiệm chi phí.'
    ],
    'en': [
        'HIGH PRIORITY — Revalidate with recent data before an operational pilot.',
        'Late day: review aircraft rotations and recovery capacity at ORD/LGA. Proposed owner: network operations.',
        'Historical evidence: severe-delay risk is 8.49% at 17–21h, versus 3.61% at 06–11h.',
        'MEDIUM TERM — Investigate matched NK segments and MQ cancellations. Owner: airline performance team.',
        'RESTORE COVERAGE — Verify the October airport-code crosswalk; never infer codes. Owner: data owner.',
        'SUCCESS METRICS — Severe delays, disruptions, cancellations, p95 and exposure on stable comparison groups.',
        'STATUS: PROPOSED. No intervention outcomes or demonstrated financial savings are available.'
    ]
}

def translate_string(value, language):
    if language == 'vi':
        return value
    if value in CATALOG:
        return CATALOG[value]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return "'" + CATALOG.get(value[1:-1], value[1:-1]) + "'"
    return value

def localize(obj, language):
    if isinstance(obj, list):
        return [localize(v, language) for v in obj]
    if not isinstance(obj, dict):
        return obj
    result = {}
    for key, value in obj.items():
        # Never translate Property/queryRef/entity/filter literals: these bind the model.
        if isinstance(value, str) and key in {'displayName','value'}:
            value = translate_string(value, language)
        elif isinstance(value, str) and key == 'Value':
            value = translate_string(value, language)
        elif isinstance(value, str) and key == 'nativeQueryRef':
            pass  # This is a technical reference, not a display label.
        else:
            value = localize(value, language)
        result[key] = value
    if 'field' in obj and 'queryRef' in obj and 'nativeQueryRef' in obj:
        name = obj['nativeQueryRef']
        result['displayName'] = (ALIASES_VI if language == 'vi' else ALIASES_EN).get(name, translate_string(name, language))
    return result

def action_textbox(obj, language):
    # A static recommendation must not depend on localized text stored in the model.
    # Both languages use the same layout and recommendation content.
    visual = obj.get('visual', {})
    if visual.get('visualType') != 'tableEx':
        return obj
    container = visual['visualContainerObjects']
    visual.clear()
    visual.update({'visualType':'textbox','visualContainerObjects':container,'objects':{'general':[{'properties':{'paragraphs':[
        {'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI','fontSize':'17px','color':'#182B43'}}]} for line in ACTIONS[language]
    ]}}]}})
    return obj

def main():
    source = DESKTOP/'Aviation_Insights.pbix'
    checks = []
    with ZipFile(source) as z:
        data_hash = hashlib.sha256(z.read('DataModel')).hexdigest()
        for language in ['vi','en']:
            target = DESKTOP/f'Aviation_Insights_{language}.pbix'
            assert not target.exists(), f'Refusing to overwrite: {target}'
            pages, visuals = [], 0
            with ZipFile(target, 'w') as out:
                for info in z.infolist():
                    if info.filename == 'SecurityBindings':
                        continue  # Desktop regenerates package bindings when it saves.
                    data = z.read(info.filename)
                    if info.filename == '[Content_Types].xml':
                        # Desktop requires the original default namespace spelling,
                        # not ElementTree's equivalent ns0:Types serialization.
                        xml = data.decode('utf-8-sig')
                        xml = re.sub(r'<Override\s+PartName="/SecurityBindings"[^>]*/>', '', xml)
                        data = xml.encode('utf-8-sig')
                    if info.filename.startswith('Report/definition/') and info.filename.endswith('.json'):
                        obj = action_textbox(localize(json.loads(data), language), language)
                        if info.filename.endswith('/page.json'):
                            pages.append(obj['displayName'])
                        if info.filename.endswith('/visual.json'):
                            visuals += 1
                        data = json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8')
                    out.writestr(copy.copy(info), data)
            with ZipFile(target) as check:
                assert check.testzip() is None
                assert hashlib.sha256(check.read('DataModel')).hexdigest() == data_hash
                assert len(pages) == 7 and visuals == 51
            checks.append({'language':language,'file':target.name,'pages':pages,'visual_count':visuals,'embedded_model_sha256':data_hash,'archive_integrity':'PASS','desktop_opened':False})
    (DESKTOP/'localization_verification.json').write_text(json.dumps({'status':'PACKAGE_CHECKS_PASS','model_unchanged':True,'desktop_validation_pending':True,'reports':checks}, ensure_ascii=False, indent=2),encoding='utf-8')
    print('Created two localized PBIX packages; embedded data/model hashes match the original.')

if __name__ == '__main__':
    main()
