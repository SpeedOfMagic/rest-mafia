import os
import socket

from protocol import RoomChangeMessage, ListRequestMessage
from mafia.client import MafiaClient


class VoiceMode:
    PUSH_TO_TALK = False
    ALWAYS = True


class ClientConsole:
    HELP_TEXT = '''
You can use this console to type one or more of the following commands:
help - print this message text
mode {voice_mode} - when voice message should be sent. Possible variants: "push_to_talk" (on v), "p", "always", "a".
list - list all users in current room
room {room number} - go to selected room or create a new room if it doesn't exist
exit - disconnect from server and exit application
'''

    sock: socket.socket
    mafia_client: MafiaClient or None
    mode: int

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.mafia_client = None

    def bind_mafia_client(self, mafia_client: MafiaClient):
        self.mafia_client = mafia_client

    def console_help(self):
        print(self.HELP_TEXT)

    def console_exit(self):
        self.sock.close()
        os._exit(0)

    def change_mode(self, mode):
        if mode in ['push_to_talk', 'p']:
            self.mode = VoiceMode.PUSH_TO_TALK
            print('Changed mode to "push_to_talk"')
        elif mode in ['always', 'a']:
            self.mode = VoiceMode.ALWAYS
            print('Changed mode to "always"')
        else:
            print(f'Unrecognized mode: "{self.mode}"')

    def change_room(self, room_id: int):
        if not 0 <= room_id < 256:
            print(f'Invalid room_id: {room_id}')
        else:
            self.sock.sendall(RoomChangeMessage(room_id).encode())
            print(f'Changed room_id to {room_id}')

    def print_list(self):
        self.sock.sendall(ListRequestMessage().encode())

    def start(self):
        self.console_help()
        self.change_mode('push_to_talk')
        self.change_room(0)
        while True:
            cmd = input().strip()
            if cmd == 'help':
                self.console_help()
            elif cmd.startswith('mode '):
                mode = cmd.removeprefix('mode ').strip()
                self.change_mode(mode)
            elif cmd == 'list':
                self.print_list()
            elif cmd.startswith('room '):
                room_id_str = cmd.removeprefix('room ').strip()
                try:
                    room_id = int(room_id_str)
                    self.change_room(room_id)
                except ValueError:
                    print(f'ERROR: {room_id_str} is not an integer')
            elif cmd.startswith('mafia '):
                if self.mafia_client is None:
                    print('ERROR: game not started')
                else:
                    mafia_cmd = cmd.removeprefix('mafia ').strip()
                    self.mafia_client.process_cmd(mafia_cmd)
            elif cmd == 'exit':
                self.console_exit()
            else:
                print(f'Unrecognized command: "{cmd}"')
