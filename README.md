# JOCKY

JOCKY is a host investigation and triage system that executes a restricted investigation DSL, collects endpoint evidence, applies deterministic analysis rules, and persists the resulting investigation report.

The system is divided into four execution stages:

1. **Lexing and parsing** — converts an investigation script into a validated internal representation.
2. **Collection** — executes explicitly allowlisted host collectors.
3. **Analysis** — evaluates collected evidence with allowlisted rules.
4. **Reporting and persistence** — builds a report and stores it in SQLite through the FastAPI service.

The repository contains both the Python backend and a React/Vite investigation dashboard.

---

## 1. Overview & Core Problem

### Problem

Host triage often requires collecting several independent evidence types and correlating them consistently:

- operating-system and host information
- running processes
- active network connections
- logged-in users
- file metadata and SHA-256 hashes
- relationships between process and network evidence
- indicators requiring investigator review

JOCKY provides a small execution language for describing these operations while keeping the set of executable collectors and analysis rules explicitly controlled.

A script such as:

```text
investigation "Endpoint Triage" {
    collect system_info;
    collect processes;
    collect network_connections;
    analyze suspicious_processes;
    analyze missing_paths;
    analyze process_network_correlation;
    report "triage_report";
}
```

is not executed as arbitrary Python. It is tokenized, parsed into an intermediate representation, and then interpreted through fixed registries.

### Execution boundaries

JOCKY is currently designed as a local/small-scale endpoint triage system rather than a distributed collection platform.

Important current boundaries:

| Area | Current boundary |
|---|---|
| File hashing | Maximum 500 files per collection |
| File traversal | Direct directory only; non-recursive |
| File hashing memory | 64 KiB read chunks |
| Persistence | One SQLite row per investigation |
| Collector execution | Sequential |
| Analysis execution | Sequential |
| API execution model | Synchronous FastAPI route handlers |
| Collector selection | Explicit registry allowlist |
| Analysis selection | Explicit rule registry |
| Frontend | Single React application |
| Database schema | Single `investigations` table |

The file-hash collector is particularly bounded: it will not recursively traverse the filesystem and stops after 500 files. Individual files are streamed in 65,536-byte chunks rather than loaded completely into memory.

The current architecture therefore favors predictable local execution and implementation simplicity over parallel collection, distributed execution, or high-volume event ingestion.

---

## 2. Architectural Design

### System topology

```text
                         ┌─────────────────────────┐
                         │     React / Vite UI     │
                         │                         │
                         │ Overview                │
                         │ Investigations           │
                         │ New Investigation        │
                         │ Investigation Detail     │
                         └────────────┬────────────┘
                                      │ HTTP
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI API        │
                         │                         │
                         │ POST /api/investigations│
                         │ GET  /api/investigations│
                         │ GET  /api/investigations│
                         │ GET  /api/health         │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │      JOCKY Pipeline      │
                         │                         │
                         │ Lexer                   │
                         │   ↓                     │
                         │ Parser                  │
                         │   ↓                     │
                         │ Investigation IR        │
                         │   ↓                     │
                         │ Interpreter             │
                         └───────┬─────────┬───────┘
                                 │         │
                    ┌────────────▼───┐   ┌─▼────────────────┐
                    │ Collector      │   │ Analysis Rules   │
                    │ Registry       │   │ Registry         │
                    │                │   │                  │
                    │ system_info    │   │ suspicious_      │
                    │ processes      │   │ processes        │
                    │ network_       │   │ missing_paths    │
                    │ connections    │   │ process_network_ │
                    │ logged_in_users│   │ correlation      │
                    │ file_hash      │   └──────────────────┘
                    └───────┬────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │ Endpoint / Host  │
                    │ Evidence         │
                    └──────────────────┘

                            │
                            ▼
                    ┌──────────────────┐
                    │ Report Builder   │
                    │ JSON / HTML      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ SQLite           │
                    │ jocky.db         │
                    └──────────────────┘
```

### Request lifecycle

A `POST /api/investigations` request follows this path:

```text
HTTP request
    │
    ▼
tokenize(script)
    │
    ├── LexError ──► HTTP 400
    │
    ▼
parse(tokens)
    │
    ├── ParseError ─► HTTP 400
    │
    ▼
run_investigation(IR)
    │
    ├── unknown collector/rule ─► InterpreterError ─► HTTP 400
    │
    ├── collector runtime failure
    │       └── recorded in CollectorResult
    │
    ▼
build_report(...)
    │
    ▼
asdict(report)
    │
    ▼
save_investigation(...)
    │
    ▼
InvestigationResponse
```

### DSL processing

The language implementation deliberately separates syntax from execution semantics.

#### Lexer

`jocky/language/lexer.py` converts source text into tokens.

Supported syntax includes:

- identifiers
- quoted strings
- `{`
- `}`
- `;`
- `//` single-line comments

The lexer tracks source line numbers so errors can identify their approximate location.

#### Parser

`jocky/language/parser.py` is a hand-written recursive-descent parser.

It validates the grammar:

```text
investigation "<name>" {
    collect <collector>;
    analyze <rule>;
    report "<name>";
}
```

The parser does **not** determine whether a collector or rule actually exists.

That distinction is intentional: grammar validation and semantic authorization are separate stages.

#### Intermediate representation

`jocky/language/ir.py` contains simple dataclasses:

```text
Investigation
 └── commands[]
      ├── CollectCommand
      ├── AnalyzeCommand
      └── ReportCommand
```

The IR contains no execution behavior.

### Collector lifecycle

Collectors are registered in:

```text
jocky/collectors/registry.py
```

The interpreter resolves a collector by name through this dictionary rather than dynamically constructing an attribute or function name.

Conceptually:

```text
script target
     │
     ▼
COLLECTOR_REGISTRY
     │
     ├── known ──► callable ──► execute
     │
     └── unknown ──► InterpreterError
```

Current collectors include:

- `system_info`
- `processes`
- `network_connections`
- `logged_in_users`
- `file_hash`

`file_hash` is currently bound to `./sample_evidence` through `functools.partial`, maintaining the interpreter's zero-argument collector contract.

### Analysis lifecycle

Analysis rules receive only evidence that has already been collected.

They do not directly access the host.

```text
CollectorResult[]
       │
       ▼
successful evidence
       │
       ▼
{target: data}
       │
       ▼
Analysis Rule
       │
       ▼
Finding[]
```

This keeps collection and analysis separate. It also makes rule behavior independent of the host-access layer.

### Persistence lifecycle

SQLite is initialized during FastAPI startup.

Each completed investigation is stored as one row containing:

- generated ID
- investigation name
- endpoint hostname
- start timestamp
- finish timestamp
- finding count
- serialized report JSON

The list endpoint deliberately returns summary columns without loading the full report document.

---

## 3. Design Choices & Trade-offs

### Explicit registries instead of dynamic dispatch

Collectors and analysis rules are resolved through dictionaries:

```python
COLLECTOR_REGISTRY = {
    "system_info": collect_system_info,
    "processes": collect_processes,
    ...
}
```

This was chosen instead of mechanisms such as:

```python
getattr(module, user_supplied_name)
```

The registry provides an explicit execution boundary. A DSL author cannot cause an arbitrary Python function to execute merely by naming it.

**Trade-off:** adding a collector requires modifying the registry. This is intentional; discoverability and control take priority over automatic plugin discovery.

---

### Hand-written parser instead of a parser generator

The DSL grammar is small enough that a recursive-descent parser is sufficient.

Advantages:

- no parser-generation dependency
- direct control over diagnostics
- small implementation surface
- straightforward mapping to the IR

**Trade-off:** grammar growth will eventually make the parser more expensive to maintain. If the DSL gains expressions, variables, nested blocks, or richer types, a dedicated grammar/parser framework may become appropriate.

---

### Dataclass IR instead of executable AST nodes

The intermediate representation contains data only.

This prevents parsing from acquiring execution behavior and makes the pipeline explicit:

```text
source → tokens → IR → execution
```

**Trade-off:** the interpreter must explicitly handle each command type. That is preferable here because adding a command should result in a visible interpreter change rather than implicit behavior.

---

### SQLite instead of an ORM or external database

The persistence layer uses Python's standard `sqlite3` module directly.

The current query model is simple:

- insert one investigation
- list investigation summaries
- retrieve one investigation

A normalized multi-table schema or ORM would introduce additional abstraction without solving a current requirement.

Reports are stored as JSON text because the report is naturally document-shaped.

**Trade-offs:**

- simple deployment
- no database service required
- low operational overhead

but:

- report fields are not independently indexed
- concurrent write throughput is limited compared with a client/server database
- historical report evolution requires application-level compatibility handling
- one large JSON document is less suitable for analytical querying

For larger deployments, the storage layer can be replaced without changing the DSL or collector interfaces.

---

### Sequential collector execution

Collectors run in script order.

This provides deterministic execution and avoids concurrent access to the same host resources.

It also makes the semantics of analysis commands clear: an analysis rule sees successful evidence collected **so far**, not evidence from future commands.

**Trade-off:** slow collectors block subsequent collectors. Parallel execution could reduce wall-clock time, but would require explicit dependency handling, resource limits, cancellation behavior, and synchronization.

---

### Chunked SHA-256 hashing

The file-hash collector reads files in 64 KiB chunks:

```text
file
 │
 ├── 64 KiB
 ├── 64 KiB
 ├── 64 KiB
 └── ...
       │
       ▼
    SHA-256
```

This bounds hashing memory independently of file size.

The collector is also capped at 500 files and performs a non-recursive directory traversal.

**Trade-off:** very large directories are intentionally incomplete. The report exposes truncation rather than silently scanning without a bound.

---

### Findings as observations, not verdicts

The analysis rules distinguish between evidence observations and conclusions.

For example, an executable located under a temporary/download-style directory generates a review-level finding, but the rule explicitly treats this as a pattern requiring investigation rather than proof of malicious activity.

This avoids embedding an unsupported classification into a deterministic rule.

---

## 4. Safety, Concurrency, & Error Handling

### DSL execution safety

The primary execution boundary is the pair of allowlists:

```text
COLLECTOR_REGISTRY
RULE_REGISTRY
```

Unknown names are hard errors.

A typo such as:

```text
collect proceses;
```

does not silently produce an empty result. The interpreter raises an `InterpreterError`.

This prevents an invalid investigation from appearing successful merely because a requested operation was skipped.

---

### Lexer and parser failures

Malformed scripts fail before any collector executes.

Examples include:

- unterminated strings
- unsupported characters
- missing `{`
- missing `}`
- missing `;`
- unknown statement keywords
- unexpected trailing content

The API converts lexer and parser failures into HTTP `400` responses.

---

### Collector failures

A collector can fail because of:

- insufficient OS permissions
- inaccessible files
- missing paths
- transient OS-level errors
- platform-specific limitations

Collector runtime exceptions are captured independently:

```text
CollectorResult
 ├── target
 ├── status = success | error
 ├── data
 └── error
```

A failure in one collector therefore does not automatically discard all other successfully collected evidence.

---

### File collector edge cases

The file-hash collector handles:

- nonexistent directories
- inaccessible directories
- unreadable files
- filesystem errors during `stat()`
- large files
- directories containing more than 500 files

Unreadable files are represented as report entries with null hash/metadata fields and an associated error.

The collector does not recurse into subdirectories.

---

### Analysis isolation

Rules operate on the evidence dictionary produced by the interpreter.

They do not re-run collectors or directly access the endpoint.

This gives the system a clean separation:

```text
Host access
    ↓
Collectors
    ↓
Evidence
    ↓
Rules
    ↓
Findings
```

A rule therefore cannot unexpectedly trigger another collection operation.

---

### Race conditions and state

The interpreter's investigation state is local to a single `run_investigation()` invocation.

There is no shared mutable investigation state between requests.

Collector results are appended in command order, and each analysis operation constructs its evidence view from the current successful collector results.

This provides deterministic ordering for a single investigation.

The current API does not introduce an explicit application-level worker queue or parallel execution model. As a result, there is no collector-level synchronization mechanism to maintain; operations are executed synchronously.

---

### SQLite resource cleanup

Database connections are opened for individual operations and closed in `finally` blocks.

The pattern is:

```text
open connection
      │
      ▼
execute query
      │
      ├── success ──► commit / fetch
      │
      └── exception
      │
      ▼
finally
      │
      ▼
close connection
```

Parameterized SQL is used for inserted values and investigation IDs.

---

### CORS boundary

The API currently permits the local Vite development origin:

```text
http://localhost:5173
```

For deployment, this should be changed to the actual frontend origin rather than leaving development origins enabled.

---

## 5. Code Highlights

### `jocky/language/interpreter.py`

This is the central execution boundary.

The interpreter:

1. walks the validated IR in source order
2. resolves collectors/rules through explicit registries
3. isolates collector failures
4. builds an evidence map for analysis
5. accumulates findings
6. records the requested report name

The important design property is that the interpreter does not dynamically execute names supplied by the script.

```text
DSL name
   ↓
allowlist lookup
   ↓
approved callable
   ↓
execution
```

This keeps the DSL declarative while preserving a controlled execution surface.

---

### `jocky/collectors/file_hash.py`

The hashing implementation combines two resource controls:

```text
MAX_FILES = 500
CHUNK_SIZE = 65536
```

The first limits the number of filesystem entries processed in a run. The second bounds memory used for each file.

The SHA-256 implementation uses incremental hashing rather than reading an entire file:

```text
read chunk
   ↓
update hash
   ↓
read next chunk
   ↓
...
```

This makes memory consumption effectively independent of individual file size.

---

### `jocky/analysis/rules.py`

The analysis module keeps rules pure with respect to host access.

`rule_process_network_correlation()` first builds a PID-indexed process map:

```python
processes = {
    p["pid"]: p
    for p in ...
}
```

Network connections can then resolve their owning process through dictionary lookup rather than repeatedly scanning the process list.

For `P` processes and `C` connections, this changes the correlation step from a potential `O(P × C)` nested scan to approximately:

```text
O(P + C)
```

assuming normal dictionary lookup behavior.

That is the appropriate structure for endpoint evidence correlation.

---

## 6. Installation & Usage

### Prerequisites

Backend:

- Python 3.10+ recommended
- `pip`
- an operating system supported by the installed `psutil` version

Frontend:

- Node.js
- npm

SQLite is provided by Python's standard library; no separate database server is required.

---

### Clone the repository

```bash
git clone <repository-url>
cd SIH26148-jocky
```

### Backend setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn jocky.api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

---

### Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server runs on the default local development port:

```text
http://localhost:5173
```

The backend CORS configuration currently allows this origin.

For a production frontend build:

```bash
npm run build
```

To preview the generated build:

```bash
npm run preview
```

---

### Run an investigation directly in Python

The repository contains an end-to-end example in `test_interpreter.py`.

Run it from the repository root:

```bash
python test_interpreter.py
```

The script executes an investigation containing:

```text
investigation "Endpoint Triage" {
    collect system_info;
    collect processes;
    collect network_connections;
    analyze suspicious_processes;
    analyze missing_paths;
    analyze process_network_correlation;
    report "triage_report";
}
```

It generates:

```text
triage_report.json
triage_report.html
```

---

### Run through the API

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/investigations \
  -H "Content-Type: application/json" \
  -d '{
    "script": "investigation \"Endpoint Triage\" { collect system_info; collect processes; collect network_connections; analyze suspicious_processes; analyze missing_paths; analyze process_network_correlation; report \"triage_report\"; }"
  }'
```

List stored investigations:

```bash
curl http://127.0.0.1:8000/api/investigations
```

Retrieve an individual investigation:

```bash
curl http://127.0.0.1:8000/api/investigations/<id>
```

The SQLite database is created automatically as:

```text
jocky.db
```

---

## Repository Layout

```text
.
├── jocky/
│   ├── analysis/
│   │   ├── finding.py
│   │   ├── registry.py
│   │   └── rules.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── collectors/
│   │   ├── file_hash.py
│   │   ├── logged_in_users.py
│   │   ├── network_connections.py
│   │   ├── processes.py
│   │   ├── registry.py
│   │   └── system_info.py
│   │
│   ├── language/
│   │   ├── interpreter.py
│   │   ├── ir.py
│   │   ├── lexer.py
│   │   └── parser.py
│   │
│   ├── reports/
│   │   ├── builder.py
│   │   ├── html_writer.py
│   │   ├── json_writer.py
│   │   └── report.py
│   │
│   └── storage/
│       └── database.py
│
├── frontend/
│   └── src/
│
├── sample_evidence/
├── requirements.txt
├── test_interpreter.py
├── test_lexer.py
├── jocky.db
├── triage_report.html
└── triage_report.json
```

---

## Current Limitations

The current implementation has several deliberate constraints:

- collector execution is synchronous and sequential
- SQLite is intended for local/small-scale persistence
- file hashing is non-recursive
- file hashing is capped at 500 files per run
- the `file_hash` collector currently uses the fixed `./sample_evidence` directory
- CORS is configured for the local Vite development origin
- the DSL has no variables, expressions, conditionals, loops, or user-defined functions
- analysis rules operate only on evidence collected earlier in the same investigation
- there is no background job queue or cancellation mechanism for long-running investigations

These boundaries should be addressed before deploying the system as a multi-user or high-volume endpoint collection service.