# AutoTrader Scheduling System Analysis

**Date**: 2026-02-12  
**Analysis**: Review of scheduling capabilities and recommendations

---

## Executive Summary

**Current State**: ❌ **NO SCHEDULING SYSTEM EXISTS**

AutoTrader currently operates on a **continuous polling model** - the engine runs in a loop and evaluates strategies every `poll_interval` seconds (default: 60s). There is **no time-based scheduling system** for:
- Scheduling strategies to start at specific times
- Scheduling one-time actions
- Delayed execution
- Cron-like recurring tasks

---

## Current Architecture

### How It Works Now

1. **Engine Startup**
   - User runs `trader start` (CLI) or engine is started via MCP
   - Engine acquires a lock file (`config/.engine.lock`)
   - Engine enters continuous loop

2. **Execution Loop**
   ```python
   while not _stop_requested:
       _run_cycle()  # Evaluate all active strategies
       sleep(poll_interval)  # Default: 60 seconds
   ```

3. **Strategy Storage**
   - **Location**: `config/strategies.yaml`
   - **Format**: YAML file with strategy definitions
   - **No scheduling fields**: Strategies have `created_at` and `updated_at` timestamps, but no `schedule_at` or `execute_at` fields

4. **Strategy Evaluation**
   - Engine loads strategies from `config/strategies.yaml` on each cycle
   - Evaluates all `enabled` strategies
   - Executes actions based on strategy state (pending → entry → position_open → exiting → completed)

### What's Missing

❌ **No scheduling fields in Strategy model**
- No `schedule_at: Optional[datetime]` field
- No `schedule_cron: Optional[str]` field
- No `schedule_enabled: bool` field

❌ **No scheduler component**
- No cron parser
- No scheduled task queue
- No time-based execution logic

❌ **No scheduled task storage**
- No separate `config/schedules.yaml` file
- No database for scheduled tasks
- No persistence mechanism for scheduled items

---

## Where Things Live Currently

### Strategy Storage
- **File**: `config/strategies.yaml`
- **Structure**: YAML array of strategy objects
- **Fields**: `id`, `symbol`, `strategy_type`, `phase`, `enabled`, `created_at`, `updated_at`, etc.
- **No scheduling**: Strategies are evaluated immediately if `enabled: true`

### Engine State
- **Lock File**: `config/.engine.lock` (prevents multiple instances)
- **PID**: Stored in lock file for debugging
- **Memory**: Engine state is in-memory only (no persistence)

### Order Storage
- **File**: `config/orders.yaml`
- **Purpose**: Persists order state locally
- **Not scheduling**: Just order history/state

---

## Mechanism of Execution

### Current Flow

```
User: trader start
  ↓
CLI: Creates TradingEngine instance
  ↓
Engine: Acquires lock file
  ↓
Engine: Enters _run_loop()
  ↓
Loop: Every poll_interval seconds
  ├─ Check if market is open
  ├─ Load strategies from config/strategies.yaml
  ├─ Evaluate each enabled strategy
  └─ Execute actions (place orders, update state)
  ↓
Sleep: poll_interval seconds
  ↓
Repeat: Until stop requested
```

### What Happens When You "Schedule" Something

**Currently**: You can't schedule anything. Strategies are evaluated immediately if:
- `enabled: true`
- Market is open
- Strategy phase allows action

**If scheduling existed**, the flow would be:
```
Scheduled Task Created
  ↓
Stored in config/schedules.yaml (or database)
  ↓
Engine checks scheduled tasks each cycle
  ↓
If schedule_time <= now:
  ├─ Execute scheduled action
  └─ Mark as executed or remove
```

---

## Recommendations

### Option 1: Simple Time-Based Scheduling (Recommended)

**Add scheduling fields to Strategy model:**
```python
# In trader/strategies/models.py
schedule_at: Optional[datetime] = None  # Execute strategy at this time
schedule_enabled: bool = False  # Enable scheduling
```

**Modify engine to check schedules:**
```python
# In trader/core/engine.py _run_cycle()
def _run_cycle(self):
    # Check scheduled strategies
    scheduled = [s for s in strategies if s.schedule_enabled and s.schedule_at]
    for strategy in scheduled:
        if strategy.schedule_at <= datetime.now():
            # Enable strategy and clear schedule
            strategy.enabled = True
            strategy.schedule_enabled = False
            strategy.schedule_at = None
            save_strategy(strategy)
    
    # Continue with normal evaluation...
```

**Storage**: Use existing `config/strategies.yaml` - add scheduling fields

**Pros**:
- Simple to implement
- Uses existing storage mechanism
- No new dependencies
- Easy to understand

**Cons**:
- Only supports one-time scheduling
- No recurring schedules (cron)

### Option 2: Full Cron-Based Scheduling

**Add scheduler component:**
```python
# New file: trader/core/scheduler.py
class TaskScheduler:
    def __init__(self):
        self.tasks: list[ScheduledTask] = []
    
    def add_task(self, task: ScheduledTask):
        """Add a scheduled task."""
    
    def check_and_execute(self):
        """Check scheduled tasks and execute if time has come."""
```

**New model:**
```python
# In trader/strategies/models.py or new file
@dataclass
class ScheduledTask:
    id: str
    task_type: str  # "strategy_start", "strategy_stop", "order_place", etc.
    schedule_cron: str  # Cron expression: "0 9 * * 1-5" (9 AM weekdays)
    schedule_at: Optional[datetime]  # One-time execution
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    task_data: dict  # Strategy ID, order details, etc.
```

**Storage**: New `config/schedules.yaml` file

**Dependencies**: Add `croniter` library for cron parsing

**Pros**:
- Supports recurring schedules
- More flexible
- Can schedule any action type

**Cons**:
- More complex
- Requires new dependency
- More code to maintain

### Option 3: Database-Based Scheduling

**Use SQLite database:**
- Store scheduled tasks in `data/schedules.db`
- Use SQL queries for efficient scheduling checks
- Better for complex scheduling needs

**Pros**:
- Scalable
- Efficient queries
- Can handle many scheduled tasks

**Cons**:
- Requires database setup
- More infrastructure
- Overkill for simple use cases

---

## Recommended Implementation Plan

### Phase 1: Basic Time-Based Scheduling (Quick Win)

1. **Add scheduling fields to Strategy model**
   - `schedule_at: Optional[datetime]`
   - `schedule_enabled: bool`

2. **Modify engine to check schedules**
   - Check `schedule_at` in `_run_cycle()`
   - Enable strategy when time arrives

3. **Add CLI/MCP commands**
   - `trader strategy schedule <id> --at "2026-02-13 09:30:00"`
   - MCP: `schedule_strategy(strategy_id, schedule_at)`

4. **Update storage**
   - Save scheduling fields to `config/strategies.yaml`

**Estimated effort**: 2-4 hours  
**Complexity**: Low  
**Dependencies**: None

### Phase 2: Cron-Based Scheduling (Future)

1. Add `croniter` dependency
2. Create `ScheduledTask` model
3. Create `TaskScheduler` component
4. Add `config/schedules.yaml` storage
5. Integrate scheduler into engine loop

**Estimated effort**: 1-2 days  
**Complexity**: Medium  
**Dependencies**: `croniter`

---

## Questions to Answer

1. **What do you want to schedule?**
   - Strategies to start at market open?
   - One-time orders at specific times?
   - Recurring tasks (daily, weekly)?

2. **How precise does scheduling need to be?**
   - Exact time (9:30 AM)?
   - Market hours only?
   - Any time?

3. **Do you need recurring schedules?**
   - Daily at market open?
   - Weekly rebalancing?
   - Or just one-time scheduling?

4. **Where should scheduled data live?**
   - In `config/strategies.yaml` (simple)?
   - Separate `config/schedules.yaml` (cleaner)?
   - Database (scalable)?

---

## Next Steps

1. **Decide on scheduling requirements** (what, when, how often)
2. **Choose implementation approach** (simple time-based vs cron-based)
3. **Implement Phase 1** (basic time-based scheduling)
4. **Test and validate** (ensure schedules execute correctly)
5. **Document** (update README, add examples)

---

## Current MCP Tools Related to Scheduling

**None exist**. Current MCP tools:
- `create_strategy()` - Creates strategy immediately
- `set_strategy_enabled()` - Enables/disables strategy immediately
- No scheduling tools

**Would need to add**:
- `schedule_strategy(strategy_id, schedule_at)` - Schedule strategy to start
- `list_schedules()` - List all scheduled tasks
- `cancel_schedule(schedule_id)` - Cancel scheduled task

---

## Conclusion

**Current State**: No scheduling system exists. Strategies are evaluated continuously when enabled.

**Recommendation**: Start with **Phase 1 (Basic Time-Based Scheduling)** - simple, quick to implement, covers most use cases.

**Storage**: Use existing `config/strategies.yaml` with new scheduling fields.

**Execution**: Modify engine `_run_cycle()` to check `schedule_at` timestamps and enable strategies when time arrives.
