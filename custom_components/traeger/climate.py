"""Climate platform for Traeger grills"""

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    PRESET_NONE,
)
from homeassistant.components.climate.const import (
    HVACMode,
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE

from .const import (
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
    PROBE_PRESET_MODES,
)

from .entity import TraegerBaseEntity, TraegerGrillMonitor


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup climate platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    grills = client.get_grills()
    for grill in grills:
        grill_id = grill["thingName"]
        async_add_devices([TraegerClimateEntity(client, grill_id, "Grill")])
        TraegerGrillMonitor(
            client, grill_id, async_add_devices, AccessoryTraegerClimateEntity
        )


class TraegerBaseClimate(ClimateEntity, TraegerBaseEntity):
    def __init__(self, client, grill_id, friendly_name):
        super().__init__(client, grill_id)
        self.friendly_name = friendly_name

    # Generic Properties
    @property
    def name(self):
        """Return the name of the climate entity"""
        return self._generate_entity_name(self.friendly_name)

    # Climate Properties
    @property
    def temperature_unit(self):
        if self.grill_units == UnitOfTemperature.CELSIUS:
            return UnitOfTemperature.CELSIUS
        else:
            return UnitOfTemperature.FAHRENHEIT

    @property
    def target_temperature_step(self):
        return 5

    @property
    def supported_features(self):
        """Return the list of supported features for the grill"""
        return ClimateEntityFeature.TARGET_TEMPERATURE


class TraegerClimateEntity(TraegerBaseClimate):
    """Climate entity for Traeger grills"""

    def __init__(self, client, grill_id, friendly_name):
        super().__init__(client, grill_id, friendly_name)
        self.grill_register_callback()

    @property
    def unique_id(self):
        base_id = self._generate_entity_id_base()
        return f"{base_id}_climate"

    @property
    def icon(self):
        return "mdi:grill"

    @property
    def available(self):
        """Reports unavailable when the grill is powered off"""
        if self.grill_state is None:
            return False
        else:
            return self.grill_state["connected"]

    # Climate Properties
    @property
    def current_temperature(self):
        if self.grill_state is None:
            return 0
        return self.grill_state["grill"]

    @property
    def target_temperature(self):
        if self.grill_state is None:
            return 0

        # Return 0 for target temperature when grill is off/idle
        state = self.grill_state["system_status"]
        if state in [
            GRILL_MODE_OFFLINE,
            GRILL_MODE_IDLE,
            GRILL_MODE_SLEEPING,
            GRILL_MODE_SHUTDOWN,
        ]:
            return 0

        return self.grill_state["set"]

    @property
    def max_temp(self):
        if self.grill_limits is None:
            return self.min_temp
        return self.grill_limits["max_grill_temp"]

    @property
    def min_temp(self):
        if self.grill_units == UnitOfTemperature.CELSIUS:
            return GRILL_MIN_TEMP_C
        else:
            return GRILL_MIN_TEMP_F

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self.grill_state is None:
            return HVACMode.OFF

        state = self.grill_state["system_status"]

        if state == GRILL_MODE_COOL_DOWN:
            return HVACMode.COOL
        elif state == GRILL_MODE_CUSTOM_COOK:
            return HVACMode.HEAT
        elif state == GRILL_MODE_MANUAL_COOK:
            return HVACMode.HEAT
        elif state == GRILL_MODE_PREHEATING:
            return HVACMode.HEAT
        elif state == GRILL_MODE_IGNITING:
            return HVACMode.HEAT
        elif state == GRILL_MODE_IDLE:
            return HVACMode.OFF
        elif state == GRILL_MODE_SLEEPING:
            return HVACMode.OFF
        elif state == GRILL_MODE_OFFLINE:
            return HVACMode.OFF
        elif state == GRILL_MODE_SHUTDOWN:
            return HVACMode.OFF
        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.HEAT, HVACMode.OFF, HVACMode.COOL]

    # Climate Methods
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        await self.client.set_temperature(self.grill_id, round(temperature))

    async def async_set_hvac_mode(self, hvac_mode):
        """Start grill shutdown sequence"""
        if hvac_mode == HVACMode.OFF or hvac_mode == HVACMode.COOL:
            await self.client.shutdown_grill(self.grill_id)


class AccessoryTraegerClimateEntity(TraegerBaseClimate):
    """Climate entity for Traeger grills"""

    def __init__(self, client, grill_id, sensor_id):
        # Generate friendlier probe name
        probe_name = (
            f"Probe {sensor_id[-4:]}" if len(sensor_id) > 8 else f"Probe {sensor_id}"
        )
        super().__init__(client, grill_id, probe_name)
        self.sensor_id = sensor_id
        self.grill_accessory = self.client.get_details_for_accessory(
            self.grill_id, self.sensor_id
        )
        self.current_preset_mode = PRESET_NONE

        # Tell the Traeger client to call grill_accessory_update() when it gets an update
        self.client.set_callback_for_grill(self.grill_id, self.grill_accessory_update)

    def grill_accessory_update(self):
        """This gets called when the grill has an update. Update state variable"""
        self.grill_refresh_state()
        self.grill_accessory = self.client.get_details_for_accessory(
            self.grill_id, self.sensor_id
        )

        if self.hass is None:
            return

        # Tell HA we have an update
        self.schedule_update_ha_state()

    # Generic Properties
    @property
    def available(self):
        """Reports unavailable when the grill is powered off"""
        if (
            self.grill_state is None
            or self.grill_state["connected"] == False
            or self.grill_accessory is None
        ):
            return False
        else:
            return self.grill_accessory["con"]

    @property
    def unique_id(self):
        base_id = self._generate_entity_id_base()
        # Use last 4 chars of sensor_id for readability
        probe_suffix = (
            self.sensor_id[-4:] if len(self.sensor_id) > 8 else self.sensor_id
        )
        return f"{base_id}_probe_{probe_suffix}"

    @property
    def icon(self):
        return "mdi:thermometer"

    # Climate Properties
    @property
    def current_temperature(self):
        if self.grill_accessory is None:
            return 0
        return self.grill_accessory["probe"]["get_temp"]

    @property
    def target_temperature(self):
        if self.grill_accessory is None:
            return 0
        return self.grill_accessory["probe"]["set_temp"]

    @property
    def max_temp(self):
        # this was the max the traeger would let me set
        if self.grill_units == UnitOfTemperature.CELSIUS:
            return 100
        else:
            return 215

    @property
    def min_temp(self):
        # this was the min the traeger would let me set
        if self.grill_units == UnitOfTemperature.CELSIUS:
            return 27
        else:
            return 80

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self.grill_state is None:
            return HVACMode.OFF

        state = self.grill_accessory["con"]

        if state == 1:  # Probe Connected
            return HVACMode.HEAT
        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return (HVACMode.HEAT, HVACMode.OFF)

    @property
    def preset_mode(self):
        if (
            self.grill_state is None
            or self.grill_state["probe_con"] == 0
            or self.target_temperature == 0
        ):
            # Reset current preset mode
            self.current_preset_mode = PRESET_NONE

        return self.current_preset_mode

    @property
    def preset_modes(self):
        return list(PROBE_PRESET_MODES.keys())

    @property
    def supported_features(self):
        """Return the list of supported features for the grill"""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )

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
                }
            )

            # Add raw connection state for debugging
            if self.grill_accessory is not None:
                attributes["raw_connection_state"] = bool(
                    self.grill_accessory.get("con", 0)
                )

        return attributes

    # Climate Methods
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature with backup."""
        self.current_preset_mode = PRESET_NONE
        temperature = kwargs.get(ATTR_TEMPERATURE)
        rounded_temp = round(temperature)

        # Backup the target temperature for persistence
        self.client.probe_reliability.backup_target_temperature(
            self.sensor_id, rounded_temp
        )

        await self.client.set_probe_temperature(self.grill_id, rounded_temp)

    async def _restore_target_temperature(self, target_temp):
        """Restore target temperature after reconnection"""
        try:
            await self.client.set_probe_temperature(self.grill_id, round(target_temp))
        except Exception as e:
            import logging

            _LOGGER = logging.getLogger(__name__)
            _LOGGER.warning(
                f"Failed to restore probe {self.sensor_id} target temperature: {e}"
            )

    async def async_set_hvac_mode(self, hvac_mode):
        """Start grill shutdown sequence"""
        if hvac_mode == HVACMode.OFF or hvac_mode == HVACMode.COOL:
            hvac_mode = hvac_mode
            # await self.client.shutdown_grill(self.grill_id)

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode with backup"""
        self.current_preset_mode = preset_mode
        temperature = PROBE_PRESET_MODES[preset_mode][self.grill_units]
        rounded_temp = round(temperature)

        # Backup the preset temperature for persistence
        self.client.probe_reliability.backup_target_temperature(
            self.sensor_id, rounded_temp
        )

        await self.client.set_probe_temperature(self.grill_id, rounded_temp)
