#!/bin/env python3.7

import requests
import sqlite3
import multiprocessing as multiproc
from multiprocessing.dummy import Pool
from lxml import html
from datetime import datetime
import sys
import os


class BashImParser:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.counter = 0
        self.last_id = 0
        self.from_id = 0
        self.bad_connections = 0
        self.sql_queries = {
            "DROP": "DROP TABLE quote",
            "CREATE_TABLE": """
                CREATE TABLE IF NOT EXISTS quote (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                url VARCHAR(255),
                likes INTEGER,
                date DATETIME);""",
            "INSERT_IN_TABLE": 'INSERT INTO quote (id, text, url, likes, date) VALUES (?, ?, ?, ?, ?)',
            "INSERT_ZERO": 'INSERT INTO quote (id, text) VALUES (?, ?)'
        }

    def connect(self):
        connect = sqlite3.connect(self.db_path, isolation_level=None)
        cursor = connect.cursor()
        return cursor, connect

    def single_core(self, tests: int = None, from_id: int = 1):
        self.bad_connections = 0
        self.counter = 0
        print("Run single process mode")

        # find last id
        main_page = requests.get("https://bash.im")
        tree = html.fromstring(main_page.content)
        self.last_id = int(tree.xpath("//article/div/header/a/text()")[0][1:]) if tests is None else tests

        # connect to database
        cursor, conn = self.connect()

        # create table
        cursor.execute(self.sql_queries["DROP"])
        cursor.execute(self.sql_queries["CREATE_TABLE"])

        # create zero index for last update
        cursor.execute(self.sql_queries["INSERT_ZERO"], (0, self.last_id))

        conn.close()

        # run speed test
        timer = datetime.now()

        for i in range(from_id, self.last_id):
            self.parse(i)

        # finish speed test
        end_timer = datetime.now()
        print("\n" + str(end_timer - timer))

    def multi_core(self, tests: int = None, processes: int = 2, from_id: int = 1):
        self.bad_connections = 0
        self.counter = 0
        self.from_id = from_id
        print(f"Run multiprocessing with {processes} process(-es) mode")

        # find last id
        main_page = requests.get("https://bash.im")
        tree = html.fromstring(main_page.content)
        self.last_id = int(tree.xpath("//article/div/header/a/text()")[0][1:]) if tests is None else tests

        # connect to database
        cursor, conn = self.connect()

        # create table
        cursor.execute(self.sql_queries["DROP"])
        cursor.execute(self.sql_queries["CREATE_TABLE"])

        # create zero index for last update
        cursor.execute(self.sql_queries["INSERT_ZERO"], (0, self.last_id))

        conn.close()

        # run speed test
        timer = datetime.now()

        # multiprocessing realization
        pool = Pool(processes=processes)
        pool.map(self.parse, [i for i in range(from_id, self.last_id)])
        pool.close()
        pool.join()

        # finish speed test
        end_timer = datetime.now()
        print("\n" + str(end_timer - timer))

    def parse(self, id: int):
        url = f"https://bash.im/quote/{id}"
        page = requests.get(url)

        if len(page.history) != 0 and (page.history[0].status_code == 302):
            self.last_id = int(self.last_id) - 1
            self.bad_connections += 1
            stroke = f"\r{self.counter} of {self.last_id - self.from_id}, skipped {self.bad_connections}"
            sys.stdout.write(stroke)
            return False

        html_tree = html.fromstring(page.content)

        quote: str = "\n      ".join(html_tree.xpath("//article/div/div/text()"), )
        date: str = html_tree.xpath("//div/header/div")[0].text.replace(" ", "").replace("\n", "")
        likes: str = html_tree.xpath("//footer/div[3]")[0].text.replace(" ", "").replace("\n", "")
        date = datetime.strptime(date, '%d.%m.%Yв%H:%M')

        cursor, conn = self.connect()

        cursor.execute(self.sql_queries["INSERT_IN_TABLE"], (id, quote, url, likes, date))
        conn.close()

        self.counter += 1
        stroke = f"\r{self.counter} of {self.last_id - self.from_id}, skipped {self.bad_connections}"
        sys.stdout.write(stroke)
        return True

    def update(self):
        cursor, conn = self.connect()

        last_id = int(cursor.execute("SELECT text FROM quote WHERE id=0").fetchall()[0][0])

        main_page = requests.get("https://bash.im")
        tree = html.fromstring(main_page.content)
        new_id = int(tree.xpath("//article/div/header/a/text()")[0][1:])

        self.multi_core(new_id, from_id=last_id, processes=multiproc.cpu_count())

    def run(self):
        self.multi_core(processes=multiproc.cpu_count())


if __name__ == '__main__':
    guide = \
f"""
enter "./{os.path.basename(__file__)} init path_to_sqlite_database" if you want to initialize the parser
enter "./{os.path.basename(__file__)} update path_to_sqlite_database" if you want update parsed data"""
    if len(sys.argv) == 3:
        main = BashImParser(sys.argv[2])
        if sys.argv[1] == "update":
            main.update()
        elif sys.argv[1] == "init":
            main.multi_core(processes=multiproc.cpu_count())
        else:
            print(guide)
    else:
        print(guide)
