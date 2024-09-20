import panel as pn
import pandas as pd
from io import BytesIO

class DataFrameLoader():

    def __init__(self) -> None:
        pass

    def find_associated_logger_location(self, current_file_path):
        for logger_id, associated_location in self.logger_locations.items():
            if logger_id in current_file_path:
                print(f"Found ID {logger_id} in file {current_file_path}, associated name: {associated_location}")
                return associated_location
    
    def convert_to_dataframe(self, file_data):
        print(type(file_data))
        if file_data is not None:
            try:
                byte_io = BytesIO(file_data)
                return pd.read_csv(byte_io)
            except Exception as e:
                return pd.DataFrame({'Error': [str(e)]})
        return pd.DataFrame()
    

#Loader = FileLoader()
#Loader.load_file("C:\\repos\\Steven_Carlson_Building_Analysis\\data\\21611332 2024-07-26.csv")
