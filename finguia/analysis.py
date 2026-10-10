"""EDA documental y gráficos de resultados, sin datos financieros reales."""
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .core import ROOT, load_sections, tokenize

FIGURES = ROOT/'results/figures'

def setup_plots():
    FIGURES.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'figure.dpi':110,'axes.spines.top':False,'axes.spines.right':False,
        'axes.titlesize':12,'axes.labelsize':10,'font.family':'DejaVu Sans','savefig.bbox':'tight'})

def corpus_eda():
    setup_plots()
    sections = pd.DataFrame(load_sections(False))
    sections['words'] = sections.text.str.split().str.len()
    sections['characters'] = sections.text.str.len()
    sections['duplicate_text'] = sections.text.duplicated()
    sections[['doc_id','section_id','topic','current','words','characters','duplicate_text']].to_csv(ROOT/'results/corpus_eda.csv',index=False)
    fig,axes = plt.subplots(1,2,figsize=(12,4))
    totals = sections.groupby('doc_id').words.sum()
    axes[0].bar(totals.index,totals.values,color=['#ad754f' if d=='D09' else '#306f60' for d in totals.index])
    axes[0].set(title='Volumen por documento · D09 es histórico',ylabel='Palabras')
    axes[1].hist(sections.words,bins=8,color='#47769a',edgecolor='white')
    axes[1].set(title='Longitud de las secciones',xlabel='Palabras',ylabel='Secciones')
    fig.tight_layout(); fig.savefig(FIGURES/'01_corpus.png')
    text_by_doc = sections.groupby('doc_id').text.apply(' '.join)
    matrix = TfidfVectorizer(tokenizer=tokenize,token_pattern=None).fit_transform(text_by_doc)
    similarity = (matrix@matrix.T).toarray()
    fig2,axes2 = plt.subplots(1,2,figsize=(12,4.5))
    counts = Counter(token for text in sections[sections.current].text for token in tokenize(text))
    top = counts.most_common(12)[::-1]
    axes2[0].barh([x[0] for x in top],[x[1] for x in top],color='#306f60')
    axes2[0].set(title='Vocabulario del corpus vigente',xlabel='Frecuencia (no preguntas)')
    im=axes2[1].imshow(similarity,vmin=0,vmax=1,cmap='Blues')
    axes2[1].set_xticks(range(len(text_by_doc)),text_by_doc.index,rotation=45)
    axes2[1].set_yticks(range(len(text_by_doc)),text_by_doc.index)
    axes2[1].set_title('Similitud TF-IDF entre documentos')
    fig2.colorbar(im,ax=axes2[1],shrink=.8,label='Coseno')
    fig2.tight_layout(); fig2.savefig(FIGURES/'02_vocabulary_similarity.png')
    return sections,fig,fig2

def retrieval_plots(summary,config):
    setup_plots()
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    val=summary[(summary.split=='val')&(summary['size']==config['size'])]
    for method,group in val.groupby('method'):
        axes[0].plot(group.k,group.recall,marker='o',label=method)
    axes[0].set(title='Validación: recuperar más contexto',xlabel='k fragmentos',ylabel='Recall por sección',ylim=(0,1.04),xticks=[1,3,5])
    axes[0].legend(fontsize=8)
    test=summary[(summary.split=='test')&(summary.k==config['k'])]
    pivot=test.pivot(index='method',columns='size',values='recall')
    pivot.plot.bar(ax=axes[1],color=['#adc2c2','#669c91','#2c6558'])
    axes[1].set(title=f'Test descriptivo: tamaño de fragmento (k={config["k"]})',ylabel='Recall por sección',xlabel='',ylim=(0,1.07))
    axes[1].tick_params(axis='x',rotation=0)
    axes[1].legend(title='Palabras',fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES/'03_retrieval.png')
    return fig

def abstention_plot(confidence,threshold):
    setup_plots()
    fig,ax=plt.subplots(figsize=(10,3.5))
    for (split,answerable),group in confidence.groupby(['split','answerable']):
        ax.scatter(group.confidence,np.arange(len(group))*.03+(0 if split=='val' else .7),
            color='#347660' if answerable else '#b26840',marker='o' if split=='val' else 'x',
            label=f'{split} · {"con respuesta" if answerable else "sin respuesta"}',s=45)
    ax.axvline(threshold,color='#344253',linestyle='--',label=f'Umbral val = {threshold:.3f}')
    ax.set(xlabel='Mayor similitud E5 entre los fragmentos recuperados',yticks=[],title='Una similitud alta no demuestra que exista la respuesta')
    ax.legend(fontsize=8,ncols=2,loc='upper left'); fig.tight_layout(); fig.savefig(FIGURES/'04_abstention.png')
    return fig
