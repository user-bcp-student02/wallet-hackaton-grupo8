"""Diseno de pruebas, casos verificables y cobertura de criterios de aceptacion."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Actua como Testing despues de Developer. Usa el Issue, toda la documentacion `docs/`,
el reporte preventivo de Security y la implementacion full stack aprobada. No afirmes
haber ejecutado pruebas ni inventes cobertura, resultados o herramientas no disponibles.

1. Construye una matriz criterio -> escenario -> nivel de prueba -> resultado
    esperado. Incluye caminos validos, errores, limites, permisos y estados relevantes.
2. Prioriza pruebas unitarias y de integracion para reglas de negocio, persistencia,
   contrato HTTP, componentes y estados de interfaz. Incluye E2E solo si el proyecto
   lo soporta. Comprueba que `/control/*` no se use como API de negocio.
3. Para pagos, agrega casos de duplicados/idempotencia, concurrencia, timeout,
    estados pendientes y fallas cuando formen parte del alcance.
4. Genera archivos de prueba completos y compatibles con el framework indicado por
    el contexto. Usa bloques independientes: Java con primera linea // NombreTest.java;
    TypeScript con // nombre.spec.ts. No inventes clases, endpoints ni metodos que no
    aparezcan en las entregas; declara el bloqueo si falta una dependencia necesaria.
5. Lista comandos reproducibles que existan en el proyecto. Marca NO EJECUTADO
    cualquier comando no ejecutado y separa claramente casos propuestos de resultados.
6. Cubre los controles del reporte Security. Para el mock, valida solo lo que el
    contrato realmente ofrece y conserva las limitaciones documentadas; no conviertas
    APIs de control ni resultados simulados en evidencia de produccion.
"""
agent = Agent(role='Ingeniero de pruebas', goal="Convertir criterios de aceptacion en pruebas reproducibles y evidencia honesta.",
                  backstory="Eres responsable de encontrar regresiones y verificar comportamiento observable sin asumir resultados.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Contenido de testing_report.md: matriz criterio -> escenario -> nivel -> resultado esperado; cobertura de controles Security; casos positivos, negativos, limites y financieros W1-W6 aplicables; pruebas API, UI, integracion y E2E si existen; comandos reproducibles, dependencias, bloqueos y resultados reales o NO EJECUTADO. Incluye archivos de prueba completos en bloques separados. No inventes ejecuciones ni capacidades del mock.', agent=agent)
