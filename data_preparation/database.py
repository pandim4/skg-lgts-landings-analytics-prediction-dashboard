import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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


def execute_sql_script(sql_query):
    """
    Executes a complete SQL script containing DDL/DML statements, 
    automatically filtering out CLI-specific meta-commands.

    Args:
        sql_query (str): The SQL script text to be executed.

    Returns:
        None
    """
    # Filter out lines that start with '\' (e.g., \connect, \copy, \unrestrict)
    cleaned_query = "\n".join(
        line for line in sql_query.splitlines() 
        if not line.strip().startswith("\\")
    )
    
    engine = create_engine(os.getenv('DB_URL'))
    
    with engine.connect() as connection:
        connection.execute(text(cleaned_query))
        connection.commit()