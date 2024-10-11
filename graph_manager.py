import io
import panel as pn
import pandas as pd
import hvplot.pandas
import holoviews as hv
import param
from pathlib import Path

class GraphManager(param.Parameterized):
    
    def __init__(self, **params):
        super().__init__(**params)
        self.plot_pane = pn.pane.HoloViews()
        self.debug_pane = pn.pane.Str()
        self.dataframes = []  # List of (DataFrame, file_name) tuples
        self.combined_plot = None

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
            if "Date-Time (CDT)" in df.columns and "Temperature (°F) " in df.columns:
                plot = df.hvplot(x="Date-Time (CDT)", y="Temperature (°F) ", label=file_name)
                
                if self.combined_plot is None:
                    self.combined_plot = plot  # Initialize with the first plot
                else:
                    self.combined_plot *= plot  # Overlay additional plots
            else:
                self.debug_pane.object = f"Update Plots: DataFrame {file_name} missing required columns."

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

    
    