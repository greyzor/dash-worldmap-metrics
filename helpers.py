"""
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

def create_country_geoloc_dataframe(source):
    """ """
    df_geo = pd.DataFrame(source['features'])
    df_geo['Country'] = df_geo['properties'].apply(lambda d: d['name'])
    df_geo['lng'] = df_geo['geometry'].apply(_extract_lng)
    df_geo['lat'] = df_geo['geometry'].apply(_extract_lat)
    df_geo = df_geo[['Country','lng','lat']]
    df_geo['hover'] = '<div/>hover text here<br>'+df_geo['Country']
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

def compute_country_airquality_scores(source, fpath='./data/air_quality_country.csv'):
    """ """
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
        """ """
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

def build_mapbox_layers_for_countries(source, partitions, colors):
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
            html.Div(
                [
                    html.Div('Exposure to PM25 air pollution for 2015, with data from: www.stateofglobalair.org')
                ],
                style={'min-height':'40px', 'background-color':'white', 'text-align':'center'}
            ),

            ## The Map
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
                                lat=30, #38.72490,
                                lon=-1.67571, #-95.61446,
                            ),
                            pitch=0,
                            zoom=1.5,
                        ),
                        margin=dict(r=0, l=0, t=0, b=0),
                        showlegend=False,
                        height=900 # FIXME
                        # **{'height':'900px','min-height':'300px','max-height':'70vh'}
                    )
                )
            ),]),
        ], className='twelve columns', style={'margin':0}
    )
    return app

def build_mapbox_geo_data(df_geo, text_col='description'):
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


def build_app(app):
    """ """
    ## load: source data
    with open('data/countries.geo.json') as f:
        source = json.load(f)

    df_geo = create_country_geoloc_dataframe(source)
    # partitions = generate_random_country_partitions(source, scale=SCALE)
    (partitions, df_scores) = compute_country_airquality_scores(source, fpath='./data/air_quality_country.csv')

    df_geo = df_geo.merge(df_scores[['Country','Exposure_Mean']])
    df_geo['description'] = df_geo['Country']+'<br>Exposure (mean) to PM25: '+df_geo['Exposure_Mean'].astype(str)

    ## build: map data and layers
    layers = build_mapbox_layers_for_countries(source, partitions, DEFAULT_COLORSCALE)
    data = build_mapbox_geo_data(df_geo, text_col='description')

    ## build: layout
    app = build_app_layout(app, MAPBOX_ACCESS_TOKEN, data, layers)

    ## styling: external
    app.css.append_css({'external_url': 'https://codepen.io/plotly/pen/EQZeaW.css'})

    return app