"""
All configuration is here.
"""

## globals: FIXME: load from conf
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiamFja3AiLCJhIjoidGpzN0lXVSJ9.7YK6eRwUNFwd3ODZff6JvA"
N_BINS = 10
SCALE = 100
# _palette = sns.light_palette((5, 90, 55), N_BINS, input="husl")
# DEFAULT_COLORSCALE = _palette.as_hex()
DEFAULT_COLORSCALE = [
	'#e8f6f8', '#fce5e7', '#f9cdd2', '#f7b4bb', '#f49ca6', '#f1848f', '#ef6c7a', '#ec5363', '#e93b4e', '#e72338'
]
DEFAULT_OPACITY = 0.8

VALUE_TO_MAPBOX_STYLE = {
    'default': 'light',
    'custom': 'mapbox://styles/mapbox/satellite-v8'
}

## export:
__all__ = [
	'MAPBOX_ACCESS_TOKEN',
	'N_BINS',
	'SCALE',
	'DEFAULT_COLORSCALE',
	'DEFAULT_OPACITY',
	'VALUE_TO_MAPBOX_STYLE'
]