import math
import pytest
from finguia.core import load_sections, make_chunks, citations_in, is_refusal, policy_boundary, read_json, ROOT
from finguia.evaluation import retrieval_metrics
from finguia.simulator import simulate

def test_corpus_and_ground_truth_integrity():
    sections = load_sections(False)
    assert len(sections)==28
    ids = {s['section_id'] for s in sections}
    assert len(ids)==len(sections)
    assert all(s['current'] for s in load_sections())
    questions=read_json(ROOT/'data/questions.json')
    assert len({q['id'] for q in questions})==len(questions)
    assert {s for q in questions for s in q['gold_sections']} <= ids
    assert not ({q['question'] for q in questions if q['split']=='val'} & {q['question'] for q in questions if q['split']=='test'})

@pytest.mark.parametrize('size',[32,64,128])
def test_chunking_preserves_all_words(size):
    for section in load_sections():
        words=section['text'].split()
        chunks=make_chunks([section],size=size,overlap=12)
        covered=set()
        for c in chunks:
            assert c.text==' '.join(words[c.start_word:c.end_word])
            covered.update(range(c.start_word,c.end_word))
        assert covered==set(range(len(words)))

def test_metrics_do_not_double_count_same_section():
    hits=[{'section_id':'A'},{'section_id':'A'},{'section_id':'B'}]
    m=retrieval_metrics(hits,{'A','C'})
    assert m['recall']==.5
    assert m['mrr']==1
    assert m['all_evidence']==0
    assert 0 <= m['ndcg'] <= 1

def test_refusal_does_not_confuse_negative_financial_answers():
    assert not is_refusal('La diversificación no garantiza evitar pérdidas [D02-S1].')
    assert is_refusal('No encuentro esa información en mis documentos.')
    assert citations_in('Dato [D08-S1]; otro [D08-S1].')=={'D08-S1'}
    assert policy_boundary('¿A cuánto cotiza hoy Apple?')
    assert policy_boundary('¿Qué es un ETF?') is None

def test_zero_rates_and_compounding():
    zero=simulate(1000,100,1,0,0,0).iloc[-1]
    assert zero.nominal==zero.real==zero.contributed==2200
    compound=simulate(1000,0,2,5,0,0).iloc[-1]
    assert math.isclose(compound.nominal,1102.5,rel_tol=1e-10)

def test_fees_inflation_negative_return_and_timing():
    frame=simulate(1000,100,1,12,1,5)
    assert frame.iloc[-1].without_fees > frame.iloc[-1].nominal > frame.iloc[-1].real
    assert math.isclose(frame.iloc[-1].real,frame.iloc[-1].nominal/1.05)
    factor=((1.12)*(.99))**(1/12)
    assert math.isclose(frame.iloc[1].nominal,1000*factor+100)
    assert simulate(1000,0,1,-10,0,0).iloc[-1].nominal==pytest.approx(900)

@pytest.mark.parametrize('kwargs',[{'initial':-1},{'years':0},{'years':1.5},{'annual_return':-100},{'annual_fee':101},{'inflation':float('nan')}])
def test_invalid_simulation_inputs(kwargs):
    with pytest.raises(ValueError):
        simulate(**kwargs)
