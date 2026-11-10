"""Plateforme button : bouton « Appairer » (apprentissage) des recepteurs.

Envoie la trame d'apprentissage Edisio (``09 <MID> 1F000010``) avec le MID lu
dans le modele du recepteur. Evite le piege du MID par defaut : les
micro-modules s'apparient en MID ``01``, le rail DIN en ``05``, etc.

Avec la passerelle RFPlayer, les volets recoivent en plus deux boutons
« Appairer montee » / « Appairer descente » (un par sortie du recepteur).
"""
from __future__ import annotations

from collections import defaultdict

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import rfplayer
from .const import CONF_NAME, DOMAIN, DONGLE_RFPLAYER
from .entity import EdisioReceiver, model_emitter_mid


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    gw = hass.data[DOMAIN][entry.entry_id]
    by_sub: dict[str | None, list[ButtonEntity]] = defaultdict(list)
    for sub_id, data in EdisioReceiver.receiver_modules(entry):
        by_sub[sub_id].append(EdisioLearnButton(gw, data))
    if gw.dongle == DONGLE_RFPLAYER:
        # RFPlayer uniquement : un volet s'appaire sortie par sortie, avec sa
        # propre trame de pilotage (cf. RFPlayerCoverLearnButton).
        for sub_id, devs in EdisioReceiver.groups_for(entry, "cover"):
            for dev in devs:
                by_sub[sub_id].extend(
                    RFPlayerCoverLearnButton(gw, dev, output)
                    for output in rfplayer.COVER_LEARN_OUTPUTS
                )
    for sub_id, buttons in by_sub.items():
        async_add_entities(buttons, config_subentry_id=sub_id)


class EdisioLearnButton(EdisioReceiver, ButtonEntity):
    """Bouton d'apprentissage : appaire le module a l'emetteur (virtuel) Edisio."""

    _attr_icon = "mdi:link-variant-plus"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, gw, dev):
        super().__init__(gw, dev)
        base = dev[CONF_NAME].rsplit(" C", 1)[0]
        self._attr_name = f"{base} — Appairer"
        self._attr_unique_id = f"{DOMAIN}_{self._id}_learn"
        self._mid = model_emitter_mid(self._model)

    async def async_press(self) -> None:
        # Module en apprentissage (LED clignotante) -> il memorise cet emetteur.
        # Route selon le dongle : trame Edisio brute ou commande ASSOC RFPlayer.
        await self._gateway.async_learn(self._id, self._mid)


class RFPlayerCoverLearnButton(EdisioReceiver, ButtonEntity):
    """RFPlayer : fait apprendre a UNE sortie d'un volet sa trame de pilotage.

    En mode volet, un recepteur Edisio s'appaire sortie par sortie (EMV-400 :
    1 appui sur « R » = sortie 1 / montee, 2 appuis = sortie 2 / descente) et
    chaque sortie memorise la commande qu'elle recoit alors. Le bouton
    « Appairer » (ASSOC, meme trame pour les deux sorties) ne suffit donc pas :
    ces deux boutons emettent la commande exacte de montee / de descente.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _LABELS = {
        "up": ("Appairer montée", "mdi:arrow-up-bold-box-outline"),
        "down": ("Appairer descente", "mdi:arrow-down-bold-box-outline"),
    }

    def __init__(self, gw, dev, output: str):
        super().__init__(gw, dev)
        self._output = output
        label, self._attr_icon = self._LABELS[output]
        self._attr_name = f"{dev[CONF_NAME]} — {label}"
        self._attr_unique_id = (
            f"{DOMAIN}_{self._id}_{self._channel}_learn_{output}"
        )

    async def async_press(self) -> None:
        await self._gateway.async_learn_cover_output(
            self._id, self._channel, self._output
        )
