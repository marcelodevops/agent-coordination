# Observaciones y acuerdos de Marcelo — AIMonk

Fecha de elaboración: 20 de octubre de 2026. Zona horaria: America/Santiago. Fuente: esta conversación, incluido el contexto recibido por el asistente de notas. No se atribuyen horas exactas a comentarios que no las tienen verificadas.

Este documento recoge comentarios y acuerdos para preparar reportes consistentes. **No es una fuente de estado operativo en vivo**, una aceptación de entregas ni evidencia de que una función esté implementada. Los resultados deben contrastarse con código, pruebas, revisiones y registros de ejecución.

## Decisiones e instrucciones del usuario

- Marca: **AIMonk**; el proyecto de producto permanece separado como **agent-bootstrap**.
- Cada plan pertenece a **un único repositorio**. Marcelo desea poder coordinar varios planes simultáneos; esa capacidad no debe darse por implementada.
- Equipo: Eiren coordina; Mr.Q y **Agy**, con A mayúscula, ejecutan. Copilot fue retirado. El identificador técnico existente `agy` puede conservarse sin cambiar el nombre visible.
- Rebalanceo aprobado: C3 y E2 pasan de Mr.Q a Agy, dos de las diez tareas originales de Mr.Q. Una reasignación no equivale a un despacho.
- Mantener commits separados por tarea y repositorio. Flujo acordado: ramas `feat/`, `fix/` o `chore/` → pull request → revisión → merge a `main`.
- Usar revisores independientes con reglas predefinidas. La aceptación automática se autoriza para casos simples con evidencia completa, pruebas aprobadas, alcance respetado y sin hallazgos; no es una autorización universal para aceptar entregas.
- Se autorizaron pushes, PR y merges tras revisión y verificaciones; también publicar candidatas en **TestPyPI** y comprobar su instalación. **PyPI de producción requiere aprobación de la candidata**.
- Marcelo pidió incorporar un asistente dedicado a registrar sus comentarios y facilitar reportes coherentes.

## Observaciones y problemas señalados

- Marcelo busca **visibilidad sin tener que intervenir**. Sus preguntas son observaciones para optimizar, no intentos de perseguir al equipo o reemplazar al coordinador.
- La espera frecuente de Mr.Q o Agy genera dudas sobre dependencias, reparto y seguimiento. Debe distinguirse una espera necesaria de trabajo listo que no se asigna o una revisión pendiente que no se atiende.
- El número de commits no explica por sí solo el progreso. Hace falta acceder a pruebas, resultados, bloqueos y entregas para comprender qué se logró y por qué algo espera.
- La interfaz parece detenida durante horas y no ofrece suficiente visibilidad en tiempo real. Marcelo expresa voluntad de ayudar y preocupación por una posible sobrecarga de Eiren.
- La conversación aclaró que ejecuciones acotadas más esperas no equivalen a 24 horas de trabajo continuo.
- Las decisiones guardadas podrían vincularse a acciones y resultados, versionarse y alimentar analíticas.
- Marcelo prefiere una interacción orgánica, con humor, puntos de vista y trato respetuoso. Esto no convierte metáforas sobre cansancio o aburrimiento en mediciones del estado de los agentes.

## Necesidades y propuestas pendientes de verificar o implementar

- Cerrar el ciclo: observar → recoger entregas → verificar evidencia → revisar → aceptar o corregir → desbloquear → despachar → esperar y repetir.
- Mostrar quién está ejecutando, última actividad, motivo y duración de esperas, próximo paso y estado del coordinador.
- Vincular cada resultado de prueba con comando, fecha, resultado y revisión exacta del código. Separar tiempo de ejecución de tiempo en cola/revisión.
- Mantener trazabilidad estructurada **decisión → motivo/evidencia → acción → resultado → revisión**, con identificadores y responsables. Conservar correcciones como registros nuevos que sustituyen explícitamente a los anteriores, sin borrar la historia.
- Analizar retrabajo, bloqueos, tiempos y efecto de cambios en las reglas. Las métricas deben derivarse de registros completos, no de impresiones o porcentajes inventados.
- Explorar chat integrado con contexto y reportes legibles; no presentar una sesión independiente como si fuera esta misma conversación.
- Coordinar varios planes respetando el límite de un repositorio por plan, capacidad compartida y conflictos de archivos.

## Automatización: distinguir configuración de funcionamiento probado

Se configuró un piloto de reactivación periódica de Codex para C2 → C3, con parada tras el despacho de C3. Después Marcelo autorizó ampliar el ciclo a pushes, PR, merges y TestPyPI, y se comunicó su reactivación. **Configurar una programación no demuestra continuidad operacional ni que cada paso haya ocurrido**. Marcelo siguió señalando visibilidad insuficiente. No deducir publicaciones, merges o progreso actual a partir de esos anuncios.

## Cómo mantener estas notas

El asistente de notas recibe contexto y mensajes que Eiren le despacha: **no escucha automáticamente futuras intervenciones**. Eiren debe reenviar los comentarios relevantes o solicitar una actualización. Las nuevas notas deben separar decisiones del usuario, observaciones, propuestas y hechos verificados. Este archivo no autoriza acciones nuevas ni sustituye los registros de aceptación.
