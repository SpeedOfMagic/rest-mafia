from mafia.game import MafiaGame
from mafia.common import Role, Phase, Winner
from mafia.subscriber_queue import SubscriberQueue
from mafia.voting import Voting
from mafia_service_pb2 import *


def test_subscriber_queue():
    subscribers = ['a', 'b', 'c']
    msg = 'Hello world!'
    queue = SubscriberQueue(subscribers)
    queue.put(msg)
    for sub in subscribers:
        assert queue.get(sub) == msg
    assert queue.get('d') is None


def test_voting():
    voting = Voting(['a', 'b', 'c'])
    voting.vote('a', 'b')
    voting.vote('b', 'b')
    voting.vote('c', 'c')
    assert voting.get_winner() == 'b'
    voting.vote('a', 'c')
    assert voting.get_winner() == 'c'
    voting.vote('a', 'a')
    assert voting.get_winner() is None
    voting.vote('a', None)
    assert voting.get_winner() is None


def test_roles():
    players = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    game = MafiaGame(players)
    roles = [game.get_role(player) for player in players]

    commissars = list(map(lambda i: players[i], filter(lambda i: roles[i] == Role.COMMISSAR, range(len(players)))))
    mafias = list(map(lambda i: players[i], filter(lambda i: roles[i] == Role.MAFIA, range(len(players)))))
    civilians = list(map(lambda i: players[i], filter(lambda i: roles[i] == Role.CIVILIAN, range(len(players)))))
    assert len(commissars) == 1
    assert len(mafias) == 2
    assert len(civilians) == 5

    for commissar in commissars:
        assert game.get_role(commissar) == Role.COMMISSAR
        assert game.is_role(commissar, Role.COMMISSAR)
    for mafia in mafias:
        assert game.get_role(mafia) == Role.MAFIA
        assert game.is_role(mafia, Role.MAFIA)
    for civilian in civilians:
        assert game.get_role(civilian) == Role.CIVILIAN
        assert game.is_role(civilian, Role.CIVILIAN)


def test_finish():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    phase = Phase.DAY
    for _ in range(50):
        assert game.phase == phase
        for player in players:
            finish_msg = CommandMessage(type=CommandType.FINISH, name=player)
            assert game.is_allowed(player, finish_msg, phase)
            game.process_command(finish_msg)
        assert game.is_phase_finished()
        for msg in game.finish_phase():
            assert msg.type == InfoType.PHASE_FINISH
        phase = Phase.NIGHT if phase == Phase.DAY else Phase.DAY


def test_investigate_publish():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    mafia = game.get_players_by_role(Role.MAFIA)[0]
    commissar = game.get_players_by_role(Role.COMMISSAR)[0]
    for _ in game.finish_phase():
        pass

    investigate_cmd = CommandMessage(type=CommandType.INVESTIGATE, name=commissar, suspect=mafia)
    assert game.is_allowed(commissar, investigate_cmd, Phase.NIGHT)
    info = game.process_command(investigate_cmd)
    assert info.type == InfoType.INVESTIGATE_RESULT
    assert info.name == mafia
    assert info.role == Role.MAFIA

    game.process_command(CommandMessage(type=CommandType.FINISH, name=mafia))
    game.process_command(CommandMessage(type=CommandType.FINISH, name=commissar))
    for _ in game.finish_phase():
        pass

    publish_cmd = CommandMessage(type=CommandType.PUBLISH, name=commissar, suspect=mafia)
    assert game.is_allowed(commissar, publish_cmd, Phase.DAY)
    info = game.process_command(publish_cmd)
    assert info.type == InfoType.PUBLISH_RESULT
    assert info.name == mafia
    assert info.role == Role.MAFIA


def test_murder():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    mafia = game.get_players_by_role(Role.MAFIA)[0]
    commissar = game.get_players_by_role(Role.COMMISSAR)[0]
    for _ in game.finish_phase():
        pass

    murder_cmd = CommandMessage(type=CommandType.MURDER, name=mafia, suspect=commissar)
    assert game.is_allowed(mafia, murder_cmd, Phase.NIGHT)
    info = game.process_command(murder_cmd)
    assert info.type == InfoType.MURDER_VOTE
    assert info.name == mafia
    assert info.candidate == commissar

    investigate_cmd = CommandMessage(type=CommandType.INVESTIGATE, name=commissar, suspect=mafia)
    assert game.is_allowed(commissar, investigate_cmd, Phase.NIGHT)
    game.process_command(investigate_cmd)

    messages = [msg for msg in game.finish_phase()]
    assert len(messages) == 2
    assert messages[0].type == InfoType.MURDERED
    assert messages[0].name == commissar
    assert messages[0].role == Role.COMMISSAR

    publish_cmd = CommandMessage(type=CommandType.PUBLISH, name=commissar, suspect=mafia)
    assert not game.is_allowed(commissar, publish_cmd, Phase.DAY)[0]

    for player in players:
        finish_msg = CommandMessage(type=CommandType.FINISH, name=player)
        if player == commissar:
            assert not game.is_allowed(player, finish_msg, Phase.DAY)
        else:
            assert game.is_allowed(player, finish_msg, Phase.DAY)
            game.process_command(finish_msg)
    assert game.is_phase_finished()


def test_execute():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    commissar = game.get_players_by_role(Role.COMMISSAR)[0]

    for player in players:
        execute_cmd = CommandMessage(type=CommandType.EXECUTE, name=player, suspect=commissar)
        assert not game.is_allowed(player, execute_cmd, Phase.DAY)[0]
    for _ in game.finish_phase():
        pass

    for player in players:
        execute_cmd = CommandMessage(type=CommandType.EXECUTE, name=player, suspect=commissar)
        assert not game.is_allowed(player, execute_cmd, Phase.NIGHT)[0]
    for _ in game.finish_phase():
        pass

    for player in players:
        execute_cmd = CommandMessage(type=CommandType.EXECUTE, name=player, suspect=commissar)
        assert game.is_allowed(player, execute_cmd, Phase.DAY)[0]
        game.process_command(execute_cmd)
    msgs = [msg for msg in game.finish_phase()]
    assert len(msgs) == 2
    assert msgs[0].type == InfoType.EXECUTED
    assert msgs[0].name == commissar
    assert msgs[0].role == Role.COMMISSAR


def test_civilian_victory():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    mafia = game.get_players_by_role(Role.MAFIA)[0]
    commissar = game.get_players_by_role(Role.COMMISSAR)[0]
    civilians = game.get_players_by_role(Role.CIVILIAN)

    for _ in game.finish_phase():
        pass
    for _ in game.finish_phase():
        pass
    for player in civilians + [commissar]:
        game.process_command(CommandMessage(type=CommandType.EXECUTE, name=player, suspect=mafia))
    messages = [msg for msg in game.finish_phase()]
    assert len(messages) == 2
    assert messages[0].type == InfoType.EXECUTED
    assert messages[0].name == mafia
    assert messages[0].role == Role.MAFIA
    assert messages[1].type == InfoType.END
    assert messages[1].winner == Winner.CIVILIANS


def test_mafia_victory():
    players = ['a', 'b', 'c', 'd']
    game = MafiaGame(players)
    mafia = game.get_players_by_role(Role.MAFIA)[0]
    commissar = game.get_players_by_role(Role.COMMISSAR)[0]
    civilians = game.get_players_by_role(Role.CIVILIAN)

    for _ in game.finish_phase():
        pass
    game.process_command(CommandMessage(type=CommandType.MURDER, name=mafia, suspect=civilians[0]))

    messages = [_ for _ in game.finish_phase()]
    assert messages[1].type == InfoType.PHASE_FINISH

    for player in [commissar, mafia]:
        game.process_command(CommandMessage(type=CommandType.EXECUTE, name=player, suspect=civilians[1]))
    messages = [msg for msg in game.finish_phase()]
    assert len(messages) == 2
    assert messages[0].type == InfoType.EXECUTED
    assert messages[0].name == civilians[1]
    assert messages[0].role == Role.CIVILIAN
    assert messages[1].type == InfoType.END
    assert messages[1].winner == Winner.MAFIA
