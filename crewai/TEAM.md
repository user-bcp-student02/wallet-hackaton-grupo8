# Trabajar en equipo

## Crear el repositorio del equipo

El líder crea el repositorio en su cuenta personal desde esta plantilla:

```sh
gh repo create crewai --template NTTData-Academy/crewai --public --clone
```

Agrega a tus compañeros como colaboradores con permiso de escritura en el repo del equipo.
Los demás integrantes clonan ese mismo repo:

```sh
gh repo clone <CAPTAIN>/crewai
cd crewai
```

## Repartir los archivos

Anota un responsable por agente. Consulta las responsabilidades, entregables y puntos de partida en [Mejora tu agente](MEJORA_TU_AGENTE.md#roles-del-flujo).

- `agents/security.py`: responsable pendiente. Define controles y riesgos antes de implementar.
- `agents/developer.py`: responsable pendiente. Implementa backend, frontend e infraestructura local necesaria.
- `agents/testing.py`: responsable pendiente. Prepara pruebas y comandos reproducibles.
- `agents/product_owner.py`: responsable pendiente. Traza criterios y brechas para la revisión humana.

## Registrar responsables para el dashboard

Copia `team.example.json` a `team.json`, reemplaza los cuatro valores por usuarios reales de GitHub distintos y publica ese archivo en `main`. El dashboard lee `roles` para asociar cada agente con su responsable. Los nombres de ejemplo no son participantes.

## Entregar un cambio

1. Acuerden un requerimiento y sus criterios de aceptación.
2. Crea tu rama, por ejemplo `git switch -c agents/developer`.
3. Edita las instrucciones de tu agente en su archivo. Coordina los cambios de contratos con el arquitecto.
4. Ejecuta `python tools/verify.py`.
5. Publica tu rama y abre un PR hacia `main` del repo del líder. No envíes el PR al template de la organización.
6. Pide a un compañero que revise el cambio antes de integrarlo.

Una persona ejecuta el pipeline integrado desde `main`. El equipo participa en las aprobaciones
humanas y aporta feedback en cada etapa. Cada integrante conserva su propia `.env`, autenticación
y entorno virtual. No compartan checkpoints entre ejecuciones de distintas computadoras.

Los agentes generan texto y archivos. El agente de pruebas propone tests y comandos;
una persona los ejecuta y adjunta la salida real al PR. Un informe del modelo no demuestra que las pruebas pasaron.

El pipeline integrado ejecuta `Security → Developer → Testing → Product Owner`.
Cada etapa recibe el Issue, las fuentes pertinentes de `docs/` y los outputs aprobados
de las etapas anteriores. Una persona conserva las decisiones HITL; el reporte de
Product Owner no sustituye la aprobacion humana.
