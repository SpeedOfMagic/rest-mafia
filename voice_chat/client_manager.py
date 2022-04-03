import random
import socket
import time


class Profile:
    name: str
    sock: socket.socket
    addr: str
    room: int

    def __init__(self, name, sock, addr):
        self.name = name
        self.sock = sock
        self.addr = addr
        self.room = 0


class ClientManager:
    clients: dict[int, Profile]
    name_id: dict[str, int]

    def __init__(self):
        self.clients = {}
        self.name_id = {}
        random.seed(time.time_ns())

    def __getitem__(self, ind):
        return self.clients[ind]

    @staticmethod
    def gen_client_id():
        return random.randint(0, 2 ** 32 - 1)

    def add_client(self, profile: Profile) -> int:
        client_id = self.gen_client_id()
        while client_id in self.clients:
            client_id = self.gen_client_id()
        self.clients[client_id] = profile
        self.name_id[profile.name] = client_id
        return client_id

    def disconnect_client(self, client_id: int):
        self.clients[client_id].sock.close()
        del self.clients[client_id]
