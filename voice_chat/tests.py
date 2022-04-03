from voice_chat.converter import UIntConverter, StrConverter, ArrayConverter
from voice_chat.protocol import (
    get_message, MessageType, VOICE_DATA_SIZE,
    VoiceMessage, ConnectedMessage, DisconnectedMessage, ShutdownMessage, ConnectedResponseMessage,
    RoomChangeMessage, ListRequestMessage, ListResponseMessage, GameStartingMessage,
)


def test_uint_converter():
    for num in range(500):
        assert UIntConverter.decode(UIntConverter.encode(num, 4)) == num


def test_str_converter():
    string = 'qwertyuiopasdfghjklzxcvbnm lorem ipsum привет, мир!'
    assert StrConverter.encode(string).decode() == string


def test_array_converter():
    arr = [1, 2, 3, 5, 7, 'a', 'b', 'o', 'b', 'a']
    enc = ArrayConverter.encode(arr)
    assert ArrayConverter.decode(enc) == arr


class MockSocket:
    data: bytes

    def __init__(self, data: bytes):
        self.data = data

    def recv(self, length: int) -> bytes:
        result = self.data[:length]
        self.data = self.data[length:]
        return result


def test_voice_message():
    data = b'\x0f' * VOICE_DATA_SIZE
    name = 'xXxSLaYeRxXx'
    voice_message = VoiceMessage(name, data)
    sock = MockSocket(voice_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.VOICE
    assert msg.name == name
    assert msg.data == data
    assert len(sock.data) == 0


def test_connected_message():
    name = 'Вася Пупкин'
    connected_message = ConnectedMessage(name)
    sock = MockSocket(connected_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.CONNECTED
    assert msg.name == name
    assert len(sock.data) == 0


def test_disconnected_message():
    name = 'Роберт'
    disconnected_message = DisconnectedMessage(name)
    sock = MockSocket(disconnected_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.DISCONNECTED
    assert msg.name == name
    assert len(sock.data) == 0


def test_room_change_message():
    room_id = 42
    room_change_message = RoomChangeMessage(room_id)
    sock = MockSocket(room_change_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.ROOM_CHANGE
    assert msg.room_id == room_id
    assert len(sock.data) == 0


def test_list_response_message():
    names = ['a', 'bb', 'cccc']
    list_response_message = ListResponseMessage(names)
    sock = MockSocket(list_response_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.LIST_RESPONSE
    assert msg.names == names
    assert len(sock.data) == 0


def test_game_starting_message():
    game_starting_message = GameStartingMessage(12345)
    sock = MockSocket(game_starting_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.GAME_STARTED
    assert msg.port == 12345
    assert len(sock.data) == 0


def test_connected_response_message():
    connected_response_message = ConnectedResponseMessage(error='I am error')
    sock = MockSocket(connected_response_message.encode())

    msg = get_message(sock)
    assert msg.message_type == MessageType.CONNECTED_RESPONSE
    assert msg.error == 'I am error'
    assert len(sock.data) == 0


def test_simple_message():
    simple_messages = [
        ListRequestMessage(),
        ShutdownMessage(),
    ]
    for message in simple_messages:
        sock = MockSocket(message.encode())
        msg = get_message(sock)
        assert msg.message_type == message.message_type
        assert len(sock.data) == 0
