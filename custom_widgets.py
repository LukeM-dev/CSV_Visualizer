import panel as pn
import pandas as pd
import hvplot.pandas
import param

class SidebarWidget(param.Parameterized):
    file_input = pn.widgets.FileInput(name="Upload CSV File", accept='.csv', multiple=False)

class GraphWidget(param.Parameterized):
    x_col = pn.widgets.Select(name='X-Axis', options=[])
    y_col = pn.widgets.Select(name='Y-Axis', options=[])
    plot_type = pn.widgets.Select(name='Plot Type', options=['line', 'scatter', 'bar', 'area'])
    color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')
    
    _graph = pn.pane.HoloViews()
    graph_df = pd.DataFrame()

    #@pn.depends(x_col.param.value, y_col.param.value, plot_type.param.value, color.param.value)
    def update_graph_visuals(self, x_col, y_col, plot_type, color):
        if x_col and y_col and plot_type:
            return self.graph_df.hvplot(x=x_col, y=y_col, kind=plot_type, color=color)
        return None
    
    def setup_graph(self, new_graph_df):
        self.graph_df = new_graph_df
        print(f"Plotting Initialized: Graph is Empty: {self.graph_df.empty}, {self.graph_df.columns}")
        # Update x_col and y_col options when the file is uploaded
        if not self.graph_df.empty and 'Error' not in self.graph_df.columns:
            self.x_col.options = list(self.graph_df.columns)
            self.y_col.options = list(self.graph_df.columns)
    
    def get_graph_df(self):
        return self.graph_df