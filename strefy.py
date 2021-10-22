# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
import pandas as pd
import numpy as np
import geopandas as gpd
#from collections import OrderedDict
from datetime import datetime
#from shapely.geometry import Point
from shapely import wkt
#from scipy.spatial import cKDTree
import os
#import psycopg2 as pg
#import seaborn as sns
#import matplotlib.pyplot as plt
import requests
from shapely.geometry import Point
from shapely.geometry import Polygon
import json
import shapely.wkt
from datetime import datetime
from re import search
#import branca
import time, random
from streamlit_folium import folium_static
import folium
import fsspec

st.title('Wyznaczanie potencjału strefy dojazdu')

city = ('Trojmiasto', 'Krakow', 'Warszawa')
mode_list = ('car', 'pedestrian')
mode_list2 = ('shortest', 'fastest')
selected_city = st.selectbox('Wybierz miasto', city)
st.text('Aby uzyskać poprawne, wyniki podane poniżej współrzędne muszą znajdować się we wybranym mieście.')
lons = st.number_input('Podaj długość geo. np. 18.345690', min_value= 13.9, max_value= 23.9, format="%.6f")

lats = st.number_input('Podaj szerokość geo. np. 52.179028', min_value= 45.9, max_value= 55.9, format="%.6f")

mode1 = st.selectbox('Wybierz sposób przemieszczania', mode_list)

mode2 = st.selectbox('Wybierz ', mode_list2)

range1 = st.slider('Odległość w metrach', min_value=0,max_value=4000,step=100)

#https://github.com/smykpython/odleglosci/blob/main/
#https://raw.githubusercontent.com/smykpython/odleglosci/main/data/Krakow.csv
#C:\Users\smykra\Documents\python_scripts\DARK_STORE\POTENCJAL\
#https://zabkapolskasa-my.sharepoint.com/personal/smyk_rafal_zabka_pl/Documents/DARK_STORE/data/Trojmiasto.csv

@st.cache
def load_data(x):
    dane = pd.read_csv(r"https://raw.githubusercontent.com/smykpython/odleglosci/main/data/" + x +"1.csv", delimiter=',' , encoding='utf8')
    locit2020_geo = gpd.GeoDataFrame(dane, geometry=gpd.points_from_xy(dane.LON, dane.LAT), crs = 'epsg:4326')
    return dane, locit2020_geo

def lat(x):
    l = x.rfind(',')
    y = x[:l]
    return y

def lon(x):
    l = x.rfind(',')
    y = x[l+1:]
    return y

if lons >14 and lats>46 and range1 > 100:
    data_load_state = st.text('OK')
    st.write(lats, lons)
    data_load_state = st.text('Pobieranie danych...')
    data_locit, locit_geo = load_data(selected_city)
    data_load_state.text('Dane pobrane')
    #if st.checkbox('Pokaż dane'):
     #   #st.subheader('Dane')
      #  st.write(data_locit.head(5))  
   
    rangetype ='distance'
    #mode1 = 'fastest'
    #mode1 = 'shortest'
    #mode2 = 'car'
    #mode2 = 'pedestrian' #6km/h to 1500m = 900s
    #range1= 2000 # w metrach
    #range1= 60 # w sekundach
    postep = 0
    poligony_izo = {}

    pkt = str(lats)+","+str(lons)  #lat #lon
    
    a ="https://isoline.route.ls.hereapi.com/routing/7.2/calculateisoline.json?apiKey=T8ZMw4jnGr25mEZ0fVUh9Zubr9GYGPnhrrMqAwA4JnQ&mode="+mode1+";"+mode2+";traffic:disabled&rangetype="+rangetype+"&start=geo!"+pkt+"&range="+str(range1)
    #print(a)
    
    sleeptime = random.randint(1,2)
    time.sleep(sleeptime)
    try:
        y = requests.get(a)
        #st.text(y)
    except:
        st.text('Bład współrzędnych')
    data = y.json()
    data1 = json.dumps(data, ensure_ascii=False)
    b = json.loads(data1)

    #st.text(b)
    
    try:
        b = b['response']['isoline'][0]['component'][0]['shape']
        lat_list = []
        lon_list = []
        
        for i in b:
            szer = float(lat(i))
            dl = float(lon(i))
            lat_list.append(szer)
            lon_list.append(dl)

        st.text(lat_list)
        st.text(lon_list)
        
        polygon_geom = Polygon(zip(lon_list, lat_list))
        key_id = 1
        poligony_izo[key_id] = polygon_geom

        #st.text(polygon_geom)

        poli_isochron1 = pd.DataFrame.from_dict(poligony_izo, orient='index', columns = ['geometry'])
        poli_isochron = gpd.GeoDataFrame(poli_isochron1, geometry = 'geometry', crs='epsg:4326')
        poli_isochron.reset_index(inplace=True)
        
        st.text(poli_isochron.head(4))

        st.write(locit_geo.head(4))

        locit_3city = gpd.sjoin(locit_geo, poli_isochron[['index','geometry']], how='inner', op='intersects')
        locit_3city_1000 = locit_3city.dissolve(by='index', aggfunc={'POPULACJA': 'sum','POPULACJA_20_44':'sum','LICZBA_GOSPODARSTW': 'sum', 'LICZB_LOKALI_MIESZKALNYCH':'sum'})
        locit_3city_1000.drop(columns=['geometry'], inplace=True)

        st.write(locit_3city_1000.head(2))
        st.write(poli_isochron.head(2))
        poli_isochron2 = poli_isochron.merge(locit_3city_1000, left_on='index', right_on='index', how='left')
    except:
        st.text('Błąd współrzędnych')
       
     #st.write(poli_isochron2[['POPULACJA','POPULACJA_20_44','LICZBA_GOSPODARSTW','LICZB_LOKALI_MIESZKALNYCH']])
#     if st.checkbox('Pokaż dane dla strefy'):
#         #st.subheader('Dane')
#         st.write(poli_isochron2) 
    
    
    # center map
    m = folium.Map(location=[lats, lons], zoom_start=13, tiles=None, control_scale=True)
    
    folium.TileLayer('OpenStreetMap', show=True).add_to(m)
    folium.TileLayer('cartodbpositron',show=False).add_to(m)
    folium.TileLayer('cartodbdark_matter', show=False).add_to(m)
    folium.TileLayer(
        tiles = 'http://services.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Street Map',
        overlay = False, control = True, show= True ).add_to(m)
    folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False, control = True, show= True ).add_to(m)


    
    isodist = range1/1000



    fg = folium.FeatureGroup(name='Lokalizacja', control=True)
    m.add_child(fg)

    fg3 = folium.FeatureGroup(name='Streafa '+str(isodist)+'km', control=True)
    m.add_child(fg3)

    # add marker 
    tooltip = "Wybrana Lokalziaca"
    folium.Marker(
        [lats, lons], popup="Wybrana Lokalizacaj", tooltip=tooltip
    ).add_to(fg)
    
    obszary2 = folium.GeoJson(data = poli_isochron2,  
                             style_function=lambda x: {'weight':0.9,'fillColor': 'green','color': 'black','fillOpacity':0.25},
                        #overlay=False,embed=False,control=False,
                        highlight_function=lambda x: {'weight':0.5,'fillColor': 'grey'},
                               tooltip=folium.GeoJsonTooltip(fields=['POPULACJA','POPULACJA_20_44','LICZBA_GOSPODARSTW','LICZB_LOKALI_MIESZKALNYCH'],
                              labels=True,
                        zoom_on_click=False,sticky=False),
                        show=True).add_to(fg3)
    m.add_child(folium.map.LayerControl(collapsed=False))

    # call to render Folium map in Streamlit
    folium_static(m)
    

else:
    data_load_state = st.text('Czekam na dane...')
