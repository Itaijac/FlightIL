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
open_world_socket.settimeout(0.1)
open_world_socket.bind(('0.0.0.0', 8888))

client_addresses = {}
""" End Of Open World Global Variables """


def handle_clients_open_world():
    while True:
        try:
            data, client_address = open_world_socket.recvfrom(1024)
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
        elif action == "ADDS":
            token = fields[1]
            with lock:
                for k,v in client_addresses.items():
                    if v == token:
                        client_addresses[k] = client_address
                        to_send = f"ADDC"
                        open_world_socket.sendto(to_send.encode(), client_address)
                        break
            


def broadcast_players():
    while True:
        with lock:
            location_data = players.values()

        to_send = f'UPDA#'
        for username, aircraft, x, y, z, h, p, r in location_data:
            to_send += f"{username}|{aircraft}|{x}|{y}|{z}|{h}|{p}|{r}$"

        to_send = to_send[:-1] # Get rid of last $

        for client_address in client_addresses.values():
            # Check if tuple and not token
            if type(client_address) is tuple:
                open_world_socket.sendto(to_send.encode(), client_address)
        time.sleep(0.04)

def handle_client(sock, addr, thread_id, db):
    global exit_all
    global logging
    global players

    global client_addresses

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

                    if aircraft in account.inventory.split('|'):
                        with lock:
                            players[token] = [account.username, aircraft, 0, 0, 0, 0, 0, 0]
                            client_addresses[account.username] = token
                        account.token = token
                        to_send = f"SELA#1"
                        current_window = "open world"
                    else:
                        to_send = f"SELA#0"

            elif current_window == "open world":
                if action == "EXTG":
                    with lock:
                        del players[token]
                        del client_addresses[account.username]
                    current_window = "select windows"
                    continue
            
            send_with_size(sock, to_send)

        except socket.error as error:
            if error.errno == 10054:
                # 'Connection reset by peer'
                logging.error(f"Error {error.errno}. Client is Gone. {str(sock)} reset by peer.")
            else:
                logging.error(f"General Sock Error {error.no}. Client {str(sock)} disconnected.")
            
            if current_window == "open world":
                with lock:
                    del players[token]
                    del client_addresses[account.username]
            break

        except Exception as error:
            logging.error(f"General Error: {error}")

            if current_window == "open world":
                with lock:
                    del players[token]
                    del client_addresses[account.username]
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
