import random
from mafia.common import *
from mafia_service_pb2 import *
from mafia.voting import Voting


def get_roles(players_count):
    roles = [Role.COMMISSAR] \
          + [Role.MAFIA] * (players_count // 3) \
          + [Role.CIVILIAN] * (players_count - 1 - players_count // 3)
    random.shuffle(roles)
    return roles


class MafiaGame:
    players: list[str]
    player_role: dict[str, int]

    finished: set[str]
    phase: bool
    can_execute: bool

    execute_voting: Voting
    dead: set[str]

    investigated: set[str]
    done_investigation: bool

    def __init__(self, players: list[str]):
        self.players = players
        roles = get_roles(len(players))
        self.player_role = {self.players[i]: roles[i] for i in range(len(players))}
        self.finished = set()
        self.investigated = set()
        self.dead = set()
        self.done_investigation = False
        self.phase = Phase.DAY
        self.can_execute = False
        self.execute_voting = Voting(self.players)

    def is_allowed(self, name: str, command: CommandMessage, phase: Phase):
        if phase != self.phase:
            return False, 'Wrong phase'
        if name in self.dead:
            return False, 'You are dead!'
        if name in self.finished:
            return False, 'This phase is already finished for you'

        if command.type == CommandType.FINISH:
            return True, None
        elif command.type == CommandType.INVESTIGATE:
            if not self.is_role(name, Role.COMMISSAR):
                return False, 'You are not allowed to investigate since you are not commissar'
            elif self.phase != Phase.NIGHT:
                return False, 'You cannot investigate since it is day'
            elif command.suspect not in self.players:
                return False, 'You cannot investigate player that does not exist!'
            elif self.done_investigation:
                return False, 'You cannot investigate since you already investigated this night'
            else:
                return True, None
        elif command.type == CommandType.PUBLISH:
            if not self.is_role(name, Role.COMMISSAR):
                return False, 'You are not allowed to publish information since you are not commissar'
            elif self.phase != Phase.DAY:
                return False, 'You cannot publish information since it is night'
            elif command.suspect not in self.investigated:
                return False, 'You cannot publish information since you do not know his role'
            elif not self.is_role(command.suspect, Role.MAFIA):
                return False, 'You cannot publish information since this player is not mafia'
            else:
                return True, None
        elif command.type == CommandType.EXECUTE:
            if command.suspect in self.dead:
                return False, 'This person is already dead!'
            elif self.phase != Phase.DAY:
                return False, 'You cannot vote to execute person in the night'
            elif not self.can_execute:
                return False, 'You cannot vote to execute person on the first day'
            else:
                return True, None
        elif command.type == CommandType.MURDER:
            if not self.is_role(name, Role.MAFIA):
                return False, 'You cannot vote for murder since you are not in mafia'
            elif self.phase != Phase.NIGHT:
                return False, 'You cannot vote for murder in the day'
            elif command.suspect in self.dead:
                return False, 'This person is already dead!'
            else:
                return True, None

    def process_command(self, command: CommandMessage) -> InfoMessage:
        if command.type == CommandType.FINISH:
            self.finished.add(command.name)
            return InfoMessage(type=InfoType.PLAYER_FINISH, name=command.name)
        elif command.type == CommandType.INVESTIGATE:
            suspect = command.suspect
            self.investigated.add(suspect)
            self.done_investigation = True
            return InfoMessage(type=InfoType.INVESTIGATE_RESULT, name=suspect, role=self.get_role(suspect))
        elif command.type == CommandType.PUBLISH:
            suspect = command.suspect
            return InfoMessage(type=InfoType.PUBLISH_RESULT, name=suspect, role=self.get_role(suspect))
        elif command.type == CommandType.EXECUTE:
            suspect = None if command.suspect == '' or command.suspect is None else command.suspect
            self.execute_voting.vote(command.name, suspect)
            return InfoMessage(type=InfoType.EXECUTE_VOTE, name=command.name, candidate=suspect)
        elif command.type == CommandType.MURDER:
            suspect = None if command.suspect == '' or command.suspect is None else command.suspect
            self.execute_voting.vote(command.name, suspect)
            return InfoMessage(type=InfoType.MURDER_VOTE, name=command.name, candidate=suspect)
        else:
            assert False, f'Found unknown command type: {command.type}'

    def is_phase_finished(self):
        return len(self.finished) == len(self.players)

    def finish_phase(self):
        if self.phase == Phase.DAY:
            if self.execute_voting.get_winner() is not None:
                to_execute = self.execute_voting.get_winner()
                self.kill(to_execute)
                yield InfoMessage(type=InfoType.EXECUTED, name=to_execute, role=self.get_role(to_execute))
            self.phase = Phase.NIGHT
            self.finished = set(self.get_players_by_role(Role.CIVILIAN))
            self.execute_voting = Voting(self.get_players_by_role(Role.MAFIA))
        else:
            if self.execute_voting.get_winner() is not None:
                to_execute = self.execute_voting.get_winner()
                self.kill(to_execute)
                yield InfoMessage(type=InfoType.MURDERED, name=to_execute, role=self.get_role(to_execute))
            self.finished.clear()
            self.phase = Phase.DAY
            self.done_investigation = False
            self.can_execute = True
            self.execute_voting = Voting(self.players)

        winner = self.is_game_finished()
        if winner == Winner.NONE:
            yield InfoMessage(type=InfoType.PHASE_FINISH)
        else:
            yield InfoMessage(type=InfoType.END, winner=winner)

    def is_game_finished(self):
        mafia_count = len(self.get_players_by_role(Role.MAFIA))
        if mafia_count == 0:
            return Winner.CIVILIANS
        civilians_count = len(self.get_players_by_role(Role.CIVILIAN)) + len(self.get_players_by_role(Role.COMMISSAR))
        if civilians_count <= mafia_count:
            return Winner.MAFIA
        return Winner.NONE

    def kill(self, player: str):
        self.dead.add(player)
        self.players.remove(player)

    def get_role(self, player: str) -> int:
        return self.player_role[player]

    def is_role(self, player: str, role: Role) -> bool:
        return self.player_role[player] == role

    def get_players_by_role(self, role: Role) -> list[str]:
        return list(filter(lambda player: self.player_role[player] == role, self.players))
