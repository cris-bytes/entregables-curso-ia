import asyncio
from bibliolab.assistant import Assistant
from bibliolab.core import write_json,ROOT

async def main():
    assistant=await Assistant().initialize()
    print('Tools:',[t.name for t in assistant.tools],flush=True)
    results=[]
    for question in ['¿Puedo llevar un portátil a casa?','Busca Procesamiento de lenguaje natural y dime cuántos ejemplares hay disponibles.','Soy estudiante. Si pido un libro el 2026-10-09, ¿cuál es la fecha de devolución?']:
        r=await assistant.ask(question);results.append(r)
        print(r['answer'],r['calls'],r['seconds'],flush=True)
    write_json(ROOT/'results/development_smoke.json',results)

if __name__=='__main__':asyncio.run(main())
