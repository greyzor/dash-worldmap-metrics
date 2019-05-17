"""
"""

## globals: FIXME: load from conf
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiamFja3AiLCJhIjoidGpzN0lXVSJ9.7YK6eRwUNFwd3ODZff6JvA"
N_BINS = 10
SCALE = 100
# _palette = sns.light_palette((5, 90, 55), N_BINS, input="husl")
# DEFAULT_COLORSCALE = _palette.as_hex()
DEFAULT_COLORSCALE = [
    u'#fee7ec', u'#fdd3dd', u'#fcbfcd', u'#fbabbd', u'#fb97ae',
    u'#fa839e', u'#f96f8f', u'#f85b7f', u'#f7476f', u'#f63360'
]
DEFAULT_OPACITY = 0.8

## export:
__all__ = [
	'MAPBOX_ACCESS_TOKEN',
	'N_BINS',
	'SCALE',
	'DEFAULT_COLORSCALE',
	'DEFAULT_OPACITY'
]