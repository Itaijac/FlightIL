import socket
from SQL_ORM import Account, AccountManagementORM
import threading
import logging
from protocol import send_with_size, recv_by_size

exit_all = False
logging.basicConfig(level=logging.INFO, filename="logs/serverside.log", filemode="w")

def handle_client(sock, thread_id, db):
    global exit_all
    global logging

    account = Account()
    current_window = "login/setup"
    logging.info(f"Client number {str(thread_id)} connected")

    while not exit_all:
        try:
            data = recv_by_size(sock)
            if data == "":
                logging.error("Seems like the client disconnected.")
                break
            
            fields = data.decode().split("#")
            action = fields[0]

            if current_window == "login/setup":
                parameters = fields[1]
                username, password = parameters.split("$") # extract the username, password
                account.username = username
                if action == "LOGR":
                    db.log_in(account, password)
                    to_send = f"LOGA#{int(account.is_logged)}".encode()
                elif action == "SGNR":
                    db.sign_up(account, password)
                    to_send = f"SGNA#{int(account.is_logged)}".encode()

                if account.is_logged:
                    current_window = "select windows"
            elif current_window == "select windows":
                if action == "SHPR":
                    balance, inventory = db.get_balance_and_inventory(account)
                    to_send = f"SHPA#{balance}${inventory}".encode()
                if action == "BUYR":
                    parameters = fields[1]
                    is_bought = db.buy_aircraft(account, parameters)
                    to_send = f"BUYA#{is_bought}"

            send_with_size(sock, to_send)

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


def main():
    global exit_all

    exit_all = False
    db = AccountManagementORM()
    db.create_table()

    s = socket.socket()
    s.bind(("0.0.0.0", 33445))

    s.listen(4)
    logging.info("after listen")

    threads = []
    i = 1
    for i in range(1000):  # For how long we want the server to run.
        cli_s, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(cli_s, i, db))
        t.start()
        i += 1
        threads.append(t)

    exit_all = True
    for t in threads:
        t.join()
    s.close()


if __name__ == "__main__":
    main()
