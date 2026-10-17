"""Graba ejecución real en Jupyter y dos consultas reales; no genera respuestas ficticias."""
import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
import imageio_ffmpeg
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]

async def main():
    token=(ROOT/'.runtime/jupyter-token').read_text().strip()
    video_dir=ROOT/'video';video_dir.mkdir(exist_ok=True)
    raw_dir=ROOT/'.runtime/video';raw_dir.mkdir(exist_ok=True)
    start=time.perf_counter();checks=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(channel='chrome',headless=True)
        context=await browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1,record_video_dir=str(raw_dir),record_video_size={'width':1440,'height':1000})
        page=await context.new_page()
        await page.goto(f'http://127.0.0.1:8892/lab/tree/BiblioLab_LangChain.ipynb?token={token}',wait_until='domcontentloaded')
        await page.wait_for_function('window.jupyterapp && window.jupyterapp.shell.currentWidget && window.jupyterapp.shell.currentWidget.content.model',timeout=60000)
        await page.wait_for_timeout(1500)
        # No se edita código: se selecciona y ejecuta la celda de lanzamiento existente.
        await page.evaluate('''async () => {
          const w=window.jupyterapp.shell.currentWidget;
          await w.sessionContext.ready;
          const n=w.content; const last=n.model.cells.length-1;
          n.activeCellIndex=last;
          await n.scrollToItem(last);
        }''')
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(ROOT/'results/figures/05_celda_gradio.png'))
        await page.evaluate("window.jupyterapp.commands.execute('notebook:run-cell')")
        await page.wait_for_function('''() => {
          const n=window.jupyterapp.shell.currentWidget.content;
          const c=n.model.cells.get(n.model.cells.length-1);
          return c.executionCount !== null && c.outputs.length > 0 && !n.node.textContent.includes('Address already in use');
        }''',timeout=60000)
        # Verificar servidor por HTTP, sin sustituir la ejecución del notebook.
        for _ in range(40):
            try:
                response=await context.request.get('http://127.0.0.1:7862/config',timeout=2000)
                if response.ok:break
            except Exception:pass
            await asyncio.sleep(.5)
        else:raise RuntimeError('Gradio no arrancó desde la celda.')
        cell_record=await page.evaluate('''() => {
          const n=window.jupyterapp.shell.currentWidget.content;
          return n.model.cells.get(n.model.cells.length-1).toJSON();
        }''')
        assert cell_record['execution_count'] is not None
        assert not any(o.get('output_type')=='error' for o in cell_record.get('outputs',[])),cell_record
        checks.append({'event':'Celda Gradio ejecutada en Jupyter y servidor verificado','execution_count':cell_record['execution_count'],'source':cell_record['source']})
        await page.wait_for_timeout(3000)
        await page.goto('http://127.0.0.1:7862',wait_until='networkidle')
        await page.get_by_role('textbox',name='Tu pregunta').wait_for()
        await page.wait_for_timeout(2500)
        queries=[
          ('Busca Procesamiento de lenguaje natural y dime cuántos ejemplares hay disponibles.','CAT-B007'),
          ('Soy estudiante. Si pido un libro el 2026-10-09, ¿cuál es la fecha de devolución?','N07-S1')]
        for i,(question,reference) in enumerate(queries,1):
            await page.get_by_role('textbox',name='Tu pregunta').fill(question)
            await page.wait_for_timeout(1500)
            await page.get_by_role('button',name='Consultar',exact=True).click()
            await page.locator('#evidencia').get_by_text('['+reference+']',exact=False).first.wait_for(timeout=60000)
            await page.wait_for_timeout(1500)
            checks.append({'question':question,'reference_visible':reference})
            await page.screenshot(path=str(ROOT/f'results/figures/0{5+i}_consulta.png'))
            await page.wait_for_timeout(7000)
        await page.locator('#evidencia').scroll_into_view_if_needed()
        await page.wait_for_timeout(4000)
        video=page.video
        await context.close()
        raw=await video.path()
        await browser.close()
    output=video_dir/'BiblioLab_demo.mp4'
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg,'-y','-i',raw,'-c:v','libx264','-preset','medium','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    probe=subprocess.run([ffmpeg,'-i',str(output)],capture_output=True,text=True)
    import re
    match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe.stderr)
    duration=int(match[1])*3600+int(match[2])*60+float(match[3])
    if duration>=120:raise RuntimeError(f'El video dura {duration}s; supera el límite y debe volver a grabarse.')
    report={'file':'video/BiblioLab_demo.mp4','duration_seconds':duration,'real_browser_recording':True,'voiceover':False,'checks':checks,'wall_seconds':round(time.perf_counter()-start,2)}
    (ROOT/'results/video_recording.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':asyncio.run(main())
