import asyncio
from bibliolab.evaluation import eda,run_retrieval,run_generation,run_followups,run_holdout

async def main():
    print(eda()[2],flush=True)
    print('Configuración:',run_retrieval()[2],flush=True)
    _,_,summary=await run_generation()
    print(summary.to_string(),flush=True)
    _,_,small=await run_generation(modes=('guiado',),model='qwen2.5:1.5b',prefix='small_')
    print(small.to_string(),flush=True)
    await run_followups()
    await run_holdout()

if __name__=='__main__':asyncio.run(main())
