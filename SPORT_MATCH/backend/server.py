"""SPORT MATCH stdlib HTTP API and local web server. No pip dependencies."""
import json,sys,urllib.parse,mimetypes
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed'/'courses.json'
FRONT=ROOT/'frontend'

def load():
    if not DATA.exists():
        sys.path.insert(0,str(ROOT/'scripts'))
        from prepare_data import normalize
        return normalize()
    return json.loads(DATA.read_text(encoding='utf-8'))
COURSES=load()

def match_courses(params, data=None):
    data=COURSES if data is None else data
    sport=params.get('sport','').strip(); q=params.get('q','').strip().casefold()
    center=params.get('center',''); day=params.get('day',''); period=params.get('period','')
    try:budget=int(params.get('budget','0') or 0)
    except ValueError:budget=0
    try:latest=int(params.get('min_year','2026') or 0)
    except ValueError:latest=2026
    results=[]
    for row in data:
        if sport and sport!='전체' and row['sport']!=sport:continue
        if center and center!='전체' and row['center']!=center:continue
        if q and q not in (row['name']+' '+row['sport']+' '+row['audience']).casefold():continue
        if day and day!='전체' and day not in row['days']:continue
        if budget and (row['price'] is None or row['price']>budget):continue
        if latest and int(row['month'][:4])<latest:continue
        if period and period!='전체':
            try:hour=int(row['time'].split(':')[0])
            except (ValueError,IndexError):continue
            if period=='오전' and not hour<12:continue
            if period=='오후' and not 12<=hour<18:continue
            if period=='저녁' and not hour>=18:continue
        item=dict(row)
        item['score']=sum([25 if row['price'] is not None else 0, 25 if row['days'] else 0,
                           25 if row['time'] else 0,25 if row['month'][:4]=='2026' else 0])
        # score is data completeness/freshness, NOT a claim of personalized matching accuracy
        results.append(item)
    results.sort(key=lambda x:(-x['score'],x['price'] if x['price'] is not None else 10**10,x['name']))
    return results

class Handler(BaseHTTPRequestHandler):
    def reply(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        parsed=urllib.parse.urlparse(self.path);path=parsed.path
        if path=='/api/courses':
            qs={k:v[0] for k,v in urllib.parse.parse_qs(parsed.query).items()};allitems=match_courses(qs)
            try:limit=max(1,min(100,int(qs.get('limit','24'))));page=max(1,int(qs.get('page','1')))
            except ValueError:limit,page=24,1
            return self.reply({'total':len(allitems),'page':page,'limit':limit,'courses':allitems[(page-1)*limit:page*limit]})
        if path=='/api/meta':
            return self.reply({'total_raw':15088,'available_normalized':len(COURSES),
                'centers':sorted({x['center'] for x in COURSES}),
                'sports':sorted({x['sport'] for x in COURSES}),
                'years':sorted({x['month'][:4] for x in COURSES}),
                'notice':'과거 공개 데이터입니다. 현재 모집·잔여석·가격 보장 불가.'})
        if path=='/health':return self.reply({'status':'ok'})
        target=(FRONT/('index.html' if path=='/' else path.lstrip('/'))).resolve()
        if FRONT.resolve() not in target.parents and target!=FRONT.resolve():return self.reply({'error':'forbidden'},403)
        if not target.is_file():return self.reply({'error':'not found'},404)
        content=target.read_bytes(); mime=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
        self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);a=p.parse_args()
    print(f'SPORT MATCH running at http://localhost:{a.port} (Ctrl+C to stop)')
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
if __name__=='__main__':main()
