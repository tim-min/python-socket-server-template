from TMserver import TMServer

def echo_command(args, client): # Команда, возвращающая текст, написанный в аргументе
    message = " ".join(args) # Достаём цельное сообщение из аргументов
    client.send_message(message) # Отправляем сообщение
    return 2

def admin_command_example(args, client): # Пример команды, доступной только администраторам
    client.send_message("Hello, admin!)")
    return 2

def move_me(args, client): # Работа с комнатами, перемещение пользователя в комнату
    global server
    if len(args) < 1: # Говорим пользователю об ошибке, если аргументов для работы команды недостаточно
        return "[Error] Invalid args!"
    server.move_client(client, int(args[0])) # Перемещаем пользователя в комнату с id, указанным в первом аргументе
    return 1

def create_room(args, client): # Работа с комнатами, создание комнаты
    global server
    if len(args) < 1:
         return "[Error] Invalid args!"
    room_id = server.create_room(args[0]) # Создаем комнату с id, указанным в первом аргументе
    return f"[Success] room id - {room_id}"

def room_messgae(args, client): # Работа с комнатами, отправка сообщения членам комнаты
    global server
    if len(args) < 1:
        return "[Error] Invalid args!"
    if client.room_id != -1:
        server.get_room(client.room_id).send_message(" ".join(args)) # ищем комнату по id комнаты, в которой находится пользователь, отправляем туда публичное сообщение
    else:
        return "[Error] You don't have a room!"

def leave_room(args, client): # Работа с комнатами, удаления пользователя из комнаты
    global server
    if client.room_id != -1:
        room = server.get_room(client.room_id) # Находим комнату по id
        room.remove_user(client.user_id) # Удаляем пользователя
        return 1
    return "[Error] You don't have a room!"


server = TMServer(host="", port=8002, adm_login="admin", adm_password="1111", log_file_path="ServerLog.txt") # инициализируем TMserver  на локальном хосте с портом 8080

# Далее добавляем наши комианды:
server.add_command("echo", echo_command, admin_command=False)
server.add_command("amiadmin", admin_command_example, admin_command=True)
server.add_command("moveme", move_me)
server.add_command("create_room", create_room)
server.add_command("rm", room_messgae)
server.add_command("leave", leave_room)

#... И запускаем сервер!
server.start()
