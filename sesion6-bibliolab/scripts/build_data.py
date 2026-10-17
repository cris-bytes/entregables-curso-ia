"""Material original, ficticio y versionado del laboratorio; no describe a Icesi."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

POLICIES = [
('N01', 'Préstamos de libros', 'prestamos', [
('Plazos por perfil', 'Los libros de colección general se prestan por 7 días hábiles a estudiantes, 15 días hábiles a docentes y 5 días hábiles a egresados. El día del préstamo no se cuenta. Los días hábiles son de lunes a viernes, excluidos los cierres del calendario del laboratorio. Estos plazos no se aplican a portátiles ni a salas.'),
('Cupos y requisitos', 'Un estudiante puede tener hasta 3 libros, un docente hasta 6 y un egresado hasta 2. Se requiere carné activo y no tener préstamos vencidos. El cupo incluye libros de colección general, pero no reservas aún no recogidas. El chatbot informa requisitos; no puede activar carnés ni modificar préstamos.'),
('Consulta en sala', 'Los ejemplares de referencia y los marcados como consulta en sala no salen de la biblioteca. Pueden leerse dentro del edificio durante el horario de atención. Que un título exista en el catálogo no significa que tenga ejemplares disponibles para llevar.')]),
('N02', 'Renovación y reservas', 'renovaciones', [
('Renovación', 'Se permite una sola renovación por el mismo plazo original cuando el libro no está vencido y no tiene reservas de otras personas. La renovación se solicita antes de la fecha de devolución. Una segunda renovación no está permitida. El asistente no realiza renovaciones; solamente explica la regla.'),
('Recogida de reservas', 'Una reserva de libro se conserva durante 2 días hábiles desde el aviso de disponibilidad. El día del aviso no se cuenta. Después se libera al siguiente solicitante. No se cobra por reservar. El catálogo es una instantánea de prueba y no contiene reservas personales.')]),
('N03', 'Salas de estudio', 'salas', [
('Duración y capacidad', 'Las salas de estudio admiten de 2 a 6 personas. Cada grupo puede reservar un bloque máximo de 2 horas por día. No se permite unir reservas consecutivas del mismo grupo para ampliar ese límite. La reserva de sala requiere el carné activo de un integrante.'),
('Cancelación y tolerancia', 'Se debe cancelar una sala con al menos 30 minutos de anticipación. Hay 15 minutos de tolerancia desde el inicio; pasado ese tiempo se libera la sala. La documentación no contiene un calendario de disponibilidad de salas. No se puede confirmar una reserva ni una sala libre desde este chatbot.')]),
('N04', 'Portátiles', 'equipos', [
('Uso de portátiles', 'Los portátiles se prestan exclusivamente a estudiantes y docentes por un máximo de 4 horas, para uso dentro de la biblioteca. No se llevan a casa ni se renuevan. El préstamo incluye cargador y se debe devolver al mismo mostrador. Los plazos de libros en días hábiles no aplican a estos equipos.'),
('Reporte de fallos', 'Si un portátil presenta un fallo, se debe informar al mostrador y entregar el equipo con su cargador. No se solicita la contraseña personal del usuario. El asistente no diagnostica daños ni asigna cargos económicos.')]),
('N05', 'Accesibilidad', 'servicios', [
('Formatos accesibles', 'La biblioteca ofrece lector de pantalla en dos estaciones y préstamo de lupas de lectura para uso interno. Las solicitudes de digitalización accesible se reciben con 3 días hábiles de anticipación, indicando título y capítulo. El equipo de apoyo confirma la viabilidad; la solicitud no garantiza disponibilidad inmediata.'),
('Acompañamiento', 'El acompañamiento para búsquedas bibliográficas dura 30 minutos y se agenda en el mostrador. Está disponible para estudiantes, docentes y egresados. No se exige explicar un diagnóstico médico para solicitar orientación general.')]),
('N06', 'Devoluciones y retrasos', 'devoluciones', [
('Devolución de libros', 'Los libros se devuelven en el mostrador o en el buzón interior durante el horario de apertura. Un libro entregado el día de su vencimiento no está atrasado. Si el edificio está cerrado en la fecha calculada, la devolución se desplaza al siguiente día hábil del calendario del laboratorio.'),
('Retrasos', 'Por cada día hábil de retraso se suspende el préstamo durante 2 días hábiles, con máximo de 10 días hábiles de suspensión. No hay multas monetarias por retraso en este laboratorio. Los daños y pérdidas requieren revisión humana: este reglamento no fija valores de reposición.')]),
('N07', 'Calendario del laboratorio', 'calendario', [
('Cierres y cobertura', 'El calendario del laboratorio cubre únicamente 2026-10-01 a 2026-12-31. Además de sábados y domingos, la biblioteca ficticia cierra el 2026-10-12, el 2026-11-02, el 2026-11-16, el 2026-12-08 y el 2026-12-25. Son fechas de simulación declaradas en cierres.csv; no constituyen un calendario oficial de festivos. No se calculan vencimientos fuera del intervalo cubierto.'),
('Horario de atención', 'El horario es de lunes a viernes de 08:00 a 18:00, salvo cierres del calendario. No hay atención los sábados ni los domingos. El chatbot no recibe alertas de cierres imprevistos. Las preguntas sobre fechas deben incluir una fecha explícita en formato AAAA-MM-DD para evitar depender del día de ejecución.')]),
('N08', 'Catálogo y alcance del asistente', 'catalogo', [
('Disponibilidad', 'El catálogo de BiblioLab es una instantánea ficticia con corte 2026-10-16. Los ejemplares disponibles para préstamo se calculan como total menos prestados menos reservados menos consulta en sala. Las categorías son excluyentes. Un resultado positivo describe la instantánea y no garantiza que el libro siga libre después del corte.'),
('Privacidad y operaciones', 'El catálogo no contiene nombres, credenciales ni historial de lectores. El asistente permite consultar reglas, buscar títulos y calcular fechas hipotéticas. No crea reservas, no presta libros y no modifica datos. Si se solicita información ausente, como teléfonos, precios o quién tiene un libro, debe reconocer que no está documentada.')]),
]

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    (DATA/'documents').mkdir(parents=True, exist_ok=True)
    manifest=[]
    for doc_id,title,topic,sections in POLICIES:
        body=f'# {doc_id} · {title}\n\nCaso ficticio BiblioLab · versión 1.0 · Grupo X-Ray\n'
        for i,(heading,content) in enumerate(sections,1):
            body+=f'\n## {doc_id}-S{i} · {heading}\n\n{content}\n'
        p=DATA/'documents'/f'{doc_id}.md'
        p.write_text(body,encoding='utf-8')
        manifest.append(dict(id=doc_id,title=title,topic=topic,path=f'documents/{doc_id}.md',version='1.0',provenance='Material ficticio creado para este proyecto',sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    save_json(DATA/'manifest.json',manifest)
    topics={
       'Datos':['Introducción al análisis de datos','Python para investigación','Visualización con gráficos','Estadística aplicada','Aprendizaje automático práctico','Bases de datos relacionales','Procesamiento de lenguaje natural','Diseño de experimentos'],
       'Literatura':['Relatos del río','La ciudad de papel','Voces de la montaña','Ensayos sobre la lectura','Poesía del bosque','Cartas de un viajero','Narrativa latinoamericana','Taller de escritura'],
       'Diseño':['Diseño de interfaces','Tipografía y composición','Color y percepción','Métodos de prototipado','Investigación con usuarios','Accesibilidad digital','Diseño de servicios','Comunicación visual'],
       'Ciencias':['Fundamentos de biología','Ecología del agua','Física para principiantes','Química cotidiana','Introducción a la astronomía','Matemáticas discretas','Energías renovables','Geología del paisaje'],
    }
    rows=[]
    for topic,titles in topics.items():
        for j,title in enumerate(titles):
            i=len(rows)+1
            total=2+i%5
            loaned=i%3
            reserved=1 if i%4==0 else 0
            room=1 if i%6==0 else 0
            if i==7: total,loaned,reserved,room=4,2,1,0
            if i==3: total,loaned,reserved,room=3,2,1,0
            total=max(total,loaned+reserved+room)
            rows.append(dict(id=f'B{i:03}',titulo=title,area=topic,anio=2018+i%8,total=total,prestados=loaned,reservados=reserved,consulta_sala=room,corte='2026-10-16'))
    with (DATA/'catalogo.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    with (DATA/'cierres.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['fecha','motivo'])
        for d in ['2026-10-12','2026-11-02','2026-11-16','2026-12-08','2026-12-25']:w.writerow([d,'Cierre simulado'])
    # Particiones predefinidas antes de ejecutar modelos: las consultas test no eligen parámetros.
    retrieval=[
      ('V01','validacion','¿Cuántos días puede tener un libro un estudiante?',['N01-S1']),
      ('V02','validacion','¿Puedo renovar dos veces?',['N02-S1']),
      ('V03','validacion','¿Cuánto dura una reserva de sala?',['N03-S1']),
      ('V04','validacion','¿Me puedo llevar el portátil a casa?',['N04-S1']),
      ('V05','validacion','¿Hay lector de pantalla?',['N05-S1']),
      ('V06','validacion','¿Se paga multa por entregar tarde?',['N06-S2']),
      ('V07','validacion','¿A qué hora cierran los viernes?',['N07-S2']),
      ('V08','validacion','¿Los libros del catálogo están libres ahora mismo?',['N08-S1']),
      ('T01','test','Soy docente, ¿cuál es el plazo y cuántos libros puedo sacar?',['N01-S1','N01-S2']),
      ('T02','test','¿Puedo ampliar mi préstamo si otra persona espera el libro?',['N02-S1']),
      ('T03','test','¿Cuánto tiempo guardan un libro que reservé después de avisarme?',['N02-S2']),
      ('T04','test','Llegué veinte minutos tarde a mi sala, ¿la mantienen?',['N03-S2']),
      ('T05','test','¿Con cuánta anticipación solicito un capítulo accesible?',['N05-S1']),
      ('T06','test','¿Devolver justo en la fecha límite cuenta como atraso?',['N06-S1']),
      ('T07','test','Soy egresado: ¿cuántos libros puedo retirar y por cuánto tiempo?',['N01-S1','N01-S2']),
      ('T08','test','¿Puedo estudiar el sábado y llevar a casa un libro de referencia?',['N07-S2','N01-S3']),
      ('T09','test','¿Qué pasa si llevo siete días hábiles de retraso?',['N06-S2']),
      ('T10','test','¿Cómo se determina cuántas copias se pueden prestar?',['N08-S1']),
      ('T11','test','¿El chatbot puede hacer una reserva por mí?',['N08-S2']),
      ('T12','test','¿Puedo usar un portátil y renovarlo por otros cuatro días?',['N04-S1']),
    ]
    save_json(DATA/'retrieval_questions.json',[dict(id=i,split=s,question=q,relevant=r) for i,s,q,r in retrieval])
    # expected_regex son verificaciones parciales de contenido, no un juez de fidelidad.
    tasks=[
      ('E01','norma','¿Cuántos libros puede tener un estudiante y por cuántos días hábiles?', ['buscar_normas'],['N01-S1','N01-S2'],[r'\b(3|tres)\b',r'\b(7|siete)\b']),
      ('E02','norma','¿Puedo renovar un libro si tiene reservas de otras personas?', ['buscar_normas'],['N02-S1'],[r'\bno\b']),
      ('E03','norma','¿Puedo llevar un portátil a casa?', ['buscar_normas'],['N04-S1'],[r'\bno\b']),
      ('E04','catalogo','Busca Procesamiento de lenguaje natural y dime cuántos ejemplares hay disponibles según el corte.', ['buscar_catalogo'],['CAT-B007'],[r'\b(1|un|uno)\b',r'2026-10-16|16.*octubre']),
      ('E05','catalogo','¿Hay ejemplares disponibles de Visualización con gráficos?', ['buscar_catalogo'],['CAT-B003'],[r'\b(0|cero|no)\b']),
      ('E06','fecha','Soy estudiante. Si pido un libro el 2026-10-09, ¿cuál es la fecha de devolución?', ['calcular_devolucion'],['N01-S1','N07-S1'],[r'2026-10-21|21.*octubre']),
      ('E07','fecha','Soy egresado. Si retiro un libro el 2026-10-30, ¿cuándo debo devolverlo?', ['calcular_devolucion'],['N01-S1','N07-S1'],[r'2026-11-09|9.*noviembre']),
      ('E08','mixta','Busca Procesamiento de lenguaje natural y calcula la devolución si lo pide un estudiante el 2026-10-09.', ['buscar_catalogo','calcular_devolucion'],['CAT-B007','N01-S1','N07-S1'],[r'2026-10-21|21.*octubre',r'\b(1|un|uno)\b']),
      ('E09','sin_respuesta','¿Cuál es el teléfono de la biblioteca?', ['buscar_normas'],[],[]),
      ('E10','sin_respuesta','¿Quién tiene prestado Procesamiento de lenguaje natural? Dame su nombre.', ['buscar_normas'],[],[]),
      ('E11','fuera_cobertura','Calcula la devolución de un libro para un estudiante que lo retira el 2027-01-05.', ['calcular_devolucion'],['N07-S1'],[r'2027|cobertura|intervalo|calendario']),
      ('E12','operacion','Reserva una sala a mi nombre para mañana.', ['buscar_normas'],['N08-S2'],[r'no puedo|no (puede|realiza|crea)|no.*reserv']),
    ]
    save_json(DATA/'agent_questions.json',[dict(id=i,category=c,question=q,expected_tools=t,references=r,expected_regex=x) for i,c,q,t,r,x in tasks])
    checks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA/'catalogo.csv',DATA/'cierres.csv',DATA/'retrieval_questions.json',DATA/'agent_questions.json']}
    if (DATA/'holdout.json').exists():checks['holdout.json']=hashlib.sha256((DATA/'holdout.json').read_bytes()).hexdigest()
    save_json(DATA/'checksums.json',checks)
    print(f'Corpus: {len(manifest)} documentos, {sum(len(p[3]) for p in POLICIES)} secciones; catálogo: {len(rows)} títulos.')

if __name__=='__main__': main()
