# User foundation provenance and identity

This is the active GoalStats User service repository. The current application is
an Item + Action reference foundation adopted from `template-goalstats-service`
at frozen commit `6600facf42ecf9a3431b44f5d19ff2ac2a3b0b07`.
User/auth product behavior is future work; do not silently turn Item into User.

The canonical Template owns shared foundation conventions. This User repository
owns its runtime identities, private configuration, data, and future product work.
Shared architecture changes belong in the Template first and require deliberate,
reviewed adoption here. This repository does not edit parent scaffolding or other
repositories. Adoption preserves existing User Git ancestry and migration history.
The parent generator is not used for this adoption.

One User compatibility correction differs from that frozen source: request
validation classifies path errors by their Pydantic path-schema context, rather
than by field names alone. Forbidden JSON fields such as `item_id` and `action_id`
remain rejected with the existing User request-body Problem detail. Path UUID
validation retains its distinct detail. Boundary regression tests cover this
correction; no validation constraints or resource contracts are weakened.

## Stable User identities

| Identity | Current value |
| --- | --- |
| Repository | `goalstats-user-service` |
| Source/import root | `src/` (flat modules; no service package directory) |
| Coverage source | `src` |
| Factory | `main:create_app()` |
| Image/runtime slug | `goalstats-user-py` |
| Image tags | `goalstats-user-py:runtime`, `goalstats-user-py:tooling` |
| Developer Compose projects | `goalstats-user-py-local`, `goalstats-user-py-dev` |
| Disposable projects | `goalstats-user-py-test-<hex>`, `goalstats-user-py-cert-<hex>` |
| Developer databases | `goalstats_user_py_local`, `goalstats_user_py_dev` |
| TEST database | `goalstats_test_runtime` |
| Cache namespace | `goalstats-user-py:<env>:v1` |
| API display title | `GoalStats User API` |
| Logger identity | `goalstats_user` (service label, not an import/package) |
| Internal Compose services | `app`, `runner`, `postgres`, `redis` |
| Disposable tool container | `goalstats-user-py-tool-<hex>` |
| CI concurrency | `goalstats-user-${{ github.workflow }}-${{ github.ref }}` |

Future identity changes must update identity producers, consumers, safety guards, fixtures,
Docker/Compose references, and observations together. There is no Python package-directory identity to transform. Flat module names,
source paths, the Item/Action reference domain and generic `goalstats_*` extension
keys remain unchanged.
Do not use broad textual substitution. The migration revision is not an identity
placeholder: preserve `b7f42e9c1a60` unless a separately reviewed migration is needed.

Dependencies remain Python 3.12 and one pinned `requirements.txt`. No generic
provider framework, async architecture, authentication platform, queues, or gRPC
is included. PostgreSQL and Redis are the only runtime providers.

## Flat Python execution contract

`src/main.py` exports `create_app` and explicitly connects application-owned resources,
cache adapters and services to typed Blueprint factories. Routes capture services directly;
`app.extensions` retains resource references for diagnostics and cleanup, not service lookup.
Modules import directly from `enums`, `exceptions`, `settings`,
`models`, `schemas`, `infra`, `services`, and `routers`. There is no
intermediate service package and no `src` package to import.

Pytest declares `pythonpath = src scripts`; Alembic uses its configuration-relative
`prepend_sys_path`; mypy declares `mypy_path = src`. Docker explicitly sets
`PYTHONPATH=/app/src`, shared by Gunicorn, LOCAL Flask CLI, migration/test runners
and certification subprocesses. CI calls the same Make/Docker workflows. Host
factory commands must explicitly expose the source directory, for example
`PYTHONPATH=src flask --app 'main:create_app()' run`. No developer shell path
configuration is assumed by the public Make workflows.

The remaining `goalstats_user` occurrences are intentional service identities:
LOCAL/DEV database names (and their producers/ownership checks) and the isolated
application logger label. They are not Python package references. Generic TEST
identities and unrelated-resource sentinels remain intentionally generic.

## Host development

Host IDE support is additive to Docker. Flat `src/`, `main:create_app()`, Python 3.12,
one `requirements.txt`, Item/Action behavior, HTTP/OpenAPI, database schema/migration
history, Redis semantics and health/readiness contracts stay unchanged. Direct
`src/main.py` adds only a LOCAL development entrypoint. `src/` is not a package;
script execution naturally exposes it, pytest uses its configured paths, Alembic
uses its existing prepend path, and Docker/Gunicorn use their existing PYTHONPATH.

Track only portable `.vscode/settings.json`, `.vscode/launch.json`, and optional
`.vscode/extensions.json`. Ignore `.idea/`, `.venv/`, `.env.local`, and
`.host-sessions/`. No extra dotenv example or dependency manifest is introduced.

Foundation updates must preserve the shared code-owned configuration schema, private setup,
manifest-based TEST ownership and portable IDE launch. Reject all real env files and
internal state from payloads; fresh User clones create their own `.env.local` and
`.env.test` through setup. Identity literals are transformed only in reviewed paths.

Direct `src/main.py` means LOCAL host development. The `load_local()` helper in
`src/settings/environment.py` belongs only to that entrypoint; factory and Alembic
configuration use `load_application()` without reading machine files. Portable VS Code app launch must not inject
an env file; PyCharm Python script Run needs no environment profile. Adoption checks
must validate this shared loader and preserve its source bytes without identity rewrites.

API body DTOs use `*Request`, resource/list DTOs use `*Response`, and path/shared
contracts use `*Schema` (including `ProblemDetailSchema`). Domain exceptions live
in `exceptions/base.py`, `item.py`, and `action.py`; Flask handling lives in
`exceptions/handlers.py`. Package markers remain empty.

Domain API contracts live in `schemas/<domain>/request.py` (`*Request`),
`response.py` (`*Response`), and `base.py` (`*Schema`). The latter owns path/query
schemas and genuine shared domain foundations; it does not require a generic base
class. Other domain schema files contain `*Schema` contracts only when genuinely
needed. Shared primitives stay in `schemas/common.py`, and singleton cross-cutting
contracts such as `schemas/problem.py` need no package hierarchy. Imports name the
defining module explicitly; empty package markers do not re-export schemas.
