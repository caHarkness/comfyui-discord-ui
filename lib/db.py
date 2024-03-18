import mysql.connector
import json

import lib.log as log

conn = None
conn_config =  {
  "user": "root",
  "password": "password",
  "host": "127.0.0.1",
  "database": "comfyui_discord_ui",
  "raise_on_warnings": True
}

def connect_to_mysql(config, attempts=3, delay=2):
    attempt = 1

    while attempt < attempts + 1:
        try:
            return mysql.connector.connect(**config)
        except (mysql.connector.Error, IOError) as err:
            if (attempts is attempt):
                print("Error connecting to DB IO Error")
                return None

            print("Error connecting to DB")
            # progressive reconnect delay
            time.sleep(delay ** attempt)
            attempt += 1
    return None

def get_connection():
    global conn

    if conn is None:
        conn = connect_to_mysql(conn_config, attempts=3)

    if not conn.is_connected():
        conn.reconnect(attempts=5, delay=1)
        
    return conn

def query(query_string, query_args=None, retry=True):
    c = get_connection()

    try:
        if c.is_connected():
            with c.cursor(prepared=True, dictionary=True) as cur:
                result = cur.execute(query_string, params=query_args, multi=True)
                rows = cur.fetchall()
                c.commit()
                cur.close()
                return rows
    except Exception as x:
        log.write("Exception!")
