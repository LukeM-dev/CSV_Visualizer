import io
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv
import param
from pathlib import Path

from widgets import GraphEditWidget

class GraphManager(param.Parameterized):
    
    def __init__(self, **params):
        super().__init__(**params)
        self.plot_pane = pn.pane.HoloViews()
        self.debug_pane = pn.pane.Str()
        self.dataframes = []  # List of (DataFrame, file_name) tuples
        self.combined_plot = None
        
        self.graph_editor = GraphEditWidget()
        self.graph_editor.datetime_selector.param.watch(self.on_datetime_column_selected, 'value')
        self.selected_datetime_column = ""
        
    def on_datetime_column_selected(self, event):
        """
        Callback when the user selects a datetime column. Converts the selected column to datetime.
        """
        self.selected_datetime_column = event.new  # Get the new selected column name
        
        self.convert_column_to_datetime_format(selected_column=self.selected_datetime_column)

        # Update the plot to reflect the new datetime column
        self.update_combined_plot()    

    def convert_column_to_datetime_format(self, selected_column):
        for idx, (df, file_name) in enumerate(self.dataframes):
            if selected_column in df.columns:
                # Convert the selected column to datetime
                df[selected_column] = pd.to_datetime(df[selected_column], errors='coerce')
                self.debug_pane.object = f"Converted {selected_column} to datetime for file: {file_name}"
                self.datetime_column_selected = True
            else:
                self.debug_pane.object = f"{selected_column} not found in DataFrame for {file_name}"
                self.datetime_column_selected = True

    def load_csv_file_data(self, file_path):
        # Check if the file exists before attempting to read it
        if not file_path.exists():
            self.debug_pane.object = f"load_csv: File not found: {file_path}"
            return None
        
        if file_path.suffix != '.csv':
            self.debug_pane.object = "load_csv: Unsupported file type. Please select a CSV file."
            return None
        
        try: 
            df = pd.read_csv(file_path)
                
            if df.empty:
                self.debug_pane.object = f"The file {file_path.name} is empty."
                return None
            
            self.graph_editor.datetime_selector.options = df.columns.tolist()
           
            return df
        except pd.errors.EmptyDataError:
            self.debug_pane.object = "load_csv: Error: The file is empty or malformed."
            return None
        except pd.errors.ParserError as e:
            self.debug_pane.object = f"load_csv: Error: Failed to parse the CSV file. Details: {e}"
            return None
        except Exception as e:
            self.debug_pane.object = f"load_csv: An error occurred while processing the file: {e}"
            return None

    def plot_file(self, file_path: Path, unselected=False):
        """
        Handles both selection and unselection of files.
        """
        if unselected:
            # Remove the DataFrame for the unselected file
            self.dataframes = [df for df in self.dataframes if df[1] != file_path.name]
            self.update_combined_plot()
            return
        
        df = self.load_csv_file_data(file_path)

        if df is not None:
            # Add the DataFrame and file name to the dataframes list
            self.dataframes.append((df, file_path.name))
            self.update_combined_plot()

    def update_combined_plot(self):
        """
        Rebuilds the combined plot with the current list of DataFrames.
        """
        self.combined_plot = None  # Reset the combined plot

        for idx, (df, file_name) in enumerate(self.dataframes):
            # Check that the required columns exist
            datetime_col = self.graph_editor.datetime_selector.value
            
            if self.selected_datetime_column is not "":
                self.convert_column_to_datetime_format(self.selected_datetime_column)
            else: 
                self.debug_pane.object = f"update combined plot: Error: could not convert datetime column"

            if datetime_col and datetime_col in df.columns:
                plot = df.hvplot(x=datetime_col, y="Temperature (°F) ", label=file_name)
            else:
                plot = df.hvplot(x=df.columns[0], y="Temperature (°F) ", label=file_name)  # Default x-axis

                
            if self.combined_plot is None:
                self.combined_plot = plot  # Initialize with the first plot
            else:
                self.combined_plot *= plot  # Overlay additional plots

        #if self.combined_plot is not None and self.combined_plot is not type(str):
        #    self.plot_pane.object = self.combined_plot.opts(
        #        title="Combined Plot",
        #        xlabel="Date-Time (CDT) ",
        #        ylabel="Temperature (°F)",
        #        #legend_position="top_left"
        #    )
        #else:
        #    self.debug_pane.object.join("test")# = "\n Update Plots: No valid plots to display."
        
        # Debug info: number of dataframes being plotted
        if self.combined_plot is not None and self.combined_plot is not type(str):
            self.plot_pane.object = self.combined_plot
        print(f'Update Plots: Now showing plots for {len(self.dataframes)} dataframes')

    
    