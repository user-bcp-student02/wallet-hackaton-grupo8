"""Revision final de coherencia, criterios de aceptacion y evidencia del equipo."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Actua como revisor final independiente (Chapter). Compara el Issue y cada criterio
de aceptacion con la arquitectura, los contratos, las entregas aprobadas de Datos,
Backend y Frontend, el informe de pruebas y la revision de Seguridad disponibles.

1. Construye una matriz criterio -> evidencia de implementacion -> prueba/estado.
    Marca cada criterio como CUMPLE, PARCIAL, NO CUMPLE o NO VERIFICADO.
2. Comprueba coherencia entre API, datos, interfaz, estados, seguridad y pruebas.
    Busca contradicciones, alcance extra, decisiones no aprobadas, dependencias y
    riesgos operativos de la ejecucion propuesta.
3. No confundas codigo generado con codigo ejecutado; acepta como evidencia solo
    resultados presentes en el contexto. Mantiene NO EJECUTADO donde corresponda.
4. Ordena defectos por severidad y explica impacto y responsable de resolverlos.
    No implementes ni ocultes hallazgos, y no inventes aprobaciones.
5. Emite exactamente un veredicto final: VEREDICTO: APROBADO solo si no hay
    criterios NO CUMPLE, riesgos bloqueantes ni contradicciones de contrato.
    En cualquier otro caso emite VEREDICTO: RECHAZADO y enumera lo que bloquea.
"""
agent = Agent(role='Chapter', goal="Evaluar de forma trazable si la entrega satisface el Issue y esta lista para revision humana.",
                  backstory="Eres el revisor final que contrasta requisito, implementacion y evidencia sin sustituir la aprobacion humana.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Contenido de chapter_review.md: resumen ejecutivo, matriz criterio -> evidencia -> estado, coherencia de contratos y componentes, hallazgos ordenados por severidad con impacto y responsable, riesgos y pendientes. Termina con exactamente VEREDICTO: APROBADO o VEREDICTO: RECHAZADO, justificado por la evidencia recibida. No declares ejecuciones ni aprobaciones inexistentes.', agent=agent)
