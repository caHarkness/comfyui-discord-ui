import mysql.connector
import json
import time
import copy

import lib.log as log

DEFAULT_MYSQL_CONNECTION_CONFIG = {
    "user": "root",
    "password": "password",
    "host": "127.0.0.1",
    "database": "comfyui_discord_ui",
    "raise_on_warnings": True
}

class MySQLConnection:
    def __init__(self, config = None):
        self.conn = None
        self.conn_config = copy.deepcopy(config)

        if self.conn_config is None:
            self.conn_config = DEFAULT_MYSQL_CONNECTION_CONFIG

        # Temporary workaround:
        # Using mysql first allows us to create and "use database later"
        self.conn_config["database"] = "mysql"

    def connect_to_mysql(self, config, attempts=3, delay=2):
        attempt = 1

        while attempt < attempts + 1:
            try:
                return mysql.connector.connect(**config)
            except Exception as x:
                if attempt == attemps:
                    raise Exception(f"Final error connecting to DB: {x}")

                log.write(f"Error connecting to DB: {x}")

                time.sleep(delay ** attempt)
                attempt += 1
        return None

    def get_connection(self):

        if self.conn is None:
            self.conn = connect_to_mysql(self.conn_config, attempts=3)

        if not self.conn.is_connected():
            self.conn.reconnect(attempts=5, delay=1)
            
        return self.conn

    def query(self, query_string, query_args=None, retry=True):
        c = self.get_connection()

        try:
            if c.is_connected():
                with c.cursor(prepared=True, dictionary=True) as cur:
                    result = cur.execute(query_string, params=query_args, multi=True)
                    rows = cur.fetchall()
                    c.commit()
                    cur.close()
                    return rows
        except Exception as x:
            log.write(f"Exception: {x}")


default_mysql_connection = MySQLConnection(DEFAULT_MYSQL_CONNECTION_CONFIG)

def connect_to_mysql(config, attempts=3, delay=2):
    return default_mysql_connection.connect_to_mysql(config, attempts, delay)

def get_connection():
    return default_mysql_connection.get_connection()

def query(query_string, query_args=None, retry=True):
    return default_mysql_connection.query(query_string, query_args, retry)
