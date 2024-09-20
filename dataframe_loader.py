import panel as pn
import pandas as pd
from io import BytesIO

class DataFrameLoader():

    def __init__(self) -> None:
        pass

    def find_associated_logger_location(self, current_file_path):
        logger_locations = {
            "219999191": "Outdoors – Courtyard Door Overhang",
            "21611332": "Tub Room 2041",
            "21611333": "Hallway 600 on Linen room door frame",
            "21611336": "Resident Room 605 on Bathroom door frame",
            "21611334": "Crawlspace - 900",
            "21611335": "Crawlspace - 600",
            "21611337": "Crawlspace - 500",
            "21611338": "Attic 2000 – Just inside access door on conduit"
        }

        for logger_key, associated_location in logger_locations.items():
            if logger_key in current_file_path:
                print(f"Found ID {logger_key} in file {current_file_path}, associated name: {associated_location}")
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
    

#Loader = DataFrameLoader()
#test_df = pd.read_csv("C:\\repos\\Steven_Carlson_Building_Analysis\\data\\21611332 2024-07-26.csv")
#convert_to_bytes = BytesIO(test_df.to_string().encode('utf-8'))
#df = Loader.convert_to_dataframe(convert_to_bytes.getvalue())
#print(df.head())
