import asyncio
import json
import pytest
from bibliolab.core import verify_data,make_chunks,load_sections,catalog,due_date,search_catalog
from bibliolab.assistant import make_client,text_content,guided_plan,citations
from bibliolab.evaluation import retrieval_metrics

def test_data_integrity_and_inventory():
    assert verify_data()['titles']==32
    assert all(r['total']==r['disponibles']+r['prestados']+r['reservados']+r['consulta_sala'] for r in catalog())

@pytest.mark.parametrize('size',[35,90])
def test_chunking_covers_every_original_word(size):
    chunks=make_chunks(size)
    for section in load_sections():
        words=section.page_content.split();covered=set()
        for c in chunks:
            if c.metadata['id']==section.metadata['id']:
                off=c.metadata['offset'];length=len(c.page_content.split())
                assert c.page_content.split()==words[off:off+length]
                covered.update(range(off,off+length))
        assert covered==set(range(len(words)))

def test_catalog_uses_inventory_not_title_presence():
    zero=search_catalog('Visualización con gráficos')['matches'][0]
    one=search_catalog('Procesamiento de lenguaje natural')['matches'][0]
    assert zero['id']=='B003' and zero['disponibles']==0
    assert one['id']=='B007' and one['disponibles']==1
    assert search_catalog('zxqv inexistente')['matches']==[]

@pytest.mark.parametrize('profile,start,expected',[('estudiante','2026-10-09','2026-10-21'),('egresado','2026-10-30','2026-11-09'),('docente','2026-10-01','2026-10-23')])
def test_dates_against_independently_counted_examples(profile,start,expected):
    result=due_date(profile,start)
    assert result['due_date']==expected
    assert start not in result['counted_dates']
    assert '2026-10-12' not in result['counted_dates']

@pytest.mark.parametrize('profile,start',[('otro','2026-10-09'),('estudiante','2026-10-10'),('estudiante','2026-10-12'),('docente','2026-12-29'),('estudiante','2027-01-05'),('estudiante','2026-02-30'),('estudiante','09/10/2026')])
def test_invalid_date_requests_are_not_silently_guessed(profile,start):
    assert 'error' in due_date(profile,start)

def test_multisource_recall_does_not_count_repeated_chunks_twice():
    recall,mrr,complete=retrieval_metrics([{'id':'A'},{'id':'A'}],['A','B'])
    assert (recall,mrr,complete)==(.5,1,0)

def test_guided_plan_requires_explicit_profile_and_date():
    plans,question=guided_plan('Calcula la devolución el 2026-10-09')
    assert not plans and question
    plans,_=guided_plan('Busca un libro y calcula la devolución para un estudiante el 2026-10-09')
    assert {p['name'] for p in plans}=={'buscar_catalogo','calcular_devolucion'}
    plans,_=guided_plan('Soy estudiante, calcula la devolución de un portátil el 2026-10-09')
    assert plans[0]['name']=='buscar_normas'

def test_protocol_discovery_and_real_tool_calls():
    async def run():
        tools=await make_client().get_tools()
        assert {t.name for t in tools}=={'buscar_normas','buscar_catalogo','calcular_devolucion'}
        tool=next(t for t in tools if t.name=='calcular_devolucion')
        result=json.loads(text_content(await tool.ainvoke({'perfil':'estudiante','fecha_retiro':'2026-10-09'})))
        assert result['due_date']=='2026-10-21'
        assert set(result['references'])=={'N01-S1','N07-S1'}
    asyncio.run(run())
