import sqlite3

class NewspaperManagementORM:
    def __init__(self):
        self.conn = None  # will store the DB connection
        self.cursor = None  # will store the DB connection cursor

    def open_DB(self):
        """
        Will open DB file and put value in:
        self.conn (need DB file name)
        self.cursor
        """
        self.conn = sqlite3.connect("accounts.db")
        self.current = self.conn.cursor()

    def close_DB(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    # -=Read Functions=-
    def log_in(self, username, password):
        self.open_DB()
        account = self.current.execute(
            f"SELECT * FROM accounts WHERE username = {username} AND password = password;"
        )
        query = account.fetchall()
        self.close_DB()
        return query

    # -=Write Functions=-

    def insert_account(self, user):
        self.open_DB()
        res = self.current.execute("SELECT MAX(accounts.id) FROM accounts;")
        query = res.fetchall()
        if query[0][0] == None:
            id = 0
        else:
            id = query[0][0] + 1
        self.current.execute(
            f"INSERT INTO accounts (id, username, password, "
            + f"email, first_name, last_name, newspaper_id) VALUES "
            + f"({id}, '{user.username}', '{user.password}', '{user.email}', "
            + f"'{user.first_name}', '{user.last_name}', {user.newspaper_id});"
        )
        self.commit()
        self.close_DB()

    def update_account(self, username, column, new_value):
        if column != id and column != username:
            self.open_DB()
            self.current.execute(
                f"UPDATE accounts SET {column} = '{new_value}' WHERE username = '{username}';"
            )
            self.commit()
            self.close_DB()

    def delete_account(self, id):
        self.open_DB()
        res = self.current.execute(f"DELETE FROM accounts WHERE id = {id};")
        self.commit()
        self.close_DB()

    def insert_newspaper(self, newspaper):
        self.open_DB()
        res = self.current.execute("SELECT MAX(newspapers.id) FROM newspapers;")
        query = res.fetchall()
        if query[0][0] == None:
            id = 0
        else:
            id = query[0][0] + 1
        self.current.execute(
            f"INSERT INTO newspapers (id, name, description, publish_rate)"
            + f"VALUES ({id}, '{newspaper.name}', '{newspaper.description}', "
            + f"{newspaper.publish_rate});"
        )
        self.commit()
        self.close_DB()

    def update_newspaper(self, name, column, new_value):
        if column != id and column != name:
            self.open_DB()
            self.current.execute(
                f"UPDATE newspapers SET {column} = '{new_value}' WHERE name = '{name}';"
            )
            self.commit()
            self.close_DB()

    def delete_newspaper(self, id):
        self.open_DB()
        self.current.execute(f"DELETE FROM newspapers WHERE id = {id};")
        self.commit()
        self.close_DB()

    def delete_all_subs(self, id):
        self.open_DB()
        self.current.execute(
            f"DELETE FROM accounts WHERE accounts.newspaper_id = {id};"
        )
        self.commit()
        self.close_DB()
