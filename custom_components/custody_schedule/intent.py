"""Intents for the Custody Schedule integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent, config_validation as cv
from homeassistant.util import slugify

from .const import DOMAIN, CONF_CHILD_NAME, CONF_CHILD_NAME_DISPLAY

INTENT_WHO_HAS_CHILD = "CustodyWhoHasChild"

async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the custody intents."""
    # Register intent only if not already present to avoid warnings on reloads
    try:
        intent.async_register(hass, CustodyWhoHasChildHandler())
    except intent.IntentError:
        # Already registered, skip
        pass

class CustodyWhoHasChildHandler(intent.IntentHandler):
    """Handler for CustodyWhoHasChild intent."""

    intent_type = INTENT_WHO_HAS_CHILD
    slot_schema = {vol.Required("child_name"): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        child_name_query = slots["child_name"]["value"].lower().strip()
        language = intent_obj.language
        
        hass = intent_obj.hass
        best_match_coordinator = None
        match_display_name = None

        # Iterate over all registered entries for our domain
        for entry_id, entry_data in hass.data.get(DOMAIN, {}).items():
            if not isinstance(entry_data, dict) or "coordinator" not in entry_data:
                continue
            
            entry = hass.config_entries.async_get_entry(entry_id)
            if not entry:
                continue
                
            display_name = (entry.data.get(CONF_CHILD_NAME_DISPLAY) or "").lower()
            slug_name = (entry.data.get(CONF_CHILD_NAME) or "").lower()
            
            if child_name_query in display_name or child_name_query in slug_name or display_name in child_name_query:
                best_match_coordinator = entry_data["coordinator"]
                match_display_name = entry.data.get(CONF_CHILD_NAME_DISPLAY, entry.data.get(CONF_CHILD_NAME))
                break
        
        response = intent_obj.create_response()
        
        if not best_match_coordinator:
            if language == "fr":
                speech = f"Désolé, je ne trouve pas d'enfant nommé {child_name_query} dans votre configuration Custody."
            else:
                speech = f"Sorry, I cannot find a child named {child_name_query} in your Custody configuration."
            response.async_set_speech(speech)
            return response
            
        data = best_match_coordinator.data
        if not data:
            if language == "fr":
                speech = f"Je n'ai pas encore pu calculer la position de {match_display_name}."
            else:
                speech = f"I haven't been able to calculate {match_display_name}'s position yet."
            response.async_set_speech(speech)
            return response
            
        if data.is_present:
            if language == "fr":
                text = f"{match_display_name} est actuellement avec vous."
            else:
                text = f"{match_display_name} is currently with you."
        else:
            if language == "fr":
                text = f"{match_display_name} est actuellement chez l'autre parent."
            else:
                text = f"{match_display_name} is currently with the other parent."
            
        response.async_set_speech(text)
        return response
