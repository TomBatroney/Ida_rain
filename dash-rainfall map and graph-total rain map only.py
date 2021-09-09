#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

# In[2]:


data_path = r"/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/20210831/202108310005-202109011910.csv" #https://www.fs.usda.gov/rds/archive/Catalog/RDS-2017-0017
rain_data = pd.read_csv(data_path,index_col='Grids')
rain_data.head()


# In[3]:


rain_data = rain_data.transpose().reset_index()
rain_data.rename(columns={"index": "date_time"},inplace=True)
rain_data['date_time'] = rain_data['date_time'].map(lambda x: x.rstrip('EDT')) #change to EST if EST 
rain_data['date_time'] =  pd.to_datetime(rain_data['date_time'], infer_datetime_format=True)
#df.rename(index={'Grids': ''}, inplace=True)
rain_data.set_index('date_time',inplace=True)
rain_data.head()


# In[4]:


cumrain = rain_data.apply(lambda x: x.cumsum())
#cumrain = cumrain.add_suffix('_cum')
cumrain.tail()


# In[5]:


df = rain_data.stack().reset_index()
df.rename(columns={"Grids": "grid_cell", 0: "rain_inches"},inplace=True)
df.tail()


# In[6]:


df_cum = cumrain.stack().reset_index()
df_cum.rename(columns={"Grids": "grid_cell", 0: "cumrain_inches"},inplace=True)
df_cum.tail()


# In[7]:


#total rainfall by grid cell
df_sum = df.groupby(['grid_cell'])[['rain_inches']].sum()
df_sum.reset_index(inplace=True)
df_sum.head()


# In[8]:


#read in grid cells shapefile and export to geojson
grid_cells = gpd.read_file("/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/_BaseGIS/1km-grid_3RWW_BaseFile.shp").to_crs(epsg=3857)
grid_cells.rename(columns={"PIXEL": "grid_cell"},inplace=True)
grid_cells['grid_cell'] = grid_cells['grid_cell'].astype(int)
grid_cells = grid_cells.drop(['RNP_ID','ConeSilenc','PIXEL2','TOTRAIN_IN'],axis=1)
grid_cells.to_file("/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/_BaseGIS/grid_cells.geojson", driver='GeoJSON')


# In[9]:


geo_df_sum = gpd.read_file("/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/_BaseGIS/grid_cells.geojson")
geo_df_sum = geo_df_sum.to_crs("EPSG:4326")
geo_df_sum = geo_df_sum.merge(df_sum, on="grid_cell")
dff_sum = geo_df_sum.set_index("grid_cell")
dff_sum.head()


# In[10]:


geo_df_time = gpd.read_file("/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/_BaseGIS/grid_cells.geojson")
geo_df_time = geo_df_time.to_crs("EPSG:4326")
geo_df_time = geo_df_time.merge(df, on="grid_cell")
geo_df_time.tail()


# In[11]:


geo_df_cum = gpd.read_file("/Users/thomasbatroney/Desktop/Python/_3rwwAnimation/_BaseGIS/grid_cells.geojson")
geo_df_cum = geo_df_cum.to_crs("EPSG:4326")
geo_df_cum = geo_df_cum.merge(df_cum, on="grid_cell")
geo_df_cum.tail()


# In[12]:


dff_sum = geo_df_sum.set_index("grid_cell")
dff_sum.head()


# In[17]:


fig = px.choropleth_mapbox(dff_sum, geojson=dff_sum.geometry, locations=dff_sum.index, color='rain_inches',
                           color_continuous_scale="temps",
                           mapbox_style="open-street-map",
                           zoom=8.75, center = {"lat": 40.44, "lon": -79.99},
                           opacity=0.70,
                           labels={'rain_inches':'rainfall inches'},
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()


# In[18]:


app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
# App layout
app.layout = dbc.Container([
    
    dbc.Row(
        dbc.Col(html.Br(),
                width=12),
    ),
    
    dbc.Row(
        dbc.Col(html.H1("Tropical Storm Ida Rainfall Data Dashboard", 
                className='text center text-primary mb-4'),
                width=12),
    ),
    
    dbc.Row(
        dbc.Col(html.Br(),
                width=12),

    
    ),
    
    dbc.Row(
        dbc.Col(dcc.Graph(
                id='my_rain_map', figure=fig,
                ),width=12),
    ),
    
    dbc.Row(
        dbc.Col(html.Br(),
                width=12),
    ),
        
    dbc.Row(
        dbc.Col(dcc.Dropdown(
                id='my-dpdn', multi=True, value=[115132,116132],
                         options=[{'label':x, 'value':x}
                                  for x in sorted(df['grid_cell'].unique())],
                         ),width=12),
    ),
    
    dbc.Row(
        dbc.Col(html.Br(),
                width=12),
    ),
    
    dbc.Row(
        dbc.Col(dcc.Graph(
                id='line-fig1', figure={},
                ), width=12),
    ),
    
    dbc.Row(
        dbc.Col(html.Br(),
                width=12),
    ),
    
    dbc.Row(
        dbc.Col(dcc.Graph(
                id='line-fig2', figure={},
                ), width=12),
    ),

])


# In[19]:


# Connect the Plotly graphs with Dash Components

#line graph 
@app.callback(
    Output('line-fig1', 'figure',),
    Input('my-dpdn', 'value')
)
def update_graph1(value):
    dff_cum = geo_df_cum[geo_df_cum['grid_cell'].isin(value)]
    figln1 = px.line(dff_cum, x='date_time', y='cumrain_inches', color='grid_cell')
    return figln1

#line graph 
@app.callback(
    Output('line-fig2', 'figure',),
    Input('my-dpdn', 'value')
)

def update_graph2(value):
    dff_time = geo_df_time[geo_df_time['grid_cell'].isin(value)]
    figln2 = px.line(dff_time, x='date_time', y='rain_inches', color='grid_cell')
    return figln2


# In[ ]:


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)


# In[ ]:




