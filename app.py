# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# import dash_colorscales
# import cufflinks as cf
import pandas as pd
import numpy as np
import re
import json
import seaborn as sns

## globals: FIXME: load from conf
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiamFja3AiLCJhIjoidGpzN0lXVSJ9.7YK6eRwUNFwd3ODZff6JvA"
N_BINS = 10
SCALE = 100
_palette = sns.light_palette((5, 90, 55), N_BINS, input="husl")
DEFAULT_COLORSCALE = _palette.as_hex()
# cm = dict(zip(BINS, DEFAULT_COLORSCALE))
DEFAULT_OPACITY = 0.8

## helpers:
def _extract_lng(d):
    """ """
    if d['type'] == 'Polygon':
        return np.mean([item[0] for item in d['coordinates'][0]])
    return np.mean([item[0] for item in d['coordinates'][0][0]])

def _extract_lat(d):
    """ """
    if d['type'] == 'Polygon':
        return np.mean([item[1] for item in d['coordinates'][0]])
    return np.mean([item[1] for item in d['coordinates'][0][0]])

def build_country_geoloc_dataframe(source):
    """ """
    df_geo = pd.DataFrame(source['features'])
    df_geo['country'] = df_geo['properties'].apply(lambda d: d['name'])
    df_geo['lng'] = df_geo['geometry'].apply(_extract_lng)
    df_geo['lat'] = df_geo['geometry'].apply(_extract_lat)
    df_geo = df_geo[['country','lng','lat']]
    df_geo['hover'] = '<div/>hover text here<br>'+df_geo['country']
    return df_geo

def generate_random_country_partitions(source, scale=SCALE):
    """ """
    global N_BINS

    data = [(d['properties']['name'], d['id']) for d in source['features']]
    df = pd.DataFrame(data)
    df['count'] = (np.random.rand(df.shape[0])*scale).astype(int)
    # return df

    df['bin'] = (df['count']/N_BINS).astype(int)
    partitions = df.groupby('bin')[0].apply(list).to_json()
    partitions = json.loads(partitions)
    return partitions

def build_layers_for_countries(source, partitions, colors):
    """ """
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
            opacity=DEFAULT_OPACITY
        )
        layers.append(layer)

    return layers


def build_app_layout(app, mapbox_access_token, data, layers):
    """ """
    app.layout = html.Div(children=[

        html.Div([
            html.H4(
                'Ecological World Panel // World Information Hot Countries',
                style={'text-align':'left'}
            ),
            dcc.Graph(
                id='countries-map',
                figure=dict(
                    data=data,
                    layout=dict(
                        mapbox=dict(
                            layers=layers,
                            accesstoken=mapbox_access_token,
                            style='mapbox://styles/mapbox/satellite-v8',
                            center=dict(
                                lat=38.72490,
                                lon=-95.61446,
                            ),
                            pitch=0,
                            zoom=1.5,
                        ),
                        margin=dict(r=0, l=0, t=0, b=0),
                        showlegend=False,
                        height=900 # FIXME
                    )
                )
            ),]),
        ], className='twelve columns', style={'margin':0}
    )
    return app

def build_geo_data(df_geo, text_col='country'):
    """ """
    data = [
        dict(
            lat=df_geo['lat'],
            lon=df_geo['lng'],
            text=df_geo[text_col],
            type='scattermapbox',
            hoverinfo='text',
            selected = dict(marker = dict(opacity=1)),
            unselected = dict(marker = dict(opacity = 0)),
            mode='markers+text',
            marker=dict(size=25, color='white', opacity=0.2),
        )
    ]
    return data


if __name__ == '__main__':
    """ """
    global SCALE
    global DEFAULT_COLORSCALE
    global MAPBOX_ACCESS_TOKEN

    ## init:
    app = dash.Dash(__name__)

    ## load: source data
    with open('data/countries.geo.json') as f:
        source = json.load(f)

    df_geo = build_country_geoloc_dataframe(source)
    partitions = generate_random_country_partitions(source, scale=SCALE)

    ## build: map data and layers
    layers = build_layers_for_countries(source, partitions, DEFAULT_COLORSCALE)
    data = build_geo_data(df_geo, text_col='country')

    ## build: layout
    app = build_app_layout(app, MAPBOX_ACCESS_TOKEN, data, layers)

    ## styling: external
    app.css.append_css({'external_url': 'https://codepen.io/plotly/pen/EQZeaW.css'})

    ## app: run
    app.run_server(debug=True)