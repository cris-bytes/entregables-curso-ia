from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
STOP = set('a al algo como con cual cuando de del el ella en es esta este esto ha hay la las lo los me mi no o para por puedo que se si sin sobre su un una y'.split())

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def tokenize(text):
    return [t for t in re.findall(r'[a-z0-9]+',normalize(text)) if t not in STOP]

def verify_data():
    for item in read_json(DATA/'manifest.json'):
        assert hashlib.sha256((DATA/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    for name,expected in read_json(DATA/'checksums.json').items():
        assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==expected,name
    rows=catalog()
    assert len({r['id'] for r in rows})==len(rows)
    assert all(r['disponibles']>=0 for r in rows)
    return {'documents':len(read_json(DATA/'manifest.json')),'sections':len(load_sections()),'titles':len(rows),'hashes':'OK'}

def load_sections():
    docs=[]
    for meta in read_json(DATA/'manifest.json'):
        text=(DATA/meta['path']).read_text(encoding='utf-8')
        for sid,title,body in re.findall(r'^## (N\d+-S\d+) · ([^\n]+)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S):
            docs.append(Document(page_content=body.strip(),metadata={'id':sid,'title':title,'document':meta['title'],'topic':meta['topic'],'path':meta['path']}))
    return docs

def make_chunks(size=90, overlap=8):
    if size<=overlap: raise ValueError('El tamaño debe superar el solapamiento.')
    chunks=[]
    for doc in load_sections():
        words=doc.page_content.split()
        for offset in range(0,len(words),size-overlap):
            chunks.append(Document(page_content=' '.join(words[offset:offset+size]),metadata={**doc.metadata,'offset':offset}))
            if offset+size>=len(words):break
    return chunks

class Index:
    def __init__(self,method='tfidf',size=90,k=3):
        if method not in {'tfidf','char','bm25','rrf'}:raise ValueError('Método desconocido')
        self.method,self.size,self.k=method,size,k
        self.chunks=make_chunks(size)
        self.texts=[d.metadata['document']+' '+d.metadata['title']+' '+d.page_content for d in self.chunks]
        self.vectorizer=TfidfVectorizer(tokenizer=tokenize,token_pattern=None,lowercase=False,ngram_range=(1,2))
        self.matrix=self.vectorizer.fit_transform(self.texts)
        self.bm25=BM25Okapi([tokenize(t) for t in self.texts])
        self.char_vectorizer=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),preprocessor=normalize)
        self.char_matrix=self.char_vectorizer.fit_transform(self.texts)

    def search(self,query,k=None):
        k=self.k if k is None else max(1,min(int(k),10))
        sparse=(self.matrix @ self.vectorizer.transform([query]).T).toarray().ravel()
        bm=self.bm25.get_scores(tokenize(query))
        if self.method=='tfidf':scores=sparse
        elif self.method=='char':scores=(self.char_matrix @ self.char_vectorizer.transform([query]).T).toarray().ravel()
        elif self.method=='bm25':scores=bm
        else:
            scores=np.zeros(len(self.chunks))
            for values in [sparse,bm]:
                for rank,i in enumerate(np.argsort(-values,kind='stable'),1):
                    if values[i]>0:scores[i]+=1/(60+rank)
        hits=[]
        for i in np.argsort(-scores,kind='stable')[:k]:
            if scores[i]<=0:continue
            doc=self.chunks[i]
            hits.append({'id':doc.metadata['id'],'title':doc.metadata['title'],'text':doc.page_content,'score':round(float(scores[i]),6),'path':'data/'+doc.metadata['path']})
        return hits

def selected_config():
    p=ROOT/'results/selected_config.json'
    return read_json(p) if p.exists() else {'method':'tfidf','size':90,'k':3}

@lru_cache(maxsize=8)
def cached_index(method,size,k):return Index(method,size,k)

def search_rules(query):
    c=selected_config()
    hits=cached_index(c['method'],c['size'],c['k']).search(query)
    return {'query':query,'results':hits,'references':list(dict.fromkeys(h['id'] for h in hits)),
            'notice':'La coincidencia temática no demuestra que la respuesta esté documentada.'}

def catalog():
    with (DATA/'catalogo.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    for row in rows:
        for field in ['anio','total','prestados','reservados','consulta_sala']:row[field]=int(row[field])
        row['disponibles']=row['total']-row['prestados']-row['reservados']-row['consulta_sala']
    return rows

def search_catalog(query,limit=5):
    rows=catalog(); tokens=set(tokenize(query))
    scored=[]
    for r in rows:
        title=set(tokenize(r['titulo'])); words=title|set(tokenize(r['area']))|{normalize(r['id'])}
        score=len(tokens & words)/max(1,len(title))
        if score>0:scored.append((score,r))
    scored.sort(key=lambda x:(-x[0],x[1]['id']))
    best=scored[0][0] if scored else 0
    matches=[{**r,'reference':'CAT-'+r['id']} for score,r in scored if score>=max(.2,best*.5)][:max(1,min(limit,5))]
    return {'query':query,'corte':'2026-10-16','matches':matches,'references':[r['reference'] for r in matches]+['N08-S1'],
            'notice':'Instantánea ficticia; no disponibilidad en tiempo real. Sin coincidencias no prueba que el título no exista.'}

def due_date(profile,start_date):
    refs=['N01-S1','N07-S1']
    terms={'estudiante':7,'docente':15,'egresado':5}
    if profile not in terms:return {'error':'Perfil inválido: estudiante, docente o egresado.','references':refs}
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',start_date):raise ValueError()
        start=date.fromisoformat(start_date)
    except (ValueError,TypeError):return {'error':'Fecha inválida. Usa AAAA-MM-DD.','references':['N07-S1']}
    low,high=date(2026,10,1),date(2026,12,31)
    if not low<=start<=high:return {'error':'Fecha fuera de cobertura: 2026-10-01 a 2026-12-31. No se extrapola el calendario.','references':['N07-S1']}
    with (DATA/'cierres.csv').open(encoding='utf-8') as f:closed={date.fromisoformat(r['fecha']) for r in csv.DictReader(f)}
    if start.weekday()>=5 or start in closed:return {'error':'La fecha de retiro corresponde a un día cerrado. Indica una fecha hábil.','references':['N07-S1']}
    cursor=start;counted=[];skipped=[]
    while len(counted)<terms[profile]:
        cursor+=timedelta(days=1)
        if cursor>high:return {'error':'El vencimiento excede la cobertura del calendario; no se puede calcular.','references':['N07-S1']}
        (counted if cursor.weekday()<5 and cursor not in closed else skipped).append(cursor.isoformat())
    return {'profile':profile,'start':start_date,'business_days':terms[profile],'due_date':cursor.isoformat(),'counted_dates':counted,'skipped_dates':skipped,'references':refs,'notice':'Cálculo hipotético de préstamo de libro; no registra una operación.'}

def reference_text(ref):
    for d in load_sections():
        if d.metadata['id']==ref:return d.metadata['document']+' — '+d.metadata['title']+'\n'+d.page_content
    if ref.startswith('CAT-'):
        rows=[r for r in catalog() if r['id']==ref[4:]]
        if rows:return json.dumps(rows[0],ensure_ascii=False,indent=2)
    return None
