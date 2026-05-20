from database import execute_sql_script
import os

def read_sql_file_and_execute(file_path):
    """
    Reads a SQL file and executes its contents to perform database operations 
    such as creating tables and inserting data.

    Args:
        file_path (str): The relative or absolute path to the SQL file.

    Returns:
        None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        execute_sql_script(sql_script)
        print(f"Success: The file '{file_path}' has been executed successfully.")
        
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' could not be found.")
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    read_sql_file_and_execute("data/output/final_data.sql")