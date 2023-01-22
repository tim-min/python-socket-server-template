import socket
import threading


class InvalidRoom(Exception):
    def __init__(self, message="You are trying to use room, that does not exist!"):
        self.message = message
        super().__init__(self.message)

class InvalidClient(Exception):
    def __init__(self, message="You are trying to use client, that does not exist!"):
        self.message = message
        super().__init__(self.message)


class Client:
    def __init__(self, conn, address, user_id) -> None:
        self.conn = conn
        self.address = address
        self.room_id = -1
        self.is_admin = False
        self.user_id = user_id
    
    def send_message(self, message):
        self.conn.send(bytes(message, encoding="utf-8"))
    
    def get_info(self):
        return (self.user_id, self.room_id, self.is_admin)


class Room:
    def __init__(self, name) -> None:
        self.name = name
        self.members = list()
    
    def send_message(self, message): # sending something to all users
        for member in self.members:
            member.conn.send(bytes(f"[Room Chat] {message}", encoding="utf-8"))
    
    def remove_user(self, user_id):
        for ind, user in enumerate(self.members):
            if user.user_id == user_id:
                user.room_id = -1
                del self.members[ind]
                break


class TMServer:
    def __init__(self, host, port, adm_password, adm_login) -> None:
        self.host, self.port = host, port
        self.sock = socket.socket()
        self.adm_password, self.adm_login = adm_password, adm_login
        self.clients = list() # online clients
        self.rooms = list() # online rooms
        self.new_cons_thread = threading.Thread(target=self.get_new_connections)
        self.client_threads = list()
        self.commands = {
            "alogin": self.admin_login
        }
        self.admin_commands = dict()
    
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
    
    def get_new_connections(self): # check for new connections
        while True:
            conn, address = self.sock.accept()
            print("[NEW USER CONNECTED]", conn, address)
            client = Client(conn, address, len(self.clients))
            self.clients.append(client)
            self.client_threads.append(threading.Thread(target=lambda: self.listen_commands(client)))
            self.client_threads[-1].start()
    
    def listen_commands(self, client): # listening commands from user
        while True:
            try:
                data = client.conn.recv(1024).decode("utf-8")
                data = data.split(":")

                success = 1

                for command in data:
                    command = command.split()
                    if self.commands.get(command[0]):
                        success = self.commands[command[0]](command[1:], client)
                    elif self.admin_commands.get(command[0]) and client.is_admin:
                        success = self.admin_commands[command[0]](command[1:], client)
                    else:
                        success = "[Error] Command not found or arguments are incorrect!"

                if success == 1:
                    client.conn.send(b"[Ok] Success!")
                elif success != 2 and success: # 2 for emty message, 1 for success, other is error message
                    client.conn.send(bytes(success, encoding="utf-8"))
            except ConnectionResetError: # if client disconnected, delete him)
                client_index = self.clients.index(client)
                print(f"[CLIENT DISCONNECTED] id - {client.user_id}")
                if client.room_id != -1:
                    self.rooms[client.room_id].remove_user(client.user_id)
                self.clients.remove(client)
                del self.client_threads[client_index]
                break

