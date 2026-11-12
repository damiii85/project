"""Normalize original CP949 CSV exports and keep latest record per stable course key."""
import csv, json, re, collections
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
OUT=ROOT/'data'/'processed'
OUT.mkdir(parents=True,exist_ok=True)
CENTERS=[('분당스포츠센터','*분당스포츠센터*.csv'),('올림픽스포츠센터','*올림픽스포츠센터*.csv')]

def safe_year(s):
    try:
        v=str(s or '')[:10]
        y=int(v[:4]); date.fromisoformat(v)
        return v if 2000<=y<=2100 else ''
    except (ValueError,TypeError):return ''

def money(v):
    try:return int(str(v or '').replace(',','').strip())
    except ValueError:return None

def normalize():
    all_records=[]; stats={}
    for center,pattern in CENTERS:
        matches=list(RAW.glob(pattern))
        if len(matches)!=1: raise FileNotFoundError(f'Expected exactly one file for {center}: {matches}')
        with matches[0].open(encoding='cp949',newline='') as fp: source=list(csv.DictReader(fp))
        by_key={}; invalid=0
        for r in source:
            month=safe_year(r.get('수강월'))
            if not month: invalid+=1; continue
            name=(r.get('강좌명') or '').strip(); sport=(r.get('종목') or '').strip()
            time=(r.get('시작종료시간') or r.get('수강시간') or '').strip()
            days=(r.get('수강요일') or '').strip()
            course_id=str(r.get('강좌번호') or r.get('강좌일련번호') or '').strip()
            # Composite key retains same-name classes offered at different times.
            key=(center,course_id,name,time,days)
            obj={'id':'', 'center':center,'sport':sport,'name':name,'time':time,'days':days,
                 'audience':(r.get('수강대상') or '').strip(), 'price':money(r.get('수강료') or r.get('수강금액')),
                 'capacity':money(r.get('정원')), 'month':month,'course_id':course_id,
                 'period_start':r.get('기간시작일') or r.get('수강시작일') or '',
                 'period_end':r.get('기간종료일') or r.get('수강종료일') or ''}
            if not name:continue
            if key not in by_key or month>by_key[key]['month']:
                by_key[key]=obj
        items=sorted(by_key.values(),key=lambda d:(d['sport'],d['name'],d['time'],d['month']))
        for i,x in enumerate(items,1):x['id']=('BD' if center.startswith('분당') else 'OL')+f'{i:05d}'
        all_records.extend(items)
        stats[center]={'raw_rows':len(source),'valid_date_rows':len(source)-invalid,
                       'bad_month_rows':invalid,'unique_latest_courses':len(items),
                       'latest_month':max((x['month'] for x in items),default=''),
                       'sports':len(set(x['sport'] for x in items))}
    with (OUT/'courses.json').open('w',encoding='utf-8') as f:json.dump(all_records,f,ensure_ascii=False,indent=1)
    with (OUT/'courses.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=all_records[0].keys());w.writeheader();w.writerows(all_records)
    with (OUT/'summary.json').open('w',encoding='utf-8') as f:json.dump(stats,f,ensure_ascii=False,indent=2)
    print('Normalized',len(all_records),'unique course records;',stats)
    return all_records
if __name__=='__main__': normalize()
