"""Corpus propio FinGuía: síntesis breves atribuidas y fichas ficticias explícitas."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'D01': ('SEC / Investor.gov', 'https://www.investor.gov/introduction-investing/getting-started/asset-allocation'),
    'D02': ('SEC / Investor.gov', 'https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset'),
    'D03': ('SEC / Investor.gov', 'https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated'),
    'D04': ('FINRA', 'https://syndication.finra.org/content/bond-investing-and-due-diligence'),
    'D05': ('SEC / Investor.gov', 'https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24'),
    'D06': ('SEC / Investor.gov', 'https://www.investor.gov/protect-your-investments/fraud/how-avoid-fraud/red-flags-investment-fraud-checklist'),
    'D07': ('SEC / Investor.gov; ejemplos matemáticos propios', 'https://www.investor.gov/introduction-investing/investing-basics/glossary/purchasing-power'),
}
# Cada síntesis de una fuente externa contiene menos de 200 palabras, sin citas literales.
DOCUMENTS = [
('D01', 'Objetivos, horizonte y riesgo', 'perfil', True, [
('Horizonte temporal', 'El horizonte temporal es el tiempo que falta hasta necesitar el dinero invertido. Debe vincularse a una meta concreta, como financiar estudios o una compra futura. Un horizonte corto deja menos margen para afrontar oscilaciones de precios. El plazo influye en la distribución entre clases de activos; no determina por sí solo una cartera adecuada.'),
('Tolerancia al riesgo', 'La tolerancia al riesgo reúne la capacidad y la disposición para soportar pérdidas a cambio de posibles rendimientos. Una persona puede sentirse cómoda con fluctuaciones y aun así necesitar pronto su capital. Antes de comparar inversiones conviene distinguir objetivo, horizonte, necesidades de liquidez y capacidad de asumir pérdidas. La rentabilidad potencial mayor suele implicar mayor riesgo.'),
('Asignación de activos', 'La asignación de activos distribuye el dinero entre categorías como acciones, bonos y efectivo. No existe una mezcla universal adecuada para todas las personas. La elección depende del horizonte y del riesgo tolerable. Las proporciones de una cartera son decisiones que requieren contexto; una etiqueta como conservador no garantiza que el capital no pueda perder valor.'),
]),
('D02', 'Diversificación y rebalanceo', 'cartera', True, [
('Diversificar entre y dentro de activos', 'Diversificar consiste en repartir la inversión entre clases de activos y también dentro de cada clase. Poseer varios títulos del mismo sector puede mantener una concentración elevada. Conviene examinar las posiciones subyacentes y no solo contar productos. La diversificación puede reducir el riesgo de concentración, pero no garantiza evitar pérdidas cuando cae el mercado.'),
('Fondos y solapamiento', 'Un fondo puede facilitar la diversificación al reunir múltiples inversiones. Sin embargo, un fondo concentrado en un sector no necesariamente diversifica una cartera completa. Dos fondos pueden mantener los mismos títulos y duplicar exposición. Antes de combinarlos se revisan sus activos, sectores y objetivos. Tener más nombres en la cuenta no implica automáticamente tener riesgos diferentes.'),
('Rebalanceo', 'Rebalancear es recuperar la distribución objetivo después de que los movimientos del mercado alteran los pesos. Puede hacerse mediante operaciones o dirigiendo nuevas aportaciones a las categorías que quedaron por debajo del objetivo. Se deben considerar costes y consecuencias fiscales. La frecuencia o la desviación que activan un rebalanceo son decisiones del plan, no una predicción del mercado.'),
]),
('D03', 'Comisiones y costes de inversión', 'costes', True, [
('Costes recurrentes y de operación', 'Los costes de inversión pueden cobrarse por transacción o de forma recurrente. Entre ellos figuran comisiones de compra y venta, mantenimiento, asesoría y gastos del fondo. El porcentaje de gastos de un fondo se consulta en su documentación. Un producto anunciado sin comisión de negociación todavía puede tener otros costes. Es necesario comparar el conjunto de cargos.'),
('Efecto acumulado', 'Una comisión pequeña reduce el capital que permanece invertido y también los rendimientos que ese capital podría generar en el futuro. Por eso los costes recurrentes se acumulan a lo largo del tiempo. Al comparar escenarios deben mantenerse iguales el capital, el horizonte y la rentabilidad bruta supuesta, cambiando únicamente el coste que se quiere estudiar.'),
('Preguntas antes de contratar', 'Antes de invertir conviene preguntar qué comisiones existen, cuándo se cobran, cómo se calculan y qué servicio remuneran. También interesa conocer costes por retirar dinero, cerrar la cuenta o cambiar de producto. Los cargos pueden depender del intermediario y del producto. Este material explica categorías; no informa tarifas vigentes de entidades concretas ni compara ofertas comerciales actuales.'),
]),
('D04', 'Bonos: precio, tasas y crédito', 'renta fija', True, [
('Tasas y precio', 'En bonos de tasa fija, el precio y las tasas de interés suelen moverse en sentidos opuestos. Cuando suben las tasas de mercado, un bono existente con cupón menor puede perder valor. Vender antes del vencimiento expone al precio de mercado. La renta fija no significa precio fijo ni elimina automáticamente el riesgo de perder capital.'),
('Riesgo de crédito', 'El riesgo de crédito consiste en que el emisor incumpla pagos de intereses o devolución de principal. La evaluación del bono incluye al emisor, las condiciones y su capacidad de pago. Una calificación crediticia aporta información, pero no equivale a una garantía. El rendimiento ofrecido debe interpretarse junto con los riesgos asumidos y no de manera aislada.'),
('Información para comparar', 'Antes de comprar un bono se revisan vencimiento, cupón, precio, rendimiento, liquidez y condiciones del instrumento. El precio de negociación puede diferir del valor nominal. Conservar el bono hasta el vencimiento no elimina el riesgo de incumplimiento. Comparar únicamente cupones puede ocultar diferencias relevantes. Este corpus no contiene precios actuales ni recomendaciones sobre emisores individuales.'),
]),
('D05', 'Fondos cotizados ETF', 'fondos', True, [
('Qué es un ETF', 'Un ETF reúne una cartera de activos y sus participaciones se negocian en bolsa durante la jornada. El inversor posee una participación del fondo, no una cuenta individual con cada activo subyacente. El precio de mercado puede diferir del valor de los activos por participación. Los ETF pueden seguir estrategias distintas; el formato no define por sí solo el riesgo.'),
('Precio y diferencial', 'Al negociar un ETF se consideran el precio de compra, el precio de venta y su diferencial, además de posibles comisiones del intermediario. El valor liquidativo refleja los activos netos por participación y puede diferir del precio negociado. Una diferencia entre precio y valor liquidativo se conoce como prima o descuento. Estos costes se suman al análisis de gastos recurrentes.'),
('Documentación del fondo', 'El folleto y la documentación del ETF describen objetivos, riesgos, estrategia y costes. Deben leerse antes de invertir. No todos los ETF son diversificados ni todos replican un índice amplio. Un producto especializado puede concentrar riesgos. La comparación debe atender a los activos subyacentes y a la forma en que funciona el producto, además de su nombre comercial.'),
]),
('D06', 'Señales de fraude en inversiones', 'fraude', True, [
('Promesas y presión', 'Son señales de alerta las promesas de ganancias elevadas garantizadas, las oportunidades que supuestamente carecen de riesgo y la presión para decidir inmediatamente. También merecen atención los contactos no solicitados y la insistencia en que todos están invirtiendo. Una señal no sustituye una investigación, pero justifica detenerse a comprobar la información antes de transferir dinero.'),
('Comprobar al oferente', 'Se debe verificar la identidad y el registro del profesional o entidad mediante fuentes oficiales correspondientes a su jurisdicción. No basta un testimonio, una captura de pantalla o una apariencia profesional. La fuente estadounidense propone comprobar antecedentes y registro en sus herramientas oficiales. Ese mecanismo no se presenta aquí como sustituto de los registros del país del usuario.'),
]),
('D07', 'Inflación e interés compuesto', 'matemáticas', True, [
('Poder adquisitivo', 'El poder adquisitivo describe cuántos bienes y servicios puede comprar una cantidad de dinero considerando la inflación. Que aumente el saldo nominal no implica que aumente en igual proporción su capacidad de compra. La comparación económica debe distinguir valores nominales de valores expresados en dinero de hoy. La fuente externa respalda este concepto; los cálculos siguientes son ejemplos propios.'),
('Rentabilidad real: ejemplo propio', 'La rentabilidad real se calcula como uno más la rentabilidad nominal dividido entre uno más la inflación, menos uno. Si el rendimiento nominal es 8 % y la inflación es 5 %, el rendimiento real es aproximadamente 2,86 %. Restar las tasas da una aproximación, no la fórmula exacta. El ejemplo es hipotético y no describe una inflación o rentabilidad observada.'),
('Capitalización: ejemplo propio', 'El interés compuesto reinvierte los rendimientos y permite que el nuevo saldo también genere resultados. Con 1000 unidades monetarias, rendimiento anual constante de 5 % y sin aportes ni costes, el saldo después de dos años es 1102,50 unidades. El rendimiento constante es un supuesto de cálculo. En inversiones reales los resultados fluctúan y pueden ser negativos.'),
]),
('D08', 'Laboratorio Horizonte: fichas vigentes', 'laboratorio', True, [
('Cartera Horizonte A — ficticia', 'Horizonte A es una cartera ficticia creada solo para este proyecto académico. Su composición objetivo es 40 % de acciones globales y 60 % de bonos. La comisión anual usada en el laboratorio es 0,30 % desde el 1 de septiembre de 2026. No representa un producto disponible, no tiene ticker y no ofrece rentabilidad garantizada. Las cifras permiten evaluar si el chatbot recupera correctamente una ficha propia, sin depender de conocimiento previo del modelo.'),
('Cartera Horizonte B — ficticia', 'Horizonte B es una cartera ficticia del mismo laboratorio. Su composición objetivo es 80 % de acciones globales y 20 % de bonos. La comisión anual supuesta es 1,20 %. Comparada con Horizonte A tiene mayor peso en acciones, pero este documento no estima sus rendimientos futuros ni calcula una probabilidad de pérdida. Ninguna cartera constituye una recomendación individual. Las fichas son datos sintéticos explícitos, no ofertas de una entidad financiera.'),
('Regla de rebalanceo del laboratorio', 'La regla experimental revisa pesos al final de cada trimestre y rebalancea si alguna clase se desvía al menos 5 puntos porcentuales de su objetivo. Por ejemplo, en Horizonte A pasar de 40 % a 46 % de acciones representa una desviación de 6 puntos y activa la regla. Pasar a 44 % no la activa. Esta es una convención del laboratorio; no es una frecuencia universal recomendada ni una norma atribuida a la SEC.'),
]),
('D09', 'Laboratorio Horizonte: ficha histórica', 'laboratorio', False, [
('Comisión anterior de Horizonte A', 'La versión histórica de Horizonte A utilizaba una comisión anual de 0,60 %. Esta cifra dejó de ser la vigente del laboratorio el 1 de septiembre de 2026. La nueva ficha D08 establece 0,30 %. Se conserva esta versión para estudiar conflictos temporales. No se debe responder a una pregunta sobre la comisión actual con el valor antiguo. Ambas versiones son ficticias y ninguna corresponde a una oferta comercial.'),
('Regla histórica de rebalanceo', 'La regla antigua del laboratorio revisaba la cartera cada mes y activaba un ajuste a partir de 3 puntos porcentuales de desviación. Fue sustituida por revisión trimestral y umbral de 5 puntos en D08. El índice por defecto excluye esta versión histórica. El experimento sin filtro permite observar el riesgo de mezclar documentos de fechas diferentes. El asistente no ofrece consultas históricas en su flujo normal.'),
]),
('D10', 'Especificación del simulador FinGuía', 'simulación', True, [
('Aportes y tasas', 'El simulador usa capital inicial y aportes iguales al final de cada mes. Convierte el rendimiento anual efectivo bruto en un factor mensual mediante la raíz doceava de uno más la tasa anual. Aplica de forma multiplicativa un factor de coste anual de uno menos la comisión, distribuido también en doce meses. La convención de costes es una simplificación explícita del laboratorio; no reproduce necesariamente el cobro de un fondo real.'),
('Valores reales y límites', 'El saldo real se obtiene dividiendo el saldo nominal por uno más la inflación anual elevado al número de años transcurridos. Los aportes mensuales permanecen constantes en valor nominal. El simulador no modela impuestos, divisas, costes por transacción ni volatilidad. Sus curvas son escenarios deterministas con tasas elegidas por el usuario, no pronósticos, probabilidades ni promesas. Una tasa supuesta negativa puede producir pérdidas; el capital no está garantizado.'),
('Ejemplo de aportes sin rendimiento', 'Con capital inicial de 1000 unidades monetarias, aporte de 100 al final de cada mes y plazo de 12 meses, el total aportado es 2200. Si rendimiento, comisión e inflación son cero, el saldo nominal y el saldo real también son 2200. Este caso permite verificar que el programa no inventa intereses cuando no existen. Las cifras pueden expresarse en COP u otra moneda siempre que todas usen la misma unidad.'),
]),
]
CASES = [
('val','literal','¿Qué es el horizonte temporal de una inversión?',['D01-S1'],['tiempo']),
('val','paráfrasis','¿Tener varios fondos del mismo sector elimina mi concentración?',['D02-S2'],['sector']),
('val','literal','¿Por qué afectan tanto las comisiones pequeñas a largo plazo?',['D03-S2'],['capital']),
('val','literal','¿Qué pasa con el precio de un bono de tasa fija cuando suben las tasas?',['D04-S1'],['perder valor']),
('val','literal','¿Qué es un ETF?',['D05-S1'],['bolsa']),
('val','vigencia','¿Cuál es la comisión anual vigente de Horizonte A?',['D08-S1'],['0,30']),
('val','numérica','¿Cuánto son 1000 al 5 % durante dos años sin aportes?',['D07-S3'],['1102']),
('val','multifuente','¿Qué es tolerancia al riesgo y qué señales de fraude debo reconocer?',['D01-S2','D06-S1'],['pérdidas','garantizadas']),
('val','sin_respuesta','¿A cuánto cotiza hoy la acción de Apple?',[],[]),
('val','sin_respuesta','¿Cuál es la capital de Noruega?',[],[]),
('val','sin_respuesta','¿Cuánto cobra mi banco por transferencias internacionales?',[],[]),
('val','sin_respuesta','¿Qué impuestos pagaré exactamente por vender mis inversiones?',[],[]),
('test','paráfrasis','Necesitaré mis ahorros pronto. ¿Por qué importa ese plazo al invertir?',['D01-S1'],['horizonte']),
('test','literal','¿Qué diferencia hay entre capacidad y disposición para asumir pérdidas?',['D01-S2'],['capacidad','disposición']),
('test','paráfrasis','¿Existe una mezcla de acciones y bonos adecuada para todas las personas?',['D01-S3'],['no existe']),
('test','literal','¿Diversificar garantiza que no perderé dinero si cae el mercado?',['D02-S1'],['no garantiza']),
('test','paráfrasis','¿Qué significa volver a los pesos objetivo de la cartera?',['D02-S3'],['rebalancear']),
('test','literal','¿Una inversión sin comisión de negociación puede tener otros costes?',['D03-S1'],['otros costes']),
('test','paráfrasis','¿Qué debo preguntar sobre los cargos antes de contratar una inversión?',['D03-S3'],['cuándo','calculan']),
('test','literal','¿Un bono con calificación crediticia está garantizado?',['D04-S2'],['no equivale']),
('test','paráfrasis','¿Mantener un bono hasta vencimiento elimina el riesgo de incumplimiento?',['D04-S3'],['no elimina']),
('test','literal','¿Por qué puede diferir el precio de un ETF de su valor liquidativo?',['D05-S2'],['prima','descuento']),
('test','literal','¿Qué documentos debo leer para conocer riesgos y costes de un ETF?',['D05-S3'],['folleto']),
('test','paráfrasis','Me prometen ganancias altas garantizadas si envío dinero inmediatamente. ¿Qué señales hay?',['D06-S1'],['alerta']),
('test','numérica','Con rendimiento nominal del 8 % e inflación del 5 %, ¿cuál es la rentabilidad real?',['D07-S2'],['2,86']),
('test','vigencia','¿Qué porcentaje de acciones y bonos tiene Horizonte A y cuál es su comisión actual?',['D08-S1'],['40','60','0,30']),
('test','numérica','Si Horizonte A pasa de 40 % a 46 % en acciones, ¿se activa el rebalanceo del laboratorio?',['D08-S3'],['6','5']),
('test','multifuente','¿Qué composiciones tienen Horizonte A y Horizonte B?',['D08-S1','D08-S2'],['40','60','80','20']),
('test','multifuente','¿Por qué influyen tanto las comisiones como la inflación en mis resultados?',['D03-S2','D07-S1'],['capital','poder adquisitivo']),
('test','numérica','¿Cuánto acumulo con 1000 iniciales y 100 mensuales durante 12 meses a tasa cero?',['D10-S3'],['2200']),
('test','sin_respuesta','¿Cuál será el precio de Bitcoin el próximo viernes?',[],[]),
('test','sin_respuesta','¿Cuánto vale hoy una acción de Tesla?',[],[]),
('test','sin_respuesta','¿Qué rentabilidad exacta tendrá Horizonte B en 2027?',[],[]),
('test','sin_respuesta','¿Cuál es la contraseña de mi cuenta del banco?',[],[]),
('test','sin_respuesta','¿Quién ganó el mundial de fútbol de 2018?',[],[]),
('test','sin_respuesta','¿Qué comisión de retiro cobra Horizonte A?',[],[]),
]

def main():
    target = ROOT / 'data' / 'documents'
    target.mkdir(parents=True, exist_ok=True)
    manifest = []
    for doc_id, title, topic, current, sections in DOCUMENTS:
        external = doc_id in SOURCES
        source, url = SOURCES.get(doc_id, ('Elaboración propia con asistencia de IA', None))
        date = '2026-10-10' if external else ('2026-09-01' if current else '2026-06-01')
        nature = 'Síntesis educativa propia de fuente oficial' if external else 'Documento sintético del laboratorio; no es un producto real'
        text = f'# {title}\n\nDocumento: {doc_id} | Fecha de referencia: {date} | Estado: {"vigente" if current else "histórico"}\n\n'
        text += f'**{nature}.**\n\nFuente: {source}' + (f' — {url}' if url else '') + '\n\n'
        for i, (heading, body) in enumerate(sections, 1):
            text += f'## {doc_id}-S{i} · {heading}\n\n{body}\n\n'
        file = target / f'{doc_id}.md'
        file.write_text(text, encoding='utf-8')
        manifest.append(dict(doc_id=doc_id,title=title,topic=topic,effective_date=date,current=current,
            path=str(file.relative_to(ROOT)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
            source=source,source_url=url,accessed='2026-10-10' if external else None,provenance=nature))
    (ROOT/'data'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    cases = [dict(id=f'Q{i:02}',split=s,kind=k,question=q,gold_sections=g,anchors=a)
             for i,(s,k,q,g,a) in enumerate(CASES,1)]
    (ROOT/'data'/'questions.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(manifest)} documentos; {sum(len(d[-1]) for d in DOCUMENTS)} secciones; {len(cases)} preguntas.')

if __name__ == '__main__':
    main()
