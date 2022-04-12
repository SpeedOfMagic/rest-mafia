import jwt
import socket
import sys
import threading

from protocol import get_message, MessageType, ConnectedResponseMessage
from client_manager import Profile, ClientManager
from server_console import ServerConsole
from room_server import RoomServer
from rest.app import app, dao, secret, get_hash


class Server:
    RETRY_LIMIT = 3

    server_ip: str
    sock: socket.socket
    client_manager: ClientManager
    room_server: dict[int, RoomServer]
    web_server: threading.Thread

    @staticmethod
    def launch_web_server():
        app.run(host='0.0.0.0', port=80)

    def __init__(self):
        self.web_server = threading.Thread(target=self.launch_web_server)
        self.web_server.start()
        self.server_ip = socket.gethostbyname(socket.gethostname())
        while 1:
            try:
                self.port = int(input('Enter port number to run on --> '))

                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.bind((self.server_ip, self.port))

                break
            except socket.error as err:
                print("Couldn't bind to that port:", err)

        self.client_manager = ClientManager()
        self.server_console = ServerConsole(self.client_manager)
        self.room_server = {0: RoomServer(self.client_manager, 0)}

        threading.Thread(target=self.accept_connections).start()
        self.server_console.start()

    def accept_connections(self):
        self.sock.listen(100)

        print('Running on IP: ' + self.server_ip)
        print('Running on port: ' + str(self.port))

        while True:
            client_sock, addr = self.sock.accept()

            msg = get_message(client_sock)

            login_pass = None
            login_success = False
            if msg.message_type != MessageType.CONNECTED or msg.name is None or msg.name == '':
                client_sock.sendall(ConnectedResponseMessage(error='Invalid ConnectedMessage').encode())
                client_sock.close()
                continue
            else:
                jwt_token = msg.name
                try:
                    login_pass = jwt.decode(jwt_token, secret, algorithms=["HS256"])
                    print(login_pass)
                    if 'login' in login_pass and 'password' in login_pass:
                        login_profile = dao.lookup_profile(login_pass['login'])
                        print(login_profile.password, get_hash(login_pass['password']))
                        if login_profile is not None and login_profile.password == get_hash(login_pass['password']):
                            login_success = True
                except jwt.DecodeError:
                    pass
            if not login_success:
                client_sock.sendall(ConnectedResponseMessage(error='Incorrect JWT token').encode())
                client_sock.close()
                continue
            else:
                client_sock.sendall(ConnectedResponseMessage(error='').encode())

            msg.name = login_pass['login']
            client_id = self.client_manager.add_client(Profile(msg.name, client_sock, addr))
            print(f'{msg.name} with client_id={client_id} has connected to the server!')
            threading.Thread(target=self.handle_client, args=(client_id,)).start()

    def handle_client(self, client_id):
        profile = self.client_manager.clients[client_id]
        retry_count = 0
        while True:
            try:
                msg = get_message(profile.sock)
                if msg.message_type == MessageType.ROOM_CHANGE:
                    print(f'Client {client_id} changed room_id from {profile.room} to {msg.room_id}')
                    if client_id in self.room_server[profile.room].client_ids:
                        self.room_server[profile.room].remove_client(client_id)
                    if msg.room_id not in self.room_server:
                        self.room_server[msg.room_id] = RoomServer(self.client_manager, msg.room_id)
                    self.room_server[msg.room_id].add_client(client_id)
                    self.client_manager[client_id].room = msg.room_id
                else:
                    self.room_server[profile.room].handle_message(client_id, msg)
                retry_count = 0
            except socket.error as err:
                if client_id not in self.client_manager.clients:
                    print(f'handle_client({client_id}): connection closed, since client_manager deleted profile')
                    sys.exit(0)
                print('ERROR could not handle client:', err)
                retry_count += 1
                if retry_count > self.RETRY_LIMIT:
                    print(f'ERROR: Amount of retries exceeded. Disconnecting client {client_id}...')
                    self.room_server[profile.room].remove_client(client_id)
                    self.client_manager.disconnect_client(client_id)
                    print(f'Client {client_id} disconnected')
                    sys.exit(1)
                else:
                    print(f'Retrying {retry_count}/3')


server = Server()
