# -*- coding: utf-8 -*-
import dash
from helpers import build_app

## external scripts
external_scripts = ["https://buttons.github.io/buttons.js"]

## init:
app = dash.Dash(__name__, external_scripts=external_scripts)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

## build:
app = build_app(app)
server = app.server

if __name__ == '__main__':
    """ """
    ## app: run
    app.run_server(host='0.0.0.0', debug=True)