from threading import Thread
import grpc
import random

from proto.mafia_service_pb2_grpc import MafiaStub
from mafia_service_pb2 import *
from mafia.common import *


class MafiaClient:
    channel: grpc.insecure_channel
    stub: MafiaStub
    game_thread: Thread
    name: str
    players: list[str]
    role: int
    port: int

    def __init__(self, port):
        self.port = port

    def start(self, ip: str, name: str):
        self.channel = grpc.insecure_channel(f'{ip}:{self.port}')
        self.name = name
        self.stub = MafiaStub(self.channel)
        self.game_thread = Thread(target=self.play_game)
        self.game_thread.start()

    def play_game(self):
        self.start_game()
        while True:
            if self.listen_day():
                break
            if self.listen_night():
                break

    def print_help_text(self):
        print(f'Your role is {get_role_name(self.role)}')
        print(f'As a {get_role_name(self.role)}, you can do the following:')

        if self.role == Role.MAFIA:
            print('mafia night murder {name} - vote for murdering player {name} on night, or change your vote')
            print('mafia night skip - skip voting for whom to murder on night')
            print('mafia night random - vote for murdering random player')
            print('mafia night finish - finish night for yourself')
        elif self.role == Role.COMMISSAR:
            print('mafia night investigate {name} - find out role of a player {name} on night')
            print('mafia night random - investigate random player')
            print('mafia night finish - finish night for yourself')
            print('mafia day publish {name} - publish result of your investigation of player {name} on day')
        elif self.role == Role.CIVILIAN:
            pass
        else:
            assert False, f'Found unknown role: {self.role}'
        print('mafia day execute {name} - vote for execution of a player {name} on 2+ day, or change your vote')
        print('mafia day skip - skip voting for whom to execute')
        print('mafia day random - vote for execution of a random player')
        print('mafia day finish - finish day phase for yourself')
        print('mafia help - print this text again')

    def start_game(self):
        game_started_message: GameStartedMessage = self.stub.start_game(NameMessage(name=self.name))
        self.role = game_started_message.role
        print('Game started!')
        print('Players participating in this game:')
        print(*game_started_message.list, sep='\n')
        self.players = game_started_message.list
        self.print_help_text()

    def day_submit_message(self, msg: CommandMessage):
        resp = self.stub.submit_day_command(msg)
        if resp.error is not None and resp.error != '':
            print('ERROR:', resp.error)

    def night_submit_message(self, msg: CommandMessage):
        resp = self.stub.submit_night_command(msg)
        if resp.error is not None and resp.error != '':
            print('ERROR:', resp.error)

    def get_random_player(self):
        suspect = random.choice(self.players)
        while suspect == self.name:
            suspect = random.choice(self.players)
        return suspect

    def process_cmd(self, phase_cmd: str):
        if phase_cmd == 'help':
            self.print_help_text()

        elif phase_cmd.startswith('day'):
            cmd = phase_cmd.removeprefix('day').strip()
            if cmd == 'finish':
                self.day_submit_message(CommandMessage(type=CommandType.FINISH, name=self.name))
            elif cmd.startswith('publish '):
                suspect = cmd.removeprefix('publish ').strip()
                self.day_submit_message(CommandMessage(type=CommandType.PUBLISH, name=self.name, suspect=suspect))
            elif cmd.startswith('execute '):
                suspect = cmd.removeprefix('execute ').strip()
                self.day_submit_message(CommandMessage(type=CommandType.EXECUTE, name=self.name, suspect=suspect))
            elif cmd == 'skip':
                self.day_submit_message(CommandMessage(type=CommandType.EXECUTE, name=self.name))
            elif cmd == 'random':
                suspect = self.get_random_player()
                print(f'Voting to execute player {suspect}...')
                self.day_submit_message(CommandMessage(type=CommandType.EXECUTE, name=self.name, suspect=suspect))
            else:
                print(f'Unrecognized command for day: "{cmd}"')

        elif phase_cmd.startswith('night'):
            cmd = phase_cmd.removeprefix('night').strip()
            if cmd == 'finish':
                self.night_submit_message(CommandMessage(type=CommandType.FINISH, name=self.name))
            elif cmd.startswith('investigate '):
                suspect = cmd.removeprefix('investigate ').strip()
                self.night_submit_message(CommandMessage(type=CommandType.INVESTIGATE, name=self.name, suspect=suspect))
            elif cmd == 'random':
                suspect = self.get_random_player()
                if self.role == Role.MAFIA:
                    print(f'Voting to murder player {suspect}...')
                    self.night_submit_message(CommandMessage(type=CommandType.MURDER, name=self.name, suspect=suspect))
                elif self.role == Role.COMMISSAR:
                    print(f'Investigating player {suspect}...')
                    cmd_type = CommandType.INVESTIGATE
                    self.night_submit_message(CommandMessage(type=cmd_type, name=self.name, suspect=suspect))
            elif cmd.startswith('murder '):
                suspect = cmd.removeprefix('murder ').strip()
                self.night_submit_message(CommandMessage(type=CommandType.MURDER, name=self.name, suspect=suspect))
            elif cmd == 'skip':
                self.night_submit_message(CommandMessage(type=CommandType.MURDER, name=self.name))
            else:
                print(f'Unrecognized command for night: "{cmd}"')
        else:
            print(f'Unrecognized command for mafia game: "{phase_cmd}"')

    def listen_day(self):
        for msg in self.stub.listen_day(NameMessage(name=self.name)):
            if msg.type == InfoType.START:
                print('New day has started!')
            elif msg.type == InfoType.PLAYER_FINISH:
                print(f'Player {msg.name} finished his day')
            elif msg.type == InfoType.PHASE_FINISH:
                print('Day is finished!')
            elif msg.type == InfoType.PUBLISH_RESULT:
                print(f'Commissar published information that {msg.name} is {get_role_name(msg.role)}!')
            elif msg.type == InfoType.EXECUTE_VOTE:
                if msg.candidate is None or msg.candidate == '':
                    print(f'{msg.name} decided to not vote for execution!')
                else:
                    print(f'{msg.name} voted to execute {msg.candidate}!')
            elif msg.type == InfoType.EXECUTED:
                print(f'{msg.name} is executed! This player was a {get_role_name(msg.role)}')
            elif msg.type == InfoType.END:
                winner = 'winner is mafia' if msg.winner == Winner.MAFIA else 'winners are commissar and civilians'
                print(f'Game is finished! The {winner}!')
                return True
            else:
                assert False, f'Found unknown info type: {msg.type}'
        return False

    def listen_night(self):
        for msg in self.stub.listen_night(NameMessage(name=self.name)):
            if msg.type == InfoType.START:
                print('Night has started! All civilians are sleeping. Mafia and commissar are doing their work.')
            elif msg.type == InfoType.PLAYER_FINISH:
                print(f'Player {msg.name} finished his night')
            elif msg.type == InfoType.PHASE_FINISH:
                print('Night is finished!')
            elif msg.type == InfoType.INVESTIGATE_RESULT:
                print(f'Player {msg.name} is {get_role_name(msg.role)}!')
            elif msg.type == InfoType.MURDER_VOTE:
                if msg.candidate is None or msg.candidate == '':
                    print(f'{msg.name} decided to not vote for murder!')
                else:
                    print(f'{msg.name} voted to murder {msg.candidate}!')
            elif msg.type == InfoType.MURDERED:
                print(f'{msg.name} is murdered! This player was a {get_role_name(msg.role)}')
            elif msg.type == InfoType.END:
                winner = 'winner is mafia' if msg.winner == Winner.MAFIA else 'winners are commissar and civilians'
                print(f'Game is finished! The {winner}!')
                return True
            else:
                assert False, f'Found unknown info type: {msg.type}'
        return False
