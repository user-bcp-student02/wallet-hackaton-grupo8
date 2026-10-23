"""Revision final de producto contra el Issue y las fuentes de docs."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'product_owner'
LABEL = 'Product Owner'
SPEC_FILE = 'product_owner_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Actua como Product Owner y realiza la revision final del Issue seleccionado.
Compara su alcance y criterios de aceptacion con `docs/`, el reporte de Security,
la implementacion de Developer y la evidencia/propuesta de Testing recibidos.

1. Revisa el Issue seleccionado, no conviertas toda la epica en alcance obligatorio.
   Usa la epica y las seis historias como contexto de producto y fuente para detectar
   contradicciones, dependencias y criterios relevantes.
2. Construye una matriz criterio -> evidencia concreta -> estado: CUMPLE, PARCIAL,
   NO CUMPLE o NO VERIFICADO. Diferencia codigo generado, pruebas propuestas y
   comandos realmente ejecutados.
3. Comprueba coherencia con los contratos W1-W6 y con los limites del mock: no hay
   dinero real ni auth; algunos datos operativos/analiticos no estan en el mock; los
   controles `/control/*` no son APIs de negocio. No cuentes estas capacidades como
   implementadas sin evidencia local.
4. Revisa que los estados pendientes, timeouts, idempotencia, callbacks, reversos,
   centimos PEN, accesibilidad, telemetria y limites de proveedor se traten solo
   cuando apliquen al Issue y segun las fuentes aprobadas.
5. Expone preguntas abiertas pertinentes de docs (KYC, monto bajo, estados, retencion
   idempotente, disputa/SLA, timestamps/canales de conciliacion u otras). No inventes
   respuestas ni conviertas metricas de trimestre en resultados medidos por el codigo.
6. Indica defectos y cambios necesarios con criterio, impacto y responsable. Emite
   `DECISION: REQUIERE AJUSTES` si algun criterio aplicable no cumple o no tiene
   evidencia suficiente; en otro caso `DECISION: LISTO PARA REVISION HUMANA`.
   Esta decision no es aprobacion de lanzamiento ni sustituye a la persona.
"""

agent = Agent(
    role=LABEL,
    goal="Verificar valor, alcance y evidencia de la entrega desde los criterios del producto.",
    backstory="Proteges la trazabilidad entre necesidad, experiencia del usuario, limites operativos y entrega verificable.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    return Task(
        description=(
            INSTRUCTIONS
            + "\nFeature: " + str(feature.get("title", ""))
            + "\n" + str(feature.get("description", ""))
            + "\n" + str(feature.get("acceptance_criteria", []))
        ),
        expected_output=(
            "Contenido de product_owner_review.md: resumen de alcance; matriz criterio -> "
            "evidencia -> estado; gaps y riesgos con responsable; preguntas abiertas; "
            "metricas que requieren medicion real y limites del mock; decision final "
            "`DECISION: REQUIERE AJUSTES` o `DECISION: LISTO PARA REVISION HUMANA`. "
            "No declares ejecuciones, aprobacion de lanzamiento ni capacidades sin evidencia."
        ),
        agent=agent,
    )