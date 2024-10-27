import io
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv
import param
from panel.viewable import Viewer
from pathlib import Path

class AxisSelector(param.Parameterized):
    x_axis = pn.widgets.Select(name='X-Axis', options=[])
    y_axis = pn.widgets.MultiSelect(name='Y-Axis', options=[])
    
    @param.depends('x_axis', 'y_axis', watch=True)
    def update_axis_options(self):
        if not self.dataframe.empty:
            # Get all columns in the DataFrame
            all_columns = list(self.dataframe.columns)
            
            # Update options based on the current selection
            # If x_axis is selected, exclude it from y_axis options and vice versa
            self.param.x_axis.objects = [col for col in all_columns if col != self.y_axis]
            self.param.y_axis.objects = [col for col in all_columns if col != self.x_axis]
            
            # Set default values if current selections are invalid
            if self.x_axis not in self.param.x_axis.objects:
                self.x_axis = self.param.x_axis.objects[0]
            if self.y_axis not in self.param.y_axis.objects:
                self.y_axis = self.param.y_axis.objects[0]

class GraphObject(Viewer, param.Parameterized):
    datetime_selector = pn.widgets.Select(name="Select Datetime Column", options=[])
    x_col = pn.widgets.Select(name='X-Axis', options=[])
    y_col = pn.widgets.Select(name='Y-Axis', options=[])
    plot_type = pn.widgets.Select(name='Plot Type', options=['line', 'scatter', 'bar', 'area'])
    color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')
    plot_pane = pn.pane.HoloViews()
    
    def __init__(self, **params):
        super().__init__()
        
        self._layout = pn.Column(
            self.plot_pane,
            pn.Row(
                self.x_col, 
                self.y_col,
                self.plot_type,
                self.color
            )
        )
        self.error_msg = ""
    
    def load_csv_file_data(self, file_path):
        # Check if the file exists before attempting to read it
        if not file_path.exists():
            self.error_msg += f"\r\n GraphObject.load_csv_file_data: File not found: {file_path}"
            return None
        
        if file_path.suffix != '.csv':
            self.error_msg += f"\r\n GraphObject.load_csv_file_data: Unsupported file type. Please select a CSV file."
            return None
        
        try: 
            self.dataframe = pd.read_csv(file_path)
                
            if self.dataframe.empty:
                self.error_msg += f"\r\n GraphObject.load_csv_file_data: The file {file_path.name} is empty."
                return None
            
            self.graph_editor.datetime_selector.options = self.dataframe.columns.tolist()
           
            return self.dataframe
        except pd.errors.EmptyDataError:
            self.error_msg += f"\r\n GraphObject.load_csv_file_data: Error: The file is empty or malformed."
            return None
        except pd.errors.ParserError as e:
            self.error_msg += f"l\r\n GraphObject.load_csv_file_data: Failed to parse the CSV file. Details: {e}"
            return None
        except Exception as e:
            self.error_msg += f"\r\n GraphObject.load_csv_file_data: An error occurred while processing the file: {e}"
            return None
    
    @param.depends("y_col")
    def set_y_axis(self):
        if self.dataframe.
        pass
    
    @param.depends("x_col")
    def set_x_axis(self, axis_name):
        pass
    
    def plot_graph(self):
        if self.dataframe is not None:
            self.plot_pane = self.dataframe.hvplot(
                x=self.dataframe.columns[0], 
                y="Temperature (°F) ", 
                label=file_name)  # Default x-axis
        else:
            raise RuntimeError(f"GraphObject: {self.name} has no data to graph")
    
    def get_hvplot_object(self):
        return self.plot_pane
    
    def combine_graph_objects(self, another_graph_object):
        pass
    
    def set_color(self):
        pass
    
    def set_plot_type(self):
        pass
    
    def set_datetime_column(self):
        pass
    
    def __panel__(self):
        return self._layout
    
    def get_error_msg(self):
        return self.error_msg