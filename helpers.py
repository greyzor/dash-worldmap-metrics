"""
Precomputing, App Layout (Layers/Markers), Callbacks helpers.
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# import dash_colorscales
# import cufflinks as cf
import pandas as pd
import numpy as np
import re
import json
import dash_dangerously_set_inner_html

from conf import *
from colors import (
    _color_from_bin,
    _opacity_from_bin,
    _border_color_from_bin
)

## helpers:
def _extract_lng(arr):
    """ Extract average longitude from array of geo-coordinates in format: (lng,lat)"""
    return np.mean([item[0] for item in arr[0]])

def _extract_lat(arr):
    """ Extract average latitude from array of geo-coordinates in format: (lng,lat)"""
    return np.mean([item[1] for item in arr[0]])

def create_country_geoloc_dataframe(source):
    """Create geolocation Dataframe from source raw data.

    :param source: raw source data.
    :type source: dict.

    :returns: a geolocation DataFrame.
    :rtype: pd.DataFrame
    """
    df_geo = pd.DataFrame(source['features'])
    df_geo['Country'] = df_geo['properties'].apply(lambda d: d['name'])

    ## For each polygon in MultiPolygon, explode into a new row.
    df_geo['geo_type'] = df_geo['geometry'].apply(lambda d: d['type'])
    df_geo['coord'] = df_geo['geometry'].apply(lambda d: d['coordinates'])
    df_geo = df_geo[['type','geo_type','Country','coord']]
    x = df_geo[df_geo.geo_type=='MultiPolygon']['coord'].apply(pd.Series)
    x = x.merge(df_geo, left_index=True, right_index=True).drop('coord',axis=1).melt(id_vars=['type', 'geo_type','Country'], value_name = "coord")
    x = x.dropna().sort_values(['Country','variable'])

    ## Merge new exploded MultiPolygon with non-exploded Polygon
    df_geo[df_geo.geo_type=='Polygon']['variable'] = 0
    df_geo = pd.concat([x,df_geo[df_geo.geo_type=='Polygon']]).sort_values(['Country','variable'])

    ## Compute geo-coordinates
    df_geo['lng'] = df_geo['coord'].apply(_extract_lng)
    df_geo['lat'] = df_geo['coord'].apply(_extract_lat)

    df_geo = df_geo[['Country','lng','lat']]
    return df_geo

def generate_random_country_partitions(source, scale=SCALE):
    """Create random country partitions from source raw data.

    :param source: raw source data.
    :type source: dict.

    :returns: a partitions of countries.
    :rtype: dict of partitions, each key is the bin idx,
            each value is the list of countries for the bin.
    """
    global N_BINS

    data = [(d['properties']['name'], d['id']) for d in source['features']]
    df = pd.DataFrame(data)
    df['count'] = (np.random.rand(df.shape[0])*scale).astype(int)
    # return df

    df['bin'] = (df['count']/N_BINS).astype(int)
    partitions = df.groupby('bin')[0].apply(list).to_json()
    partitions = json.loads(partitions)
    return partitions

def compute_country_airquality_scores(source, fpath='./data/air_quality_country.csv'):
    """Compute Air Quality scores from source raw data.

    :param source: raw source data.
    :type source: dict.
    :param fpath: data file path.
    :type fpath: str

    :returns: a partitions of countries, and dataframe of scores
    :rtype: tuple (dict of partitions, pd.DataFrame of bin scores per country)
    """
    ## Countries list
    all_countries = [d['properties']['name'] for d in source['features']]

    ## Air quality data
    df = pd.read_csv(fpath, sep=',')
    df_latest = df[df.Year==2015]

    ## Cleanify data
    mapping = {
        'Guinea-Bissau': 'Guinea Bissau',
        "Cote d'Ivoire": 'Ivory Coast',
        'Serbia': 'Republic of Serbia',
        'Congo': 'Republic of the Congo',
        'Russian Federation': 'Russia',
        'Tanzania': 'United Republic of Tanzania',
        'United States': 'United States of America',
    }
    def replace_country_name(x):
        """ Replace country name by its mapping using dict. """
        if x in mapping.keys():
            return mapping[x]
        return x

    df_latest['Country'] = df_latest['Type'].apply(replace_country_name)

    ## Merge list of countries with Normalized Air quality estimate
    df_final = pd.DataFrame(all_countries, columns=['Country']).merge(df_latest[['Country', 'Exposure_Mean']])
    scaler = np.max(df_latest['Exposure_Mean'])*1.05
    df_final['Exposure_Norm'] = (100*df_final['Exposure_Mean']/scaler).astype(int)

    df_final['bin'] = (df_final['Exposure_Norm']/N_BINS).astype(int)
    partitions = df_final.groupby('bin')['Country'].apply(list).to_json()
    partitions = json.loads(partitions)
    return (partitions, df_final)

def build_mapbox_layers_for_countries(source, partitions, colors, layer_border_colors='white'):
    """Build Mapbox layers struct.

    :param source: raw source data.
    :type source: dict.
    :param partitions: dict of partitions, key is bin, value is list of countries for bin.
    :type partitions: dict[list]
    :param colors: list of colors, one per layer.
    :type colors: list[str]
    :param layer_border_colors: borders color per layer.
    :type layer_border_colors: list[str] or str

    :returns: Mapbox layers inner struct.
    :rtype: list[dict], each dict being an inner map layer.
    """
    first_symbol_id = None

    layers = []
    for _bin in partitions.keys():
        countries = partitions[_bin]

        _source = {}
        _source.setdefault('type', source['type'])
        _source['features'] = filter(
            lambda d: d['properties']['name'] in countries,
            source['features']
        )

        layer = dict(
            sourcetype='geojson',
            source=_source,
            type='fill',
            color=colors[int(_bin)],
            opacity=DEFAULT_OPACITY,
            # below="water"
            # below="state-label-sm",
            # below="mapbox"
        )
        layers.append(layer)

        layer = dict(
            sourcetype='geojson',
            source=_source,
            type='line',
            color=layer_border_colors[int(_bin)],
            opacity=1.0,
        )
        layers.append(layer)

    return layers

def build_app_layout(app, data, layers, mapbox_access_token, default_style_value='custom'):
    """Build Application Layout.

    :param app: dash app.
    :type app: dash.dash.Dash
    :param data: mapbox data inner struct.
    :type data: list[dict]
    :param layers: mapbox layers inner struct.
    :type layers: list[dict], each dict being an inner map layer.
    :param mapbox_access_token: mapbox access token.
    :type mapbox_access_token: str
    :param default_style_value: default style.
    :type default_style_value: str.

    :returns: app object with layout field updated.
    :rtype: dash.dash.Dash
    """
    ## Main layout
    app.layout = html.Div(children=[

        html.Div([
            ## Header
            html.Div(
                [
                    html.H4(
                        'World Map Metrics',
                        style={'text-align':'center', 'display':'inline-block', 'margin':'20px 0px 20px 40px'}
                    ),
                    html.Div(
                        # [
                        #     dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
                        #         <a class="github-button" href="https://github.com/greyzor/dash-worldmap-metrics" data-size="large" data-show-count="true" aria-label="Star greyzor/dash-worldmap-metrics on GitHub">Star</a>
                        #     ''')
                        # ],
                        html.A(
                            html.Button('Show on Github!'),
                            href='https://github.com/greyzor/dash-worldmap-metrics',
                            target='_blank'
                        ),
                        style={'float':'right', 'background-color':'white', 'margin':'20px 40px 20px 0px'},
                    )
                ],
                style={'background-color':'#e51b79', 'color':'white'}
            ),

            ## Inputs and selection dropdowns
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Dropdown(
                                id='metric-1-dropdown',
                                options=[
                                    {'label': 'PM25 pollution exposure', 'value': 'PM25'},
                                    {'label': 'Other metric', 'value': 'OTHER'},
                                ],
                                value='PM25',
                            ),
                        ],
                        className='three columns'
                    ),
                    html.Div(
                        'Exposure to PM25 air pollution for 2015, with data from: www.stateofglobalair.org',
                        className='six columns',
                        style={'font-weight':'bold', 'font-size':'16px'}
                    ),
                    html.Div(
                        dcc.Dropdown(
                            id='map-style-selector',
                            options=[
                                {'label': 'Style: Default', 'value': 'default'},
                                {'label': 'Style: Custom', 'value': 'custom'},
                            ],
                            value=default_style_value,
                        ),
                        className='three columns'
                    ),
                ],
                style={'background-color':'white', 'text-align':'center', 'padding':'1.5rem'},
                className='row'
            ),

            ## The Map
            dcc.Graph(
                id='world-map',
                figure=build_map_figure(
                    data,
                    None,
                    mapbox_access_token,
                    DEFAULT_COLORSCALE,
                    map_style=VALUE_TO_MAPBOX_STYLE[default_style_value]
                ),
                style={'height':'80vh'}
            ),
        ], style={'height':'100%'}),
    ], className='twelve columns', style={'margin':0, 'height':'98vh', 'background-color':'white'})
    return app

def build_mapbox_geo_data(df_geo, text_col='description', markers=None):
    """Build Mapbox geolocation inner data struct.

    :param df_geo: a geolocation DataFrame.
    :type df_geo: pd.DataFrame
    :param text_col: column name for text.
    :type text_col: str
    :param markers: markers to be displayed on map.
    :type markers: dict

    :returns: mapbox data inner struct.
    :rtype: list[dict]
    """
    data = [
        dict(
            lat=df_geo['lat'],
            lon=df_geo['lng'],
            text=df_geo[text_col],
            type='scattermapbox',
            hoverinfo='text',
            selected = dict(marker = dict(opacity=1)),
            unselected = dict(marker = dict(opacity = 0)),
            # mode='markers+text',
            mode='markers+text',
            marker=markers,
        )
    ]
    return data


def build_map_figure(data, layers, mapbox_access_token, annot_colors, map_style='light'):
    """Build Mapbox figure.

    :param data: mapbox data inner struct.
    :type data: list[dict]
    :param layers: mapbox layers inner struct.
    :type layers: list[dict], each dict being an inner map layer.
    :param mapbox_access_token: mapbox access token.
    :type mapbox_access_token: str
    :param annot_colors: annotation colors used to show a legend.
    :type annot_colors: list
    :param map_style: default map style.
    :type map_style: str.

    :returns: dash dcc.Graph figure field.
    :rtype: dict
    """
    annotations = None
    if layers is not None and len(layers) > 0:
        annotations = [dict(
            showarrow=False,
            align='right',
            text='<b>PM25 level ranges:</b>',
            x=0.975,
            y=0.95,
            bgcolor='white'
        )]

        for k, color in enumerate(annot_colors):
            annotations.append(
                dict(
                    arrowcolor = color,
                    text='range: %s-%s'%(10*k, 10*(k+1)),
                    x = 0.975,
                    y = 0.90-0.3*k/N_BINS,
                    ax = -90,
                    ay = 0,
                    arrowwidth=12,
                    arrowhead=0,
                    bgcolor = '#EFEFEE'
                )
            )

    return dict(
        data=data,
        layout=dict(
            mapbox=dict(
                layers=layers,
                accesstoken=mapbox_access_token,
                style=map_style,
                center=dict(
                    lat=30, #38.72490,
                    lon=-1.67571, #-95.61446,
                ),
                pitch=0,
                zoom=1.5,
            ),
            annotations=annotations,
            margin=dict(r=0, l=0, t=0, b=0),
            showlegend=False,
            # **{'height':'900px','min-height':'300px','max-height':'70vh'}
        )
    )

def build_app(app):
    """From default dash.dash.Dash application, return build and customized app."""
    ## load: source data
    with open('data/countries.geo.json') as f:
        source = json.load(f)

    df_geo = create_country_geoloc_dataframe(source)
    # partitions = generate_random_country_partitions(source, scale=SCALE)
    (partitions, df_scores) = compute_country_airquality_scores(source, fpath='./data/air_quality_country.csv')

    df_geo = df_geo.merge(df_scores[['Country','Exposure_Mean', 'bin']])
    df_geo['description'] = df_geo['Country']+': '+df_geo['Exposure_Mean'].astype(str)

    ## colors for markers (one per country), and borders (one color per layer)
    marker_colors = df_geo['bin'].apply(lambda idx: _color_from_bin(idx, N_BINS))
    layer_border_colors = [_border_color_from_bin(int(_bin), N_BINS) for _bin in partitions.keys()]

    markers = dict(
        size=25,
        color=marker_colors,
        # opacity=df_geo['bin'].apply(lambda idx: _opacity_from_bin(idx, N_BINS))
        opacity=1.
    )

    ## build: map data and layers
    layers = build_mapbox_layers_for_countries(
        source, partitions, DEFAULT_COLORSCALE,
        layer_border_colors=layer_border_colors
    )
    data = build_mapbox_geo_data(df_geo, text_col='description', markers=markers)

    ## build: layout
    app = build_app_layout(app, data, layers, MAPBOX_ACCESS_TOKEN, default_style_value='custom')

    ## styling: external
    app.css.append_css({'external_url': 'https://codepen.io/plotly/pen/EQZeaW.css'})

    ## callbacks
    def _change_map_style_callback(value):
        """ Callback to change map style, according to value."""
        map_style = VALUE_TO_MAPBOX_STYLE[value]

        return build_map_figure(
            data,
            layers,
            MAPBOX_ACCESS_TOKEN,
            DEFAULT_COLORSCALE,
            map_style=map_style
        )

    app.callback(
        Output('world-map', 'figure'),
        [Input('map-style-selector', 'value')]
    )(_change_map_style_callback)

    return app