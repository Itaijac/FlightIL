import socket
import SQL_ORM
import threading
import logging
import pickle
from protocol import send_with_size, recv_by_size, build_message

DEBUG = True
exit_all = False
logging.basicConfig(level=logging.INFO, filename="logs/serverside.log", filemode="w")

class Client:
    def __init__(self, sock, db):
        self.sock = sock
        self.db = db

        self.user = None
        self.selected_aircraft = None


    def handle_client(self):
        global exit_all
        global logging

        while not exit_all:
            try:
                data = recv_by_size(self.sock)
                if data == "":
                    logging.error("Seems like the client disconnected.")
                    break

                to_send = self.do_action(data, self.db)
                send_with_size(self.sock, to_send)

                if self.selected_aircraft is not None:
                    pass # Need to enter game

            except socket.error as error:
                if error.errno == 10054:
                    # 'Connection reset by peer'
                    logging.error(f"Error {error.errno}. Client is Gone. {str(sock)} reset by peer.")
                    break
                else:
                    logging.error(f"General Sock Error {error.no}. Client {str(sock)} disconnected.")
                    break

            except Exception as error:
                logging.error(f"General Error: {error}")
                break

        sock.close()

    def do_action(self, data):
        """
        check what client ask and fill to send with the answer
        """
        to_send = "Not Set Yet"
        fields = data.decode().split("#")
        action = fields[0]
        parameters = fields[1]

        logging.info(f"Got client request {action} -- {str(parameters)}")

        if action == "LOGR":
            parameter_fields = parameters.split("$")
            to_send = ("LOGA#" + self.db.log_in(parameter_fields[0], parameter_fields[1])).encode()
            if to_send == 1:
                self.user = parameter_fields[0]
        elif action == "SGNR":
            parameter_fields = parameters.split("$")
            to_send = ("SGNA#" + self.db.sign_up(parameter_fields[0], parameter_fields[1])).encode()
            if to_send == 1:
                self.user = parameter_fields[0]
        elif action == "MNYR":
            try:
                to_send = ("MNYR#" + self.db.get_money(self.user)).encode()
            except Exception as error:
                logging.error(f"General Error: {error}")
        elif action == "BUYR":
            try:
                to_send = ("BUYR#" + self.db.buy_aircraft(self.user, parameter_fields)).encode()
            except Exception as error:
                logging.error(f"General Error: {error}")
        elif action == "SELR":
            try:
                to_send = ("SELA#" + self.db.select_aircraft(self.user, parameter_fields)).encode()
                if to_send[5] == "1": # Chosen aircraft
                    self.selected_aircraft = parameter_fields
            except Exception as error:
                logging.error(f"General Error: {error}")
        else:
            to_send = build_message("ERR").encode() + b"001"
        return to_send


def main():
    global exit_all

    exit_all = False
    db = SQL_ORM.AccountManagementORM()

    s = socket.socket()
    s.bind(("0.0.0.0", 33445))

    s.listen(4)
    logging.info("after listen")

    threads = []
    i = 1
    for i in range(10):  # For how long we want the server to run.
        cli_s, addr = s.accept()
        client = Client(cli_s, db)
        t = threading.Thread(target=client.handle_client)
        t.start()
        i += 1
        threads.append(t)

    exit_all = True
    for t in threads:
        t.join()
    s.close()


if __name__ == "__main__":
    main()
