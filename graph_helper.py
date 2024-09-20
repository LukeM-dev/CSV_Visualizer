# External Packages
import io
import panel as pn
import pandas as pd
import numpy as np
import hvplot.pandas

# Internal Imports
from dataframe_loader import DataFrameLoader as loader
from pandas_helper import PandasHelper as helper

class GraphHelper():

    PRIMARY_COLOR = "#0072B5"
    SECONDARY_COLOR = "#B54300"

    def __init__(self, upload: pn.widgets.FileInput):
        self.file_upload = upload

    def load_csv(self, file_path: str):
        return pd.read_csv(file_path)  

    # Create a function to update the graph based on user settings
    def update_graph(self, data, x_col, y_col, plot_type, color):
        return data.hvplot(x=x_col, y=y_col, kind=plot_type, color=color) 

    def add_data(self, event, upload: pn.widgets.FileInput):
        b = io.BytesIO()
        upload.save(b)
        b.seek(0)
        name = '.'.join(upload.filename.split('.')[:-1])
    
    @pn.cache
    def get_data(self, csv_filepath):
        return pd.read_csv(csv_filepath, parse_dates=["date"], index_col="date")

    def explore(self, csv):
        df = pd.read_csv(csv)
        explorer = hvplot.explorer(df)
        def plot_code(**kwargs):
            code = f'```python\n{explorer.plot_code()}\n```'
            return pn.pane.Markdown(code, sizing_mode='stretch_width')
        return pn.Column(
            explorer,
            '**Code**:',
            pn.bind(plot_code, **explorer.param.objects())
        )
    
    def transform_data(self, variable, window, sigma):
        """Calculates the rolling average and identifies outliers"""
        avg = data[variable].rolling(window=window).mean()
        residual = data[variable] - avg
        std = residual.rolling(window=window).std()
        outliers = np.abs(residual) > std * sigma
        return avg, avg[outliers]


    def get_plot(self, variable="Temperature", window=30, sigma=10):
        """Plots the rolling average and the outliers"""
        avg, highlight = self.transform_data(variable, window, sigma)
        return avg.hvplot(
            height=300, legend=False, color=self.PRIMARY_COLOR
        ) * highlight.hvplot.scatter(color=self.SECONDARY_COLOR, padding=0.1, legend=False)


    
    