# Video · BiblioLab

La entrega exige menos de dos minutos y debe mostrar la ejecución de la celda de Gradio y dos interacciones con referencias.

## Grabación de demostración

El archivo [BiblioLab_demo.mp4](../video/BiblioLab_demo.mp4) está generado y dura **58,92 segundos**. La grabación automatizada usa un navegador real: ejecuta la última celda del notebook, abre Gradio y realiza consultas reales al modelo local. No reemplaza las respuestas con texto editado y no incluye narración. El registro técnico está en `results/video_recording.json`.

Se puede adjuntar directamente en Intu. La generación local del archivo no equivale a haberlo enviado a la plataforma. Si se prefiere un video narrado por el estudiante, seguir el guion siguiente.

## Guion sugerido (1:30–1:50)

| Tiempo | Acción |
|---|---|
| 0:00–0:15 | Mostrar el notebook: «BiblioLab consulta reglas, inventario y fechas de una biblioteca ficticia». |
| 0:15–0:30 | Ejecutar la última celda, donde se ve `demo.queue().launch(...)`, y abrir Gradio. |
| 0:30–0:55 | Preguntar: «Busca Procesamiento de lenguaje natural y dime cuántos ejemplares hay disponibles». Mostrar respuesta, corte y `[CAT-B007]`. |
| 0:55–1:25 | Preguntar: «Soy estudiante. Si pido un libro el 2026-10-09, ¿cuál es la fecha de devolución?». Mostrar 2026-10-21 y referencias a reglas y calendario. |
| 1:25–1:45 | Mostrar evidencia y fechas contadas: «Las herramientas consultan y calculan; el modelo redacta. Podemos revisar las fuentes». |

Ensayar antes y precargar Ollama para reducir la espera. El panel distingue las fuentes adjuntas por la aplicación de las citas del modelo. Si aparece una advertencia de citas, no ocultarla ni presentarla como respuesta validada.
