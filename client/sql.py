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

    def get_aircraft_name_and_description(self, id):
        """
        Returns the name and the description of aircraft by ID.
        """
        self.open_DB()
        query = f"SELECT name, description FROM aircrafts WHERE id = {id};"
        name, description = self.current.execute(query).fetchone()
        self.close_DB()
        return name, description
    
    def get_aircrafts_amount(self):
        """
        Returns the amount of aircrafts in the DB.
        """
        self.open_DB()
        query = f"SELECT COUNT(*) FROM aircrafts;"
        amount = self.current.execute(query).fetchone()
        self.close_DB()
        return amount

    def get_price(self, id):
        """
        Returns the price of aircraft by ID.
        """
        self.open_DB()
        query = f"SELECT price FROM aircrafts WHERE id = {id};"
        price = self.current.execute(query).fetchone()
        self.close_DB()
        return price
    
    def get_mass_and_max_thrust(self, id):
        """
        Returns the mass and max thrust of aircraft by ID.
        """
        self.open_DB()
        query = f"SELECT mass, max_thrust FROM aircrafts WHERE id = {id};"
        values = self.current.execute(query).fetchone()
        self.close_DB()
        return values