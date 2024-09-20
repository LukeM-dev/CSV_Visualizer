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
    
    def convert_datetime_column(self, key: str) -> bool:
        pass

    def set_column_as_index(self, key: str) -> bool: 
        self.data_dict[key].

    def get_all_df_columns(self):
        """returns a list of the columns that all Excel files share"""
        columns_set = set()
        for key, value in self.data_dict:
            columns_set.intersection_update(value.columns)
        return list(columns_set)

    def merge_all_df(self) -> pd.DataFrame:
        """Leaving this method here, but empty because it might be useful in the future for me to do, but as of right now, its not going to help"""
        pass

    def get_all_keys(self) -> list:
        return list(self.data_dict.keys())
    
    