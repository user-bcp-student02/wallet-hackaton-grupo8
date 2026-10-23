# Mejora tu agente

Los agentes de `agents/` parten con instrucciones mínimas. El flujo, las pausas humanas, los formatos de salida y los controles siguen funcionando. El ejercicio consiste en mejorar la responsabilidad, los entregables y las instrucciones del rol que te asignó el equipo.

1. Edita las instrucciones de tu archivo `agents/<rol>.py`. Puedes ampliar `INSTRUCTIONS` y, en CrewAI, el objetivo, contexto y salida de la tarea.
2. Especifica entregables verificables y evidencia para comprobarlos. Indica qué hacer con errores y observaciones. Prohíbe inventar pruebas o resultados.
3. Conserva firmas, claves de estado, imports, nombres de artefactos y formatos que consume el flujo.
4. Publica el cambio en tu rama y abre un PR para revisión del equipo.
5. Abre «Mi equipo» en el portal. Consulta el overview y ejecuta la evaluación de tu equipo sobre el código publicado en su rama principal.

El dashboard separa pruebas del flujo, cobertura de instrucciones por agente y total del equipo. El template básico puede aprobar el flujo y obtener una puntuación baja en instrucciones. Esa es la situación inicial esperada.

La rúbrica estática busca responsabilidades del rol, entregables, evidencia, honestidad y correcciones con feedback. Es orientativa: no mide las respuestas reales del modelo ni garantiza calidad del código generado. El instructor revisa los casos no reconocidos.


## Roles del flujo

El flujo es `Security → Developer → Testing → Product Owner`. Antes de ampliar un Issue, lee su descripcion, criterios y las fuentes pertinentes de `docs/`. El orquestador carga la epica, los limites/contratos del mock y las historias relacionadas; cada etapa tambien recibe los outputs aprobados anteriores.

| Rol y archivo | Responsabilidad | Entregable |
| --- | --- | --- |
| Security, `agents/security.py` | Analiza riesgos preventivamente antes de que exista codigo. Usa los limites documentados de W1-W6, separa hechos de preguntas y define controles verificables. | `security_report.md`: activos, amenazas, mitigaciones para Developer y casos de verificacion para Testing. No afirma auditorias ni controles implementados. |
| Developer, `agents/developer.py` | Implementa el Issue de extremo a extremo en Quarkus 3.x, Angular 17, pruebas de soporte y configuracion/infra local que sea necesaria. | `developer_spec.md` y archivos completos. Conserva contratos mock, no inventa integraciones ni amplía a toda la epica; incluye comandos, bloqueos y matriz criterio -> codigo -> evidencia. |
| Testing, `agents/testing.py` | Convierte los criterios y controles de Security en pruebas positivas, negativas, limites, API/UI e integracion cuando el proyecto lo permite. | `testing_report.md`, tests completos y comandos reales. Marca `NO EJECUTADO` lo no ejecutado; no trata el mock como evidencia de produccion. |
| Product Owner, `agents/product_owner.py` | Compara el Issue con la implementacion, pruebas, limites operativos y fuentes de `docs/`. Expone gaps y preguntas sin inventar decisiones. | `product_owner_review.md`: matriz criterio -> evidencia -> estado, pendientes, responsables y decision `REQUIERE AJUSTES` o `LISTO PARA REVISION HUMANA`. No aprueba el lanzamiento. |

Mantén `KEY`, `SPEC_FILE`, `EXTRACT_CODE` y la firma de `build_task` alineados con `crew/workflow.py` y `main.py`. No agregues agentes al orden activo sin cambiar el contrato, el checkpoint y sus pruebas.

Las APIs de `docs/mockups/` son escenarios ficticios: no mueven dinero y no ofrecen autenticacion. Respeta las diferencias entre el mock y las historias, en especial eventos de onboarding, filtros/fechas comerciales, auditoria de idempotencia, soporte/reversos y reportes de conciliacion. Si una capacidad no existe, documenta la brecha; no la simules como integrada.
