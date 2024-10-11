import panel as pn
from pathlib import Path
import pandas as pd
import hvplot.pandas

from widgets import SidebarWidget
from graph_manager import GraphManager

# Initialize Panel
pn.extension('tabulator', sizing_mode="stretch_width")

# Folder path to monitor
folder_path = Path('data')

# Initialize GraphManager
graph_manager = GraphManager()

# Define the callback for when a file is selected in the SidebarWidget
def on_file_selected(file_name, unselected=False):
    file_path = folder_path / file_name
    graph_manager.plot_file(file_path, unselected=unselected)

# Initialize Widgets
sidebar_widget = SidebarWidget(folder_path=folder_path, on_file_selected_callback=on_file_selected)

# Add periodic callback to refresh the file list every 2 seconds
pn.state.add_periodic_callback(sidebar_widget.update_checkbox_options, period=2000)

# Layout the Panel app
sidebar_col = pn.Column(
    pn.pane.Markdown("### File Selector"),
    sidebar_widget.checkbox,
)

main_graph_col = pn.Column(
    sidebar_col,
    graph_manager.combined_plot,
    graph_manager.debug_pane
)

template = pn.template.FastGridTemplate(
    title="CSV Visualizer",
    #sidebar=[sidebar_col],
    main=pn.Row(
        main_graph_col
    )
).servable()