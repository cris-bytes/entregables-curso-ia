# Entrega del mini proyecto RAG

**Caso:** FinGuía, asesor educativo de inversión con fuentes documentales y simulador de aportes.

| Criterio de la rúbrica | Evidencia concreta |
|---|---|
| Notebook completo | Problema, hipótesis, datos, EDA, implementación, experimentos, interpretación y conclusiones en `FinGuia_RAG_Inversion.ipynb`. |
| Reproducibilidad | Dependencias fijadas, revisiones de modelos, hashes documentales, partición fija, semillas, ejecución integral y pruebas. |
| Chatbot RAG | Recuperación real, modelos generativos locales, respuestas crudas, referencias por sección, abstención y aplicación Gradio. La indexación se distingue del entrenamiento. |
| Innovación | Comparación de cuatro recuperadores y dos generadores, RRF, parámetros de fragmentación y k, ablación de vigencia, calibración de abstención y simulación matemática. |
| Video | Pendiente del estudiante: menos de dos minutos, ejecución de la celda Gradio y dos interacciones con referencias. |

La tabla localiza evidencias; no garantiza una calificación. La comparación de generadores es exploratoria, y las métricas de recuperación no se presentan como precisión factual del chatbot.

## Pendientes antes de subir a Intu

- Revisar y personalizar el texto del proyecto; verificar la política de uso de IA del curso.
- Incorporar el enlace de los notebooks guía y contrastar los requisitos específicos cuando esté disponible.
- Realizar pruebas de uso en el equipo del estudiante.
- Crear el repositorio de GitHub cuando se decida publicar. Se ha respetado la indicación de mantener el proyecto local por ahora.
- Grabar y subir el video o adjuntarlo directamente en Intu.

**Repositorio GitHub:** pendiente; no creado.

**Video:** pendiente de grabación y subida por el estudiante.

**Notebooks guía del curso:** enlace pendiente de proporcionar.

## Estructura futura para todos los entregables del curso

Se puede ubicar esta carpeta en `entregables/01-finguia-rag/` dentro de un repositorio del curso y añadir nuevas actividades como carpetas hermanas. Al publicar, excluir `.venv`, `.cache`, archivos de entorno y videos pesados; conservar notebook con salidas, documentos, código y resultados pequeños. No se han copiado otros proyectos del directorio padre ni modificado su historial Git.
