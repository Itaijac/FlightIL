import sqlite3
import secrets
import hashlib
import base64
import time
from dataclasses import dataclass


@dataclass
class Account:
    id: int = None
    username: str = None
    password: str = None
    balance: str = 500
    inventory: str = "F-16"
    is_logged: bool = None


class AccountManagementORM:
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

    def create_table(self):
        """
        Creates the accounts table if it doesn't exist already.
        """
        self.open_DB()
        self.current.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id integer PRIMARY KEY,
                username text NOT NULL UNIQUE,
                password text,
                balance integer,
                inventory text
            );
        """)
        self.commit()
        self.close_DB()
    
    def log_in(self, account: Account, password: str) -> bool:
        """
        Logs in a user with a given account and password. Returns True if successful, False otherwise.

        Args:
            account (Account): The user account to log in with.
            password (str): The password to use for authentication.

        Returns:
            bool: True if the login was successful, False otherwise.
        """
        # Sanitize the user input
        self.open_DB()
        query = "SELECT * FROM accounts WHERE username = '%s'"
        self.current.execute(query % account.username)
        result = self.current.fetchone()
        self.close_DB()

        if not result:
            account.is_logged = False
            return

        # Extract the hash function, salt, and hashed password from the result
        hash_fn_name, salt, hashed_password = result[2].split('$')
        hash_fn = self.hash_from_name(hash_fn_name)
        pepper = self.get_global_pepper()

        # Hash the password using the same salt, pepper, and hash function, and compare to the stored hashed password
        h = self.hash_str_and_b64_encode(hash_fn, pepper + salt + password)
        account.is_logged = self.compare_passwords(h.encode(), hashed_password.encode())

        if account.is_logged:
            account.id = result[0]
            account.balance = result[3]
            account.inventory = result[4]

    def sign_up(self, account: Account, password: str, hash_fn=None) -> None:
        """
        Signs up a new user with a given account and password.

        Args:
            account (Account): The user account to sign up with.
            password (str): The password to use for authentication.
        """
        # Get next ID
        self.open_DB()
        query = "SELECT MAX(id) FROM accounts;"
        self.current.execute(query)
        result = self.current.fetchone()
        if result[0] is None:
            account.id = 0
        else:
            account.id = result[0] + 1
    
        # Hash the password with a new salt and pepper
        if not hash_fn:
            hash_fn = self.hash_from_name('sha256')

        salt = secrets.token_urlsafe(20)
        pepper = self.get_global_pepper()
        hashed_password = self.hash_str_and_b64_encode(hash_fn, pepper + salt + password)
        account.password = f"{self.hash_name(hash_fn)}${salt}${hashed_password}"

        # Add the new user account to the database
        query = "INSERT INTO accounts (id, username, password, balance, inventory) VALUES (%s, '%s', '%s', %s, '%s');"
        params = (account.id, account.username, account.password,
                  account.balance, account.inventory)

        try:
            self.current.execute(query % params)
        except Exception:
            account.is_logged = False
            return

        # If the insertion worked
        self.commit()
        self.close_DB()
        account.is_logged = True

    def get_global_pepper(self):
        return "Z0dFBDC2gwWyY_Up-FP_9XMyQ3w"

    def compare_passwords(self, a, b):
        starting_time = time.time()
        is_equal = a == b
        time.sleep(1 - (time.time() - starting_time))
        return is_equal

    def hash_name(self, hash_fn):
        if hash_fn.name == "sha256":
            return "sha256"
        raise ValueError

    def hash_from_name(self, name):
        if name == "sha256":
            def hash_fn(b: bytes) -> bytes:
                return hashlib.sha256(b).digest()

            hash_fn.name = "sha256"
            return hash_fn
        raise ValueError

    def hash_str_and_b64_encode(self, hash_fn, password):
        pw_bytes = password.encode("utf-8")
        hash_bytes = hash_fn(pw_bytes)
        hash_bytes = base64.b64encode(hash_bytes)
        hashed_password = hash_bytes.decode("ascii")
        return hashed_password

    def get_balance_and_inventory(self, account):
        self.open_DB()
        query = f"SELECT balance, inventory FROM accounts WHERE id = {account.id};"
        balance, inventory = self.current.execute(query).fetchone()
        self.close_DB()
        return balance, inventory

    def buy_aircraft(self, account, aircraft_to_purchase):
        # Double check to make sure that the user isn't buying a plane that he already has
        if aircraft_to_purchase not in account.inventory.split('|'):
            self.open_DB()
            query = f"SELECT price FROM aircrafts WHERE name = '{aircraft_to_purchase}'"
            price = self.current.execute(query).fetchone()[0]

            if price > account.balance:
                self.close_DB()
                return False
                
            query = f"UPDATE accounts SET balance = balance - {price} WHERE username = '{account.username}'"
            self.current.execute(query)

            query = f"UPDATE accounts SET inventory = '{account.inventory}|{aircraft_to_purchase}' WHERE username = '{account.username}'"
            self.current.execute(query)

            self.commit()
            self.close_DB()

            account.balance =- price
            account.invnentory = f"{account.inventory}|{aircraft_to_purchase}"
            return True
        return False
