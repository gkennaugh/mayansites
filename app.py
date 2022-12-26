from dash import Input, Output, State, Dash, dcc, html
import pandas as pd
import geopandas as gpd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import fiona
import shapely
import json
import numpy as np
from bs4 import BeautifulSoup
import requests

external_stylesheets = [dbc.themes.DARKLY]
load_figure_template('DARKLY')

mapbox_access_token = 'pk.eyJ1IjoiYWxpc2hvYmVpcmkiLCJhIjoiY2ozYnM3YTUxMDAxeDMzcGNjbmZyMmplZiJ9.ZjmQ0C2MNs1AzEBC_Syadg'
px.set_mapbox_access_token(mapbox_access_token)

fiona.drvsupport.supported_drivers['KML'] = 'rw'

df = gpd.read_file('Ancient Sites in Mexico.kml', driver='KML')
df2 = gpd.read_file('maya_6000.geojson')
rutatren = gpd.read_file('Ruta+y+estaciones+del+Tren+Maya.geojson')
edjag = pd.read_csv('edjag.csv')

lats = []
lons = []
names = []

for feature, name in zip(rutatren.geometry, rutatren.name):
    if isinstance(feature, shapely.geometry.linestring.LineString):
        linestrings = [feature]
    elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
        linestrings = feature.geoms
    else:
        continue
    for linestring in linestrings:
        x, y = linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        names = np.append(names, [name]*len(y))
        lats = np.append(lats, None)
        lons = np.append(lons, None)
        names = np.append(names, None)
        
stations = rutatren[[type(rutatren['geometry'][x])==shapely.geometry.point.Point for x in range(len(rutatren))]]

#comment out
#from app import app

#comment out
app = Dash(__name__, external_stylesheets=external_stylesheets)

#layout = html.Div([
app.layout = html.Div([
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='mayan_graph1', style={'height':'60vh', 'margin':'10px'}),
            html.Div([
                html.Iframe(id='mayan_yt', width='48%', height='400px', style={'margin':'10px'}),
                #html.Iframe(id='mayan_gmap', width='48%', height='400px', allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture", style={'margin':'10px'})
                html.Div(id='mayan_gmap', style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030', 'width':'48%', 'height':'400px', 'overflow':'scroll'}),
            ], style={'display':'flex', 'width':'100%'})
        ], md=9, lg=9),
        dbc.Col([
            html.Div([
                html.H4('Rank'),
                dcc.RadioItems(id='rank', options=[{'label':i, 'value':i} for i in ['All', '1','2','3','4','5']], value='All', style={'margin':'5px'}),
                html.P(id='mayan-test'),
            ], style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030'}),
            html.Div([
                html.H4('Info'),
                html.H6(id='info_title'),
                dcc.Markdown(id='info'),
            ], style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030'}),
            html.Div([
                html.H4('Subset'),
                dcc.Dropdown(id='mayan_dropdown'),
                html.Div([
                    html.Button('Zoom', id='button', n_clicks_timestamp=0),
                    html.Button('Reset', id='button_reset', n_clicks_timestamp=0),
                    html.Button('Zoom Out', id='button_zoomout', n_clicks_timestamp=0)
                ], style={'display':'flex'}),
            ], style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030'}),
            html.Div(id='mayan_text', style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030', 'maxHeight':'30vh', 'overflow':'scroll'}),
            #html.Div(html.Iframe(id='mayan_plan', width='100%', height='300px'), style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030'}),
            html.Div(id='mayan_plan', style={'padding':'10px', 'margin':'10px', 'backgroundColor':'#303030', 'maxHeight':'30vh', 'overflow':'scroll'}),
        ], md=3, lg=3)
    ])
      
])

@app.callback(
    Output('mayan_graph1', 'figure'),
    [Input('rank', 'value'),
     Input('button', 'n_clicks_timestamp'),
    Input('button_reset', 'n_clicks_timestamp'),
    Input('button_zoomout', 'n_clicks_timestamp')],
    State('mayan_dropdown', 'value')
)
def update_mayan_graph1(v, n1, n2, n3, v2):
    if v == 'All':
        fig = px.scatter_mapbox(df2,lat=df2.geometry.y,lon=df2.geometry.x, zoom=5, color=df2['rank'], size=1/df2['rank'].astype('int'), category_orders={'rank':['1','2','3','4','5']}, hover_name=df2.name, mapbox_style='open-street-map')
        fig.add_trace(px.line_mapbox(lat=lats, lon=lons, hover_name=names).data[0])
        fig.add_trace(px.scatter_mapbox(stations, lat=stations.geometry.y, lon=stations.geometry.x, hover_name=stations.name).data[0])
    else:
        df3 = df2[df2['rank']==v]
        if (n1 > n2) and (n1 > n3):
            lat = df3[df3['name']==v2]['geometry'].y.item()
            lon = df3[df3['name']==v2]['geometry'].x.item()
            fig = px.scatter_mapbox(df3,lat=df3.geometry.y,lon=df3.geometry.x,zoom=15, hover_name=df3.name, color_discrete_sequence=['yellow'], center=dict(lat=lat, lon=lon), mapbox_style='satellite')
        elif (n2 > n1) and (n2 > n3):
            fig = px.scatter_mapbox(df3,lat=df3.geometry.y,lon=df3.geometry.x,zoom=5, hover_name=df3.name, color_discrete_sequence=['yellow'], mapbox_style='open-street-map')
        elif (n3 > n2) and (n3 > n1):
            lat = df3[df3['name']==v2]['geometry'].y.item()
            lon = df3[df3['name']==v2]['geometry'].x.item()
            fig = px.scatter_mapbox(df3,lat=df3.geometry.y,lon=df3.geometry.x,zoom=9, hover_name=df3.name, color_discrete_sequence=['yellow'], center=dict(lat=lat, lon=lon), mapbox_style='open-street-map') 
        else:
            fig = px.scatter_mapbox(df3,lat=df3.geometry.y,lon=df3.geometry.x,zoom=5, hover_name=df3.name, color_discrete_sequence=['yellow'], mapbox_style='open-street-map')
    #    fig.update_layout(mapbox_style="white-bg",
    #        mapbox_layers=[
    #            {
    #                "below": 'traces',
    #                "sourcetype": "raster",
    #                "sourceattribution": "United States Geological Survey",
    #                "source": [
    #                    #"https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
    #                ]
    #            }
    #          ])
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    
    return fig
    
@app.callback(
    [Output('info_title', 'children'),
     Output('info', 'children')],
    [Input('mayan_graph1', 'clickData'),
    Input('rank', 'value'),
    Input('mayan_dropdown', 'value')]
)
def update_info(clicked, v, v2):
    df3 = df2[df2['rank']==v].reset_index(drop=True)
    if clicked is not None:
        return df3['name'][clicked['points'][0]['pointNumber']], df3['desc'][clicked['points'][0]['pointNumber']]
    else:
        return df3[df3['name']==v2]['name'], df3[df3['name']==v2]['desc']
    return df2['name'][clicked['points'][0]['pointNumber']], df2['desc'][clicked['points'][0]['pointNumber']]
    
    
@app.callback(
    Output('mayan_dropdown', 'options'),
    Input('rank', 'value')
)
def update_mayan_dropdown(v):
    if v == 'All':
        df3 = df2
    else:
        df3 = df2[df2['rank']==v].reset_index(drop=True)
    return [{'label':i, 'value':i} for i in df3['name']]

@app.callback(
    [Output('mayan_yt', 'src'),
     Output('mayan-test', 'children')],
    Input('mayan_dropdown', 'value')
)
def update_mayan_yt(v):
    #return 'https://www.youtube.com/@exploradormaya/search?query='+v
    if type(edjag[edjag['link'].str.contains(v.strip(), case=False)]['_follow'].max()) is not float:
        return 'https://www.youtube.com/embed/'+edjag[edjag['link'].str.contains(v.strip(), case=False)]['_follow'].max().split('/')[3].replace('watch?v=', ''), 'https://www.youtube.com/embed/'+edjag[edjag['link'].str.contains(v.strip(), case=False)]['_follow'].max().split('/')[3].replace('watch?v=', '')
    else:
        page = requests.get('https://search.brave.com/search?q=youtube+'+v+'&source=web')
        soup = BeautifulSoup(page.content)
        return 'https://www.youtube.com/embed/'+soup.find_all('a', 'result-header')[0]['href'].split('/')[3].replace('watch?v=', ''), 'https://www.youtube.com/embed/'+soup.find_all('a', 'result-header')[0]['href'].split('/')[3].replace('watch?v=', '')
    

@app.callback(
    Output('mayan_gmap', 'children'),
    Input('mayan_dropdown', 'value')
)
def update_mayan_gmap(v):
    #return 'https://www.google.com/maps/place/zona arqueologica '+v
    page = requests.get('https://search.brave.com/api/images?q=archelogical+zone+'+v).json()
    return html.Div([html.Img(src=page['results'][0]['thumbnail']['src']), html.Img(src=page['results'][1]['thumbnail']['src'])])

@app.callback(
    Output('mayan_text', 'children'),
    Input('mayan_dropdown', 'value')
)
def update_mayan_text(v):
    page = requests.get('https://en.wikipedia.org/wiki/'+v)
    soup = BeautifulSoup(page.content)
    return [x.text for x in soup.find_all('p')]

@app.callback(
    Output('mayan_plan', 'children'),
    Input('mayan_dropdown', 'value')
)
def update_mayan_plan(v):
    #return 'https://duckduckgo.com/?q='+v+'+layout&t=h_&iar=images&iax=images&ia=images'
    page = requests.get('https://search.brave.com/api/images?q=layout'+v).json()
    return html.Div([html.Img(src=page['results'][0]['thumbnail']['src']), html.Img(src=page['results'][1]['thumbnail']['src'])])
    
if __name__ == '__main__':
    app.run_server(debug=True, port=8062)