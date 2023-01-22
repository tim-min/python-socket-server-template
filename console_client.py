import threading
import socket
import os

# --------------------- CONSOLE CLIENT -----------------------


class Client:
    def __init__(self, host, port) -> None:
        self.sock = socket.socket()
        self.sock.connect((host, int(port)))
        self.listen_thread = threading.Thread(target=self.listen) # thread for getting answers from server
        self.listen_thread.start()
        self.commands_thread = threading.Thread(target=self.commands) # thread for console commands (you can remove it)
        self.commands_thread.start()
        self.client_commands = {
            "clear": self.clear_console
        }
        print("New command: (help for help, clear to clear)")

    def clear_console(self, args):
        os.system("cls")
        print("New command: (help for help, clear to clear)")

    def commands(self): # CONSOLE commands
        while True:
            message = input()
            if self.client_commands.get(message.split()[0]):
                self.client_commands[message.split()[0]](message.split()[1:])
                continue # ignore server check command
            self.sock.send(bytes(message, encoding="utf-8"))
    
    def listen(self): # waiting data from server
        while True:
            data = self.sock.recv(1024)
            data = data.decode("utf-8")
            print(data)


if __name__ == "__main__":
    client = Client(input("Host: "), input("Port: "))
