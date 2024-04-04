import socket
import threading
import rsa
import json
import time
from datetime import datetime


class InvalidRoom(Exception):
    def __init__(self, message="You are trying to use room, that does not exist!"):
        self.message = message
        super().__init__(self.message)


class InvalidClient(Exception):
    def __init__(self, message="You are trying to use client, that does not exist!"):
        self.message = message
        super().__init__(self.message)


class SecurityError(Exception):
    def __init__(self, message = "Security Error") -> None:
        self.message = message
        super().__init__(self.message)


class Logger:
    def __init__(self, log_file_path) -> None:
        self.log_file_path = log_file_path
        self.log_file = open(log_file_path, "a")
        self.log_file.write(f"[SERVER] Server Started | {datetime.now()} \n")
        self.log_file.close()

        print("[!] Logger started")
    
    def create_new_string(self, string):
        self.log_file = open(self.log_file_path, "a")
        self.log_file.write(string + "\n")
        self.log_file.close()

    def new_client_connection(self, client):
        self.create_new_string(f"[SERVER] New user connected. Address: {client.address}. Session UID: {client.user_id} | {datetime.now()} \n")
    
    def user_disconnected(self, client):
        self.create_new_string(f"[SERVER] User disconnected. Address: {client.address}. Session UID: {client.user_id} | {datetime.now()}\n")
    
    def command_used(self, client, command_name, arguments):
        self.create_new_string(f"[USER_ACTIONS] Command '{command_name}' used by client (id {client.user_id}, {client.address}). Arguments: {arguments} | {datetime.now()}\n")


class TMFirewall:
    def __init__(self, config_file_path) -> None:
        self.config_file = open(config_file_path)
        self.settings = json.load(self.config_file)["TMfirewall"]

        print("[!] firewall started")

    def check_xss(self, message):
        for x in self.settings["xss_blacklist"]:
            if x in message:
                return 0
        
        return 1

    def check_sql(self, message):
        if message.count("'")%2 or message.count('"')%2:
            return 0
        
        for x in self.settings["sql_blacklist"]:
            if x in message:
                return 0
        
        return 1

    def check_client(self, client):
        if client.address in self.settings["banned_clients"]:
            return 0

        time_now = int(time.time())

        if client.last_message_secs is None:
            client.last_message_secs = time_now
            return 1
        else:
            if time_now <= client.last_message_secs + 1:
                client.messages_per_sec_counter += 1

                if client.messages_per_sec_counter > self.settings["max_messages_ps"]:
                    return 0
            else:
                client.messages_per_sec_counter = 0
                client.last_message_secs = time_now

        return 1



class Client:
    def __init__(self, conn, address, user_id) -> None:
        self.conn = conn
        self.address = address
        self.room_id = -1
        self.is_admin = False
        self.user_id = user_id
        self.last_message_secs = None
        self.messages_per_sec_counter = 0
        self.RSA_key = None
    
    def send_message(self, message):
        try:
            self.conn.send(rsa.encrypt(message.encode(), self.RSA_key))
        except OverflowError:
            self.conn.send(rsa.encrypt("[!] Too large message to send".encode(), self.RSA_key))
    
    def send_bytes(self, data):
        self.conn.send(data)
    
    def get_info(self):
        return (self.user_id, self.room_id, self.is_admin)


class Room:
    def __init__(self, name) -> None:
        self.name = name
        self.members = list()
    
    def send_message(self, message):
        for member in self.members:
            member.send_message(f"[Room Chat] {message}")
    
    def remove_user(self, user_id):
        for ind, user in enumerate(self.members):
            if user.user_id == user_id:
                user.room_id = -1
                del self.members[ind]
                break


class TMServer:
    def __init__(self, host, port, adm_password, adm_login, log_file_path="ServerLog.txt") -> None:
        self.host, self.port = host, port
        self.sock = socket.socket()
        self.adm_password, self.adm_login = adm_password, adm_login
        self.clients = list()
        self.rooms = list()
        self.new_cons_thread = threading.Thread(target=self.get_new_connections)
        self.client_threads = list()
        self.commands = {
            "alogin": self.admin_login
        }
        self.admin_commands = dict()

        self.func_disconnected_user = None
        self.func_connected_user = None

        self.RSA_keys = tuple(rsa.newkeys(1024))

        self.firewall = TMFirewall("config.json")

        self.logger = Logger(log_file_path)
    
    def get_client_room(self, client):
        if client.room_id == -1:
            return None
        return client.room_id

    def get_all_rooms(self):
        answer = [(id, room.name) for id, room in enumerate(self.rooms) if room != -1]
        return answer
    
    def get_all_clients(self):
        answer = [(id, client) for id, client in enumerate(self.clients)]
        return answer

    def get_client(self, client_id):
        try:
            client = [client for client in self.clients if client.user_id == client_id][0]
            return client
        except IndexError:
            return -1
    
    def move_client(self, client, room_id):
        if len(self.rooms) > room_id and room_id >= 0 and self.rooms[room_id] != -1:
            client.room_id = room_id
            self.rooms[room_id].members.append(client)
        else:
            raise InvalidRoom(f"You are trying to move client (id={client.user_id}) to room (id={room_id}) that does not exist!")
            

    def create_room(self, room_name):
        room = Room(room_name)
        self.rooms.append(room)
        return len(self.rooms)-1
    
    def delete_room(self, room_id):
        if len(self.rooms) > room_id and room_id >= 0 and self.rooms[room_id] != -1:
            for client in self.rooms[room_id].members:
                client.room_id = -1
            self.rooms[room_id] = -1
        else:
            raise InvalidRoom(f"You are trying to delete room (id={room_id}) that does not exist!")

    def get_room(self, room_id):
        if len(self.rooms) > room_id and room_id >= 0 and self.rooms[room_id] != -1:
            return self.rooms[room_id]
        else:
            raise InvalidRoom(f"You are trying to get room (id={room_id}) that does not exist!")

    def start(self):
        self.sock.bind((self.host, int(self.port)))
        self.sock.listen(1)
        self.new_cons_thread.start()
    
    def admin_login(self, args, client):
        if len(args) < 2:
            return "[Error] Incorrect arguments!"
        if args[0] == self.adm_login and args[1] == self.adm_password:
            client.is_admin = True
        return 1

    def add_command(self, command_name, target, admin_command=False):
        if not admin_command:
            self.commands[command_name] = target
        else:
            self.admin_commands[command_name] = target
    
    def get_new_connections(self):
        while True:
            conn, address = self.sock.accept()
            print("[NEW USER CONNECTED]", conn, address)

            client = Client(conn, address, len(self.clients))

            check_client = self.firewall.check_client(client)
            if not check_client:
                print("[USER DISCONNECTED]", conn, address)
                continue
            
            self.logger.new_client_connection(client)

            if self.func_connected_user is not None:
                self.func_connected_user(client.user_id)

            client.send_bytes(self.RSA_keys[0].save_pkcs1("PEM"))

            try:
                client.RSA_key = rsa.PublicKey.load_pkcs1(client.conn.recv(1024))
            except Exception as e:
                print("[USER DISCONNECTED] (Error with RSA keys)", conn, address)
                self.logger.create_new_string(f"[ERROR] Failed RSA configuration with client (id {client.user_id}, {client.address}) | {datetime.now()}")
                continue

            self.logger.create_new_string(f"[SERVER] RSA configured with client (id {client.user_id}, {client.address}) | {datetime.now()}")
            client.send_message("[OK]")

            self.clients.append(client)
            self.client_threads.append(threading.Thread(target=lambda: self.listen_commands(client)))
            self.client_threads[-1].start()
    
    def fw_check_command(self, command):
        xss_check_result, sql_check_result = 1, 1

        if command[0] in self.firewall.settings["xss_check_commands"]:
            xss_check_result = self.firewall.check_xss(" ".join(command[1:]))
        if command[0] in self.firewall.settings["sql_check_commands"]:
            sql_check_result = self.firewall.check_sql(" ".join(command[1:]))
        
        if not xss_check_result or not sql_check_result:
            return 0

        return 1

    def listen_commands(self, client): # listening commands from user
        while True:
            try:
                data = rsa.decrypt(client.conn.recv(1024), self.RSA_keys[1]).decode()
                data = data.split(":")

                success = 1

                check_client = self.firewall.check_client(client)
                if not check_client:
                    raise SecurityError

                for command in data:
                    command = command.split()
                    if self.commands.get(command[0]):

                        if not self.fw_check_command(command):
                            success = "[ERROR] Dangerous actions detected!"
                            self.logger.create_new_string(f"[ERROR] Dangerous actions detected. Client (id {client.user_id}, {client.address}) used command {command[0]} with dangerous arguments ({' '.join(command[1:])}) | {datetime.now()}")
                            break

                        success = self.commands[command[0]](command[1:], client)
                        self.logger.command_used(client, command[0], " ".join(command[1:]))
                    elif self.admin_commands.get(command[0]) and client.is_admin:
                        
                        if not self.fw_check_command(command):
                            success = "[ERROR] Dangerous actions detected!"
                            self.logger.create_new_string(f"[ERROR] Dangerous actions detected. Client (id {client.user_id}, {client.address}) used command {command[0]} with dangerous arguments ({' '.join(command[1:])}) | {datetime.now()}")
                            break

                        success = self.admin_commands[command[0]](command[1:], client)
                        self.logger.command_used(client, command[0], " ".join(command[1:]))
                    else:
                        success = "[Error] Command not found or arguments are incorrect!"

                if success == 1:
                    client.send_message("[Ok] Success!")
                elif success != 2 and success: # 2 for emty message, 1 for success, other is error message
                    client.send_message(success)

            except (ConnectionResetError, SecurityError, IndexError, rsa.DecryptionError): # if client disconnected, delete him)
                client_index = self.clients.index(client)
                print(f"[CLIENT DISCONNECTED] id - {client.user_id}")
                self.logger.user_disconnected(client)

                if self.func_disconnected_user is not None:
                    self.func_disconnected_user(client.user_id) 

                if client.room_id != -1:
                    self.rooms[client.room_id].remove_user(client.user_id)
                self.clients.remove(client)
                del self.client_threads[client_index]
                break

