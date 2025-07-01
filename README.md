# Traeger Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A comprehensive Home Assistant integration for [Traeger WiFire Grills][traeger] with real-time monitoring and control capabilities.

## ✨ Recent Updates (v1.0.0)

- **Smart Temperature Display**: Target temperature now shows as 0 when grill is off for clearer status indication
- **Feature-Based Entity Creation**: Entities are dynamically created based on your grill's actual capabilities
- **Improved Entity Naming**: More user-friendly entity names and better organization in Home Assistant
- **Enhanced Probe Reliability**: Comprehensive improvements to probe temperature monitoring and state detection
- **Robust MQTT Connection**: Improved connection resilience with automatic retry logic for uninterrupted monitoring

## 🏠 Home Assistant Integration Examples

![Device View][deviceimg]
*Complete device overview showing all available entities and controls*

![Lovelace Dashboard][lovelaceimg] 
*Custom dashboard cards for monitoring and controlling your grill*

![Grill Climate Control][grillimg]
*Dual thermostat control for both grill and probe temperatures*

![Probe Monitoring][probeimg]
*Advanced probe state monitoring with smart alerts*

## 📊 Available Platforms

Platform | Description | Features
-- | -- | --
`climate` | Temperature control for grill and probe | Dual thermostats, HVAC modes, preset support
`sensor` | Temperature readings and status monitoring | Smart heating/cooling detection, probe reliability
`switch` | Feature toggles and connectivity | SuperSmoke, KeepWarm with conditional availability  
`number` | Timer control | 1-1440 minute range with Home Assistant integration

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Search for "Traeger" in HACS
3. Install the integration
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for "Traeger"

### Option 2: Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the `custom_components/traeger/` folder to your Home Assistant config directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for "Traeger"

## ⚙️ Configuration

Configuration is handled entirely through the Home Assistant UI:

1. **Add Integration**: Go to Settings → Devices & Services → Add Integration
2. **Enter Credentials**: Provide your Traeger app username and password
3. **Select Platform**: Choose your Traeger grill platform
4. **Automatic Discovery**: The integration will automatically discover and configure entities based on your grill's capabilities

## 🔧 Advanced Features

### Real-Time Communication Architecture
This integration uses a sophisticated dual-protocol approach:
- **Commands**: Sent via REST API for reliable execution
- **State Updates**: Real-time via MQTT WebSocket for instant feedback
- **Authentication**: AWS Cognito with automatic token refresh

### Smart Entity Management
- **Feature Detection**: Only creates entities your grill actually supports
- **Conditional Availability**: Entities automatically enable/disable based on grill state
- **Intelligent State Logic**: Advanced algorithms for heating/cooling detection

## 📋 Entity Reference

### Grill State Sensor
Provides detailed operational status aligned with the Traeger app:
State | Description
-- | --
`offline` | Powered off (or not accesible)
`sleeping` | Standing by (power switch on, screen off)
`idle` | Standing by (power switch on, screen on)
`igniting` | Igniting the fire pot
`preheating` | Ignition is complete, heating to set temperature
`manual_cook` | Cooking mode
`custom_cook` | Cooking mode, using preset cook cycle
`cool_down` | Cool down cycle
`shutdown` | Cool down cycle complete, heading to sleep
`unknown` | Unkown state, report to developers

### Heating State Sensor
Provides intelligent heating status with enhanced logic for automation triggers:
State | Description
-- | --
`idle` | Not in igniting, preheating, cooking or cool_down modes
`preheating` | Igniting or preheating (and under 165°F)
`heating` | Trying to get temperature **up** to new target temperature
`cooling` | Trying to get temperature **down** to new target temperature
`at_temp` | Temperature has reached the target temperature (and is holding at ±20°F of target temperature)
`over_temp` | Was `at_temp`, but is now more than 20°F **above** target temperature
`under_temp` | Was `at_temp`, but is now more than 20°F **below** target temperature
`cool_down` | Cool down cycle

### Probe State Sensor
Enhanced probe monitoring with reliability improvements and smart state detection:
State | Description
-- | --
`idle` | Probe target temperature is **not** set (or grill is not in igniting, preheating or cooking modes)
`set` | Probe target temperature **is** set
`close` | Probe temperature is within 5°F of target temperature
`at_temp` | Probe alarm has fired
`fell_out` | Probe probably fell out of the meat (Probe temperature is greater that 215°F)

## 🔍 Troubleshooting

### Common Issues
- **Connection Issues**: Ensure your Traeger grill is connected to WiFi and accessible via the official app
- **Authentication Errors**: Verify your username and password match your Traeger account credentials  
- **Missing Entities**: Some entities only appear when relevant (e.g., probe entities when probe is connected)
- **State Updates**: If states aren't updating, check your network connection and grill WiFi status

### Debug Logging
Add this to your `configuration.yaml` for detailed logs:
```yaml
logger:
  default: info
  logs:
    custom_components.traeger: debug
```

## 🤝 Contributing

Contributions are welcome! Please read the [Contribution Guidelines](CONTRIBUTING.md) for details on:
- Code style and formatting requirements
- Development setup with flake8, black, and isort
- Testing procedures and requirements
- Pull request process

## 📈 Automation Ideas

This integration enables powerful Home Assistant automations:

- **Temperature Alerts**: Get notified when grill reaches target temperature
- **Probe Monitoring**: Alerts when meat probe reaches desired doneness
- **Maintenance Reminders**: Track cook times and suggest cleaning schedules  
- **Energy Monitoring**: Log cooking sessions and pellet consumption patterns
- **Smart Notifications**: Context-aware alerts based on cooking state and time

***

[traeger]: https://www.traegergrills.com/
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[deviceimg]: device.png
[lovelaceimg]: lovelace.png
[probeimg]: probe.png
[grillimg]: grill.png
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/sebirdman/hass_traeger.svg?style=for-the-badge
[releases]: https://github.com/sebirdman/hass_traeger/releases
