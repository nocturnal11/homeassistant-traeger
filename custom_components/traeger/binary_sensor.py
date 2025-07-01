"""Binary sensor platform for Traeger."""

import time
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.const import UnitOfTemperature

from .const import (
    CONF_PELLET_OUTAGE_TEMP_DROP,
    CONF_PELLET_OUTAGE_TIME_THRESHOLD,
    DOMAIN,
    GRILL_MODE_CUSTOM_COOK,
    GRILL_MODE_MANUAL_COOK,
    GRILL_MODE_PREHEATING,
    GRILL_MODE_IGNITING,
    PELLET_OUTAGE_TEMP_DROP_F,
    PELLET_OUTAGE_TEMP_DROP_C,
    PELLET_OUTAGE_TIME_THRESHOLD,
    PELLET_OUTAGE_MIN_TARGET_F,
    PELLET_OUTAGE_MIN_TARGET_C,
)

from .entity import TraegerBaseEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup binary sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    grills = client.get_grills()
    entities_to_add = []

    for grill in grills:
        grill_id = grill["thingName"]
        entities_to_add.append(PelletOutageSensor(client, grill_id, entry))

    async_add_devices(entities_to_add)


class PelletOutageSensor(BinarySensorEntity, TraegerBaseEntity):
    """Binary sensor to detect pellet outage based on temperature drop patterns."""

    def __init__(self, client, grill_id, config_entry):
        super().__init__(client, grill_id)
        self.grill_register_callback()
        self._config_entry = config_entry

        # State tracking for pellet outage detection
        self._temp_history = []  # List of (timestamp, temp, target_temp) tuples
        self._pellet_outage_detected = False
        self._last_check_time = time.time()
        self._active_cooking_modes = [
            GRILL_MODE_CUSTOM_COOK,
            GRILL_MODE_MANUAL_COOK,
            GRILL_MODE_PREHEATING,
            GRILL_MODE_IGNITING,
        ]

    def _get_temp_drop_threshold(self):
        """Get the temperature drop threshold from config or default."""
        config_temp_drop = self._config_entry.options.get(CONF_PELLET_OUTAGE_TEMP_DROP)
        if config_temp_drop is not None:
            # Convert to Celsius if needed
            if self.grill_units == UnitOfTemperature.CELSIUS:
                return int((config_temp_drop - 32) * 5 / 9)
            return config_temp_drop

        # Use default based on unit system
        return (
            PELLET_OUTAGE_TEMP_DROP_C
            if self.grill_units == UnitOfTemperature.CELSIUS
            else PELLET_OUTAGE_TEMP_DROP_F
        )

    def _get_time_threshold(self):
        """Get the time threshold from config or default."""
        return self._config_entry.options.get(
            CONF_PELLET_OUTAGE_TIME_THRESHOLD, PELLET_OUTAGE_TIME_THRESHOLD
        )

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._generate_entity_name("Pellet Outage")

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        base_id = self._generate_entity_id_base()
        return f"{base_id}_pellet_outage"

    @property
    def device_class(self):
        """Return the device class."""
        return BinarySensorDeviceClass.PROBLEM

    @property
    def icon(self):
        """Return the icon for the sensor."""
        if self.is_on:
            return "mdi:fire-alert"
        return "mdi:fire"

    @property
    def is_on(self):
        """Return true if pellet outage is detected."""
        return self._pellet_outage_detected

    @property
    def available(self):
        """Return True if entity is available."""
        if self.grill_state is None:
            return False
        return self.grill_state.get("connected", False)

    def _should_monitor_pellet_outage(self):
        """Determine if we should monitor for pellet outage based on grill state."""
        if self.grill_state is None:
            return False

        # Only monitor during active cooking modes
        grill_mode = self.grill_state.get("system_status")
        if grill_mode not in self._active_cooking_modes:
            return False

        # Only monitor when target temperature is high enough
        target_temp = self.grill_state.get("set", 0)
        min_target = (
            PELLET_OUTAGE_MIN_TARGET_C
            if self.grill_units == UnitOfTemperature.CELSIUS
            else PELLET_OUTAGE_MIN_TARGET_F
        )

        return target_temp >= min_target

    def _update_temperature_history(self):
        """Update the temperature history for pellet outage detection."""
        if not self._should_monitor_pellet_outage():
            # Clear history when not monitoring
            self._temp_history.clear()
            return

        current_time = time.time()
        current_temp = self.grill_state.get("grill", 0)
        target_temp = self.grill_state.get("set", 0)

        # Add current reading to history
        self._temp_history.append((current_time, current_temp, target_temp))

        # Remove old readings (keep only last 10 minutes)
        cutoff_time = current_time - 600  # 10 minutes
        self._temp_history = [
            reading for reading in self._temp_history if reading[0] > cutoff_time
        ]

    def _detect_pellet_outage(self):
        """Analyze temperature history to detect pellet outage."""
        if len(self._temp_history) < 2:
            return False

        current_time = time.time()
        temp_drop_threshold = self._get_temp_drop_threshold()
        time_threshold = self._get_time_threshold()

        # Get current temperature and target
        current_temp = self._temp_history[-1][1]
        current_target = self._temp_history[-1][2]

        # Look for sustained temperature drop over time threshold
        threshold_time = current_time - time_threshold

        # Find the highest temperature in the recent past
        max_recent_temp = current_temp
        for timestamp, temp, target in reversed(self._temp_history):
            if timestamp < threshold_time:
                break
            max_recent_temp = max(max_recent_temp, temp)

        # Check conditions for pellet outage:
        # 1. Current temperature is significantly below target
        # 2. Temperature has dropped significantly from recent peak
        # 3. We've been in this state for the threshold time
        temp_below_target = (current_target - current_temp) > temp_drop_threshold
        significant_drop = (max_recent_temp - current_temp) > temp_drop_threshold
        sustained_duration = any(
            timestamp <= threshold_time for timestamp, _, _ in self._temp_history
        )

        return temp_below_target and significant_drop and sustained_duration

    def _reset_pellet_outage(self):
        """Reset pellet outage detection when conditions change."""
        if not self._should_monitor_pellet_outage():
            self._pellet_outage_detected = False
            return

        # Reset if target temperature has changed significantly (new cook started)
        if len(self._temp_history) >= 2:
            current_target = self._temp_history[-1][2]
            previous_readings = [reading[2] for reading in self._temp_history[:-1]]

            # If target changed by more than 25 degrees, reset
            target_change_threshold = (
                14 if self.grill_units == UnitOfTemperature.CELSIUS else 25
            )
            for prev_target in previous_readings:
                if abs(current_target - prev_target) > target_change_threshold:
                    self._pellet_outage_detected = False
                    break

    def grill_refresh_state(self):
        """Called when grill state is updated."""
        super().grill_refresh_state()

        # Update temperature tracking
        self._update_temperature_history()

        # Reset detection if conditions changed
        self._reset_pellet_outage()

        # Only detect outage if not already detected
        if not self._pellet_outage_detected and self._should_monitor_pellet_outage():
            self._pellet_outage_detected = self._detect_pellet_outage()

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        attributes = super().extra_state_attributes.copy()

        if self.grill_state:
            current_temp = self.grill_state.get("grill", 0)
            target_temp = self.grill_state.get("set", 0)
            temp_diff = target_temp - current_temp

            attributes.update(
                {
                    "current_temperature": current_temp,
                    "target_temperature": target_temp,
                    "temperature_difference": temp_diff,
                    "monitoring_active": self._should_monitor_pellet_outage(),
                    "history_count": len(self._temp_history),
                    "last_check": self._last_check_time,
                }
            )

            # Add current threshold configuration
            attributes["temp_drop_threshold"] = self._get_temp_drop_threshold()
            attributes["time_threshold_seconds"] = self._get_time_threshold()

        return attributes
