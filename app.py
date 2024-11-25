import panel as pn
from pathlib import Path
import pandas as pd
import hvplot.pandas
import param
from panel.viewable import Viewer

# Initialize Panel
pn.extension(sizing_mode="stretch_width")

# Folder path to monitor
folder_path = Path('data')


class SidebarWidget(param.Parameterized):
    """
    Widget for file selection in the sidebar. Allows the user to select and load CSV files.
    """

    def __init__(self, folder_path, on_file_selected_callback, **params):
        """
        Initialize SidebarWidget.

        Args:
            folder_path (Path): The directory containing the CSV files.
            on_file_selected_callback (function): Callback to handle file selection.
        """
        super().__init__(**params)
        self.folder_path = folder_path
        self.checkbox = pn.widgets.CheckBoxGroup(
            name='Select Files', options=self.get_files_in_folder())
        self.on_file_selected_callback = on_file_selected_callback
        self.checkbox.param.watch(self.on_checkbox_selection, 'value')
        self.selected_files = set()

    def get_files_in_folder(self):
        """
        Retrieve the list of files in the specified folder.

        Returns:
            List[str]: A list of file names found in the folder.
        """
        return [f.name for f in self.folder_path.iterdir() if f.is_file()]

    def update_checkbox_options(self):
        """
        Update the options in the checkbox widget to reflect the current files in the folder.
        """
        self.checkbox.options = self.get_files_in_folder()

    def on_checkbox_selection(self, event):
        """
        Callback for checkbox selection. Detects selected and unselected files, triggering actions accordingly.

        Args:
            event: Event containing the current selection of files.
        """
        current_selection = event.new
        newly_selected_files = set(
            current_selection) - set(self.selected_files)
        unselected_files = set(self.selected_files) - set(current_selection)

        # Process newly selected and unselected files
        for file_name in newly_selected_files:
            self.on_file_selected_callback(file_name)

        for file_name in unselected_files:
            self.on_file_selected_callback(file_name, unselected=True)

        # Update the stored selection
        self.selected_files = current_selection

    def get_checkbox(self):
        """
        Get the checkbox widget.

        Returns:
            pn.widgets.CheckBoxGroup: The checkbox widget for selecting files.
        """
        return self.checkbox


class GraphControlWidget(param.Parameterized):
    """
    Widget for controlling graph parameters (x-axis, y-axis, plot type, and color).
    This widget applies settings to all active GraphObject instances in GraphManager.
    """
    x_col = pn.widgets.Select(name='X-Axis', options=[])
    y_col = pn.widgets.Select(name='Y-Axis', options=[])
    plot_type = pn.widgets.Select(name='Plot Type', options=[
                                  'line', 'scatter', 'bar', 'area'], value='scatter')
    color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')

    def __init__(self, graph_manager, **params):
        """
        Initialize GraphControlWidget.

        Args:
            graph_manager (GraphManager): Reference to the GraphManager instance to apply controls.
        """
        super().__init__(**params)
        self.graph_manager = graph_manager

        # allows for the x and y axis selectors to update the graphs whenever they change.
        self.x_col.param.watch(self.apply_controls, 'value')
        self.y_col.param.watch(self.apply_controls, 'value')

    def update_common_columns(self):
        """
        Update x_col and y_col options with common columns across all selected files.
        """
        if self.graph_manager.graph_objects:
            # Find common columns across all DataFrames in GraphObjects
            common_columns = set(
                self.graph_manager.graph_objects[0].dataframe.columns)
            for graph_obj in self.graph_manager.graph_objects[1:]:
                common_columns.intersection_update(graph_obj.dataframe.columns)

            # Update x_col and y_col options to the common columns
            common_columns = list(common_columns)
            self.x_col.options = common_columns
            self.y_col.options = common_columns

            # Set defaults if common columns are available
            if common_columns:
                self.x_col.value = common_columns[0]
                self.y_col.value = common_columns[0]

    def apply_controls(self, event=None):
        """
        Apply current control settings (x_col, y_col, plot_type, color) to all GraphObject instances.
        """
        for graph_obj in self.graph_manager.graph_objects:
            graph_obj.set_controls(
                x_col=self.x_col.value,
                y_col=self.y_col.value,
                plot_type=self.plot_type.value,
                color=self.color.value
            )
            graph_obj.update_plot()
        self.graph_manager.update_combined_plot()


class GraphManager(param.Parameterized):
    """
    Manager for multiple GraphObjects, responsible for handling data loading,
    adding/removing graphs, and updating the combined plot.
    """

    def __init__(self, **params):
        """
        Initialize GraphManager.
        """
        super().__init__(**params)
        self.plot_pane = pn.pane.HoloViews()
        self.debug_pane = pn.pane.Str()
        self.graph_objects = []
        self.main_graph_display = pn.Column(self.plot_pane, self.debug_pane)

    def load_csv_file_data(self, file_path):
        """
        Load CSV data from the specified file path.

        Args:
            file_path (Path): Path to the CSV file to load.

        Returns:
            DataFrame: The loaded DataFrame if successful, None otherwise.
        """
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                self.log_error(f"The file {file_path.name} is empty.")
                return None
            return df
        except pd.errors.EmptyDataError:
            self.log_error(
                f"Error: The file {file_path.name} is empty or malformed.")
            return None
        except pd.errors.ParserError as e:
            self.log_error(
                f"Error: Failed to parse the CSV file {file_path.name}. Details: {e}")
            return None
        except Exception as e:
            self.log_error(
                f"An error occurred while processing the file {file_path.name}: {e}")
            return None

    def add_graph_object(self, file_path, graph_control):
        """
        Add a new GraphObject for the specified file and update axis options in the control widget.

        Args:
            file_path (Path): Path to the CSV file to add.
            graph_control (GraphControlWidget): Reference to the control widget for updating options.
        """
        df = self.load_csv_file_data(file_path)
        if df is not None:
            graph_object = GraphObject(
                dataframe=df, file_name=file_path.name, on_update_callback=self.update_combined_plot)
            self.graph_objects.append(graph_object)
            graph_control.update_common_columns()
            graph_control.apply_controls()  # Set up axis options for controls
            self.update_combined_plot()

    def remove_graph_object(self, file_name):
        """
        Remove a GraphObject by file name and update the combined plot.

        Args:
            file_name (str): Name of the file associated with the GraphObject to remove.
        """
        self.graph_objects = [
            graph_obj for graph_obj in self.graph_objects if graph_obj.file_name != file_name]
        self.update_combined_plot()

    def update_combined_plot(self):
        """
        Combine all GraphObject plots and update the main display pane with the combined plot.
        """
        combined_plot = None
        for graph_object in self.graph_objects:
            plot = graph_object.get_hvplot_object()
            if plot is not None:
                combined_plot = plot if combined_plot is None else combined_plot * plot

        if combined_plot is not None:
            self.plot_pane.object = combined_plot
        else:
            self.log_error("No plots to display.")

    def log_error(self, message):
        """
        Log an error message to the debug pane.

        Args:
            message (str): The error message to log.
        """
        if isinstance(self.debug_pane.object, str):
            self.debug_pane.object += f"\n\n---\n\n{message}"
        else:
            self.debug_pane.object = message


class GraphObject(param.Parameterized):
    """
    Represents an individual graph, responsible for loading data and plotting based on control settings.
    """
    dataframe = param.DataFrame()
    file_name = param.String()
    graph_ready = param.Boolean(default=False)
    plot_pane = pn.pane.HoloViews()

    def __init__(self, dataframe, file_name, on_update_callback, **params):
        """
        Initialize GraphObject.

        Args:
            dataframe (DataFrame): The data to plot.
            file_name (str): The name of the associated file.
            on_update_callback (function): Callback to update combined plot in GraphManager.
        """
        super().__init__(**params)
        self.dataframe = dataframe
        self.file_name = file_name
        self.on_update_callback = on_update_callback

    def update_axis_options(self):
        """
        Set the default columns for x and y axes to the first column in the dataframe.
        """
        all_columns = list(self.dataframe.columns)
        self.x_col_default = all_columns[0] if all_columns else None
        self.y_col_default = all_columns[0] if all_columns else None

    def set_controls(self, x_col, y_col, plot_type, color):
        """
        Apply graph control settings.

        Args:
            x_col (str): Column to use as x-axis.
            y_col (str): Column to use as y-axis.
            plot_type (str): Type of plot to generate (line, scatter, etc.).
            color (str): Color for the plot.
        """
        self.x_col = x_col
        self.y_col = y_col
        self.plot_type = plot_type
        self.color = color
        self.graph_ready = bool(x_col and y_col)

    def update_plot(self, event=None):
        """
        Update the plot pane based on the current control settings.

        Args:
            event: Optional event triggering the update.
        """
        if self.dataframe is not None and self.graph_ready:
            try:
                plot = self.dataframe.hvplot(
                    x=self.x_col,
                    y=self.y_col,
                    kind=self.plot_type,
                    color=self.color,
                    title=f"Plot for {self.file_name}",
                    width=600,
                    alpha=0.1
                )
                self.plot_pane.object = plot
            except Exception as e:
                self.log_error(f"Error creating plot: {e}")

    def get_hvplot_object(self):
        """
        Retrieve the current hvplot object from the plot pane.

        Returns:
            The hvplot object if available, None otherwise.
        """
        return self.plot_pane.object if isinstance(self.plot_pane.object, type(None)) else self.plot_pane.object

    def log_error(self, message):
        """
        Log an error specific to this GraphObject's debug pane.

        Args:
            message (str): Error message to display.
        """
        if isinstance(self.debug_pane.object, str):
            self.debug_pane.object += f"\n\n---\n\n{message}"
        else:
            self.debug_pane.object = message


# Initialize GraphManager and Graph Control Widget
graph_manager = GraphManager()
graph_control_widget = GraphControlWidget(graph_manager)

# Define the callback for when a file is selected in the SidebarWidget


def on_file_selected(file_name, unselected=False):
    """
    Callback function for file selection. Adds or removes files from the GraphManager.

    Args:
        file_name (str): Name of the file selected or deselected.
        unselected (bool): Whether the file is being unselected.
    """
    file_path = folder_path / file_name
    if not unselected:
        graph_manager.add_graph_object(file_path, graph_control_widget)
    else:
        graph_manager.remove_graph_object(file_name)


# Initialize Widgets
sidebar_widget = SidebarWidget(
    folder_path=folder_path, on_file_selected_callback=on_file_selected)

# Add periodic callback to refresh the file list every 2 seconds
pn.state.add_periodic_callback(
    sidebar_widget.update_checkbox_options, period=2000)

# Layout the Panel app
sidebar_col = pn.Column(
    pn.pane.Markdown("### File Selector"),
    sidebar_widget.get_checkbox(),
    pn.Column(
        graph_control_widget.x_col,
        graph_control_widget.y_col,
        graph_control_widget.plot_type,
        graph_control_widget.color
    )
)

main_graph_col = pn.Column(
    graph_manager.main_graph_display,
    sizing_mode="stretch_both"
)

# Assemble and serve the full template
template = pn.template.FastListTemplate(
    title="CSV Visualizer",
    sidebar=[sidebar_col],
    main=pn.Row(
        main_graph_col
    )
).servable()
