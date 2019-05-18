"""
Color helpers.
"""
def _color_from_bin(bin, n_bins):
    """ """
    if n_bins <= 0:
        return 'white'
    ratio = bin/float(n_bins)
    if ratio <= 0.2:
        return '#6fdba5'
    elif ratio <= 0.3:
        return 'orange'
    elif ratio <= 0.5:
        # return DEFAULT_COLORSCALE[bin]
        return 'red'
    return 'red'

def _opacity_from_bin(bin, n_bins):
    """ """
    if n_bins <= 0:
        return 0.35
    ratio = bin/float(n_bins)
    if ratio < 0.2:
        return 0.6
    elif ratio < 0.3:
        return 0.85
    elif ratio < 0.5:
        return 1.0
    return 1.0

def _border_color_from_bin(bin, n_bins):
    """ """
    if n_bins <= 0:
        return 'grey'
    ratio = bin/float(n_bins)
    if ratio <= 0.3:
        return 'grey'
    elif ratio <= 0.5:
        return 'black'
    return 'black'