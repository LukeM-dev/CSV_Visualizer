# Python Std. Library Imports
from pathlib import Path

# Import 3rd Party Modules
import panel as pn
import pandas as pd
import param
import hvplot.pandas


# Initialize Panel, Before Internal Imports because they sometimes use Panel
# Potentially use 'tabulator' and 'codeeditor' extension in the future
pn.extension(sizing_mode="stretch_width")

# Constants Used
ALLOWED_PLOT_TYPES = ['line', 'scatter', 'bar', 'area']

# Folder path to monitor, and Global File Variables
FOLDER_PATH = Path('data')

# Start Helper Methods -----------------------------------------------------------------------------

def selection_in_options(selected, options) -> bool:
    """That the selected option is within the options

    Args:
        selected (str): the selected str option thats is currently selected
        options (list[str]): the list of options that are available to be selected 

    Returns:
        bool: true if the selected option is amoung the options, then True is returned, false is returned otherwise
    """
    for opt in options:
        if selected == opt:
            return True

    return False


def log_error(gm, message) -> None:
    """
    Log an error message to the debug pane.

    Args:
        message (str): The error message to log.
    """
    if isinstance(gm, GraphManager) is False:
        raise RuntimeError(
            "Attempted to log an error, but GraphManager wasn't initialized, or passed into the log_error() method.")

    if isinstance(gm.debug_pane.object, str):
        gm.debug_pane.object += f"\n\n---\n\n{message}"
    else:
        gm.debug_pane.object = message


def get_files_in_folder() -> list[str]:
    """
    Retrieve the list of files in the specified folder.

    Returns:
        List[str]: A list of file names found in the folder.
    """
    return [f.name for f in FOLDER_PATH.iterdir() if f.is_file()]


def load_csv_file(file_path) -> pd.DataFrame:
    """
    Load CSV data from the specified file path.

    Args:
        file_path (Path): Path to the CSV file to load.

    Returns:
        DataFrame: The loaded DataFrame if successful, None otherwise.
    """
    try:
        df = pd.read_csv(file_path)
        # TODO Provide method to modify incoming data for Data Normalization and Operations in separate file.
        return df
    except pd.errors.EmptyDataError as e:
        raise pd.errors.EmptyDataError(
            f"Load CSV Error: The file {file_path.name} is empty or malformed. Details: {e}")
    except pd.errors.ParserError as e:
        raise pd.errors.ParserError(
            f"Load CSV Error: Failed to parse the CSV file {file_path.name}. Details: {e}")
    except Exception as e:
        raise Exception(
            f"Load CSV Error: An error occurred while processing the file {file_path.name}: {e}")


# End Helper Methods -------------------------------------------------------------------------------

# Start Data Structs -------------------------------------------------------------------------------

class GraphManager(param.Parameterized):
    """
    Manager for multiple GraphObjects, responsible for handling data loading,
    adding/removing graphs, and updating the combined plot.
    """

    def __init__(self, graph_control, **params):
        """
        Initialize GraphManager.
        """
        super().__init__(**params)

        # Graph UI elements
        self.plot_pane = pn.pane.HoloViews()
        self.debug_pane = pn.pane.Str()
        self.main_graph_display = pn.Column(self.plot_pane, self.debug_pane)

        # All GraphObjects contained by GraphManager
        self.graph_objects = []

        # GraphControlWidget to provide controls to GraphManagers Combined Graph.
        self.graph_controls: GraphControlWidget = graph_control


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

    def __init__(self, **params):
        """
        Initialize GraphControlWidget.

        Args:
            graph_manager (GraphManager): Reference to the GraphManager instance to apply controls.
        """
        super().__init__(**params)


class FileManager(param.Parameterized):
    """To Hold a Record of the Selected and Unselected Files

    Args:
        param (_type_): _description_
    """
    file_select_checkbox_widget: pn.widgets.CheckBoxGroup

    selected_files: list[str] = []
    unselected_files: list[str] = []

    def __init__(self, on_file_selected_callback, **params):
        """
        Initialize FileManager, and primarily the Widget controlling which datasets are
        added into the graphs or not.

        Args:
            on_file_selected_callback (function): Callback to handle file selection.
        """
        super().__init__(**params)
        self.file_select_checkbox_widget = pn.widgets.CheckBoxGroup(
            name='Select Files', options=get_files_in_folder())

        # No selected files at initialization of File Manager
        self.selected_files = []

        # Update unselected options with all files that exist in the data folder.
        self.unselected_files = get_files_in_folder()

        # setup callback to hit when a new file is selected
        self.callback = on_file_selected_callback

    def init_widget(self) -> None:
        """
        Update the options in the checkbox widget to reflect the current files in the folder.
        """
        self.file_select_checkbox_widget = pn.widgets.CheckBoxGroup(
            name='Select Files', value=self.selected_files, options=get_files_in_folder())


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

    def get_hvplot_object(self):
        """
        Retrieve the current hvplot object from the plot pane.

        Returns:
            The hvplot object if available, None otherwise.
        """
        return self.plot_pane.object if isinstance(self.plot_pane.object, type(None)) else self.plot_pane.object

# End Data Structs ---------------------------------------------------------------------------------

# Start Callback Methods ---------------------------------------------------------------------------


def on_file_selected_callback(event, file_name, unselected=False):
    """
    Callback function for file selection. Adds or removes files from the GraphManager.
    Callback for checkbox selection. Detects selected and unselected files, triggering actions accordingly.

    Args:
        event: Event containing the current selection of files.
        file_name (str): Name of the file selected or deselected.
        unselected (bool): Whether the file is being unselected.
    """

    current_selection = event.new

    newly_selected_files = set(current_selection) - set(selected_files)
    unselected_files = set(selected_files) - set(current_selection)

    return (newly_selected_files, unselected_files)
    
    file_path = FOLDER_PATH / file_name
    if not unselected:
        add_graph_object(graph_manager, file_path, graph_control_widget)
    else:
        remove_graph_object(graph_manager, file_name)


def on_checkbox_selection_callback(event) -> tuple:
    pass

# End Callback Methods -----------------------------------------------------------------------------

# Start Widget Specific Methods --------------------------------------------------------------------


def init_graph_control_widgets(gcw,
                               x_col_selected,
                               x_col_options,
                               y_col_selected,
                               y_col_options,
                               plot_type_selected='scatter',
                               color_selected='#1f77b4') -> None:
    """Regenerates new widgets to make sure they display the most recent options. 

    Args:
        gm (GraphControlWidget): Container/Dataclass that contains all the graph control widgets
        x_col_selected (str): _description_
        x_col_options (list[str]): _description_
        y_col_selected (str): _description_
        y_col_options (list[str]): _description_
        plot_type_selected (str, optional): _description_. Defaults to 'scatter'.
        color_selected (str, optional): _description_. Defaults to '#1f77b4'.
    """
    # Setup x_col select widget
    if x_col_options is not None and len(x_col_options) > 0:
        if x_col_selected is not None and selection_in_options(x_col_selected, x_col_options):
            gcw.x_col = pn.widgets.Select(
                name='X-Axis', value=x_col_selected, options=x_col_options)
        else:
            gcw.x_col = pn.widgets.Select(name='X-Axis', options=x_col_options)

    # Setup y_col select widget
    if y_col_options is not None and len(y_col_options) > 0:
        if y_col_selected is not None and selection_in_options(y_col_selected, y_col_options):
            gcw.y_col = pn.widgets.Select(
                name='Y-Axis', value=y_col_selected, options=y_col_options)
        else:
            gcw.y_col = pn.widgets.Select(name='Y-Axis', options=y_col_options)

    # Setup plot_type select widget
    if selection_in_options(plot_type_selected, ALLOWED_PLOT_TYPES):
        if plot_type_selected == '':
            gcw.plot_type = pn.widgets.Select(
                name='Plot Type', value='scatter', options=ALLOWED_PLOT_TYPES)
        else:
            gcw.plot_type = pn.widgets.Select(
                name='Plot Type', value=plot_type_selected, options=ALLOWED_PLOT_TYPES)

    # Setup ColorPicker widget
    gcw.color = pn.widgets.ColorPicker(name='Color', value=color_selected)

# End Widget Specific Methods ----------------------------------------------------------------------

# Start Init Data Structs --------------------------------------------------------------------------


graph_control_widget = GraphControlWidget()
graph_manager = GraphManager(graph_control_widget)

file_manager = FileManager()
file_manager.init_widget()

# End Init Data Structs ----------------------------------------------------------------------------


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
                title=f"Plot for {self.file_name}"
            )
            self.plot_pane.object = plot
        except Exception as e:
            self.log_error(f"Error creating plot: {e}")


@pn.depends(graph_control_widget.x_col, graph_control_widget.y_col, graph_control_widget.plot_type, graph_control_widget.color)
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


@pn.depends(file_manager.file_select_checkbox_widget)
def add_graph_object(file_select_widget):
    """
    Add a new GraphObject for the specified file and update axis options in the control widget.

    Args:
        file_path (Path): Path to the CSV file to add.
        graph_control (GraphControlWidget): Reference to the control widget for updating options.
    """
    selected_files = file_select_widget.value
    file_manager.selected_files = selected_files


def remove_graph_object(gm, file_name):
    """
    Remove a GraphObject by file name and update the combined plot.

    Args:
        file_name (str): Name of the file associated with the GraphObject to remove.
    """
    gm.graph_objects = [
        graph_obj for graph_obj in gm.graph_objects if graph_obj.file_name != file_name]
    gm.update_combined_plot()


# Initialize file selector checkbox widget.
file_select_checkbox_widget: pn.widgets.CheckBoxGroup = pn.widgets.CheckBoxGroup(
    name='Select Files', options=get_files_in_folder())
# file_select_checkbox_widget.param.watch(on_checkbox_selection, 'value')


# Add periodic callback to refresh the file list every 2 seconds
pn.state.add_periodic_callback(file_manager.init_widget, period=2000)

# Layout the Panel app
sidebar_col = pn.Column(
    pn.pane.Markdown("### File Selector"),
    file_select_checkbox_widget,
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
