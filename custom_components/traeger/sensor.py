"""Sensor platform for Traeger."""

from homeassistant.helpers.entity import Entity
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    GRILL_MODE_OFFLINE,
    GRILL_MODE_COOL_DOWN,
    GRILL_MODE_CUSTOM_COOK,
    GRILL_MODE_MANUAL_COOK,
    GRILL_MODE_PREHEATING,
    GRILL_MODE_IGNITING,
    GRILL_MODE_IDLE,
    GRILL_MODE_SLEEPING,
    GRILL_MODE_SHUTDOWN,
    GRILL_MIN_TEMP_C,
    GRILL_MIN_TEMP_F,
)

from .entity import TraegerBaseEntity, TraegerGrillMonitor


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    grills = client.get_grills()
    for grill in grills:
        grill_id = grill["thingName"]

        # Get grill features to conditionally create entities
        grill_features = client.get_features_for_device(grill_id)

        entities_to_add = []

        # Only add Pellet Sensor if connected
        if grill_features and grill_features.get("pellet_sensor_connected") == 1:
            entities_to_add.append(
                PelletSensor(client, grill["thingName"], "Pellet Level", "pellet_level")
            )

        # Always add core sensors (no feature detection needed)
        entities_to_add.extend(
            [
                ValueTemperature(
                    client, grill["thingName"], "Ambient Temperature", "ambient"
                ),
                GrillTimer(
                    client, grill["thingName"], "Timer Start", "cook_timer_start"
                ),
                GrillTimer(client, grill["thingName"], "Timer End", "cook_timer_end"),
                GrillState(client, grill["thingName"], "State", "grill_state"),
                HeatingState(
                    client, grill["thingName"], "Heating State", "heating_state"
                ),
            ]
        )

        async_add_devices(entities_to_add)
        TraegerGrillMonitor(client, grill_id, async_add_devices, ProbeState)


class TraegerBaseSensor(TraegerBaseEntity):

    def __init__(self, client, grill_id, friendly_name, value):
        super().__init__(client, grill_id)
        self.value = value
        self.friendly_name = friendly_name
        self.grill_register_callback()

    # Generic Properties
    @property
    def available(self):
        """Reports unavailable when the grill is powered off"""
        if self.grill_state is None:
            return False
        else:
            return self.grill_state["connected"]

    @property
    def name(self):
        """Return the name of the sensor"""
        return self.friendly_name

    @property
    def unique_id(self):
        base_id = self._generate_entity_id_base()
        return f"{base_id}_{self.value}"

    # Sensor Properties
    @property
    def state(self):
        return self.grill_state[self.value]


class ValueTemperature(TraegerBaseSensor):
    """Traeger Temperature Value class."""

    # Generic Properties
    @property
    def icon(self):
        return "mdi:thermometer"

    # Sensor Properties
    @property
    def unit_of_measurement(self):
        return self.grill_units


class PelletSensor(TraegerBaseSensor):
    """Traeger Pellet Sensor class."""

    # Generic Properties
    @property
    def available(self):
        """Reports unavailable when the pellet sensor is not connected"""
        if self.grill_features is None:
            return False
        else:
            return (
                True if self.grill_features["pellet_sensor_connected"] == 1 else False
            )

    @property
    def icon(self):
        return "mdi:gauge"

    # Sensor Properties
    @property
    def unit_of_measurement(self):
        return "%"


class GrillTimer(TraegerBaseSensor):
    """Traeger Timer class."""

    # Generic Properties
    @property
    def icon(self):
        return "mdi:timer"

    # Sensor Properties
    @property
    def unit_of_measurement(self):
        return "sec"


class GrillState(TraegerBaseSensor):
    """Traeger Grill State class.
    These states correlate with the Traeger application.
    """

    # Generic Properties
    @property
    def icon(self):
        return "mdi:grill"

    # Sensor Properties
    @property
    def state(self):

        state = self.grill_state["system_status"]

        if state == GRILL_MODE_COOL_DOWN:
            return "cool_down"
        elif state == GRILL_MODE_CUSTOM_COOK:
            return "cook_custom"
        elif state == GRILL_MODE_MANUAL_COOK:
            return "cook_manual"
        elif state == GRILL_MODE_PREHEATING:
            return "preheating"
        elif state == GRILL_MODE_IGNITING:
            return "igniting"
        elif state == GRILL_MODE_IDLE:
            return "idle"
        elif state == GRILL_MODE_SLEEPING:
            return "sleeping"
        elif state == GRILL_MODE_OFFLINE:
            return "offline"
        elif state == GRILL_MODE_SHUTDOWN:
            return "shutdown"
        else:
            return "unknown"  # Likely a new state we don't know about


class HeatingState(TraegerBaseSensor):
    """Traeger Heating State class."""

    def __init__(self, client, grill_id, friendly_name, value):
        super().__init__(client, grill_id, friendly_name, value)
        self.previous_target_temp = None
        self.previous_state = "idle"
        self.preheat_modes = [GRILL_MODE_PREHEATING, GRILL_MODE_IGNITING]
        self.cook_modes = [GRILL_MODE_CUSTOM_COOK, GRILL_MODE_MANUAL_COOK]

    # Generic Properties
    @property
    def icon(self):
        if self.state == "over_temp":
            return "mdi:fire-alert"
        else:
            return "mdi:fire"

    # Sensor Properties
    @property
    def state(self):
        if self.grill_state is None:
            return "idle"

        target_temp = self.grill_state["set"]
        grill_mode = self.grill_state["system_status"]
        current_temp = self.grill_state["grill"]
        target_changed = True if target_temp != self.previous_target_temp else False
        min_cook_temp = (
            GRILL_MIN_TEMP_C
            if self.grill_units == UnitOfTemperature.CELSIUS
            else GRILL_MIN_TEMP_F
        )
        temp_swing = 11 if self.grill_units == UnitOfTemperature.CELSIUS else 20
        low_temp = target_temp - temp_swing
        high_temp = target_temp + temp_swing

        if grill_mode in self.preheat_modes:
            if current_temp < min_cook_temp:
                state = "preheating"
            else:
                state = "heating"
        elif grill_mode in self.cook_modes:
            if self.previous_state == "heating" or self.previous_state == "preheating":
                if current_temp >= target_temp:
                    state = "at_temp"
                else:
                    state = "heating"
            elif self.previous_state == "cooling":
                if current_temp <= target_temp:
                    state = "at_temp"
                else:
                    state = "cooling"
            elif self.previous_state == "at_temp":
                if current_temp > high_temp:
                    state = "over_temp"
                elif current_temp < low_temp:
                    state = "under_temp"
                else:
                    state = "at_temp"
            elif self.previous_state == "under_temp":
                if current_temp > low_temp:
                    state = "at_temp"
                else:
                    state = "under_temp"
            elif self.previous_state == "over_temp":
                if current_temp < high_temp:
                    state = "at_temp"
                else:
                    state = "over_temp"
            # Catch all if coming from idle/unavailable
            else:
                target_changed = True

            if target_changed:
                if current_temp <= target_temp:
                    state = "heating"
                else:
                    state = "cooling"
        elif grill_mode == GRILL_MODE_COOL_DOWN:
            state = "cool_down"
        else:
            state = "idle"

        self.previous_target_temp = target_temp
        self.previous_state = state

        return state


class ProbeState(TraegerBaseSensor):
    """Probe state sensor with enhanced reliability"""

    def __init__(self, client, grill_id, sensor_id):
        # Generate friendlier probe name
        probe_name = (
            f"Probe {sensor_id[-4:]} State"
            if len(sensor_id) > 8
            else f"Probe {sensor_id} State"
        )
        probe_value = (
            f"probe_state_{sensor_id[-4:]}"
            if len(sensor_id) > 8
            else f"probe_state_{sensor_id}"
        )
        super().__init__(client, grill_id, probe_name, probe_value)
        self.sensor_id = sensor_id
        self.grill_accessory = self.client.get_details_for_accessory(
            self.grill_id, self.sensor_id
        )
        self.previous_target_temp = None
        self.probe_alarm = False
        self.active_modes = [
            GRILL_MODE_PREHEATING,
            GRILL_MODE_IGNITING,
            GRILL_MODE_CUSTOM_COOK,
            GRILL_MODE_MANUAL_COOK,
        ]

        # Initialize probe reliability tracking
        if not hasattr(client, "probe_reliability"):
            from .entity import TraegerProbeReliabilityManager

            client.probe_reliability = TraegerProbeReliabilityManager()

        # Tell the Traeger client to call grill_accessory_update() when it gets an update
        self.client.set_callback_for_grill(self.grill_id, self.grill_accessory_update)

    def grill_accessory_update(self):
        """This gets called when the grill has an update. Update state variable"""
        self.grill_refresh_state()
        old_accessory = self.grill_accessory
        self.grill_accessory = self.client.get_details_for_accessory(
            self.grill_id, self.sensor_id
        )

        # Update probe reliability tracking
        if self.grill_accessory is not None:
            is_connected = bool(self.grill_accessory.get("con", 0))
            temperature = self.grill_accessory.get("probe", {}).get("get_temp")

            self.client.probe_reliability.update_probe_connection(
                self.sensor_id, is_connected, temperature
            )

        if self.hass is None:
            return

        # Tell HA we have an update
        self.schedule_update_ha_state()

    # Generic Properties
    @property
    def available(self):
        """Reports unavailable when the probe is not connected with enhanced reliability"""

        if (
            self.grill_state is None
            or self.grill_state["connected"] == False
            or self.grill_accessory is None
        ):
            # Reset probe alarm if accessory becomes unavailable
            self.probe_alarm = False
            return False

        # Use enhanced availability logic with grace periods
        raw_connected = bool(self.grill_accessory.get("con", 0))

        # Reset probe alarm if accessory is not connected
        if not raw_connected:
            self.probe_alarm = False

        return self.client.probe_reliability.should_show_available(
            self.sensor_id, raw_connected
        )

    @property
    def unique_id(self):
        base_id = self._generate_entity_id_base()
        # Use last 4 chars of sensor_id for readability
        probe_suffix = (
            self.sensor_id[-4:] if len(self.sensor_id) > 8 else self.sensor_id
        )
        return f"{base_id}_probe_state_{probe_suffix}"

    @property
    def icon(self):
        return "mdi:thermometer"

    # Sensor Properties
    @property
    def state(self):
        if self.grill_accessory is None:
            return "idle"

        probe_data = self.grill_accessory.get("probe", {})
        target_temp = probe_data.get("set_temp", 0)
        probe_temp = probe_data.get("get_temp", 0)
        target_changed = target_temp != self.previous_target_temp
        grill_mode = self.grill_state["system_status"]
        fell_out_temp = 102 if self.grill_units == UnitOfTemperature.CELSIUS else 215

        # Enhanced disconnection detection using reliability manager
        reliability_state = self.client.probe_reliability.get_probe_state(
            self.sensor_id
        )

        # Check for multiple disconnection indicators
        is_physically_connected = bool(self.grill_accessory.get("con", 0))
        temp_indicates_disconnection = probe_temp >= fell_out_temp
        has_temp_validation_failures = reliability_state["temp_validation_failures"] > 2

        # Latch probe alarm, reset if target changed or grill leaves active modes
        if probe_data.get("alarm_fired", False):
            self.probe_alarm = True
        elif (target_changed and target_temp != 0) or (
            grill_mode not in self.active_modes
        ):
            self.probe_alarm = False

        # Enhanced fell_out detection
        if temp_indicates_disconnection or (
            not is_physically_connected and has_temp_validation_failures
        ):
            state = "fell_out"
        elif self.probe_alarm:
            state = "at_temp"
        elif target_temp != 0 and grill_mode in self.active_modes:
            close_temp = 3 if self.grill_units == UnitOfTemperature.CELSIUS else 5
            if probe_temp + close_temp >= target_temp:
                state = "close"
            else:
                state = "set"
        else:
            self.probe_alarm = False
            state = "idle"

        self.previous_target_temp = target_temp
        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes with probe reliability info."""
        attributes = super().extra_state_attributes.copy()

        # Add probe reliability information
        if hasattr(self.client, "probe_reliability"):
            reliability_state = self.client.probe_reliability.get_probe_state(
                self.sensor_id
            )
            connection_quality = self.client.probe_reliability.get_connection_quality(
                self.sensor_id
            )

            attributes.update(
                {
                    "connection_quality": connection_quality,
                    "connection_failures": reliability_state["connection_failures"],
                    "consecutive_failures": reliability_state["consecutive_failures"],
                    "temp_validation_failures": reliability_state[
                        "temp_validation_failures"
                    ],
                    "probe_alarm_state": self.probe_alarm,
                }
            )

            # Add raw connection state for debugging
            if self.grill_accessory is not None:
                attributes["raw_connection_state"] = bool(
                    self.grill_accessory.get("con", 0)
                )
                probe_data = self.grill_accessory.get("probe", {})
                attributes["last_valid_temp"] = reliability_state.get("last_valid_temp")
                attributes["probe_temperature"] = probe_data.get("get_temp")

        return attributes
