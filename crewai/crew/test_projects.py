"""Detecta los proyectos generados y crea test_backend (Karate) y test_frontend (Playwright).

Sigue los procedimientos de .github/agents/automation-backend.agent.md y
.github/agents/automation-frontend.agent.md. Solo escribe dentro de las carpetas
test_backend/ y test_frontend/ de cada proyecto; nunca toca el código productivo.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", ".venv", "target", "dist", "build", ".angular", "__pycache__"}
TEST_DIRS = {"test_backend", "test_frontend"}
HTTP_METHODS = ("get", "post", "put", "delete", "patch")
KARATE_VERSION = "1.4.1"
PLAYWRIGHT_VERSION = "1.49.1"
FRONT_FRAMEWORKS = ("@angular/core", "react", "vue", "svelte")


# ── Detección de proyectos ──────────────────────────────────────────

def _candidates(root: Path, depth: int = 2):
    yield root
    if depth == 0:
        return
    for child in sorted(root.iterdir()) if root.is_dir() else []:
        if child.is_dir() and child.name not in SKIP_DIRS | TEST_DIRS and not child.name.startswith("."):
            yield from _candidates(child, depth - 1)


def _is_backend(path: Path) -> bool:
    return any((path / name).is_file() for name in ("pom.xml", "build.gradle", "build.gradle.kts"))


def _is_frontend(path: Path) -> bool:
    if (path / "angular.json").is_file():
        return True
    package = path / "package.json"
    if not package.is_file():
        return False
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return any(name in deps for name in FRONT_FRAMEWORKS)


def detect_projects(root: Path) -> dict:
    """Devuelve {"backend": [Path], "frontend": [Path]} buscando bajo root."""
    found = {"backend": [], "frontend": []}
    for path in _candidates(Path(root)):
        if path.name in TEST_DIRS:
            continue
        if _is_backend(path):
            found["backend"].append(path)
        if _is_frontend(path):
            found["frontend"].append(path)
    return found


# ── Backend: endpoints desde OpenAPI o fuentes JAX-RS ──────────────

def _norm_path(*parts: str) -> str:
    joined = "/".join(p.strip("/") for p in parts if p and p.strip("/"))
    joined = re.sub(r"\{(\w+)[^}]*\}", r"{\1}", "/" + joined)
    return joined


def _root_path(project: Path) -> str:
    props = project / "src/main/resources/application.properties"
    if props.is_file():
        match = re.search(r"^\s*quarkus\.(?:http|rest)\.root-path\s*=\s*(\S+)", props.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    return ""


def _openapi_endpoints(project: Path) -> tuple[list[dict], str | None]:
    for path in sorted(project.rglob("*")):
        if SKIP_DIRS & set(path.parts) or TEST_DIRS & set(path.parts):
            continue
        if not (path.is_file() and re.match(r"(openapi|swagger).*\.(ya?ml|json)$", path.name, re.I)):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                spec = json.loads(text)
            else:
                import yaml
                spec = yaml.safe_load(text)
            endpoints = []
            for route, operations in (spec.get("paths") or {}).items():
                for method, operation in (operations or {}).items():
                    if method.lower() not in HTTP_METHODS:
                        continue
                    codes = sorted(int(c) for c in (operation or {}).get("responses", {}) if str(c).isdigit() and 200 <= int(c) < 300)
                    endpoints.append({"method": method.lower(), "path": _norm_path(route), "status": codes[0] if codes else 200})
            if endpoints:
                return endpoints, str(path)
        except Exception:
            continue
    return [], None


_CLASS_RE = re.compile(
    r'@Path\("([^"]*)"\)(?:\s*@[\w.]+(?:\([^)]*\))?)*\s*(?:public\s+)?(?:abstract\s+)?class\s+\w+')
_METHOD_RE = re.compile(
    r'((?:@[\w.]+(?:\((?:[^()]|\([^)]*\))*\))?\s*)+)(?:public|protected|private)?\s*[\w<>\[\],?.\s]+?\s+\w+\s*\(')


def _jaxrs_endpoints(project: Path) -> list[dict]:
    endpoints = []
    prefix = _root_path(project)
    for java in sorted((project / "src/main/java").rglob("*.java")):
        text = java.read_text(encoding="utf-8", errors="ignore")
        cls = _CLASS_RE.search(text)
        if not cls:
            continue
        for match in _METHOD_RE.finditer(text, cls.end()):
            annotations = match.group(1)
            verb = re.search(r"@(GET|POST|PUT|DELETE|PATCH)\b", annotations)
            if not verb:
                continue
            sub = re.search(r'@Path\("([^"]*)"\)', annotations)
            endpoints.append({
                "method": verb.group(1).lower(),
                "path": _norm_path(prefix, cls.group(1), sub.group(1) if sub else ""),
                "status": 200,
            })
    return endpoints


def discover_endpoints(project: Path) -> tuple[list[dict], str]:
    endpoints, source = _openapi_endpoints(project)
    origin = f"contrato OpenAPI {source}" if source else "anotaciones JAX-RS del código fuente"
    if not endpoints:
        endpoints = _jaxrs_endpoints(project)
    unique = {(e["method"], e["path"]): e for e in endpoints}
    return [unique[k] for k in sorted(unique, key=lambda k: (k[1], k[0]))], origin


# ── Backend: proyecto Karate ───────────────────────────────────────

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>pe.bcp.wallet</groupId>
  <artifactId>test-backend</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>

  <properties>
    <maven.compiler.release>17</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <karate.version>__KARATE__</karate.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>com.intuit.karate</groupId>
      <artifactId>karate-junit5</artifactId>
      <version>${karate.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <testResources>
      <testResource>
        <directory>src/test/resources</directory>
      </testResource>
    </testResources>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.5</version>
        <configuration>
          <includes>
            <include>**/*Test.java</include>
          </includes>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""

RUNNER = """package runner;

import com.intuit.karate.Results;
import com.intuit.karate.Runner;
import com.intuit.karate.core.MockServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class KarateRunnerTest {

    private static MockServer server;

    @BeforeAll
    static void startMock() {
        server = MockServer.feature("classpath:mock/mock.feature").http(0).build();
        System.setProperty("baseUrl", "http://localhost:" + server.getPort());
    }

    @AfterAll
    static void stopMock() {
        if (server != null) {
            server.stop();
        }
    }

    @Test
    void runAll() {
        String tags = System.getProperty("karate.tags");
        Runner.Builder<?> builder = Runner.path("classpath:features").reportDir("target/karate-reports");
        if (tags != null && !tags.isBlank()) {
            builder.tags(tags);
        }
        Results results = builder.parallel(1);
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
        assertEquals(true, results.getScenariosTotal() > 0, "No se ejecutó ningún escenario");
    }
}
"""

KARATE_CONFIG = """function fn() {
  // La URL la fija el runner al arrancar el mock local; no se apunta a servicios reales.
  var baseUrl = karate.properties['baseUrl'];
  karate.configure('connectTimeout', 5000);
  karate.configure('readTimeout', 5000);
  return { baseUrl: baseUrl };
}
"""


def _concrete(path: str) -> str:
    return re.sub(r"\{\w+\}", "1", path)


def _mock_feature(endpoints: list[dict]) -> str:
    lines = ["Feature: Mock HTTP local generado desde los endpoints detectados", ""]
    for e in endpoints:
        lines += [f"Scenario: methodIs('{e['method']}') && pathMatches('{e['path']}')",
                  f"  * def responseStatus = {e['status']}",
                  f"  * def response = {{ mock: true, route: '{e['method'].upper()} {e['path']}' }}", ""]
    for route in sorted({e["path"] for e in endpoints}):
        lines += [f"Scenario: pathMatches('{route}')",
                  "  * def responseStatus = 405",
                  "  * def response = { error: 'METHOD_NOT_ALLOWED' }", ""]
    lines += ["Scenario:", "  * def responseStatus = 404", "  * def response = { error: 'NOT_FOUND' }", ""]
    return "\n".join(lines)


def _endpoints_feature(endpoints: list[dict]) -> str:
    lines = ["@mock", "Feature: Endpoints detectados contra el mock local", "",
             "Background:", "  * url baseUrl", ""]
    for e in endpoints:
        concrete = _concrete(e["path"])
        lines += [f"@smoke @{e['method']}",
                  f"Scenario: {e['method'].upper()} {e['path']} responde {e['status']}",
                  f"  Given path '{concrete}'".replace("path '/", "path '/"),
                  f"  When method {e['method']}",
                  f"  Then status {e['status']}",
                  f"  And match response.route == '{e['method'].upper()} {e['path']}'", ""]
    for route in sorted({e["path"] for e in endpoints}):
        declared = {e["method"] for e in endpoints if e["path"] == route}
        other = next((m for m in HTTP_METHODS if m not in declared), None)
        if other:
            lines += ["@negative",
                      f"Scenario: {other.upper()} {route} no está declarado y responde 405",
                      f"  Given path '{_concrete(route)}'", f"  When method {other}", "  Then status 405", ""]
    lines += ["@negative", "Scenario: una ruta inexistente responde 404",
              "  Given path '/__ruta-inexistente__'", "  When method get", "  Then status 404",
              "  And match response.error == 'NOT_FOUND'", ""]
    return "\n".join(lines)


def _backend_readme(project: Path, endpoints: list[dict], origin: str) -> str:
    rows = "\n".join(f"| {e['method'].upper()} {e['path']} | {origin} | responde {e['status']} | "
                     f"endpoints.feature | Implementado |" for e in endpoints) or "| (ninguno detectado) | - | - | - | Pendiente |"
    return f"""# test_backend — pruebas Karate DSL

Proyecto backend: `{project.name}`. Suite contra un **mock HTTP local de Karate** generado
desde los endpoints detectados ({origin}). Requisitos: JDK 17+ y Maven 3.9+.

## Comandos (desde `test_backend/`)

```powershell
mvn test                                  # toda la suite
mvn test "-Dkarate.tags=@smoke"           # solo un tag
mvn test "-Dkarate.tags=@negative"
```

Reportes: `target/karate-reports/` (HTML/JSON) y `target/surefire-reports/` (JUnit).

## Ciclo de vida del mock
`KarateRunnerTest` arranca `mock/mock.feature` en un puerto dinámico, publica la URL en la
propiedad `baseUrl` (leída por `karate-config.js`) y lo detiene al terminar.

## Trazabilidad
| Operación | Origen | Caso | Feature | Estado |
|---|---|---|---|---|
{rows}

## Limitaciones
- Sin contrato OpenAPI, solo se verifican rutas, métodos y códigos de éxito inferidos; el cuerpo y las
  validaciones de entrada no se cubren porque no hay fuente contractual.
- Los parámetros de ruta se prueban con el valor `1`.
- Pasar contra el mock valida la suite y la simulación, **no** la conformidad del backend real.
"""


def _write_new(path: Path, content: str, created: list) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path)


def scaffold_backend_tests(project: Path) -> dict:
    endpoints, origin = discover_endpoints(project)
    root = project / "test_backend"
    created: list[Path] = []
    _write_new(root / "pom.xml", POM.replace("__KARATE__", KARATE_VERSION), created)
    _write_new(root / "src/test/java/runner/KarateRunnerTest.java", RUNNER, created)
    _write_new(root / "src/test/resources/karate-config.js", KARATE_CONFIG, created)
    _write_new(root / "src/test/resources/mock/mock.feature", _mock_feature(endpoints), created)
    _write_new(root / "src/test/resources/features/endpoints.feature", _endpoints_feature(endpoints), created)
    _write_new(root / ".gitignore", "target/\n", created)
    _write_new(root / "README.md", _backend_readme(project, endpoints, origin), created)
    return {"project": project, "tests": root, "endpoints": len(endpoints), "created": created}


# ── Frontend: proyecto Playwright ──────────────────────────────────

def _discover_routes(src_app: Path) -> dict:
    """Mapea nombre de componente -> {path, guarded} leyendo los archivos *routes*.ts."""
    routes = {}
    for file in src_app.rglob("*routes*.ts"):
        text = file.read_text(encoding="utf-8", errors="ignore")
        for obj in re.findall(r"\{[^{}]*\}", text):
            path = re.search(r"path:\s*['\"]([^'\"]*)['\"]", obj)
            comp = re.search(r"component:\s*(\w+)", obj) or re.search(r"=>\s*\w+\.(\w+)", obj)
            if path and comp and path.group(1) not in ("", "**"):
                routes[comp.group(1)] = {"path": path.group(1), "guarded": "canActivate" in obj}
    return routes


def discover_components(front: Path) -> list[dict]:
    src_app = front / "src" / "app"
    if not src_app.is_dir():
        return []
    routes = _discover_routes(src_app)
    components = []
    for file in sorted(src_app.rglob("*.component.ts")):
        text = file.read_text(encoding="utf-8", errors="ignore")
        name = re.search(r"export\s+class\s+(\w+)", text)
        selector = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", text)
        if not name:
            continue
        info = routes.get(name.group(1), {})
        components.append({
            "name": name.group(1),
            "selector": selector.group(1) if selector else None,
            "route": info.get("path"),
            "guarded": info.get("guarded", False),
            "file": file.relative_to(front).as_posix(),
        })
    return components


PLAYWRIGHT_PACKAGE = """{
  "name": "test-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "playwright test",
    "test:ui": "playwright test --ui",
    "test:headed": "playwright test --headed",
    "report": "playwright show-report reports/html"
  },
  "devDependencies": {
    "@playwright/test": "__PW__"
  }
}
"""

PLAYWRIGHT_CONFIG = """import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.FRONTEND_URL ?? 'http://localhost:4200';

export default defineConfig({
  testDir: './tests',
  outputDir: 'reports/test-results',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/results.json' }],
    ['junit', { outputFile: 'reports/junit.xml' }],
  ],
  use: { baseURL, trace: 'on-first-retry', screenshot: 'only-on-failure' },
  // Levanta el frontend (npm start en la carpeta padre) salvo que ya esté corriendo.
  webServer: process.env.FRONTEND_URL ? undefined : {
    command: 'npm start',
    cwd: '..',
    url: baseURL,
    reuseExistingServer: true,
    timeout: 180_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
"""


def _component_spec(c: dict) -> str:
    title = c["name"]
    guard_note = ("  // Ruta protegida por guard: no se asume que el componente quede visible.\n"
                  if c["guarded"] else "")
    attach = ""
    if c["selector"] and not c["guarded"]:
        attach = (f"    await expect(page.locator('{c['selector']}')).toBeAttached();\n")
    return f"""import {{ test, expect }} from '@playwright/test';

test.describe('{title}', () => {{
  test.beforeEach(async ({{ page }}) => {{
    // Aísla el backend: ninguna prueba llama a servicios reales.
    await page.route('**/api/**', (route) =>
      route.fulfill({{ status: 200, contentType: 'application/json', body: '{{}}' }}));
  }});

  test('se renderiza sin errores de ejecución', async ({{ page }}) => {{
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
{guard_note}    await page.goto('/{c['route']}');
    await expect(page.locator('app-root')).toBeAttached();
{attach}    expect(errors).toEqual([]);
  }});

  test('los botones visibles tienen nombre accesible', async ({{ page }}) => {{
    await page.goto('/{c['route']}');
    await expect(page.locator('app-root')).toBeAttached();
    for (const button of await page.getByRole('button').all()) {{
      const name = (await button.innerText()).trim() || (await button.getAttribute('aria-label')) || '';
      expect(name).not.toBe('');
    }}
  }});
}});
"""


def _frontend_readme(front: Path, components: list[dict]) -> str:
    rows = "\n".join(
        f"| {c['name']} | {'ruta /' + c['route'] if c['route'] else 'sin ruta'} | render y accesibilidad | "
        f"{c['name']}.spec.ts | {'Implementado' if c['route'] else 'Pendiente (sin ruta)'} |"
        for c in components) or "| (ninguno detectado) | - | - | - | Pendiente |"
    return f"""# test_frontend — pruebas Playwright

Proyecto frontend: `{front.name}`. Pruebas e2e por componente sobre la app en ejecución
(`@playwright/experimental-ct-*` no soporta Angular, por eso se usa la app real con red simulada
mediante `page.route`). Requisitos: Node 18+ y dependencias del frontend instaladas (`npm install`).

## Comandos (desde `test_frontend/`)

```powershell
npm install
npx playwright install chromium
npm test                                   # toda la suite (levanta `npm start` en la carpeta padre)
npx playwright test tests/login.component.spec.ts
npx playwright test -g "renderiza"
npm run report                             # abre reports/html
$env:FRONTEND_URL = "http://localhost:4200"; npm test   # contra una app ya levantada
```

Reportes dentro de `reports/`: `html`, `results.json`, `junit.xml`, `test-results`, `mcp`.

## Trazabilidad
| Componente | Ruta | Caso | Prueba | Estado |
|---|---|---|---|---|
{rows}

## Limitaciones
- Los componentes sin ruta no se prueban aislados: quedan pendientes.
- Las pruebas verifican render, errores de ejecución y accesibilidad básica; el comportamiento
  funcional se amplía con la evidencia del MCP de Playwright guardada en `reports/mcp/`.
"""


def scaffold_frontend_tests(front: Path) -> dict:
    components = discover_components(front)
    root = front / "test_frontend"
    created: list[Path] = []
    _write_new(root / "package.json", PLAYWRIGHT_PACKAGE.replace("__PW__", PLAYWRIGHT_VERSION), created)
    _write_new(root / "playwright.config.ts", PLAYWRIGHT_CONFIG, created)
    _write_new(root / ".gitignore", "node_modules/\nreports/html/\nreports/test-results/\n", created)
    _write_new(root / "reports/mcp/.gitkeep", "", created)
    for c in components:
        if c["route"]:
            _write_new(root / "tests" / f"{c['name']}.spec.ts", _component_spec(c), created)
    if not any(c["route"] for c in components):
        _write_new(root / "tests" / "app.spec.ts", """import { test, expect } from '@playwright/test';

test('la aplicación carga sin errores de ejecución', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('app-root')).toBeAttached();
  expect(errors).toEqual([]);
});
""", created)
    _write_new(root / "README.md", _frontend_readme(front, components), created)
    return {"project": front, "tests": root, "components": len(components), "created": created}


# ── Orquestación ───────────────────────────────────────────────────

def prepare_test_projects(root: Path) -> dict:
    """Identifica proyectos bajo root y crea test_backend / test_frontend en cada uno."""
    projects = detect_projects(root)
    return {
        "backend": [scaffold_backend_tests(p) for p in projects["backend"]],
        "frontend": [scaffold_frontend_tests(p) for p in projects["frontend"]],
    }


def _karate_java_home() -> str | None:
    """Karate 1.4.1 (GraalVM JS) no corre en JDK > 21: busca un JDK 17-21 si el actual es mayor."""
    explicit = os.getenv("KARATE_JAVA_HOME")
    if explicit:
        return explicit
    roots = [Path.home() / ".jdks", Path("C:/Program Files/Java"), Path("C:/Program Files/Eclipse Adoptium"),
             Path("C:/Program Files/Microsoft"), Path("/usr/lib/jvm")]
    for root in roots:
        if root.is_dir():
            for jdk in sorted(root.iterdir(), reverse=True):
                if re.search(r"(?<!\d)(17|21)(?!\d)", jdk.name) and (jdk / "bin").is_dir():
                    return str(jdk)
    return None


def _run(command: list[str], cwd: Path, timeout: int, env: dict | None = None) -> dict:
    exe = shutil.which(command[0])
    if not exe:
        return {"status": "BLOQUEADO", "detail": f"{command[0]} no está disponible"}
    try:
        done = subprocess.run([exe, *command[1:]], cwd=cwd, capture_output=True, text=True, timeout=timeout,
                              env=env, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"status": "BLOQUEADO", "detail": f"tiempo agotado ({timeout}s)"}
    tail = "\n".join((done.stdout + done.stderr).strip().splitlines()[-15:])
    return {"status": "APROBADO" if done.returncode == 0 else "FALLIDO", "detail": tail}


def run_test_projects(prepared: dict, timeout: int = 900) -> list[dict]:
    """Ejecuta de verdad las suites creadas y devuelve el resultado de cada una."""
    results = []
    env = None
    java_home = _karate_java_home()
    if java_home:
        env = {**os.environ, "JAVA_HOME": java_home, "PATH": str(Path(java_home) / "bin") + os.pathsep + os.environ.get("PATH", "")}
    for item in prepared["backend"]:
        results.append({"suite": str(item["tests"]), **_run(["mvn", "-B", "test"], item["tests"], timeout, env)})
    for item in prepared["frontend"]:
        tests = item["tests"]
        install = _run(["npm", "install"], tests, timeout)
        if install["status"] != "APROBADO":
            results.append({"suite": str(tests), **install})
            continue
        _run(["npx", "playwright", "install", "chromium"], tests, timeout)
        results.append({"suite": str(tests), **_run(["npx", "playwright", "test"], tests, timeout)})
    return results


def summarize(prepared: dict) -> str:
    lines = []
    for item in prepared["backend"]:
        lines.append(f"- backend `{item['project'].name}` → {item['tests']} ({item['endpoints']} endpoints)")
    for item in prepared["frontend"]:
        lines.append(f"- frontend `{item['project'].name}` → {item['tests']} ({item['components']} componentes)")
    return "\n".join(lines) or "- No se detectaron proyectos backend/frontend."
