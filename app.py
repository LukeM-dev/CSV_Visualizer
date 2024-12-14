from config import USR_CONFIG, TABLE_NAMES, TABLE_TEMPLATES, ENVIRON_TABLE_LOCATION_MAPPING, CSV_TO_ENVIRON_TABLE_COLUMN_MAP

# Imports from other Local Files
from DatabaseHandler import SqlConnection

# Third Party Libraries to handle using Data
import pandas as pd  # Data Manip Tool
import sqlite3 as db  # Data Storage Tool

# Panel/Holoviz Libraries 
import param
import panel as pn
import hvplot.pandas

pn.extension(sizing_mode="stretch_width")

# First Party Libraries
import os
import datetime 




sql_connection = SqlConnection(USR_CONFIG)
sql_connection.init_connection()

# Example SQL query
query = "SELECT datetime, temp_F FROM EnvironData WHERE location_id = ?"
params = (21611332,)

# Call the method
df = sql_connection.query_to_dataframe(query, params)

# Display the resulting DataFrame
print(df.head())

def convert_to_datetime(datetime_str: str):
    # Parse and format the date-time field
    formatted_date = datetime.datetime.strptime( 
    datetime_str, "%m/%d/%Y %H:%M:%S")
    return formatted_date

if not df.empty:
    df['datetime'] = df['datetime'].apply(convert_to_datetime)
    
print(df.head())
print(df["datetime"].dtype)

df.drop('index', axis=1, inplace=True)

# Interactive widgets
start_date_widget = pn.widgets.DatePicker(
    name="Start Date Picker", value=datetime.datetime(2024, 5, 2)).rx()
end_date_widget = pn.widgets.DatePicker(
    name="End Date Picker", value=datetime.datetime(2024, 7, 26)).rx()

location_key_list = list(ENVIRON_TABLE_LOCATION_MAPPING.keys())
location_select_widget = pn.widgets.MultiChoice(
    name="Location MultiChoice", value=[location_key_list[0]], options=location_key_list).rx()


column_selector = pn.widgets.MultiChoice(
    name="Column MultiChoice",
    options=sql_connection.get_column_names(TABLE_NAMES[0])
).rx()

refresh_button = pn.widgets.Button(
    name='Refresh Button',
    icon='caret-right',
    button_type='primary'
).rx()

displayible_table = pn.widgets.DataFrame(df).rx()

wig_box = pn.WidgetBox()

def load_dataframe_based_on_widget(displayible_table):
    available_cols = df.columns
    
    #for col in available_cols:
        

def temp_avg_temp(df):
    return df.loc[:,'temp'].mean()

mean_temp_rx = pn.rx(temp_avg_temp(df=df))

template = pn.template.FastListTemplate(
    title="CSV Visualizer",
    sidebar=[],
    main=pn.Row(
        column_selector,
        location_select_widget,
        
        refresh_button,
        displayible_table
    )
).servable()
