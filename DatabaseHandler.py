from config import USR_CONFIG, TABLE_NAMES, TABLE_TEMPLATES, ENVIRON_TABLE_LOCATION_MAPPING, CSV_TO_ENVIRON_TABLE_COLUMN_MAP

# Third Party Libraries to handle using Data
import pandas as pd  # Data Manip Tool
import sqlite3 as db  # Data Storage Tool

# Panel/Holoviz Libraries 
import param

class SqlConnection(param.Parameterized):

    def __init__(self, config: dict[str, str], **params) -> None:
        super().__init__(**params)
        
        # DB Connection Variables
        self.config = config 
        self.cnx = None  # Database connection
        self.cursor = None  # Database cursor in use
        self.results = None # Contains one or more results
        
        # Error Specific Variables
        self.error = None  # Last error encountered
        self.error_log: list[str] = []  # list of errors the db has encountered
        # Want to know if a serious DB error has happened as opposed to me doing things out of order.
        self.sqlite_error_flag = False

    def log_error(self, err=None, error_msg="") -> None:
        if err is not None:
            self.error = err
            # self.error_log.append(str(err))
        elif error_msg != "":
            self.error = error_msg
            self.error_log.append(error_msg)
        else:
            print("Unable to store error")

    def init_connection(self) -> None:
        if self.cnx is None:
            self.cnx = db.connect(self.config['database'])
        else:
            msg = f"Database already Initialized {self.config['database']}"
            print(msg)
            self.log_error(error_msg=msg)

    def close_connection(self) -> None:
        if self.cnx is not None:
            if self.cursor is not None:
                self.cursor.close()
            self.cnx.close()
        else:
            msg = f"Database already closed {self.config['database']}, please reinitialized to continue."
            print(msg)
            self.log_error(error_msg=msg)

    def get_current_cursor(self) -> db.Cursor | None:
        # Ensure Db Connection is established
        if self.cnx is None:
            msg = f"No connection to {self.config['database']} established, attempting to establish connection now"
            self.log_error(error_msg=msg)
            self.init_connection()

            if self.cnx is None:
                msg = f"No connection to {self.config['database']} established, aborting operation"
                self.log_error(error_msg=msg)
                return None

        # Create Cursor if One already doesn't exist
        if self.cursor is None:
            self.cursor = self.cnx.cursor()

        return self.cursor

    def close_current_cursor(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        else:
            msg = f"Attempted to close cursor to {self.config['database']} when one already didn't exist."
            self.log_error(error_msg=msg)

    def execute_command(self, command: str) -> bool:
        cursor = self.get_current_cursor()
        if cursor is not None:
            cursor.execute(command)
            return True
        return False
        
    def fetch_result(self, one=False, many=0, fetchall=True):
        cursor = self.get_current_cursor()
        
        if cursor is None: 
            msg = "Unable to fetch result from DB because Cursor wasn't created"
            print(msg)
            self.log_error(error_msg=msg)
            return None
        
        if fetchall:
            return cursor.fetchall()
        elif many != 0:
            return cursor.fetchmany(many)
        elif one:
            return cursor.fetchone()
        else:
            return None

    def get_column_names(self, table_name="") -> list[str] | None:
        """
        Get the column names of a table in the SQLite database.

        :param table_name: Name of the table.
        :return: List of column names, or an empty list if the table does not exist.
        """
        cursor = self.get_current_cursor()
        if cursor is None:
            self.log_error(error_msg="No database connection.")
            return []
        
        try:
            # Query the table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()

            # Extract and return column names
            return [column[1] for column in columns_info]
        except db.Error as e:
            self.log_error(err=e)
            print(f"Error fetching column names for table '{table_name}': {e}")
            return []
        
        
    def alter_to_add_column(self, table="", new_column_name=""):
        alter_query = f"""
        ALTER TABLE {table}
        ADD COLUMN location_id VARCHAR(50) AFTER dew_point_F;
        """
        
        if table == "" or new_column_name == "":
            msg = f"New Column Name or Table name param wasn't filled in, Aborting Operation"
            print(msg)
            self.log_error(error_msg=msg) 
            return None
    
        if self.execute_command(alter_query):
            return self.fetch_result()
        return None
    
    # Method to check if the table exists and create it if it does not
    def ensure_table_exists(self, table_name: str, create_table_sql: str) -> bool:
        """
        Ensure that a table exists in the database. If it does not exist, create it.

        :param table_name: Name of the table to check or create.
        :param create_table_sql: SQL statement to create the table if it doesn't exist.
        :return: True if the table exists or was created successfully, False otherwise.
        """
        try:
            cursor = self.get_current_cursor()
            if cursor is None:
                self.log_error(error_msg="No database connection.")
                return False

            # Check if the table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone() is None:
                # Table does not exist; create it
                cursor.execute(create_table_sql)
                self.cnx.commit()
            return True
        except db.Error as e:
            self.log_error(err=e)
            print(f"Error ensuring table exists: {e}")
            return False
    
    def insert_from_dataframe(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Insert rows from a pandas DataFrame into the specified table.

        :param table_name: Name of the table to insert rows into.
        :param df: pandas DataFrame containing the data to insert.
        :return: True if all rows were inserted successfully, False otherwise.
        """
        if not table_name or df is None or df.empty:
            self.log_error(error_msg="Table name or DataFrame not provided or empty.")
            return False

        cursor = self.get_current_cursor()
        if cursor is None:
            self.log_error(error_msg="No database connection.")
            return False

        # Get column names from the DataFrame
        columns = ', '.join(df.columns)
        placeholders = ', '.join(['?'] * len(df.columns))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        try:
            # Convert DataFrame rows to list of tuples
            data = [tuple(row) for row in df.itertuples(index=False, name=None)]
            cursor.executemany(query, data)
            self.cnx.commit()
            return True
        except db.Error as e:
            self.log_error(err=e)
            print(e)
            return False

    def load_csv_files_to_db(self, folder_path: str, table_name: str, schema_columns: list[str], location_id: int) -> None:
        """
        Load all .csv files from the specified folder into the database.

        :param folder_path: Path to the folder containing .csv files.
        :param table_name: Name of the database table to insert data into.
        :param schema_columns: List of columns in the database table (excluding auto-increment keys).
        :param location_id: Default location ID to add to the DataFrame.
        """
        if not os.path.exists(folder_path):
            print(f"Folder path '{folder_path}' does not exist.")
            return

        # List all .csv files in the folder
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        if not csv_files:
            print(f"No .csv files found in folder '{folder_path}'.")
            return

        for file_name in csv_files:
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing file: {file_name}")

            try:
                # Load CSV into DataFrame
                df = pd.read_csv(file_path)

                # Preprocess DataFrame (strip whitespace, rename columns, and add location_id)
                df.columns = df.columns.str.strip()
                df = df.rename(columns={k: v for k, v in CSV_TO_ENVIRON_TABLE_COLUMN_MAP.items() if k in df.columns})
                df['location_id'] = location_id

                # Ensure the DataFrame matches the schema columns
                df = df[schema_columns]

                # Insert DataFrame into the database
                if not self.insert_from_dataframe(table_name=table_name, df=df):
                    print(f"Failed to insert data from file: {file_name}")

            except Exception as e:
                self.log_error(err=e)
                print(f"Error processing file '{file_name}': {e}")
                              
    def query_to_dataframe(self, query: str, params: tuple = (), fetchall: bool = True) -> pd.DataFrame:
        """
        Execute a query and return the results as a pandas DataFrame.

        :param query: SQL query string to execute.
        :param params: Tuple of parameters to use in the query (optional).
        :param fetchall: Whether to fetch all results (default True).
        :return: pandas DataFrame containing the query results.
        """
        cursor = self.get_current_cursor()
        if cursor is None:
            self.log_error(error_msg="No database connection.")
            return pd.DataFrame()

        try:
            # Execute the query
            cursor.execute(query, params)

            # Fetch results using the fetch_result() method
            results = self.fetch_result(fetchall=fetchall)

            # Get column names from the cursor description
            if cursor.description is not None:
                column_names = [desc[0] for desc in cursor.description]
            else:
                column_names = []

            # Convert to pandas DataFrame
            return pd.DataFrame(results, columns=column_names)

        except db.Error as e:
            self.log_error(err=e)
            print(f"Error executing query: {e}")
            return pd.DataFrame()

