# Claude Code — project context


<!-- cloude-code-toolbox:mcp-skills-awareness-begin -->

### MCP & Skills awareness (Cloude Code ToolBox)

_Last synced: 2026-04-23T16:34:07.115Z._

- **Full report:** `.claude/cloude-code-toolbox-mcp-skills-awareness.md` in this workspace (auto-overwritten on each scan). Use it as ground truth for configured servers and skill folders.
- **MCP:** For **live tools** in Claude Code, enable the matching server via `/mcp` (and VS Code `mcp.json` where applicable).
- **When the user’s task matches a server** (e.g. Confluence work and a **Confluence** / **Atlassian** MCP is listed), **prefer that server id** and plan on tool use—not only file search.
- **Skills:** Folders below contain `SKILL.md`; attach or cite paths in chat when relevant.

#### Workspace MCP

- `c:\Users\LENOVO\Documents\certypro\SystemCertification\.vscode\mcp.json` _(workspace: SystemCertification)_ — _file missing_

_No active workspace servers in mcp.json._

#### User MCP

- `C:\Users\LENOVO\AppData\Roaming\Code\User\mcp.json` — _file missing_

_No active user-scoped servers in mcp.json._

#### Project skills

_None found (or no workspace open)._

#### User skills

_None found._

<!-- cloude-code-toolbox:mcp-skills-awareness-end -->

---

## 🧪 Configuración de Pruebas de Integración (Mayo 2026)

### Estado: ✅ COMPLETADO

Se ha implementado un entorno **completo de pruebas de integración con Testcontainers y PostgreSQL**, replicando la lógica del documento "Pruebas Unitarias Testcontainers-Proyecto Spring Boot.pdf".

### Archivos Clave

#### Nuevos Archivos
- **`conftest.py`** - Gestión del ciclo de vida del contenedor PostgreSQL
- **`events/test_db_integration.py`** - Suite de 13+ pruebas parametrizadas
- **`events/factories.py`** - Factories con factory-boy
- **`TESTING.md`** - Documentación completa
- **`RUNNING_TESTS.md`** - Guía rápida
- **`SETUP_SUMMARY.md`** - Resumen de configuración

#### Archivos Modificados
- **`requirements.txt`** - Dependencias testcontainers
- **`pytest.ini`** - Configuración de cobertura
- **`sonar-project.properties`** - Exclusiones

### Comandos Rápidos

```bash
pytest -v                    # Ejecutar todas
pytest -m integration -v     # Solo integración
pytest --cov=. --cov-report=xml:coverage.xml  # Con cobertura
```

### Referencias Generadas

- 📖 [TESTING.md](./TESTING.md) - Documentación completa
- ⚡ [RUNNING_TESTS.md](./RUNNING_TESTS.md) - Guía rápida
- 📋 [SETUP_SUMMARY.md](./SETUP_SUMMARY.md) - Resumen
