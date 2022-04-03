from __future__ import annotations

from voice_chat.converter import UIntConverter, StrConverter, ArrayConverter


MESSAGE_TYPE_SIZE = 1
ROOM_TYPE_SIZE = 1
ERROR_SIZE = 1
CLIENT_NAME_SIZE = 2  # NAME_LIMIT is smaller than 256^CLIENT_NAME_SIZE since each symbol in name may take up to 4 bytes
PORT_SIZE = 2
NAMES_LIST_SIZE = 4
VOICE_DATA_SIZE = 1024


class MessageType:
    VOICE: int = 0
    CONNECTED: int = 1
    DISCONNECTED: int = 2
    SHUTDOWN: int = 3
    LIST_REQUEST: int = 4
    LIST_RESPONSE: int = 5
    ROOM_CHANGE: int = 6
    GAME_STARTED: int = 7
    CONNECTED_RESPONSE: int = 8


class Message:
    message_type: int

    def encode(self):
        raise NotImplementedError('encode is not defined!')


class VoiceMessage(Message):
    message_type: int = MessageType.VOICE
    name: str  # We should not give away client_id, since hackers can use it to fake profiles
    data: bytes

    def __init__(self, name: str = '', data: bytes = b''):
        self.name = name
        self.data = data
        assert len(self.data) == VOICE_DATA_SIZE, f'Wrong data size: Expected {VOICE_DATA_SIZE}, got {len(self.data)}'

    def encode(self):
        enc_name = StrConverter.encode(self.name)
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(len(enc_name), CLIENT_NAME_SIZE) \
            + enc_name \
            + self.data


class ConnectedMessage(Message):
    message_type: int = MessageType.CONNECTED
    name: str

    def __init__(self, name: str):
        self.name = name

    def encode(self):
        enc_name = StrConverter.encode(self.name)
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(len(enc_name), CLIENT_NAME_SIZE) \
            + enc_name


class DisconnectedMessage(ConnectedMessage):
    message_type: int = MessageType.DISCONNECTED


class ListRequestMessage(Message):
    message_type: int = MessageType.LIST_REQUEST

    def encode(self):
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE)


class ListResponseMessage(Message):
    message_type: int = MessageType.LIST_RESPONSE
    names: list[str]

    def __init__(self, names: list[str]):
        self.names = names

    def encode(self):
        names_enc = ArrayConverter.encode(self.names)
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(len(names_enc), NAMES_LIST_SIZE) \
            + names_enc


class RoomChangeMessage(Message):
    message_type: int = MessageType.ROOM_CHANGE
    room_id: int

    def __init__(self, room_id: int):
        self.room_id = room_id

    def encode(self):
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(self.room_id, ROOM_TYPE_SIZE)


class ShutdownMessage(Message):
    message_type: int = MessageType.SHUTDOWN

    def encode(self):
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE)


class GameStartingMessage(Message):
    message_type: int = MessageType.GAME_STARTED
    port: int

    def __init__(self, port):
        self.port = port

    def encode(self):
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(self.port, PORT_SIZE)


class ConnectedResponseMessage(Message):
    message_type: int = MessageType.CONNECTED_RESPONSE
    error: str

    def __init__(self, error):
        self.error = error

    def encode(self):
        error_enc = StrConverter.encode(self.error)
        return UIntConverter.encode(self.message_type, MESSAGE_TYPE_SIZE) \
            + UIntConverter.encode(len(error_enc), ERROR_SIZE) \
            + error_enc


def get_message(sock):  # socket.socket or MockSocket
    message_type = UIntConverter.decode(sock.recv(MESSAGE_TYPE_SIZE))

    if message_type == MessageType.VOICE:
        len_name = UIntConverter.decode(sock.recv(CLIENT_NAME_SIZE))
        name = StrConverter.decode(sock.recv(len_name))
        return VoiceMessage(name, sock.recv(VOICE_DATA_SIZE))

    elif message_type == MessageType.CONNECTED:
        len_name = UIntConverter.decode(sock.recv(CLIENT_NAME_SIZE))
        return ConnectedMessage(StrConverter.decode(sock.recv(len_name)))

    elif message_type == MessageType.DISCONNECTED:
        len_name = UIntConverter.decode(sock.recv(CLIENT_NAME_SIZE))
        return DisconnectedMessage(StrConverter.decode(sock.recv(len_name)))

    elif message_type == MessageType.LIST_REQUEST:
        return ListRequestMessage()

    elif message_type == MessageType.LIST_RESPONSE:
        len_names = UIntConverter.decode(sock.recv(NAMES_LIST_SIZE))
        names = ArrayConverter.decode(sock.recv(len_names))
        return ListResponseMessage(names)

    elif message_type == MessageType.ROOM_CHANGE:
        room = UIntConverter.decode(sock.recv(ROOM_TYPE_SIZE))
        return RoomChangeMessage(room)

    elif message_type == MessageType.SHUTDOWN:
        return ShutdownMessage()

    elif message_type == MessageType.GAME_STARTED:
        port = UIntConverter.decode(sock.recv(PORT_SIZE))
        return GameStartingMessage(port)

    elif message_type == MessageType.CONNECTED_RESPONSE:
        error_len = UIntConverter.decode(sock.recv(ERROR_SIZE))
        error = StrConverter.decode(sock.recv(error_len))
        return ConnectedResponseMessage(error)
    else:
        assert False, f'Found unknown message_type: {message_type}'
