import grpc
from concurrent import futures

from mafia.common import *
from proto.mafia_service_pb2_grpc import MafiaServicer, add_MafiaServicer_to_server
from mafia_service_pb2 import *
from mafia.game import MafiaGame
from mafia.subscriber_queue import SubscriberQueue


class Servicer(MafiaServicer):
    names: list[str]
    mafia_game: MafiaGame
    day_queue: SubscriberQueue
    night_civilian_queue: SubscriberQueue
    night_mafia_queue: SubscriberQueue
    night_commissar_queue: SubscriberQueue

    def __init__(self, names: list[str], room_server):
        self.names = names
        self.mafia_game = MafiaGame(names)
        self.day_queue = SubscriberQueue(names)
        self.day_finished = set()
        self.night_civilian_queue = SubscriberQueue(self.mafia_game.get_players_by_role(Role.CIVILIAN))
        self.night_mafia_queue = SubscriberQueue(self.mafia_game.get_players_by_role(Role.MAFIA))
        self.night_commissar_queue = SubscriberQueue(self.mafia_game.get_players_by_role(Role.COMMISSAR))
        self.night_finished = set(self.mafia_game.get_players_by_role(Role.CIVILIAN))
        self.room_server = room_server
        self.room_server.notify_mafia(self.mafia_game.get_players_by_role(Role.MAFIA))

    def start_game(self, request: NameMessage, context):
        return GameStartedMessage(
            list=self.mafia_game.players,
            role=self.mafia_game.get_role(request.name)
        )

    def submit_day_command(self, request: CommandMessage, context) -> DummyMessage:
        allowed, reason = self.mafia_game.is_allowed(request.name, request, Phase.DAY)
        if not allowed:
            return DummyMessage(error=reason)

        info = self.mafia_game.process_command(request)
        self.day_queue.put(info)

        if self.mafia_game.is_phase_finished():
            for info in self.mafia_game.finish_phase():
                self.day_queue.put(info)
        return DummyMessage()

    def listen_day(self, request: NameMessage, context) -> InfoMessage:  # stream
        yield InfoMessage(type=InfoType.START)
        while True:
            msg = self.day_queue.get(request.name)
            if msg.type == InfoType.EXECUTED:
                self.room_server.notify_dead(msg.name)
            yield msg
            if msg.type == InfoType.PHASE_FINISH:
                self.room_server.notify_phase(Phase.NIGHT)
                break
            elif msg.type == InfoType.END:
                self.room_server.notify_finish()
                break

    def submit_night_command(self, request, context):
        allowed, reason = self.mafia_game.is_allowed(request.name, request, Phase.NIGHT)
        if not allowed:
            return DummyMessage(error=reason)

        info = self.mafia_game.process_command(request)
        if self.mafia_game.is_role(request.name, Role.CIVILIAN):
            self.night_civilian_queue.put(info)
        elif self.mafia_game.is_role(request.name, Role.MAFIA):
            self.night_mafia_queue.put(info)
        elif self.mafia_game.is_role(request.name, Role.COMMISSAR):
            self.night_commissar_queue.put(info)

        if self.mafia_game.is_phase_finished():
            for info in self.mafia_game.finish_phase():
                self.night_civilian_queue.put(info)
                self.night_mafia_queue.put(info)
                self.night_commissar_queue.put(info)
        return DummyMessage()

    def listen_night(self, request: NameMessage, context):
        yield InfoMessage(type=InfoType.START)
        while True:
            msg = None
            if self.mafia_game.is_role(request.name, Role.CIVILIAN):
                msg = self.night_civilian_queue.get(request.name)
            elif self.mafia_game.is_role(request.name, Role.MAFIA):
                msg = self.night_mafia_queue.get(request.name)
            elif self.mafia_game.is_role(request.name, Role.COMMISSAR):
                msg = self.night_commissar_queue.get(request.name)
            if msg.type == InfoType.MURDERED:
                self.room_server.notify_dead(msg.name)
            yield msg
            if msg.type == InfoType.PHASE_FINISH:
                self.room_server.notify_phase(Phase.DAY)
                break
            elif msg.type == InfoType.END:
                self.room_server.notify_finish()
                break


def build_server(players: list[str], port, room_server):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=len(players) + 1))
    add_MafiaServicer_to_server(Servicer(players, room_server), server)
    server.add_insecure_port(f'[::]:{port}')
    return server
