import pandas

class PandasHelper:

    def print_heads(csv_dict: dict):
        for filename, df in csv_dict.items():
            print(f"{filename}, {df.head}")

    def compare_column_headers(csv_dict: dict) -> bool:
        # Get the column names from the first DataFrame as the reference
        reference_columns = None
        columns_are_equal = True

        # Iterate through the dictionary to compare column headers
        for filename, df in csv_dict.items():
            if reference_columns is None:
                # Set the first DataFrame's columns as the reference
                reference_columns = df.columns
                print(f"Using {filename} as the reference for column headers.")
            else:
                # Compare the current DataFrame's columns with the reference columns
                if df.columns.equals(reference_columns):
                    print(f"Columns of {filename} match the reference columns.")
                else:
                    print(f"Columns of {filename} do NOT match the reference columns.")
                    print(f"Expected: {reference_columns}")
                    print(f"Found: {df.columns}")
                    columns_are_equal = False
        return columns_are_equal