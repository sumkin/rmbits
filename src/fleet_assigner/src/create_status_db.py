import os
import yaml
import sqlite3

if __name__ == "__main__":
    yaml_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file_path = yaml_dir + "/../../../config.yaml"
    with open(yaml_file_path, "r") as file:
        data = yaml.safe_load(file)
        db_file_name = data["FA_SQLITE3_DATABASE"]["DB_FILE_NAME"]

        conn = sqlite3.connect(db_file_name)
        cursor = conn.cursor()
        q = "CREATE TABLE IF NOT EXISTS optimization_status (\
                 id INTEGER PRIMARY KEY AUTOINCREMENT,\
                 dt DATETIME DEFAULT CURRENT_TIMESTAMP,\
                 uuid TEXT,\
                 status TEXT)"
        cursor.execute(q)
        conn.commit()

