# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code Quality Commands

```bash
# Lint the code using flake8
flake8 custom_components/traeger/

# Format code using black
black custom_components/traeger/

# Sort imports using isort
isort custom_components/traeger/
```

## Architecture Overview

This is a Home Assistant custom component for Traeger WiFire grill integration. The architecture follows a hybrid cloud communication pattern:

### Core Components

- **`traeger.py`**: Main API client handling AWS Cognito authentication and dual-protocol communication (REST + MQTT WebSocket)
- **`entity.py`**: Base entity classes with callback-driven state updates and unified device info
- **Platform modules**: `climate.py`, `sensor.py`, `switch.py`, `number.py` implement specific entity types
- **`config_flow.py`**: UI-based configuration with credential validation and platform selection

### Communication Architecture

**Dual Protocol Design:**
- **Commands**: Sent via REST API to AWS API Gateway endpoints
- **State Updates**: Real-time via MQTT WebSocket connection to AWS IoT Core
- **Authentication**: AWS Cognito with automatic token refresh (60-second buffer)

**Key API Patterns:**
```python
# Commands use numeric codes: "11,{temp}" for grill temp, "14,{temp}" for probe
# State updates arrive as JSON via MQTT callbacks
# All entities register callbacks with the traeger client for real-time updates
```

### Entity Update Flow

1. MQTT message received → `mqtt_onmessage()`
2. State cached in `grill_status[grill_id]`
3. Registered callbacks triggered
4. Entities call `grill_refresh_state()` 
5. Home Assistant state updated via `schedule_update_ha_state()`

### Code Organization Patterns

**Entity Inheritance:**
- `TraegerBaseEntity` → platform-specific base classes → concrete entities
- Shared device info, availability tracking, and callback registration
- Platform entities dynamically created based on grill capabilities

**State Management:**
- Centralized state caching in traeger client
- Complex state logic in sensor entities (heating states, probe states)
- Conditional entity availability based on grill operational modes

### Development Configuration

**Code Style (setup.cfg):**
- Flake8 with Black compatibility (88 char line length)
- isort for import organization
- Specific ignore patterns for Black compatibility

**Platform Architecture:**
- **Climate**: Dual thermostats (grill + probe) with HVAC mode mapping and preset support
- **Sensors**: Complex state sensors with smart heating/cooling detection logic
- **Switches**: Feature toggles (SuperSmoke, KeepWarm) with conditional availability
- **Number**: Timer control with 1-1440 minute range

### Key Constants (const.py)

- AWS endpoints and CLIENT_ID (hardcoded)
- Grill states, probe presets, temperature limits
- Platform configuration flags
- Command protocol mappings

### Integration Patterns

This component uses standard HA integration patterns:
- Config entry-based setup with platform forwarding
- Async/await throughout with proper HA event loop integration
- Observer pattern for real-time updates via callbacks
- Factory pattern for dynamic entity creation based on device capabilities