# Dashboard Functionality Guide

## Overview

The dashboard provides real-time monitoring and control of the Pokémon Blue AI agent. Built with Streamlit, it offers insights into game progress, performance metrics, and agent behavior.

## Features

### Live Game View
- Current game screen capture
- Real-time frame rate display
- Emulator controls (pause/resume)

### Game State
- Current location and coordinates
- Party Pokémon with levels and HP
- Badges obtained
- Money and key items
- Current game state (overworld, battle, etc.)

### Action History
- Timeline of recent actions
- Mistral API requests and responses
- Tool usage history
- Decision reasoning

### Performance Metrics
- Frames per second
- API call latency
- Memory usage
- Action success rate
- Progress over time

### Configuration
- Adjustable parameters
- Checkpoint management
- Log level control
- Run history

## Usage

### Starting the Dashboard

```bash
streamlit run dashboard/dashboard.py
```

### Navigation

The dashboard is organized into tabs:

1. **Overview**: High-level status and controls
2. **Game State**: Detailed current state
3. **Actions**: Recent action history
4. **Metrics**: Performance charts
5. **Logs**: Detailed event logs
6. **Config**: Runtime configuration

### Controls

**Emulator Controls:**
- Pause/Resume: Temporarily stop agent
- Step: Execute single frame
- Fast Forward: Increase frame skip

**Agent Controls:**
- Soft Reset: Restart current run
- Hard Reset: Full restart with new run ID
- Checkpoint: Save current state
- Restore: Load from checkpoint

## Customization

### Layout Options

```python
# In dashboard.py
config = {
    "show_metrics": True,
    "show_history": True,
    "refresh_interval": 1,  # seconds
    "theme": "dark"
}
```

### Adding New Metrics

1. Add metric to database schema
2. Create visualization component
3. Add to metrics tab

```python
def add_custom_metric(name, query):
    """Register custom metric for dashboard"""
    @st.cache_data(ttl=60)
    def fetch_metric():
        return database.execute(query).fetchall()
    st.metric(label=name, value=fetch_metric())
```

## Integration

The dashboard connects to the agent through:

1. **Shared Database**: Reads from SQLite
2. **WebSocket**: Real-time updates (optional)
3. **REST API**: Control interface

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Current agent status |
| `/api/pause` | POST | Pause agent |
| `/api/resume` | POST | Resume agent |
| `/api/config` | GET/POST | Configuration |
| `/api/checkpoint` | POST | Save checkpoint |

## Troubleshooting

**Dashboard not updating:**
- Check database connection
- Verify agent is running
- Refresh browser cache

**Performance issues:**
- Reduce refresh interval
- Disable metrics tab
- Use lighter theme

**Connection errors:**
- Ensure agent and dashboard use same database
- Check WebSocket configuration
- Verify CORS settings