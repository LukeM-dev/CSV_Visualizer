import pandas as pd

from dataframe_loader import DataFrameLoader as df_loader

class DataManager():
    def __init__(self):
        self.data_dict = {}
        self.merged_df = None
        pass

    def add_df(self, key: str, df: pd.DataFrame) -> bool:
        if key not in self.data_dict:
            self.data_dict[key] = df
            self.merged_df = None # Purge merged df as its supposed to represent all currently added datapoints
            return True
        else: 
            return False
        
    def remove_df(self, key: str) -> bool:
        if key in self.data_dict:
            self.data_dict[key].pop()
            return True
        else: 
            return False
        
    def replace_df(self, key: str, new_df: pd.DataFrame) -> bool:
        if key in self.data_dict:
            self.data_dict[key] = new_df
            return True
        else: 
            return False

    def get_df(self, key: str) -> pd.DataFrame:
        return self.data_dict[key]
    
    def convert_datetime_column(self, key: str, column_name: str) -> bool:
        self.data_dict[key] = pd.to_datetime(self.data_dict[key])

    def set_column_as_index(self, key: str, column_name: str) -> bool:
        """
        Sets the specified column as the index for the DataFrame associated with the given key.
        :param key: The key to the DataFrame in data_dict.
        :param column_name: The column to be set as the index.
        :return: True if successful, False if any error occurs.
        """

        if key not in self.data_dict:
            print(f"Key '{key}' not found in data_dict.")
            return False
        elif column_name not in self.data_dict[key].columns:
            print(f"Column '{column_name}' not found in DataFrame '{key}'.")
            return False

        df = self.data_dict[key]
        try:
            df.set_index(column_name, inplace=True)
            print(f"Column '{column_name}' set as index for DataFrame '{key}'.")
            return True
        except Exception as e:
            print(f"Error setting column '{column_name}' as index: {str(e)}")
            return False

    def merge_all_df(self) -> pd.DataFrame:
        """
        Leaving this method here, but empty because it might be useful in the future for me to do, 
        but as of right now, its not going to help
        """
        pass

    def get_all_keys(self) -> list:
        return list(self.data_dict.keys())
    
    