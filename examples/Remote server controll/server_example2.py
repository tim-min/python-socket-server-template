from TMserver import TMServer
import subprocess


# Пример реализации удалённого доступа к системе:


def run_command(args, client): # Тут выполняем команду, которую ввел пользователь
    command = list(args)

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response, error = proc.communicate()

    client.send_message('Result:\n' + response.decode("ascii") + "\n Error:\n" + error.decode('ascii'))
    return 2


server = TMServer(host="", port=9999, adm_login="admin", adm_password="1111") # Инициализируем TMServer
server.add_command("#", run_command, admin_command=True) # Добавляем новую команду, которая будет выполняться только с правами администратора
server.start()
