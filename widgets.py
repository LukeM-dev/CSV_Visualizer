import panel as pn
import param

class SidebarWidget(param.Parameterized):
    file_input = pn.widgets.FileInput(name="Upload CSV File", accept='.csv', multiple=False)
    
    def __init__(self, folder_path, on_file_selected_callback, **params):
        super().__init__(**params)
        self.folder_path = folder_path
        self.checkbox = pn.widgets.CheckBoxGroup(name='Select Files', options=self.get_files_in_folder())
        
        # Callback triggered when a file is selected
        self.on_file_selected_callback = on_file_selected_callback
        self.checkbox.param.watch(self.on_checkbox_selection, 'value')
        self.selected_files = set()
    
    # Function to get the list of files in the folder
    def get_files_in_folder(self):
        return [f.name for f in self.folder_path.iterdir() if f.is_file()]

    # Function to dynamically update the CheckboxGroup options
    def update_checkbox_options(self):
        self.checkbox.options = self.get_files_in_folder()
    
    # Callback for when a checkbox is selected
    def on_checkbox_selection(self, event):
        current_selection = event.new  # List of currently selected files
        
        # Find newly selected and unselected files
        newly_selected_files = set(current_selection) - set(self.selected_files)
        unselected_files = set(self.selected_files) - set(current_selection)
        
        # Handle newly selected files
        for file_name in newly_selected_files:
            self.on_file_selected_callback(file_name)  # Plot or process the new file
        
        # Handle unselected files
        for file_name in unselected_files:
            self.on_file_selected_callback(file_name, unselected=True)  # Unselect and remove plot
        
        # Update the stored selection
        self.selected_files = current_selection
    
    def get_checkbox(self):
        return self.checkbox

class GraphEditWidget(param.Parameterized):
    x_col = pn.widgets.Select(name='X-Axis', options=[])
    y_col = pn.widgets.Select(name='Y-Axis', options=[])
    plot_type = pn.widgets.Select(name='Plot Type', options=['line', 'scatter', 'bar', 'area'])
    color = pn.widgets.ColorPicker(name='Color', value='#1f77b4')