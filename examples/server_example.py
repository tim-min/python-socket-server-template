from server import Server

def echo_command(args, client):
    message = " ".join(args)
    client.send_message(message)
    return 2

def admin_command_example(args, client):
    client.send_message("Hello, admin!)")
    return 2

def move_me(args, client):
    global server
    if len(args) < 1:
        return "[Error] Invalid args!"
    server.move_client(client, int(args[0]))
    return 1

def create_room(args, client):
    global server
    if len(args) < 1:
         return "[Error] Invalid args!"
    room_id = server.create_room(args[0])
    return f"[Success] room id - {room_id}"

def room_messgae(args, client):
    global server
    if len(args) < 1:
        return "[Error] Invalid args!"
    if client.room_id != -1:
        server.get_room(client.room_id).send_message(" ".join(args))
    else:
        return "[Error] You don't have a room!"


server = Server(host="", port=9999, adm_login="admin", adm_password="1111")
server.add_command("echo", echo_command)
server.add_command("amiadmin", admin_command_example, admin_command=True)
server.add_command("moveme", move_me)
server.add_command("create_room", create_room)
server.add_command("rm", room_messgae)
server.start()
