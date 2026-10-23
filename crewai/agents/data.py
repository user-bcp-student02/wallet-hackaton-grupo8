"""Diseno de datos y persistencia para equipos que habilitan el septimo rol."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'data'
LABEL = 'Datos y persistencia'
SPEC_FILE = 'data_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Actua como responsable de Datos y persistencia. Usa el Issue y la arquitectura
aprobada del contexto; no inventes requisitos ni afirmes haber inspeccionado una
base de datos que no se haya descrito.

1. Determina si el Issue necesita persistencia. Si no la necesita, justifica por
    que y no generes SQL.
2. Define entidades/tablas, columnas, tipos, claves primarias y foraneas,
    restricciones de unicidad, nulabilidad, indices y relaciones necesarias para
    los criterios de aceptacion. Justifica cada decision relevante.
3. Protege integridad, atomicidad y concurrencia. Para operaciones financieras,
    indica limites transaccionales, precision monetaria, idempotencia y restricciones
    necesarias solo cuando apliquen al Issue y a la arquitectura aprobada.
4. Propone migraciones aditivas y reversibles compatibles con el esquema conocido.
    No ejecutes SQL, no borres datos y no cambies contratos o tablas existentes sin
    una decision aprobada. Si falta el esquema actual, declara el bloqueo.
5. Entrega un contrato claro para Backend: nombres, tipos, restricciones,
    comportamiento ante duplicados y errores de persistencia.
"""
agent = Agent(role=LABEL, goal="Definir persistencia segura, minima y compatible con la arquitectura aprobada.",
                  backstory="Eres responsable de integridad de datos, transacciones y migraciones revisables.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Contenido de data_spec.md: decision sobre necesidad de persistencia; modelo de tablas, tipos, claves, relaciones, restricciones e indices; contrato de persistencia para Backend; limites transaccionales y riesgos; propuesta de migracion aditiva y estrategia de reversa cuando aplique. Cada archivo SQL completo en un bloque markdown sql independiente, primera linea -- nombre.sql. No ejecutes migraciones ni inventes evidencia. Si no requiere persistencia, justifica la decision sin generar SQL.', agent=agent)
