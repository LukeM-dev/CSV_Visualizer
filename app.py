import panel as pn
from pathlib import Path
import pandas as pd
import hvplot.pandas
import param
from panel.viewable import Viewer

# Initialize Panel
pn.extension('tabulator', 'codeeditor', sizing_mode="stretch_width")

# Folder path to monitor
folder_path = Path('data')

class SidebarWidget(param.Parameterized):
    
    def __init__(self, folder_path, on_file_selected_callback, **params):
        super().__init__(**params)
        self.folder_path = folder_path
        self.checkbox = pn.widgets.CheckBoxGroup(name='Select Files', options=self.get_files_in_folder())
        self.on_file_selected_callback = on_file_selected_callback
        self.checkbox.param.watch(self.on_checkbox_selection, 'value')
        self.selected_files = set()
    
    def get_files_in_folder(self):
        return [f.name for f in self.folder_path.iterdir() if f.is_file()]

    def update_checkbox_options(self):
        self.checkbox.options = self.get_files_in_folder()

    def on_checkbox_selection(self, event):
        current_selection = event.new
        newly_selected_files = set(current_selection) - set(self.selected_files)
        unselected_files = set(self.selected_files) - set(current_selection)
        
        for file_name in newly_selected_files:
            self.on_file_selected_callback(file_name)
        
        for file_name in unselected_files:
            self.on_file_selected_callback(file_name, unselected=True)
        
        self.selected_files = current_selection
        
    def get_checkbox(self):
        return self.checkbox
    
class GraphControlWidget(param.Parameterized):
    x_col = pn.widgets.Select(name='X-Axis', options=[])
    y_col = pn.widgets.Select(name='Y-Axis', options=[])
    plot_type = pn.widgets.Select(name='Plot Type', options=['line', 'scatter', 'bar', 'area'], value='scatter')
    color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')
    
    def __init__(self, graph_manager, **params):
        super().__init__(**params)
        self.graph_manager = graph_manager
        
    def update_graphs(self):
        self.graph_manager.update_combined_plot()
        

class GraphManager(param.Parameterized):
    
    def __init__(self, **params):
        super().__init__(**params)
        self.plot_pane = pn.pane.HoloViews()
        self.debug_pane = pn.pane.Str()
        self.graph_objects = []
        
        self.main_graph_display = pn.Column(self.plot_pane, self.debug_pane)

    def load_csv_file_data(self, file_path):
        try: 
            df = pd.read_csv(file_path)
            if df.empty:
                self.log_error(f"The file {file_path.name} is empty.")
                return None
            return df
        except pd.errors.EmptyDataError:
            self.log_error(f"Error: The file {file_path.name} is empty or malformed.")
            return None
        except pd.errors.ParserError as e:
            self.log_error(f"Error: Failed to parse the CSV file {file_path.name}. Details: {e}")
            return None
        except Exception as e:
            self.log_error(f"An error occurred while processing the file {file_path.name}: {e}")
            return None

    def add_graph_object(self, file_path):
        df = self.load_csv_file_data(file_path)
        if df is not None:
            graph_object = GraphObject(dataframe=df, file_name=file_path.name, on_update_callback=self.update_combined_plot)
            self.graph_objects.append(graph_object)
            self.update_combined_plot()

    def remove_graph_object(self, file_name):
        self.graph_objects = [graph_obj for graph_obj in self.graph_objects if graph_obj.file_name != file_name]
        self.update_combined_plot()

    def update_combined_plot(self):
        
        for child_graph in self.graph_objects:
            child_graph.update_plot()
            
        if not all(graph_obj.graph_ready for graph_obj in self.graph_objects):
            # Not all graph objects are ready to be plotted.
            self.log_error("GraphManager.update_combined_plot: Not all graphs are ready")
            return

        combined_plot = None
        for graph_object in self.graph_objects:
            plot = graph_object.get_hvplot_object()
            if plot is not None:
                if combined_plot is None:
                    combined_plot = plot
                else:
                    combined_plot *= plot  # Combine plots

        if combined_plot is not None:
            self.plot_pane.object = combined_plot
        else:
            self.log_error("No plots to display.")

        # Update main_display with each GraphObject's layout
        self.main_display[:] = [self.plot_pane, self.debug_pane] + [obj.plot_pane for obj in self.graph_objects]

    def log_error(self, message):
        if isinstance(self.debug_pane.object, str):
            self.debug_pane.object += f"\n\n---\n\n{message}"
        else:
            self.debug_pane.object = message

class GraphObject(param.Parameterized):
    dataframe = param.DataFrame()
    file_name = param.String()
    graph_ready = param.Boolean(default=False)
    
    plot_pane = pn.pane.HoloViews()
    
    def __init__(self, dataframe, file_name, graph_control, on_update_callback, **params):
        super().__init__(**params)
        self.dataframe = dataframe
        self.file_name = file_name
        self.on_update_callback = on_update_callback
        self.graph_control = graph_control

        self.update_axis_options()

        self.x_col.param.watch(self.graph_control._axis_selection_changed, 'value')
        self.y_col.param.watch(self.graph_control._axis_selection_changed, 'value')
        self.plot_type.param.watch(self.graph_control.update_plot, 'value')
        self.color.param.watch(self.graph_control.update_plot, 'value')

    def update_axis_options(self):
        all_columns = list(self.dataframe.columns)
        self.x_col.options = all_columns
        self.y_col.options = all_columns
        
        # default the parameters to the first column of the csv to have something display.
        self.x_col.value = self.dataframe.columns[0]
        self.y_col.value = self.dataframe.columns[0]

    def _axis_selection_changed(self, event):
        # Check if both x and y axes have been selected
        if self.x_col.value and self.y_col.value:
            self.graph_ready = True
            self.update_plot()
        else:
            self.graph_ready = False
            print(f"GraphObject._axis_selection_changed(), {self.name}, {self.file_name}: graph is not ready")
        
        # Trigger combined plot update if ready
        self.on_update_callback()

    def update_plot(self, event=None):
        if self.dataframe is not None and self.graph_ready:
            try:
                plot = self.dataframe.hvplot(
                    x=self.x_col.value,
                    y=self.y_col.value,
                    kind=self.plot_type.value,
                    color=self.color.value,
                    title=f"Plot for {self.file_name}"
                )
                self.plot_pane.object = plot
            except Exception as e:
                self.plot_pane.object = f"Error creating plot: {e}"

    def get_hvplot_object(self):
        return self.plot_pane.object if isinstance(self.plot_pane.object, type(None)) else self.plot_pane.object

# Initialize GraphManager
graph_manager = GraphManager()

# Define the callback for when a file is selected in the SidebarWidget
def on_file_selected(file_name, unselected=False):
    file_path = folder_path / file_name
    if not unselected:
        graph_manager.add_graph_object(file_path)
    else:
        graph_manager.remove_graph_object(file_name)

# Initialize Widgets
sidebar_widget = SidebarWidget(folder_path=folder_path, on_file_selected_callback=on_file_selected)

graph_control_widget = GraphControlWidget(graph_manager)

# Add periodic callback to refresh the file list every 2 seconds
pn.state.add_periodic_callback(sidebar_widget.update_checkbox_options, period=2000)

# Layout the Panel app
sidebar_col = pn.Column(
    pn.pane.Markdown("### File Selector"),
    sidebar_widget.get_checkbox(), 
    graph_control_widget
)

main_graph_col = pn.Column(
    graph_manager.main_graph_display,
    sizing_mode="stretch_both"
)

template = pn.template.FastListTemplate(
    title="CSV Visualizer",
    sidebar=[sidebar_col],
    main=pn.Row(
        main_graph_col
    )
).servable()
