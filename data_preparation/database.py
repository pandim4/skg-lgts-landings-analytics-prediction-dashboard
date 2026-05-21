import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def create_table_in_database(df, name):
    """
    Uploads a pandas DataFrame into the SQL database as a table.
    
    If the table already exists, it will be replaced.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be stored.
        name (str): The name of the database table to create or replace.

    Returns:
        None
    """
    engine = create_engine(os.getenv('DB_URL'))
    df.to_sql(name, con=engine, if_exists='replace', index=False)

def get_data_from_database(query):
    """
    Executes a SQL query on the database and returns the result as a DataFrame.

    Args:
        query (str): The SQL query string to execute.

    Returns:
        pd.DataFrame: A DataFrame containing the query results.
    """
    engine = create_engine(os.getenv('DB_URL'))
    df = pd.read_sql(query, engine)
    return df