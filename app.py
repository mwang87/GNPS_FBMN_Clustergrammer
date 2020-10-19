import dash_clustergrammer
import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from flask import Flask, send_from_directory

import json


external_scripts = [
    {'src': 'https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js'}
]
external_stylesheets = [{"external_url": 'custom.css'}, dbc.themes.BOOTSTRAP]
    
server = Flask(__name__)

app = dash.Dash(
    __name__,
    server=server, 
    external_scripts=external_scripts,
    external_stylesheets=external_stylesheets
)
server = app.server

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS FBMN Clustergram Dashboard", href="#")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DASHBOARD = [
    dcc.Location(id='url', refresh=False),
    html.Link(
        rel='stylesheet',
        href='./static/custom.css'
    ),

    #html.Div(id='version', children="Version - 0.1"),
    html.Div(id="cgram-component")
]

BODY = html.Div(
    [
        dbc.Row(DASHBOARD, style={"marginTop": 0, "marginLeft": 50}),
    ],
)

app.layout = html.Div(children=[BODY], style={"height": "80%"})


# Loading data from GNPS
def _get_quant_df(task):
    remote_url = "https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&file=quantification_table_reformatted/".format(task)
    df = pd.read_csv(remote_url, sep=",")
    df = df.dropna(how='all', axis='columns')
    df.index = df["row ID"]
    df = df.drop(["row ID", "row m/z", "row retention time"], axis=1)

    print(df.head())
    for column in df.columns:
        if "row" in column:
            continue
        print(column)
        df[column] = df[column] / df[column].max()

    from clustergrammer2 import Network
    import json
    net = Network()
    net.load_df(df)

    # calculate clustering using default parameters
    net.cluster()

    return json.loads(net.export_net_json())



@app.callback(
    [Output('cgram-component', 'children')],
    [Input('url', 'pathname')])
def update_output(pathname):
    if pathname is not None and len(pathname) > 1:
        task = pathname[1:]
    else:
        task = "c3bdf3a172f9482bb734857640e1781b"

    network_data = _get_quant_df(task)

    cgram_fig = dash_clustergrammer.DashClustergrammer(
        id='cgram-component',
        label='Clustergrammer Dash Component',
        network_data=network_data,
    )

    return [[cgram_fig]]

@app.server.route('/static/<path>')
def static_file(path):
    import os
    from flask import send_from_directory
    static_folder = os.path.join(os.getcwd(), 'static')
    return send_from_directory(static_folder, path)

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=5000, debug=True)
