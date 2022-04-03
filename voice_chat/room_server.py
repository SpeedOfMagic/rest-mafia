import socket
import threading
from time import sleep

from client_manager import ClientManager
from protocol import MessageType, Message,\
    ListResponseMessage, ConnectedMessage, DisconnectedMessage, GameStartingMessage
from mafia.servicer import build_server
from mafia.common import WAIT_TIME_TO_START, Phase


class RoomServer:
    RETRY_LIMIT = 3
    MIN_PLAYER_COUNT = 4

    client_manager: ClientManager
    client_ids: set[int]
    game_starting: bool

    phase: Phase
    mafia: list[str]
    dead: set[str]
    finish_thread: threading.Thread

    def __init__(self, client_manager: ClientManager, room_id: int):
        self.client_manager = client_manager
        self.client_ids = set()
        self.mafia_game = None
        self.game_starting = False
        self.port = 10000 + room_id

        self.phase = Phase.DAY
        self.dead = set()
        self.mafia = []

    def add_client(self, client_id: int):
        self.client_ids.add(client_id)
        self.handle_message(client_id, ConnectedMessage(self.client_manager[client_id].name))
        if self.game_starting:
            self.client_manager[client_id].sock.sendall(GameStartingMessage(self.port).encode())
        if len(self.client_ids) == self.MIN_PLAYER_COUNT and self.mafia_game is None:
            self.launch_game()

    def launch_game(self):
        self.game_starting = True
        for client_id in self.client_ids:
            self.client_manager[client_id].sock.sendall(GameStartingMessage(self.port).encode())
        sleep(WAIT_TIME_TO_START)
        self.game_starting = False
        self.mafia_game = build_server([self.client_manager[cid].name for cid in self.client_ids], self.port, self)
        self.mafia_game.start()

    def remove_client(self, client_id: int):
        self.client_ids.remove(client_id)
        self.handle_message(client_id, DisconnectedMessage(self.client_manager[client_id].name))

    def broadcast(self, sender_id, msg_bytes):
        client_ids = self.get_clients_to_broadcast(sender_id)
        for client_id in client_ids:
            if client_id != sender_id:
                try:
                    self.client_manager[client_id].sock.sendall(msg_bytes)
                except socket.error as err:
                    print(f'ERROR Could not broadcast message to client {client_id}:', err)

    def handle_message(self, sender_id: int, msg: Message):
        if msg.message_type in [MessageType.VOICE, MessageType.CONNECTED, MessageType.DISCONNECTED]:
            msg.name = self.client_manager[sender_id].name
            self.broadcast(sender_id, msg.encode())
        elif msg.message_type == MessageType.LIST_REQUEST:
            names = sorted([self.client_manager[client_id].name for client_id in self.client_ids])
            self.client_manager[sender_id].sock.sendall(ListResponseMessage(names).encode())
        else:
            print(f'Discarded message with unknown message type: {msg.message_type}')

    def get_clients_to_broadcast(self, sender_id: int):
        if self.client_manager[sender_id].name in self.dead:
            return set()
        if self.phase == Phase.DAY:
            return set(filter(lambda cl_id: cl_id in self.client_manager.clients, self.client_ids))
        elif self.phase == Phase.NIGHT:
            if self.client_manager[sender_id].name in self.mafia:
                return [self.client_manager.name_id[name] for name in self.mafia]
            else:
                return set()

    def notify_phase(self, phase: Phase):
        self.phase = phase

    def notify_mafia(self, mafia: list[str]):
        self.mafia = mafia

    def notify_dead(self, name: str):
        self.dead.add(name)

    def notify_finish(self):
        self.finish_thread = threading.Thread(target=self.finish)

    def finish(self):
        self.mafia_game.wait_for_termination()
        self.mafia_game = None
