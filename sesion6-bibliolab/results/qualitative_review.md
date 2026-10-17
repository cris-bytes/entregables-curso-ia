## Revisión cualitativa de la ejecución de referencia

El notebook ejecutó sus 14 celdas de código sin errores y las 17 pruebas pasaron. Esto verifica funcionamiento del programa; **no implica que el generador responda correctamente a todas las preguntas**.

### Hallazgos concretos

| Caso | Observación | Interpretación |
|---|---|---|
| E01, 3B guiado | Responde 3 libros y 7 días hábiles, pero omite referencias | El contenido mínimo es correcto; falla la citación del modelo |
| E02 y E03, 3B guiado | Dice que no está documentado aunque las reglas recuperadas sí responden | Falsa abstención: el problema está en la generación |
| E04, 3B guiado | Identifica un ejemplar y cita CAT-B007; no escribe la fecha exacta del corte | Respuesta parcialmente completa; la evidencia conserva el corte |
| E05, 3B guiado | Se abstiene aunque el catálogo informa cero disponibles | Cero es un valor conocido, no información ausente |
| E06, 3B guiado | Da 2026-10-21 y cita la regla | El cálculo viene de Python; el modelo lo comunica correctamente |
| E07, 3B guiado | Da la fecha correcta, pero dice que los días omitidos no están excluidos | Error factual pese a fecha y citas válidas; el chequeo por regex no lo detecta |
| E08, 3B guiado | Se abstiene aun después de recibir catálogo y cálculo | Llamar todas las herramientas no garantiza integrar su información |
| H01 y H04 | Comunica el dato solicitado, pero sin citas | Recuperación correcta y generación útil con fallo de formato |
| H02, H03, H05 y H06 | Omite o niega información que sí aparece en la evidencia | Cuatro fallos de respuesta con todas las secciones esperadas recuperadas |

En las seis consultas adicionales, la recuperación encontró toda la evidencia anotada, pero el modelo no produjo citas en ninguna. Por tanto, **100 % de Recall en ese pequeño conjunto no equivale a 100 % de respuestas correctas**. El panel añade las fuentes consultadas con una etiqueta explícita; no se atribuyen esas citas al modelo.

El flujo guiado de 3B cubrió las herramientas esperadas en 12/12 tareas, frente a 8/12 del agente autónomo. La cobertura media de citas esperadas fue 25 % en el flujo guiado de 3B y 0 % en 1,5B. Estos porcentajes son indicadores parciales sobre tareas de desarrollo; no son una estimación de calidad general.

Los controles de perfil faltante, fechas cerradas y calendario fuera de cobertura funcionan en Python. El LLM suele resumir los errores como «no está documentado», perdiendo la explicación específica. Por eso la interfaz muestra también la salida del cálculo. Una mejora futura sería presentar estos errores directamente, identificándolos como mensajes del programa, sin pedir al modelo que los reescriba.

### Alcance de las conclusiones

La entrega demuestra la arquitectura de herramientas, la recuperación y la evaluación, y ofrece una demo funcional. El generador pequeño necesita mejoras antes de usarse como atención autónoma en una biblioteca real. Una evaluación externa, mejores modelos compatibles con el equipo y verificación por afirmación son pasos posteriores; no se afirma que ya estén resueltos.

La revisión se hizo después de observar las salidas y no se usó para modificar el prompt, el recuperador ni las preguntas adicionales. Las respuestas originales se conservan en los JSON.
