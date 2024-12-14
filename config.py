
USR_CONFIG = {
    'database': "CsvVisualizer.db"
}

TABLE_NAMES = [
    'EnvironData',
    'LocationMap'
]

CSV_TO_ENVIRON_TABLE_COLUMN_MAP = {
    "#": "entry_no",
    "Date-Time (CDT)": "datetime",
    "Temperature (°F)": "temp_F",
    "RH (%)": "rh_percent",
    "Dew Point (°F)": "dew_point_F"
}

TABLE_TEMPLATES = {
    'EnvironData': (
        """
        CREATE TABLE "EnvironData" (
        "key"	INTEGER,
        "entry_no"	INTEGER NOT NULL,
        "datetime"	TEXT NOT NULL,
        "temp_F"	REAL NOT NULL,
        "rh_percent"	REAL NOT NULL,
        "dew_point_F"	REAL NOT NULL,
        "location_id"	INTEGER NOT NULL,
        PRIMARY KEY("key" AUTOINCREMENT)
        )
        """
    ),
    'LocationMap': (
        """CREATE TABLE `{tb_name}` (
         `location_id` int(5) NOT NULL, 
         `location_description` text(100), 
         PRIMARY KEY (`location_id`), 
        );"""
    )
}

ENVIRON_TABLE_LOCATION_MAPPING = {
    '21611332': 'Outdoors – Courtyard Door Overhang',
    '21999191': 'Tub Room 2041',
    '21611333': 'Hallway 600 on Linen room door frame',
    '21611336': 'Resident Room 605 on Bathroom door frame',
    '21611334': 'Crawlspace - 900 Below occupied wing',
    '21611335': 'Crawlspace - 600 Below occupied wing',
    '21611337': 'Crawlspace - 500 Below occupied wing',
    '21611338': 'APc 2000 – Just inside access door on conduit'
}