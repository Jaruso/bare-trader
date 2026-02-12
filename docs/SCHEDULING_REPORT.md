# AutoTrader Scheduling System - Implementation Report

**Date**: 2026-02-12  
**Status**: ✅ **BASIC SCHEDULING IMPLEMENTED**

---

## Executive Summary

### What I Found

❌ **No scheduling system existed** - AutoTrader used a continuous polling model:
- Engine runs in a loop, checking strategies every 60 seconds (default)
- Strategies are evaluated immediately when `enabled: true`
- No time-based scheduling capabilities
- No cron or recurring task support

### What I Implemented

✅ **Basic Time-Based Scheduling** (Phase 1):
- Added scheduling fields to Strategy model
- Engine checks scheduled strategies each cycle
- Strategies can be scheduled to start at a specific datetime
- Scheduling data stored in existing `config/strategies.yaml`

---

## How Scheduling Works Now

### Storage Location

**File**: `config/strategies.yaml`

Scheduled strategies are stored alongside regular strategies with two new fields:
```yaml
strategies:
  - id: abc123
    symbol: AAPL
    enabled: false  # Disabled until schedule time
    schedule_enabled: true
    schedule_at: '2026-02-13T09:30:00'  # ISO format datetime
    # ... other strategy fields
```

### Execution Mechanism

**Engine Loop** (`trader/core/engine.py`):

1. **Every cycle** (default: every 60 seconds):
   ```python
   def _run_cycle(self):
       # Step 1: Check scheduled strategies
       self._check_scheduled_strategies()
       
       # Step 2: Check if market is open
       if not broker.is_market_open():
           return
       
       # Step 3: Evaluate active strategies
       strategies = get_active_strategies()  # Excludes scheduled strategies
       # ... execute strategies
   ```

2. **Schedule Check** (`_check_scheduled_strategies()`):
   ```python
   def _check_scheduled_strategies(self):
       strategies = load_strategies()
       now = datetime.now()
       
       for strategy in strategies:
           if strategy.schedule_enabled and strategy.schedule_at:
               if strategy.schedule_at <= now:
                   # Time has arrived - enable strategy
                   strategy.enabled = True
                   strategy.schedule_enabled = False
                   strategy.schedule_at = None
                   save_strategy(strategy)  # Persist to YAML
   ```

3. **Active Strategy Filter** (`get_active_strategies()`):
   - Excludes strategies where `schedule_enabled: true` and `schedule_at > now`
   - Only returns strategies that are ready to execute

### Data Flow

```
User schedules strategy
  ↓
Strategy saved to config/strategies.yaml with:
  - enabled: false
  - schedule_enabled: true
  - schedule_at: <datetime>
  ↓
Engine running (every 60s)
  ↓
_check_scheduled_strategies() runs
  ↓
If schedule_at <= now:
  - Set enabled: true
  - Clear schedule_enabled: false
  - Clear schedule_at: null
  - Save to config/strategies.yaml
  ↓
Next cycle: Strategy is now active and evaluated
```

---

## Implementation Details

### Files Modified

1. **`trader/strategies/models.py`**
   - Added `schedule_at: Optional[datetime]` field
   - Added `schedule_enabled: bool` field
   - Updated `to_dict()` to serialize scheduling fields
   - Updated `from_dict()` to deserialize scheduling fields

2. **`trader/core/engine.py`**
   - Added `_check_scheduled_strategies()` method
   - Modified `_run_cycle()` to check schedules before evaluating strategies

3. **`trader/strategies/loader.py`**
   - Updated `get_active_strategies()` to exclude scheduled strategies that haven't reached their time

### How to Use (Currently)

**Via Code** (Python):
```python
from datetime import datetime
from trader.strategies.models import Strategy, StrategyType
from trader.strategies.loader import save_strategy

# Create strategy
strategy = Strategy(
    symbol="AAPL",
    strategy_type=StrategyType.TRAILING_STOP,
    quantity=10,
    trailing_stop_pct=Decimal("5.0"),
    enabled=False,  # Disabled initially
    schedule_enabled=True,
    schedule_at=datetime(2026, 2, 13, 9, 30, 0),  # 9:30 AM tomorrow
)

save_strategy(strategy)
```

**Via YAML** (Manual edit):
```yaml
strategies:
  - id: abc123
    symbol: AAPL
    strategy_type: trailing_stop
    quantity: 10
    enabled: false
    schedule_enabled: true
    schedule_at: '2026-02-13T09:30:00'
    trailing_stop_pct: '5.0'
    # ... other fields
```

---

## What's Missing (Future Enhancements)

### Not Yet Implemented

1. **CLI Commands**
   - `trader strategy schedule <id> --at "2026-02-13 09:30:00"`
   - `trader strategy schedule list`
   - `trader strategy schedule cancel <id>`

2. **MCP Tools**
   - `schedule_strategy(strategy_id, schedule_at)`
   - `list_scheduled_strategies()`
   - `cancel_schedule(strategy_id)`

3. **Recurring Schedules**
   - Cron expressions (e.g., "0 9 * * 1-5" for 9 AM weekdays)
   - Daily/weekly/monthly schedules
   - Requires `croniter` library

4. **Schedule Management**
   - View all scheduled strategies
   - Edit schedule times
   - Cancel schedules

---

## Testing

### How to Test

1. **Create a scheduled strategy** (via code or YAML):
   ```yaml
   - id: test123
     symbol: AAPL
     enabled: false
     schedule_enabled: true
     schedule_at: '2026-02-12T14:00:00'  # 2 PM today
   ```

2. **Start engine**:
   ```bash
   trader start
   ```

3. **Wait for schedule time** - Engine will check every 60 seconds

4. **Verify**:
   - Check `config/strategies.yaml` - `schedule_at` should be cleared
   - Check logs - should see "Scheduled strategy test123 enabled at scheduled time"
   - Strategy should now be active and evaluated

---

## Limitations

1. **Precision**: Schedules are checked every `poll_interval` (default 60s), so execution may be up to 60 seconds late
2. **One-time only**: No recurring schedules (cron support)
3. **No persistence of schedule history**: Once executed, schedule info is cleared
4. **No timezone handling**: Uses system local time
5. **No validation**: Doesn't check if schedule time is in the past

---

## Recommendations

### Immediate Next Steps

1. **Add CLI commands** for scheduling:
   ```bash
   trader strategy schedule <id> --at "2026-02-13 09:30:00"
   trader strategy schedule list
   trader strategy schedule cancel <id>
   ```

2. **Add MCP tools**:
   - `schedule_strategy(strategy_id, schedule_at)`
   - `list_scheduled_strategies()`
   - `cancel_schedule(strategy_id)`

3. **Add validation**:
   - Reject schedules in the past
   - Validate datetime format
   - Warn if schedule is far in the future

### Future Enhancements

1. **Cron support** (Phase 2):
   - Add `croniter` dependency
   - Support cron expressions: `"0 9 * * 1-5"`
   - Recurring schedules

2. **Schedule management UI**:
   - List all scheduled strategies
   - Show next execution time
   - Edit/cancel schedules

3. **Timezone support**:
   - Store timezone with schedule
   - Convert to market timezone

---

## Conclusion

✅ **Basic scheduling is now functional**:
- Strategies can be scheduled to start at a specific time
- Engine checks schedules every cycle
- Scheduling data persists in `config/strategies.yaml`
- No database required - uses existing YAML storage

**Next**: Add CLI/MCP commands for easier scheduling management.
