import socket
from SQL_ORM import Account, AccountManagementORM
import threading
import logging
import time
from protocol import send_with_size, recv_by_size

exit_all = False
logging.basicConfig(level=logging.INFO, filename="logs/serverside.log", filemode="w")

""" Open World Global Variables """
players = {}
lock = threading.Lock()

open_world_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
open_world_socket.settimeout(0.05)
open_world_socket.bind(('0.0.0.0', 8888))

client_addresses = []
""" End Of Open World Global Variables """


def handle_clients_open_world():
    while True:
        try:
            data, client_address = open_world_socket.recvfrom(1024)
            if client_address not in client_addresses:
                client_addresses.append(client_address)
        except:
            continue
        fields = data.decode().split("#")
        action = fields[0]
        if action == "UPDR":
            parameters = fields[1]
            token, x, y, z, h, p, r = parameters.split("$") # extract the position and rotation
            with lock:
                try:
                    players[token] = [players[token].pop(0), players[token].pop(0), x, y, z, h, p, r] # keep aircraft type
                except:
                    logging.error("Invalid token recieved.")

def broadcast_players():
    while True:
        with lock:
            location_data = players.values()

        to_send = f'UPDA#'
        for username, aircraft, x, y, z, h, p, r in location_data:
            to_send += f"{username}|{aircraft}|{x}|{y}|{z}|{h}|{p}|{r}$"

        for client_address in client_addresses:
            open_world_socket.sendto(to_send.encode(), client_address)
        time.sleep(0.01)

def handle_client(sock, addr, thread_id, db):
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
            to_send = f"ERRR#0"

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
                elif action == "BUYR":
                    parameters = fields[1]
                    is_bought = db.buy_aircraft(account, parameters)
                    to_send = f"BUYA#{int(is_bought)}"
                elif action == "SELR":
                    aircraft, token = fields[1].split('|')
                    with lock:
                        players[token] = [account.username, aircraft, 0, 0, 0, 0, 0, 0]
                    to_send = f"SELA#1" # Need to add 1 or 0 verification

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

    # Open world threads
    client_thread = threading.Thread(target=handle_clients_open_world)
    client_thread.start()

    broadcast_thread = threading.Thread(target=broadcast_players)
    broadcast_thread.start()

    s.listen(4)
    logging.info("after listen")

    threads = []
    i = 1
    for i in range(1000):  # For how long we want the server to run.
        cli_s, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(cli_s, addr, i, db))
        t.start()
        i += 1
        threads.append(t)

    exit_all = True
    for t in threads:
        t.join()
    s.close()


if __name__ == "__main__":
    main()
