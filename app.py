import pandas as pd
import hvplot.pandas
import panel as pn
import io
import time

from dataframe_loader import DataFrameLoader as df_loader
from custom_widgets import SidebarWidget as sidebar

# Initialize Panel
pn.extension(sizing_mode="stretch_width", design="material")

# Create a function to update the graph based on user settings
def update_graph(data, x_col, y_col, plot_type, color):
    if x_col and y_col and plot_type:
        return data.hvplot(x=x_col, y=y_col, kind=plot_type, color=color)
    return None

# Widgets for user input
# Bring in sidebar widgets
sidebar_widgets = sidebar()
#global file_data_dataframe

#file_input = pn.widgets.FileInput(name="Upload CSV File")
x_col = pn.widgets.Select(name='X-Axis', options=[])
y_col = pn.widgets.Select(name='Y-Axis', options=[])
plot_type = pn.widgets.Select(name='Plot Type', options=['line', 'scatter', 'bar', 'area'])
color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')
#plot_button = pn.widgets.Button(name='Plot Graph', button_type='primary')  # Button to trigger graphing
#load_data_button = pn.widgets.Button(name='Load CSV', button_type='primary')
# Placeholder for the graph
graph_area = pn.pane.HoloViews()

def load_data_on_click(event):
    # Load data from the uploaded file
    print(f"file_input value: {sidebar_widgets.file_input.filename}")
    # Read the file content into a DataFrame if it's uploaded
    loader = df_loader()            
    global file_data_dataframe
    file_data_dataframe = loader.convert_to_dataframe(file_data=sidebar_widgets.file_input.value)
    print(file_data_dataframe.head())

# Function to be called when button is clicked
def on_plot_click(event):
    print(f"Plotting Initialized: {file_data_dataframe.empty}, {file_data_dataframe.columns}")
    # Update x_col and y_col options when the file is uploaded
    if not file_data_dataframe.empty and 'Error' not in file_data_dataframe.columns:
        print("Plotting Continues! File data is not empty and has no errors")
        x_col.options = list(file_data_dataframe.columns)
        y_col.options = list(file_data_dataframe.columns)
        # Plot the graph and update the graph area
        print("Plotting Data Now")
        graph = update_graph(file_data_dataframe, x_col.value, y_col.value, plot_type.value, color.value)
        print("Generated Plot, Serving to GUI now")
        graph_area = graph

#bound_plot = pn.bind(update_graph,
#                     data=file_data_dataframe,
#                     x_col=x_col,
#                     y_col=y_col,
#                     plot_type=plot_type,
#                     color=color)

# Attach the function to the button click event
sidebar_widgets.plot_button.on_click(on_plot_click)
sidebar_widgets.load_data_button.on_click(load_data_on_click)

# Layout the app
#app = pn.Column(
#    file_input,
#    pn.Row(x_col, y_col, plot_type, color),
#    load_data_button,
#    plot_button,
#    graph_area
#)

pn.template.MaterialTemplate(
    site="Panel",
    title="CSV Visualizer",
    sidebar=[pn.Column(sidebar_widgets.file_input,
                       sidebar_widgets.load_data_button,
                       sidebar_widgets.plot_button)],
    main=[graph_area]
).servable()

