import sqlite3


class SQL:
    def __init__(self):
        self.conn = None  # will store the DB connection
        self.cursor = None  # will store the DB connection cursor

    def open_DB(self):
        """
        Will open DB file and put value in:
        self.conn (need DB file name)
        self.cursor
        """
        self.conn = sqlite3.connect("database.db")
        self.current = self.conn.cursor()

    def close_DB(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def get_aircraft_name_and_decsription(self, id):
        self.open_DB()
        query = f"SELECT name, description FROM aircrafts WHERE id = {id};"
        balance, inventory = self.current.execute(query).fetchone()
        self.close_DB()
        return balance, inventory
    
    def get_aircrafts_amount(self):
        self.open_DB()
        query = f"SELECT COUNT(*) FROM aircrafts;"
        amount = self.current.execute(query).fetchone()
        self.close_DB()
        return amount

    def get_price(self, id):
        self.open_DB()
        query = f"SELECT price FROM aircrafts WHERE id = {id};"
        price = self.current.execute(query).fetchone()
        self.close_DB()
        return price