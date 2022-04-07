# -*- coding: utf-8 -*-
from flask import Flask
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
#import lxml

app = Flask(__name__)

@app.route("/")
def index():
  url = 'https://www.mygov.in/corona-data/covid19-statewise-status/'
  # headers = {
  #   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
  # }
  web = requests.get(url)

  india_web = BeautifulSoup(web.text, 'html.parser')

  main_content = india_web.find('div',{'class':'field-collection-container'})

  trail = main_content.find('div',{'class':'field-items'})
  content = trail.find_all('div',{'class':'content'})

  li = [ ]
  for i in range(0,len(content)):
    all_label = content[i].find_all('div',{'class':'field-label'})
    all_items = content[i].find_all('div',{'class':'field-item even'})
    dict={}
    for j in range(0,len(all_label)):
      dict[all_label[j].string] = all_items[j].string
    li.append(dict)

  data = pd.DataFrame(li)

  data.columns = ['State Name','Total Confirmed','Cured/Discharged/Migrated','Death','State Code','Last Confirmed cases','Last cured Discharged','Last Death','Whatsapp chatbot Url','FB chatbot Url','E-pass Url']
  data[['Total Confirmed','Cured/Discharged/Migrated','Death','State Code','Last Confirmed cases','Last cured Discharged','Last Death']] = data[['Total Confirmed','Cured/Discharged/Migrated','Death','State Code','Last Confirmed cases','Last cured Discharged','Last Death']].astype('int64')

  ## geofile in url
  url = "https://raw.githubusercontent.com/shoukath-ali/Covid-Dashboard-India/main/stateindia.geojson"
  geodata = gpd.read_file(url)

  """#Data Preparation"""

  geodata.columns = ['id','State Code','State Name','geometry']

  geodata.drop(['id','State Code'], axis =1, inplace = True)


  """##Comparing with GeoJson and DataFrame"""
  dstate = data[['State Name']]
  jstate = geodata[['State Name']]

  #Compare
  jstate.merge(dstate,
              how='outer',
              left_on='State Name',
              right_on='State Name')

  mapper = {'Andaman and Nicobar':'Andaman & Nicobar Island',
            'Arunachal Pradesh':'Arunanchal Pradesh',
            'Dadra and Nagar Haveli and Daman and Diu':'Dadara & Nagar Havelli',
            'Delhi':'NCT of Delhi',
            'Jammu and Kashmir':'Jammu & Kashmir','Telengana':'Telangana'}

  data.iloc[:,0] = data.iloc[:, 0].apply(lambda s: mapper[s] if s in mapper.keys() else s)

  data['Active Cases'] = data['Total Confirmed']-(data['Cured/Discharged/Migrated'] + data['Death'])
  data['Last 24hr Cases'] = data['Total Confirmed']-data['Last Confirmed cases']
  data['Last 24hr Cure'] = data['Cured/Discharged/Migrated']-data['Last cured Discharged']
  data['Last 24hr death'] = data['Death']-data['Last Death']

  df = data

  dg = geodata

  """###Combine /merge data"""

  df.set_index('State Name', inplace = True)

  dg.set_index('State Name', inplace = True)

  dg[['Active Cases','Last 24hr Cases','Last 24hr Cure','Last 24hr death']] = df[['Active Cases','Last 24hr Cases','Last 24hr Cure','Last 24hr death']]

  dg.reset_index(inplace = True)


  ##folium
  total = geodata["Active Cases"].max()
  #tiles ='cartodbdark_matter'
  india = folium.Map(location=[20.5,78.9],tiles ='cartodbpositron', zoom_start=5,min_zoom = 3, max_zoom = 6,max_lat =30 , max_lon =100 , min_lat = 10 , min_lon =60, max_bounds = True)

  # create a numpy array of length 6 and has linear spacing from the minimum total immigration to the maximum total immigration
  # threshold_scale = np.linspace(geodata['Active Cases'].min(),
  #                               geodata['Active Cases'].max(),
  #                               6, dtype=int)
  # threshold_scale = threshold_scale.tolist() # change the numpy array to a list
  # threshold_scale[-1] = threshold_scale[-1] + 1

  chloro = folium.Choropleth(
      geo_data=geodata ,
      data=geodata ,
      columns=['State Name', 'Active Cases'] ,
      key_on='properties.State Name' ,
      #threshold_scale=threshold_scale,
      fill_color='YlOrRd' ,
      #bins = [0, 100, 400, 700, 900, 1000, 1200, 1500, total+1],
      bins = [0, 0.02*total, 0.1*total, 0.3*total,0.5*total, 0.7*total,total+1], 
      fill_opacity=0.7 , 
      line_opacity=0.2 ,
      labels ='Total Cases',
      legend_name='Todays Cases',
      highlight = True,
  ).add_to(india)

  chloro.geojson.add_child(folium.features.GeoJsonTooltip(['State Name','Active Cases','Last 24hr Cases','Last 24hr Cure','Last 24hr death']))

  #folium.LayerControl().add_to(india) 
  
  return india._repr_html_()

if __name__ == "__main__":
    app.run()
