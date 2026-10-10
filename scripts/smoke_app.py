"""Prueba real de servidor, generación, archivos citados y controles en Chrome."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import build_demo
from finguia.core import ROOT, Assistant
from finguia.simulator import simulate
import requests
from gradio_client import Client
from playwright.sync_api import sync_playwright

def main():
    demo=build_demo(Assistant())
    url='http://127.0.0.1:7862'
    errors=[]
    try:
        demo.queue().launch(server_name='127.0.0.1',server_port=7862,share=False,
            prevent_thread_lock=True,allowed_paths=[str(ROOT/'data/documents')],quiet=True)
        assert requests.get(url,timeout=15).status_code==200
        client=Client(url,verbose=False)
        response=client.predict('¿Cuál es la comisión anual vigente de Horizonte A?',[],
            'Respuesta explicada',api_name='/chat')
        assert '0,30' in response[1][-1]['content'] or '0.30' in response[1][-1]['content']
        assert 'D08-S1' in response[1][-1]['content']
        print('Generación API verificada:',response[1][-1]['content'],flush=True)
        with sync_playwright() as p:
            executable='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            browser=p.chromium.launch(headless=True,executable_path=executable if Path(executable).exists() else None)
            page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
            page.on('pageerror',lambda exc:errors.append(str(exc)))
            page.goto(url,wait_until='networkidle')
            page.get_by_label('¿Qué quieres entender?').fill('¿Diversificar garantiza que no perderé dinero si cae el mercado?')
            page.get_by_role('button',name='Consultar ↗').click()
            page.locator('.evidence-card').first.wait_for(timeout=180000)
            assert 'D02-S1' in page.locator('.evidence-card').all_text_contents()[0]
            source=page.get_by_role('link',name='Documento del corpus ↗').first.get_attribute('href')
            assert requests.get(url+source,timeout=15).status_code==200
            (ROOT/'results/figures').mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(ROOT/'results/figures/05_demo_chat.png'),full_page=True)
            page.get_by_role('tab',name='Simular aportes').click()
            page.get_by_label('Capital inicial',exact=True).fill('2000000')
            page.get_by_role('button',name='Calcular escenario').click()
            expected=f"Saldo nominal: {simulate(2000000,100000,10,6,.3,3).iloc[-1].nominal:,.0f}"
            page.get_by_text(expected,exact=True).wait_for(timeout=30000)
            page.wait_for_timeout(500)
            page.screenshot(path=str(ROOT/'results/figures/06_demo_simulator.png'),full_page=True)
            page.get_by_role('tab',name='Biblioteca').click()
            page.get_by_role('heading',name='D01-S1 · Horizonte temporal',exact=True).wait_for()
            page.set_viewport_size({'width':390,'height':844})
            page.get_by_role('tab',name='Conversar').click()
            page.wait_for_timeout(500)
            overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 2')
            page.screenshot(path=str(ROOT/'results/figures/07_demo_mobile.png'),full_page=True)
            browser.close()
        assert not errors,errors
        assert not overflow,'La página desborda el ancho móvil'
        report={'http':200,'generated_answer_with_reference':True,'document_link_http':200,
            'desktop_chat':True,'simulator':True,'library':True,'mobile_no_overflow':True,'javascript_errors':errors}
        (ROOT/'results/app_smoke.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
    finally:
        demo.close()

if __name__=='__main__':
    main()
