import pandas as pd
import hvplot.pandas
import panel as pn
import io
import time

from dataframe_loader import DataFrameLoader as df_loader
from custom_widgets import SidebarWidget, GraphWidget

from data_manager import DataManager

# Initialize Panel
pn.extension(sizing_mode="stretch_width", design="material")

# Bring in DataManager to handle multiple dataframes easily
data_manager = DataManager()

# Bring in sidebar widgets
sidebar_widgets = SidebarWidget()
graph_widget = GraphWidget()

def get_data():
    pass

def load_data(event):
    # Load data from the uploaded file
    print(f"file_input value: {sidebar_widgets.file_input.filename}")
    # Read the file content into a DataFrame if it's uploaded
    loader = df_loader()            
    file_data_dataframe = loader.convert_to_dataframe(file_data=sidebar_widgets.file_input.value)
    
    file_key = loader.find_associated_logger_location(sidebar_widgets.file_input.filename)
    print(f"file key: {file_key}")
    data_manager.add_df(file_key, file_data_dataframe)
    data_manager.convert_datetime_column(file_key, "Date-Time (CDT)")
    #data_manager.set_column_as_index(file_key, "#")
    print(file_data_dataframe.head())

    graph_widget.setup_graph(data_manager.get_df(file_key))
    #graph_widget.update_graph_visuals()


# Attach the function to the button click event
sidebar_widgets.file_input.param.watch(load_data, 'value')

widget_column = pn.Column(
    sidebar_widgets.file_input
)

graph_options_column = pn.Column(
    graph_widget.x_col,
    graph_widget.y_col,
    pn.Row(graph_widget.plot_type, graph_widget.color)
)

graph_display = pn.bind(graph_widget.update_graph_visuals, 
                    x_col=graph_widget.x_col, 
                    y_col=graph_widget.y_col, 
                    plot_type=graph_widget.plot_type, 
                    color=graph_widget.color)

app = pn.template.MaterialTemplate(
    site="panel",
    title="CSV Visualizer",
    sidebar=[widget_column, graph_options_column],
    main=[graph_display]
)

app.servable()