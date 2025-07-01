"""Switch platform for Traeger."""

from homeassistant.components.switch import SwitchEntity

from .const import (
    DOMAIN,
    GRILL_MODE_CUSTOM_COOK,
    GRILL_MODE_IGNITING,
)

from .entity import TraegerBaseEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup Switch platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    grills = client.get_grills()
    for grill in grills:
        grill_id = grill["thingName"]

        # Get grill features to conditionally create entities
        grill_features = client.get_features_for_device(grill_id)

        entities_to_add = []

        # Only add Super Smoke entity if supported by the grill
        if grill_features and grill_features.get("super_smoke_enabled") == 1:
            entities_to_add.append(
                TraegerSuperSmokeEntity(
                    client,
                    grill["thingName"],
                    "smoke",
                    "Super Smoke",
                    "mdi:weather-fog",
                    20,
                    21,
                )
            )

        # Always add Keep Warm and Connect entities (no feature detection needed)
        entities_to_add.append(
            TraegerSwitchEntity(
                client, grill["thingName"], "keepwarm", "Keep Warm", "mdi:beach", 18, 19
            )
        )
        entities_to_add.append(
            TraegerConnectEntity(client, grill["thingName"], "connect", "WiFi Connect")
        )

        async_add_devices(entities_to_add)


class TraegerBaseSwitch(SwitchEntity, TraegerBaseEntity):
    def __init__(self, client, grill_id, devname, friendly_name):
        TraegerBaseEntity.__init__(self, client, grill_id)
        self.devname = devname
        self.friendly_name = friendly_name
        self.grill_register_callback()

    # Generic Properties
    @property
    def name(self):
        """Return the name of the switch"""
        return self.friendly_name

    @property
    def unique_id(self):
        base_id = self._generate_entity_id_base()
        return f"{base_id}_{self.devname}"


class TraegerConnectEntity(TraegerBaseSwitch):
    """Traeger Switch class."""

    # Generic Properties
    @property
    def icon(self):
        return "mdi:lan-connect"

    # Switch Properties
    @property
    def is_on(self):
        if self.grill_state is None:
            return 0
        return self.grill_cloudconnect

    # Switch Methods
    async def async_turn_on(self, **kwargs):
        """Set new Switch Val."""
        await self.client.start(1)

    async def async_turn_off(self, **kwargs):
        """Set new Switch Val."""
        await self.client.kill()


class TraegerSwitchEntity(TraegerBaseSwitch):
    """Traeger Switch class."""

    def __init__(
        self, client, grill_id, devname, friendly_name, iconinp, on_cmd, off_cmd
    ):
        super().__init__(client, grill_id, devname, friendly_name)
        self.grill_register_callback()
        self.iconinp = iconinp
        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

    # Generic Properties
    @property
    def icon(self):
        return self.iconinp

    @property
    def available(self):
        if self.grill_state is None:
            return False
        else:
            if (
                GRILL_MODE_IGNITING
                <= self.grill_state["system_status"]
                <= GRILL_MODE_CUSTOM_COOK
            ):
                return True
        return False

    # Switch Properties
    @property
    def is_on(self):
        if self.grill_state is None:
            return 0
        return self.grill_state[self.devname]

    # Switch Methods
    async def async_turn_on(self, **kwargs):
        """Set new Switch Val."""
        if (
            GRILL_MODE_IGNITING
            <= self.grill_state["system_status"]
            <= GRILL_MODE_CUSTOM_COOK
        ):
            await self.client.set_switch(self.grill_id, self.on_cmd)

    async def async_turn_off(self, **kwargs):
        """Set new Switch Val."""
        if (
            GRILL_MODE_IGNITING
            <= self.grill_state["system_status"]
            <= GRILL_MODE_CUSTOM_COOK
        ):
            await self.client.set_switch(self.grill_id, self.off_cmd)


class TraegerSuperSmokeEntity(TraegerSwitchEntity):
    """Traeger Super Smoke Switch class."""

    @property
    def available(self):
        if self.grill_state is None:
            return False
        else:
            if (
                GRILL_MODE_IGNITING
                <= self.grill_state["system_status"]
                <= GRILL_MODE_CUSTOM_COOK
            ):
                return (
                    True if self.grill_features["super_smoke_enabled"] == 1 else False
                )
        return False
