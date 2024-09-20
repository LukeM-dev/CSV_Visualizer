import panel as pn
import param

class SidebarWidget(param.Parameterized):
    file_input = pn.widgets.FileInput(name="Upload CSV File")
    plot_button = pn.widgets.Button(name='Plot Graph', button_type='primary')
    load_data_button = pn.widgets.Button(name='Load CSV', button_type='primary')