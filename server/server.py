import socket
from account_management import Account, AccountManagement
import threading
import logging
import time
import rsa
import pickle
from protocol import send_with_size, recv_by_size

exit_all = False
logging.basicConfig(level=logging.INFO, filename="logs/serverside.log", filemode="w")

""" Open World Global Variables """
players = {}
lock = threading.Lock()

open_world_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
open_world_socket.settimeout(0.001)
open_world_socket.bind(('0.0.0.0', 8888))

client_addresses = {}
""" End Of Open World Global Variables """


def handle_clients_open_world():
    """
    This function handles incoming data from clients in an open world game. It extracts
    the action and parameters from the incoming message and updates the players' positions
    or client addresses accordingly.

    """
    while True:
        try:
            data, client_address = open_world_socket.recvfrom(1024) # Receive data from clients
        except:
            continue
        fields = data.decode().split("#") # Split data into fields based on "#" delimiter
        action = fields[0] # Get the action from the first field
        if action == "UPDR": # If the action is "UPDR", update the player's position
            parameters = fields[1]
            token, x, y, z, h, p, r = parameters.split("$") # Extract the position and rotation
            with lock:
                try:
                    players[token] = [players[token].pop(0), players[token].pop(0), x, y, z, h, p, r] # Update player's position
                except:
                    logging.error("Invalid token recieved.")
        elif action == "ADDS": # If the action is "ADDS", update the client's address
            token = fields[1]
            with lock:
                for k,v in client_addresses.items():
                    if v == token:
                        client_addresses[k] = client_address
                        to_send = f"ADDC"
                        open_world_socket.sendto(to_send.encode(), client_address) # Send acknowledgement message to the client
                        break


def broadcast_players():
    """
    This function broadcasts the players' positions to all clients in the open world game.

    """
    while True:
        with lock:
            location_data = players.values() # Get the current location data of all players

        to_send = f'UPDA#' # Start building the message to be sent
        for username, aircraft, x, y, z, h, p, r in location_data:
            to_send += f"{username}|{aircraft}|{x}|{y}|{z}|{h}|{p}|{r}$" # Add each player's position data to the message

        to_send = to_send[:-1] # Get rid of last "$" delimiter

        with lock:
            for client_address in client_addresses.values():
                if type(client_address) is tuple: # Check if the client address is a tuple (i.e., not a token)
                    open_world_socket.sendto(to_send.encode(), client_address) # Send the message to the client's address
        time.sleep(0.02) # Sleep for a short time before sending the next update


def handle_client(sock, addr, thread_id, db, AES_key):
    """
    This function handles a single client connection by receiving and processing messages sent from the client.
    It also sends responses back to the client as needed."
    """
    global exit_all
    global logging
    global players

    global client_addresses

    account = Account()
    current_window = "login/setup"
    logging.info(f"Client number {str(thread_id)} connected")

    while not exit_all:
        try:
            # Recieve data from client
            data = recv_by_size(sock, AES_key)
            
            # Check if server is down
            if data == "":
                logging.error("Seems like the client disconnected.")
                break
            
            # Parse response from server
            fields = data.decode().split("#")
            action = fields[0]
            to_send = f"ERRR#0"

            # According to the value of current_window treat the request
            if current_window == "login/setup":
                parameters = fields[1]
                username, password = parameters.split("$") # Extract the username, password

                # Fill in the instance of the dataclass Account.
                account.username = username
                if action == "LOGR":
                    db.log_in(account, password)
                    to_send = f"LOGA#{int(account.is_logged)}".encode()
                elif action == "SGNR":
                    db.sign_up(account, password)
                    to_send = f"SGNA#{int(account.is_logged)}".encode()

                # If login/sign up was succesful, change windows accordingly
                if account.is_logged:
                    current_window = "select windows"

            elif current_window == "select windows":
                if action == "SHPR":
                    balance, inventory = db.get_balance_and_inventory(account)
                    to_send = f"SHPA#{balance}${inventory}".encode()
                elif action == "BUYR":
                    parameters = fields[1]
                    is_bought = db.buy_aircraft(account, parameters)
                    to_send = f"BUYA#{int(is_bought)}".encode()
                elif action == "SELR":
                    aircraft, token = fields[1].split('|')

                    # If the aircraft chosen is in the inventory, move to open world
                    if aircraft in account.inventory.split('|'):
                        with lock:
                            # Add player to the global lists. The token will be replaced by the clients' address
                            # In the future
                            players[token] = [account.username, aircraft, 0, 0, 0, 0, 0, 0]
                            client_addresses[account.username] = token

                        # Fill in account
                        account.token = token

                        to_send = f"SELA#1".encode()

                        # Change window to open world
                        current_window = "open world"

                        # Start measuring time for balance updating purposes
                        time_started_playing = time.time()
                    else:
                        # If the user tried to manipulate the server and join with an aircraft
                        # that does not belong to him
                        to_send = f"SELA#0".encode()

            elif current_window == "open world":
                # If the player wishes to exist the open world
                if action == "EXTG":
                    with lock:
                        # Get rid of his spot in the global lists
                        del players[token]
                        del client_addresses[account.username]

                        # Update his balance for his time playing
                        earned_coins = int((time.time() - time_started_playing) / 60)
                        db.update_balance(account, earned_coins)
                    current_window = "select windows"
                    continue
            
            send_with_size(sock, to_send, AES_key)

        except socket.error as error:
            logging.error(f"General Sock Error. Client {str(sock)} disconnected.")
            
            # Remove client from global lists as part of exception handeling,
            # to prevent sending updates to a dead socket.
            if current_window == "open world":
                with lock:
                    del players[token]
                    del client_addresses[account.username]
                    earned_coins = (time.time() - time_started_playing) / 60
                    db.update_balance(account, earned_coins)
            break

        except Exception as error:
            logging.error(f"General Error: {error}")

            # Remove client from global lists as part of exception handeling,
            # to prevent sending updates to a dead socket.
            if current_window == "open world":
                with lock:
                    del players[token]
                    del client_addresses[account.username]
                    earned_coins = (time.time() - time_started_playing) / 60
                    db.update_balance(account, earned_coins)
            break

    sock.close()


def main():
    global exit_all

    exit_all = False

    # Open the Database for future use
    db = AccountManagement()
    db.create_table()

    # Set up the RSA key exchange
    public_key, private_key = rsa.newkeys(1024)

    # Create the socket and bind it
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
        # Accept new client
        cli_s, addr = s.accept()

        # key exchange with specific client
        send_with_size(cli_s, pickle.dumps(public_key))

        AES_key_encoded = recv_by_size(cli_s)
        AES_key = rsa.decrypt(AES_key_encoded, private_key)
        
        t = threading.Thread(target=handle_client, args=(cli_s, addr, i, db, AES_key))
        t.start()
        i += 1
        threads.append(t)

    exit_all = True
    for t in threads:
        t.join()
    s.close()


if __name__ == "__main__":
    main()
