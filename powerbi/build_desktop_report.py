"""Generate native Power BI report/model definitions from verified local data."""
from pathlib import Path
from zipfile import ZipFile
import json, re, uuid
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'/'desktop'
REPORT=OUT/'Aviation.Report'
MODEL=OUT/'Aviation.SemanticModel'
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/'

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def ident(label):return uuid.uuid5(uuid.NAMESPACE_URL,'aviation:'+label).hex[:20]
def expr(table,column,measure=False):return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}}
def literal(v):return {'expr':{'Literal':{'Value':v}}}
def color(v):return {'solid':{'color':literal("'"+v+"'")}}

OUT.mkdir(parents=True,exist_ok=True)
write(OUT/'Aviation_Insights.pbip',{'$schema':SCHEMA+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Aviation.Report'}}],'settings':{'enableAutoRecovery':True}})
write(REPORT/'definition.pbir',{'$schema':SCHEMA+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Aviation.SemanticModel'}}})
write(MODEL/'definition.pbism',{'$schema':SCHEMA+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
for folder,kind in [(REPORT,'Report'),(MODEL,'SemanticModel')]:
    write(folder/'.platform',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json','metadata':{'type':kind,'displayName':'Aviation Insights'},'config':{'version':'2.0','logicalId':str(uuid.uuid5(uuid.NAMESPACE_URL,str(folder)))}})

# Use the exact installed Desktop base theme, exported by Desktop itself.
with ZipFile(ROOT/'powerbi'/'schema'/'desktop_empty_template.pbix') as z:
    theme=z.read('Report/StaticResources/SharedResources/BaseThemes/CY25SU10.json')
theme_path=REPORT/'StaticResources'/'SharedResources'/'BaseThemes'/'CY25SU10.json'
theme_path.parent.mkdir(parents=True,exist_ok=True);theme_path.write_bytes(theme)
custom={'name':'Aviation Consulting','dataColors':['#167D93','#C75C3B','#DAAE55','#6573A6','#4B9987'],'background':'#F4F6FA','foreground':'#182B43','tableAccent':'#167D93','textClasses':{'label':{'fontFace':'Segoe UI','fontSize':10},'title':{'fontFace':'Segoe UI Semibold','fontSize':13},'callout':{'fontFace':'Segoe UI Semibold','fontSize':28}}}
write(REPORT/'StaticResources'/'RegisteredResources'/'AviationTheme.json',custom)
write(REPORT/'definition'/'version.json',{'$schema':SCHEMA+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
write(REPORT/'definition'/'report.json',{
    '$schema':SCHEMA+'item/report/definition/report/1.0.0/schema.json',
    'themeCollection':{'baseTheme':{'name':'CY25SU10','reportVersionAtImport':'5.67','type':'SharedResources'},'customTheme':{'name':'AviationTheme','reportVersionAtImport':'5.67','type':'RegisteredResources'}},
    'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':'CY25SU10','path':'BaseThemes/CY25SU10.json','type':'BaseTheme'}]},{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'AviationTheme','path':'AviationTheme.json','type':'CustomTheme'}]}],
    'layoutOptimization':'None',
    'settings':{'useStylableVisualContainerHeader':True,'exportDataMode':'AllowSummarized','defaultDrillFilterOtherVisuals':True,'allowChangeFilterTypes':True,'useEnhancedTooltips':True}})

def import_table(name,path,headers,text_columns=(),decimal_columns=(),date_columns=(),measures=None,gzip=False):
    columns=[];types=[]
    for col in headers:
        typ='string' if col in text_columns else 'dateTime' if col in date_columns else 'double' if col in decimal_columns else 'int64'
        c={'name':col,'dataType':typ,'sourceColumn':col,'summarizeBy':'none' if typ in ['string','dateTime'] else 'sum'}
        if typ=='dateTime':c['formatString']='Short Date'
        columns.append(c)
        types.append('{'+json.dumps(col,ensure_ascii=False)+', '+('type text' if typ=='string' else 'type date' if typ=='dateTime' else 'type number' if typ=='double' else 'Int64.Type')+'}')
    source='File.Contents('+json.dumps(str(path),ensure_ascii=False).replace('\\\\','\\')+')'
    if gzip:source='Binary.Decompress('+source+', Compression.GZip)'
    m='let\n    Source = Csv.Document('+source+', [Delimiter=",", Columns='+str(len(headers))+', Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),\n    Typed = Table.TransformColumnTypes(Nulls, {'+', '.join(types)+'}, "en-US")\nin\n    Typed'
    return {'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':m.splitlines()}}],**({'measures':measures} if measures else {})}

textcols=['AIRLINE','TAIL_NUMBER','ORIGIN_AIRPORT','DESTINATION_AIRPORT','CANCELLATION_REASON','TIME_BAND','SEASON','ORIGIN_KEY','DESTINATION_KEY','ROUTE']
headers=list(pd.read_csv(ROOT/'data'/'processed'/'flights_cleaned.csv.gz',nrows=0).columns)
measuretext=(ROOT/'powerbi'/'measures.dax').read_text(encoding='utf-8')
measuretext=re.sub(r'^//.*$','',measuretext,flags=re.M)
parts=re.split(r'\n\n+',measuretext.strip())
measures=[]
for part in parts:
    name,expression=part.split('=',1)
    name=name.strip();expression=expression.strip()
    form='0.00%' if 'Rate' in name or 'Coverage' in name or 'Share' in name or 'Threshold' in name else '#,0.00' if 'Delay' in name else '#,0'
    if name=='Data Scope Label':form=''
    measures.append({'name':name,'expression':expression.splitlines(),'formatString':form})

tables=[import_table('FactFlight',ROOT/'data'/'processed'/'flights_cleaned.csv.gz',headers,textcols,date_columns=['DATE'],measures=measures,gzip=True)]
for name,file,texts,decimals,dates in [
    ('DimAirline','dim_airline.csv',['IATA_CODE','AIRLINE'],[],[]),
    ('DimOrigin','dim_airport.csv',['IATA_CODE','AIRPORT','CITY','STATE','COUNTRY'],['LATITUDE','LONGITUDE'],[]),
    ('DimDestination','dim_airport.csv',['IATA_CODE','AIRPORT','CITY','STATE','COUNTRY'],['LATITUDE','LONGITUDE'],[]),
    ('DimDate','dim_date.csv',[],[],['DATE']),('DimHour','dim_hour.csv',[],[],[])]:
    path=ROOT/'data'/'processed'/file
    tables.append(import_table(name,path,list(pd.read_csv(path,nrows=0).columns),texts,decimals,dates))

route=pd.read_csv(ROOT/'reports'/'tables'/'route.csv')[['ROUTE']]
route=pd.concat([route,pd.DataFrame({'ROUTE':['__UNRESOLVED__ > __UNRESOLVED__']})],ignore_index=True)
route.to_csv(OUT/'DimRoute.csv',index=False,encoding='utf-8-sig')
tables.append(import_table('DimRoute',OUT/'DimRoute.csv',['ROUTE'],['ROUTE']))
cause=pd.DataFrame({'Cause':['Late aircraft','Airline','NAS','Weather','Security'],'Sort':[1,2,3,4,5]})
cause.to_csv(OUT/'DimCause.csv',index=False)
cause_measure={'name':'Cause Minutes','expression':'SWITCH(SELECTEDVALUE(DimCause[Cause]), "Late aircraft", [Late Aircraft Minutes], "Airline", [Airline Minutes], "NAS", [NAS Minutes], "Weather", [Weather Minutes], "Security", [Security Minutes])','formatString':'#,0'}
tables.append(import_table('DimCause',OUT/'DimCause.csv',['Cause','Sort'],['Cause'],measures=[cause_measure]))
actions=pd.DataFrame([
    ['1. Cao','Cập nhật dữ liệu và nối mã sân bay tháng 10','Data owner','Dữ liệu 2015; 486.165 chuyến chưa nối mã','Coverage và chất lượng trước refresh','Đề xuất'],
    ['2. Cao','Kiểm tra rotation và phục hồi 17–21h tại ORD/LGA','Điều hành','Buổi tối severe 8,49% so với 3,61% sáng','Severe, disruption, p95; không tăng hủy','Đề xuất'],
    ['3. Cao','Tách chương trình giảm hủy và giảm chậm nặng','Điều hành / phục hồi','Tháng 2 hủy 4,78%; tháng 6 severe 8,15%','Cancellation và disruption đồng thời','Đề xuất'],
    ['4. Vừa','Điều tra tuyến NK và hủy chuyến MQ','Quản lý hiệu suất','NK matched +5,47 điểm % severe','Matched risk và cancellation theo cơ cấu','Đề xuất'],
    ['5. Vừa','Theo dõi mean, median và phần đuôi cùng lúc','BI / phân tích','Mean 4,41 phút nhưng p95 66 phút','Rate, count, coverage và p95','Đề xuất']
],columns=['Ưu tiên','Hành động','Phụ trách đề xuất','Bằng chứng','Đo thành công','Trạng thái'])
actions.to_csv(OUT/'Actions.csv',index=False,encoding='utf-8-sig')
tables.append(import_table('Actions',OUT/'Actions.csv',list(actions.columns),list(actions.columns)))
rels=[]
for dim,dk,fk in [('DimAirline','IATA_CODE','AIRLINE'),('DimOrigin','IATA_CODE','ORIGIN_KEY'),('DimDestination','IATA_CODE','DESTINATION_KEY'),('DimDate','DATE','DATE'),('DimHour','DEP_HOUR','DEP_HOUR'),('DimRoute','ROUTE','ROUTE')]:
    rels.append({'name':ident(dim),'fromTable':'FactFlight','fromColumn':fk,'toTable':dim,'toColumn':dk,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
model={'name':'Aviation Insights','compatibilityLevel':1601,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':True},'tables':tables,'relationships':rels,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([t['name'] for t in tables])},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}}
write(MODEL/'model.bim',model)

PAGES=[]
def field(table,col,is_measure=False):
    return {'field':expr(table,col,is_measure),'queryRef':table+'.'+col,'nativeQueryRef':col,**({} if is_measure else {'active':True})}
def filtering(table,col,values):
    source=ident(table+col)[:1]
    literals=[[{'Literal':{'Value':str(v)+'L' if isinstance(v,int) else "'"+str(v).replace("'","''")+"'"}}] for v in values]
    return {'name':'Filter'+uuid.uuid4().hex[:24],'field':expr(table,col),'type':'Categorical','filter':{'Version':2,'From':[{'Name':source,'Entity':table,'Type':0}],'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':source}},'Property':col}}],'Values':literals}}}]},'howCreated':'User'}
def visual(page,key,typ,x,y,w,h,title='',roles=None,sort=None,filters=None,objects=None):
    vid=ident(page+key);v={'visualType':typ,'drillFilterOtherVisuals':True}
    if roles:
        v['query']={'queryState':{role:{'projections':[field(*f) for f in fields]} for role,fields in roles.items()}}
        if sort:v['query']['sortDefinition']={'sort':[{'field':expr(*sort[0]),'direction':sort[1]}],'isDefaultSort':True}
    v['visualContainerObjects']={'background':[{'properties':{'show':literal('true'),'color':color('#FFFFFF'),'transparency':literal('0D')}}], 'border':[{'properties':{'show':literal('false')}}]}
    if title:v['visualContainerObjects']['title']=[{'properties':{'show':literal('true'),'text':literal("'"+title.replace("'","''")+"'"),'fontColor':color('#182B43'),'fontSize':literal('12D'),'fontFamily':literal("'Segoe UI Semibold'")}}]
    if objects:v['objects']=objects
    if typ=='textbox':v['visualContainerObjects']['padding']=[{'properties':{k:literal('0D') for k in ['top','bottom','left','right']}}]
    if typ in ['lineChart','clusteredBarChart','clusteredColumnChart']:
        for axis in ['categoryAxis','valueAxis']:v.setdefault('objects',{}).setdefault(axis,[{'properties':{}}])[0].setdefault('properties',{})['showAxisTitle']=literal('false')
    obj={'$schema':SCHEMA+'item/report/definition/visualContainer/2.0.0/schema.json','name':vid,'position':{'x':x,'y':y,'z':len(PAGES)*1000+100,'width':w,'height':h,'tabOrder':0},'visual':v}
    if filters:obj['filterConfig']={'filters':filters}
    write(REPORT/'definition'/'pages'/page/'visuals'/vid/'visual.json',obj)
def text(page,key,content,x,y,w,h,size=14,bold=False,ink='#182B43'):
    visual(page,key,'textbox',x,y,w,h,objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI Semibold' if bold else 'Segoe UI','fontSize':str(size)+'px','color':ink}}]} for line in content.split('\n')]}}]})
def page(number,title,insight,geo=False):
    pid=ident('page'+str(number));PAGES.append(pid)
    o={'$schema':SCHEMA+'item/report/definition/page/1.0.0/schema.json','name':pid,'displayName':f'{number}. {title}','displayOption':'FitToPage','width':1280,'height':800}
    if geo:o['filterConfig']={'filters':[filtering('FactFlight','GEO_ELIGIBLE',[1])]}
    write(REPORT/'definition'/'pages'/pid/'page.json',o)
    text(pid,'title',title.upper(),24,12,1232,45,27,True)
    text(pid,'scope','DỮ LIỆU LỊCH SỬ 2015  •  '+('11 tháng nhận diện sân bay — không gồm tháng 10' if geo else 'Đủ 12 tháng')+'  •  Chậm nặng: đến muộn ≥60 phút',24,61,1232,28,12,ink='#5C6C80')
    text(pid,'insight',insight,24,710,1232,65,15,ink='#116C80')
    return pid
def card(p,key,measure,title,x,y=103,w=290,h=115):
    visual(p,key,'card',x,y,w,h,title,{'Values':[('FactFlight',measure,True)]},objects={'labels':[{'properties':{'color':color('#167D93'),'fontSize':literal('26D'),'labelDisplayUnits':literal('1D')}}],'categoryLabels':[{'properties':{'show':literal('false')}}]})
def chart(p,key,typ,title,category,ys,x,y,w,h,filters=None,sort=None,tooltips=True):
    roles={'Category':[category],'Y':ys}
    if tooltips:roles['Tooltips']=[('FactFlight','Total Flights',True),('FactFlight','Arrival Eligible Flights',True),('FactFlight','Cancellation Rate',True)]
    visual(p,key,typ,x,y,w,h,title,roles,sort,filters,{'legend':[{'properties':{'show':literal('true')}}]})

p=page(1,'Tổng quan vận hành','Mean chỉ 4,41 phút nhưng có 325.591 chuyến chậm ≥60 phút. Theo dõi cả mức trung bình, phần đuôi và hủy chuyến.')
for i,(measure,title) in enumerate([('Total Flights','Chuyến theo lịch'),('On-Time Rate','Đúng giờ / chuyến hoàn tất'),('Severe Delay Rate','Chậm đến ≥60 phút'),('Cancellation Rate','Tỷ lệ hủy chuyến')]):card(p,'kpi'+str(i),measure,title,24+314*i)
chart(p,'trend','lineChart','Chậm nặng và hủy có nhịp khác nhau theo tháng',('DimDate','MONTH',False),[('FactFlight','Severe Delay Rate',True),('FactFlight','Cancellation Rate',True)],24,240,760,438,sort=(('DimDate','MONTH',False),'Ascending'))
for i,(measure,title) in enumerate([('Average Arrival Delay','Chậm đến trung bình (phút)'),('Median Arrival Delay','Trung vị chậm đến (phút)'),('P95 Arrival Delay','95% chuyến có chậm đến ≤ (phút)')]):card(p,'side'+str(i),measure,title,810,240+i*146,446,130)

p=page(2,'Hiệu suất hãng','NK có tỷ lệ chậm nặng cao; MQ nổi bật về hủy. Đây là so sánh mô tả; cơ cấu tuyến/tháng/giờ có thể làm đổi thứ hạng.')
chart(p,'severe','clusteredBarChart','Chậm nặng theo hãng',('DimAirline','IATA_CODE',False),[('FactFlight','Severe Delay Rate',True)],24,105,600,540,sort=(('FactFlight','Severe Delay Rate',True),'Descending'))
chart(p,'cancel','clusteredBarChart','Hủy chuyến theo hãng',('DimAirline','IATA_CODE',False),[('FactFlight','Cancellation Rate',True)],650,105,606,540,sort=(('FactFlight','Cancellation Rate',True),'Descending'))
text(p,'support','Mỗi thanh có tooltip cỡ mẫu. Nhấp chọn hãng để lọc chéo hai biểu đồ. US chỉ có dữ liệu tháng 1–6.',24,660,1232,35,13)

p=page(3,'Sân bay: quy mô và rủi ro','ORD nhiều phút chậm nhất; LGA có rủi ro cao. Chọn theo cả volume và rate; chỉ so sân bay ≥10.000 chuyến. Phạm vi 11 tháng.',True)
orig=pd.read_csv(ROOT/'reports'/'tables'/'origin.csv')
top_vol=orig.nlargest(12,'positive_arr_minutes').ORIGIN_KEY.tolist();top_risk=orig[orig.flights.ge(10000)].nlargest(12,'severe_rate').ORIGIN_KEY.tolist()
chart(p,'volume','clusteredBarChart','12 sân bay đi: nhiều phút chậm dương nhất',('DimOrigin','IATA_CODE',False),[('FactFlight','Positive Arrival Minutes',True)],24,105,600,540,[filtering('DimOrigin','IATA_CODE',top_vol)],(('FactFlight','Positive Arrival Minutes',True),'Descending'))
chart(p,'risk','clusteredBarChart','12 sân bay đi: chậm nặng cao nhất (N ≥10.000)',('DimOrigin','IATA_CODE',False),[('FactFlight','Airport Rate With Sample Threshold',True)],650,105,606,540,[filtering('DimOrigin','IATA_CODE',top_risk)],(('FactFlight','Airport Rate With Sample Threshold',True),'Descending'))
text(p,'support','Kết quả arrival của chuyến khởi hành từ sân bay; chưa chứng minh nguyên nhân phát sinh ở sân bay đi.',24,660,1232,35,13)

p=page(4,'Tuyến bay: chọn nơi can thiệp','ORD → JFK cao về rủi ro, SFO → LAX lớn về phút chậm cộng dồn. Quy mô và tỷ lệ trả lời hai câu hỏi khác nhau.',True)
r=pd.read_csv(ROOT/'reports'/'tables'/'route.csv')
top_vol=r.nlargest(10,'positive_arr_minutes').ROUTE.tolist();top_risk=r[r.flights.ge(1000)].nlargest(10,'severe_rate').ROUTE.tolist()
chart(p,'volume','clusteredBarChart','10 tuyến có nhiều phút chậm dương nhất',('DimRoute','ROUTE',False),[('FactFlight','Positive Arrival Minutes',True)],24,105,600,540,[filtering('DimRoute','ROUTE',top_vol)],(('FactFlight','Positive Arrival Minutes',True),'Descending'))
chart(p,'risk','clusteredBarChart','10 tuyến có chậm nặng cao nhất (N ≥1.000)',('DimRoute','ROUTE',False),[('FactFlight','Route Rate With Sample Threshold',True)],650,105,606,540,[filtering('DimRoute','ROUTE',top_risk)],(('FactFlight','Route Rate With Sample Threshold',True),'Descending'))
text(p,'support','Danh sách top được xác định trên dữ liệu nền 2015. Tooltip luôn kèm N chuyến theo lịch và số arrival đủ điều kiện.',24,660,1232,35,13)

p=page(5,'Thời điểm và chậm tích lũy','17–21h: severe 8,49% so với 3,61% lúc 6–11h. Chênh lệch còn sau so cùng hãng–sân bay–tháng; chưa phải quan hệ nhân quả.')
chart(p,'hour','lineChart','Chậm nặng theo giờ khởi hành lịch địa phương',('DimHour','DEP_HOUR',False),[('FactFlight','Severe Delay Rate',True)],24,105,600,275,sort=(('DimHour','DEP_HOUR',False),'Ascending'))
chart(p,'means','lineChart','Mean và median arrival theo giờ lịch',('DimHour','DEP_HOUR',False),[('FactFlight','Average Arrival Delay',True),('FactFlight','Median Arrival Delay',True)],650,105,606,275,sort=(('DimHour','DEP_HOUR',False),'Ascending'))
chart(p,'month','clusteredColumnChart','Chậm nặng và hủy theo tháng',('DimDate','MONTH',False),[('FactFlight','Severe Delay Rate',True),('FactFlight','Cancellation Rate',True)],24,402,760,275,sort=(('DimDate','MONTH',False),'Ascending'))
card(p,'severe','Severe Delay Rate','Chậm nặng trong bộ lọc',810,402,446,130)
card(p,'disrupted','Disruption Rate','Hủy / đổi hướng / chậm nặng',810,547,446,130)

p=page(6,'Bằng chứng về nguyên nhân','Late aircraft 39,84% và airline 32,20% PHÚT NGUYÊN NHÂN được ghi nhận. Nhãn báo cáo chưa xác minh được cơ chế độc lập.')
chart(p,'causes','clusteredBarChart','Phút nguyên nhân: chuyến arrival chậm ≥15 phút',('DimCause','Cause',False),[('DimCause','Cause Minutes',True)],24,105,760,540,sort=(('DimCause','Cause Minutes',True),'Descending'))
card(p,'reported','Reported Cause Minutes','Tổng phút nguyên nhân ghi nhận',810,105,446,130)
card(p,'positive','Positive Arrival Minutes','Tổng phút chậm dương',810,254,446,130)
card(p,'late','Late Aircraft Share of Reported Minutes','Late aircraft / phút nguyên nhân',810,403,446,130)
text(p,'denominator','Không trộn mẫu số: weather chiếm 4,95% phút nguyên nhân của chuyến chậm, nhưng 54,35% CHUYẾN HỦY mang mã weather.',810,555,446,115,15)

p=page(7,'Hành động và theo dõi','Chưa có kết quả can thiệp trong nguồn. Tái xác nhận bằng dữ liệu mới trước pilot; đo severe/disruption/p95 và bảo vệ tỷ lệ hủy.')
visual(p,'actions','tableEx',24,105,1232,420,'Ưu tiên dựa trên bằng chứng — trạng thái: đề xuất',{'Values':[('Actions',c,False) for c in actions.columns]})
text(p,'pilot','THIẾT KẾ THỬ NGHIỆM\nChọn tuyến/khung giờ có nhóm đối chiếu. Theo dõi 4–8 tuần sau khi có mức nền mới; điều chỉnh volume và cơ cấu khai thác.',24,548,600,135,16)
text(p,'guardrails','CHỈ TIÊU BẢO VỆ\nKhông gọi là cải thiện nếu mean giảm nhưng hủy tăng, số chuyến giảm hoặc bản ghi bị loại. Chưa lượng hóa chi phí/hành khách vì thiếu dữ liệu.',650,548,606,135,16)

write(REPORT/'definition'/'pages'/'pages.json',{'$schema':SCHEMA+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':PAGES,'activePageName':PAGES[0]})
print(f'Generated {len(PAGES)} native pages, {len(list(REPORT.rglob("visual.json")))} visuals, {len(tables)} model tables, {len(measures)} fact measures.')
print(OUT/'Aviation_Insights.pbip')
