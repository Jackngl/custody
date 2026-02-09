import aiohttp

def async_get_clientsession(hass):
    return aiohttp.ClientSession()
