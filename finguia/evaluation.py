"""Experimentos con validación separada; test descriptivo, pequeño y de autoría propia."""
from __future__ import annotations
import json
import platform
import time
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix

from .core import ROOT, Assistant, Retriever, citations_in, encode, normalize, policy_boundary, read_json

RESULTS = ROOT/'results'

def retrieval_metrics(hits, gold):
    # Recall por sección, no por documento. Una sección parcialmente recuperada
    # cuenta; por eso esta métrica NO verifica la respuesta ni cada hecho.
    seen, ranks = set(), []
    for rank, hit in enumerate(hits,1):
        sid = hit['section_id']
        if sid in gold and sid not in seen:
            ranks.append(rank)
            seen.add(sid)
    recall = len(seen)/len(gold)
    reciprocal = 1/min(ranks) if ranks else 0
    dcg = sum(1/np.log2(r+1) for r in ranks)
    ideal = sum(1/np.log2(r+1) for r in range(1,min(len(gold),len(hits))+1))
    return dict(recall=recall,hit=float(bool(ranks)),mrr=reciprocal,ndcg=dcg/ideal if ideal else 0,
                all_evidence=float(len(seen)==len(gold)))

def bootstrap_interval(values, seed=42, n=2000):
    v = np.asarray(values,dtype=float)
    rng = np.random.default_rng(seed)
    means = rng.choice(v,size=(n,len(v)),replace=True).mean(axis=1)
    return list(np.quantile(means,[.025,.975]))

def run_retrieval():
    RESULTS.mkdir(exist_ok=True)
    cases = read_json(ROOT/'data/questions.json')
    vectors = encode([q['question'] for q in cases],'query')
    rows, engines = [], {}
    # 4 recuperadores x 3 tamaños x 3 k = 36 configuraciones.
    for size in (32,64,128):
        engine = Retriever(size=size,overlap=12)
        engines[size] = engine
        print(f'Índice size={size}: {len(engine.chunks)} fragmentos',flush=True)
        for q, vec in zip(cases,vectors):
            if not q['gold_sections']:
                continue
            for method in ('tfidf','bm25','dense','hybrid'):
                for k in (1,3,5):
                    start = time.perf_counter()
                    hits = engine.search(q['question'],method,k,vec)
                    rows.append(dict(id=q['id'],split=q['split'],kind=q['kind'],size=size,overlap=12,
                        method=method,k=k,search_ms=(time.perf_counter()-start)*1000,
                        sections=';'.join(h['section_id'] for h in hits),
                        **retrieval_metrics(hits,set(q['gold_sections']))))
    detail = pd.DataFrame(rows)
    detail.to_csv(RESULTS/'retrieval_detail.csv',index=False)
    summary = detail.groupby(['split','size','method','k'],as_index=False)[['recall','hit','mrr','ndcg','all_evidence','search_ms']].mean()
    summary.to_csv(RESULTS/'retrieval_summary.csv',index=False)
    # Selección SOLO en val. Menor k primero si empatan; fragmentos completos
    # preferidos en empate para evitar cortar hechos. Orden léxico final estable.
    selected = summary[summary.split=='val'].sort_values(
        ['recall','mrr','k','size','method'],ascending=[False,False,True,False,True]).iloc[0]
    config = dict(size=int(selected['size']),overlap=12,method=selected['method'],k=int(selected['k']))
    engine = engines[config['size']]
    confidence_rows = []
    for q, vec in zip(cases,vectors):
        hits = engine.search(q['question'],config['method'],config['k'],vec)
        confidence_rows.append(dict(id=q['id'],split=q['split'],kind=q['kind'],answerable=bool(q['gold_sections']),
            confidence=max(h['dense_score'] for h in hits),boundary=bool(policy_boundary(q['question']))))
    confidence = pd.DataFrame(confidence_rows)
    val = confidence[confidence.split=='val']
    thresholds = np.unique(np.r_[0,np.nextafter(val.confidence.to_numpy(),np.inf),1])
    calibration = []
    for threshold in thresholds:
        predicted = val.confidence >= threshold
        calibration.append(dict(threshold=float(threshold),balanced_accuracy=balanced_accuracy_score(val.answerable,predicted),
            false_accepts=int((predicted & ~val.answerable).sum()),false_rejects=int((~predicted & val.answerable).sum())))
    calibration = pd.DataFrame(calibration).sort_values(['balanced_accuracy','false_accepts','threshold'],ascending=[False,True,False])
    config['threshold'] = float(calibration.iloc[0].threshold)
    config['selection'] = 'validación únicamente; recall, MRR, menor k, mayor size, método alfabético'
    config['threshold_selection'] = 'balanced accuracy en val; empate: menos falsas aceptaciones'
    (RESULTS/'selected_config.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n')
    calibration.to_csv(RESULTS/'threshold_calibration.csv',index=False)
    confidence['accepted_threshold'] = confidence.confidence >= config['threshold']
    confidence['accepted_with_scope'] = confidence.accepted_threshold & ~confidence.boundary
    confidence.to_csv(RESULTS/'abstention.csv',index=False)

    # Ablación controlada: misma configuración con/sin filtro de documentos históricos.
    historical = Retriever(size=config['size'],overlap=12,current_only=False)
    ablation = []
    for q in cases:
        if q['kind']!='vigencia':
            continue
        for label, index in [('vigentes',engine),('sin_filtro',historical)]:
            hits = index.search(q['question'],config['method'],config['k'])
            ablation.append(dict(id=q['id'],split=q['split'],index=label,
                obsolete_retrieved=sum(not h['current'] for h in hits),
                sections=';'.join(h['section_id'] for h in hits),**retrieval_metrics(hits,set(q['gold_sections']))))
    pd.DataFrame(ablation).to_csv(RESULTS/'version_ablation.csv',index=False)
    test = detail[(detail.split=='test') & (detail['size']==config['size']) & (detail.method==config['method']) & (detail.k==config['k'])]
    report = dict(config=config,test_answerable_n=len(test),
        test_recall=float(test.recall.mean()),test_recall_bootstrap95=bootstrap_interval(test.recall),
        test_all_evidence=float(test.all_evidence.mean()),test_mrr=float(test.mrr.mean()),
        threshold_confusion=confusion_matrix(confidence[confidence.split=='test'].answerable,
            confidence[confidence.split=='test'].accepted_threshold,labels=[False,True]).tolist(),
        scope_confusion=confusion_matrix(confidence[confidence.split=='test'].answerable,
            confidence[confidence.split=='test'].accepted_with_scope,labels=[False,True]).tolist(),
        confusion_order='filas real [sin respuesta, con respuesta]; columnas predicción [rechazar, aceptar]')
    (RESULTS/'retrieval_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)
    return detail,summary,config

def run_generation(model_key='generator',prefix=''):
    """Compara salida final extractiva/neuronal en un subconjunto declarado de test."""
    import gc
    import torch
    from .core import get_generator
    get_generator.cache_clear()
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    assistant = Assistant(generator_key=model_key)
    # 6 con evidencia y 3 sin respuesta; incluye cálculo y composición multifuente.
    ids = {'Q16','Q24','Q25','Q26','Q28','Q30','Q31','Q33','Q36'}
    cases = [q for q in read_json(ROOT/'data/questions.json') if q['id'] in ids]
    outputs = []
    for q in cases:
        for mode in ('extractive','generative'):
            result = assistant.answer(q['question'],mode)
            text = normalize(result['answer'])
            # Anclas léxicas detectan contenido básico, pero no contradicción ni causalidad.
            anchor_coverage = (sum(normalize(a) in text for a in q['anchors'])/len(q['anchors'])) if q['anchors'] else None
            cited_gold_recall = len(citations_in(result['raw_generation']) & set(q['gold_sections']))/len(q['gold_sections']) if q['gold_sections'] and mode=='generative' else None
            record = dict(id=q['id'],question=q['question'],kind=q['kind'],gold_sections=q['gold_sections'],
                anchors=q['anchors'],anchor_coverage=anchor_coverage,cited_gold_recall=cited_gold_recall,
                expected_abstention=not bool(q['gold_sections']),**result)
            outputs.append(record)
            print(f"{q['id']} {mode}: {result['seconds']:.1f}s; abstención={result['abstained']}; fallback={result['fallback']}",flush=True)
    (RESULTS/f'{prefix}generation_outputs.json').write_text(json.dumps(outputs,indent=2,ensure_ascii=False)+'\n')
    pd.DataFrame([{k:o[k] for k in ['id','mode','kind','anchor_coverage','cited_gold_recall','expected_abstention','abstained','fallback','citation_ids_valid','seconds']} for o in outputs]).to_csv(RESULTS/f'{prefix}generation_metrics.csv',index=False)
    return outputs

def run_final_checks():
    """Preguntas adicionales definidas tras el prompt final, antes de ver sus respuestas."""
    assistant=Assistant()
    outputs=[]
    for q in read_json(ROOT/'data/final_checks.json'):
        result=assistant.answer(q['question'])
        outputs.append({**q,**result})
        print(q['id'],result['answer'],flush=True)
    (RESULTS/'final_checks_outputs.json').write_text(json.dumps(outputs,indent=2,ensure_ascii=False)+'\n')
    return outputs

def record_environment():
    import os
    import torch
    packages = ['numpy','pandas','scikit-learn','torch','transformers','sentence-transformers','gradio','nbclient']
    environment = dict(python=platform.python_version(),platform=platform.platform(),
        embedding_device='cpu',generator_device=os.environ.get('FINGUIA_DEVICE','mps' if torch.backends.mps.is_available() else 'cpu'),
        generator_dtype='float16',attention='sdpa',
        seed=42,decoding='greedy; do_sample=False',packages={p:version(p) for p in packages},
        models=read_json(ROOT/'models.lock.json'))
    (RESULTS/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    return environment
