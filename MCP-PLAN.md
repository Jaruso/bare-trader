# MCP Server + CLI Dual-Interface Plan

This plan describes how AutoTrader will operate as both a CLI tool and an
MCP-compliant server while preserving a single source of truth for trading
logic, safety, and data access.

## Goals

- Provide feature parity between CLI and MCP tools.
- Keep trading logic centralized in a shared application layer (`trader/app`).
- Offer clear, structured JSON I/O for agents and humans.
- Maintain safety-first defaults (paper trading by default).
- Document every feature with CLI and MCP usage examples.
- Use official MCP protocol standards (stdio/SSE transport).

## Non-Goals (for initial rollout)

- Web dashboard UI (planned later).
- Multi-broker support beyond Alpaca.
- Streaming-only strategies as a first requirement.

## Architecture Overview

```
auto-trader/
├── trader/
│   ├── cli/             # Click CLI adapter (human-friendly interface)
│   ├── mcp/             # MCP server adapter (agent interface via MCP protocol)
│   ├── app/             # 🎯 Shared application services (single source of truth)
│   ├── schemas/         # Pydantic models for contracts/validation
│   ├── strategies/      # Strategy implementations
│   ├── backtest/        # Backtesting engine
│   ├── analysis/        # Performance analysis
│   ├── indicators/      # Technical indicators
│   ├── core/            # Domain models, portfolio, safety
│   ├── oms/             # Order management
│   └── ...
├── docs/                # User and agent documentation
└── tests/
    ├── unit/
    ├── integration/
    └── contracts/       # CLI/MCP parity tests
```

### Module Responsibilities

**`trader/app/`** (Application Services)
- Business logic and orchestration
- Uses dependency injection for broker, storage, config
- Returns structured data (Pydantic models)
- Stateless operations (state managed by dependencies)
- Used by BOTH CLI and MCP adapters

**`trader/schemas/`** (Contracts)
- Pydantic models for all inputs/outputs
- Validation rules and error models
- Shared across CLI, MCP, and app layer
- Serializable to JSON for both interfaces

**`trader/cli/`** (CLI Adapter)
- Click commands for human users
- Argument parsing and validation
- Calls `trader/app` services
- Formats output (human-readable by default, `--json` opt-in)
- Delegates all logic to app layer

**`trader/mcp/`** (MCP Server Adapter)
- MCP protocol implementation (stdio/SSE transport)
- Tool registration and request handling
- Calls same `trader/app` services as CLI
- Returns JSON responses per MCP spec
- Authentication and rate limiting

## Architecture Principles

1. **One core, two adapters**: CLI and MCP are thin adapters around a shared
   `trader/app` service layer. Zero logic duplication.
2. **Service layer pattern**: Application services use dependency injection,
   are stateless, and return Pydantic models.
3. **Contract-driven**: All I/O defined via Pydantic schemas in `trader/schemas`.
   Both CLI and MCP use identical contracts.
4. **JSON-first**: CLI supports `--json` flag for structured output. MCP always
   returns JSON per protocol spec.
5. **Consistent error model**: Shared error schema with actionable guidance
   across both interfaces.
6. **Safety gates**: Production operations require explicit confirmation,
   strict guardrails, and audit logging (shared implementation).
7. **Tool parity**: Every CLI command has a corresponding MCP tool with
   identical functionality.

## Proposed Application Layer

Create a thin service layer that both CLI and MCP call.

```
trader/
├── app/
│   ├── backtests.py
│   ├── strategies.py
│   ├── portfolio.py
│   ├── orders.py
│   ├── analysis.py
│   ├── optimize.py
│   └── data.py
├── schemas/             # Pydantic models for IO + validation
└── errors.py            # Shared error types + error-to-JSON mapping
```

## MCP Server Design

- **Framework**: FastAPI
- **Transport**: HTTP (MCP tools over REST)
- **Entry point**: `mcp/app.py`
- **Tool registry**: `mcp/tools.py` exposing tool metadata + handlers
- **Auth**: API key (env var) or local-only default
- **Output**: MCP-compliant responses with structured JSON

### Tool Design Template

- `name`
- `description`
- `parameters` (JSON schema)
- `returns` (JSON schema)
- `examples`

## CLI + MCP Parity Matrix (Initial)

| Feature | CLI Command | MCP Tool |
|---------|-------------|----------|
| Status | `trader status` | `get_status()` |
| Portfolio | `trader portfolio` | `get_portfolio()` |
| Positions | `trader positions` | `list_positions()` |
| Orders | `trader orders` | `list_orders()` |
| Quote | `trader quote` | `get_quote(symbol)` |
| Strategy CRUD | `trader strategy ...` | `create_strategy`, `list_strategies`, `update_strategy`, `delete_strategy` |
| Backtest | `trader backtest run` | `backtest_strategy(...)` |
| Backtest List | `trader backtest list` | `list_backtests(...)` |
| Backtest Show | `trader backtest show` | `get_backtest(id)` |
| Compare | `trader backtest compare` | `compare_backtests(ids)` |
| Optimize | `trader optimize` | `optimize_strategy(...)` |
| Analyze | `trader analyze` | `analyze_performance(...)` |
| Indicators | `trader indicator ...` | `list_indicators`, `describe_indicator` |
| Data | `trader data ...` | `get_historical_data`, `list_data_sources` |
| Engine Control | `trader start/stop` | `start_engine`, `stop_engine` |
| Notifications | `trader notify ...` | `send_notification(...)` |

## Documentation Plan

Create dedicated docs that show both CLI and MCP usage for every feature.

```
docs/
├── CLI.md               # CLI usage for all commands
├── MCP.md               # MCP tool reference
├── FEATURES.md          # Feature overview + links
└── EXAMPLES.md          # End-to-end workflows
```

For each feature:
- Short description
- CLI usage with examples
- MCP tool schema + example request/response
- Safety considerations

## Implementation Phases

### Phase 0: Groundwork (Design + Scaffolding) ✅ COMPLETE
- ✅ Add `MCP-PLAN.md` and cross-links from `PLAN.md` and `README.md`.
- ✅ Define module split (`cli/`, `mcp/`, `trader/`).
- ✅ Add `trader/app/` service layer (10 modules: indicators, engine, strategies, portfolio, orders, analysis, backtests, optimization, data).
- ✅ Add `trader/schemas/` Pydantic v2 models (11 modules: common, errors, portfolio, orders, strategies, backtests, analysis, optimization, indicators, engine).
- ✅ Add `trader/errors.py` shared error hierarchy (AppError, ValidationError, NotFoundError, ConfigurationError, BrokerError, SafetyError, EngineError).
- ✅ Refactor CLI (`trader/cli/main.py`) to delegate to app layer with `--json` flag support.
- ✅ 115 tests passing, lint clean, type check clean.

### Phase 1: MCP Server Skeleton
- Create `mcp/` package and FastAPI app.
- Implement health endpoint and tool registry endpoint.
- Add config + auth for MCP requests.
- Add basic tool: `get_status()`.

### Phase 2: Core Tool Parity
- Backtest, analyze, optimize, visualize.
- Strategy CRUD and engine controls.
- Data providers and indicator tools.
- Ensure outputs are consistent with CLI JSON mode.

### Phase 3: Safety, Auditing, and Rate Controls
- Central audit log for CLI and MCP actions.
- Safety gate validation shared across CLI/MCP.
- Rate limit + timeouts for long-running tasks.

### Phase 4: Docs + Contract Tests
- Write CLI + MCP usage docs for each feature.
- Add MCP contract tests for tool schemas.
- Add parity tests to ensure CLI and MCP return equivalent data.

## Open Questions

- Should MCP tools use synchronous responses for long-running jobs, or return
  job IDs with polling endpoints?
- Should the CLI JSON mode be default for all commands, or opt-in via `--json`?
- Should the MCP server run locally only by default (no network bind)?

