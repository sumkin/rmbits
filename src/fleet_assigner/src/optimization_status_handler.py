import os
import yaml
import sqlite3

class OptimizationStatusHandler:

    def __init__(self):
        yaml_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_file_path = yaml_dir + "/../../../config.yaml"
        with open(yaml_file_path, "r") as file:
            data = yaml.safe_load(file)
            db_file_name = data["FA_SQLITE3_DATABASE"]["DB_FILE_NAME"]
            self.conn = sqlite3.connect(db_file_name)
            self.cursor = self.conn.cursor()

    def update_status(self, uuid, status):
        q = "INSERT INTO optimization_status (uuid, status) \
             VALUES ('{}', '{}')".format(uuid, status)
        self.cursor.execute(q)
        self.conn.commit()

    def get_status(self, uuid):
        q = "SELECT status FROM optimization_status\
             WHERE uuid = '{}' ORDER BY dt DESC LIMIT 1".format(uuid)
        self.cursor.execute(q)
        self.conn.commit()
        res = self.cursor.fetchone()
        return res[0]

if __name__ == "__main__":
    osh = OptimizationStatusHandler()
    status = osh.get_status('2')
    print("status = {}".format(status))