# python-socket-server-template
<h2> Create your own python socket server with commands using this template! </h2>

<h3>Creating server:</h3>

```python

server = TMServer(host="", port=9999, adm_login="admin", adm_password="1111")
server.start()

```
<li>adm_login and adm_password are requiered for access to admin commands</li>

<h3> Creating command </h3>

```python
  
  def echo_command(args, client):
    message = " ".join(args)
    client.send_message(message)
    return 2
  
  server.add_command("echo", echo_command)

```

<li>You should create method for your command with "args" and "client" arguments. For example, if client will use "echo 123 456", args will be ["123", "456"]. client is client class</li>
<li> Return types: </li>
If you want to send something to client after command work, you can return message. Example: <br>

```python

def move_me(args, client):
    global server
    if len(args) < 1:
        return "[Error] Invalid args!"
    server.move_client(client, int(args[0]))
    return 1

```
Here, if client will use command with incorrect arguments count, he will receive "[Error] Invalud args!". But, if everything is ok, you can return 1, so client will receive [Ok] Success!. <br>
<br>All return codes (except your own return text): <br>
1 - [Ok] Success!<br>
2 - empty return (client will receive nothing)

<li>Creating admin command:</li><br>

```python

def admin_command_example(args, client):
    client.send_message("Hello, admin!)")
    return 2

server.add_command("amiadmin", admin_command_example, admin_command=True)

```

This command will work only if client become an admin. To do this, use server command "alogin admin_login admin_password"<br>

<h3> Other Server methods: </h3>

```python
TMServer.get_client(cleint_id) # returns client class (or -1 if client not found).
TMServer.get_client_room(client) # returns client's room_id (or None if he don't have a room).
TMServer.get_all_rooms() # returns list of tuples that contains id and room name. Example: [(0, "test"), (1, "friends")].
TMServer.get_all_clients() # returns list of tuples that contains id and client class. Example: [(0, class), (1, class)].
TMServer.move_client(client, room_id) # transfer client to the room
TMServer.create_room(room_name) # creates new room (returns room id)
TMServer.delete_room(room_id) # delete room
TMServer.get_room(room_id) # returns room class
TMServer.add_command(command_name, target, admin_command) # creates new command

```

<h3> Client class methods: </h3>

``` python
client.send_message(message) # sends message to client
client.get_info() # returns client id, room_id, is_admin flag

```

<h3> Room class methods: </h3>

``` python

room.send_message(message) # sends message to all clients in the room
room.remove_user(user_id) # removes user from the room

```


