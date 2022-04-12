import socket
import threading
import os
import pyaudio
import keyboard

from protocol import (
    MessageType,
    VoiceMessage,
    ConnectedMessage,
    get_message,
    VOICE_DATA_SIZE,
)

from client_console import VoiceMode, ClientConsole
from mafia.client import MafiaClient
from mafia.common import WAIT_TIME_TO_START


class Client:
    RETRY_LIMIT = 3
    NAME_LEN_LIMIT = 200

    sock: socket.socket
    console: ClientConsole
    cur_speaker: str
    mafia_client: MafiaClient or None

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cur_speaker = ''
        self.mafia_client = None

        while 1:
            try:
                self.name = input(f'Enter JWT token --> ')
                if not 1 <= len(self.name) <= self.NAME_LEN_LIMIT:
                    print('Maximum name length exceeded or name is empty')
                    continue

                self.target_ip = input('Enter IP address of server --> ')
                target_port = int(input('Enter target port of server --> '))

                self.sock.connect((self.target_ip, target_port))
                self.sock.sendall(ConnectedMessage(self.name).encode())

                resp = get_message(self.sock)
                if resp.error != '':
                    print(resp.error)
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    continue

                break
            except socket.error as err:
                print('Could not connect to the server: ', err)

        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # initialise microphone recording
        self.audio = pyaudio.PyAudio()
        self.playing_stream = self.audio.open(format=audio_format, channels=channels, rate=rate,
                                              output=True, frames_per_buffer=VOICE_DATA_SIZE)
        self.recording_stream = self.audio.open(format=audio_format, channels=channels, rate=rate,
                                                input=True, frames_per_buffer=VOICE_DATA_SIZE)

        print('Connected to server')

        # start threads
        threading.Thread(target=self.send_data_to_server).start()
        threading.Thread(target=self.receive_server_data).start()
        self.console = ClientConsole(self.sock)
        self.console.start()

    def receive_server_data(self):
        retry_count = 0
        while True:
            try:
                msg = get_message(self.sock)
                if msg.message_type == MessageType.VOICE:
                    assert msg.name != ''
                    if msg.name != self.cur_speaker:
                        self.cur_speaker = msg.name
                        print(f'{self.cur_speaker} is talking...')
                    self.playing_stream.write(msg.data)

                elif msg.message_type == MessageType.CONNECTED:
                    assert msg.name != ''
                    print(f'{msg.name} has connected to this room!')

                elif msg.message_type == MessageType.DISCONNECTED:
                    assert msg.name != ''
                    print(f'{msg.name} has disconnected from this room!')

                elif msg.message_type == MessageType.LIST_RESPONSE:
                    print('Clients in this room:')
                    print(*msg.names, sep='\n')

                elif msg.message_type == MessageType.SHUTDOWN:
                    print('Server has shut down')
                    os._exit(0)

                elif msg.message_type == MessageType.GAME_STARTED:
                    print(f'Four people have gathered. Waiting {WAIT_TIME_TO_START} seconds for new players,'
                          f' then the game starts')
                    self.mafia_client = MafiaClient(msg.port)
                    self.console.bind_mafia_client(self.mafia_client)
                    self.mafia_client.start(self.target_ip, self.name)

                retry_count = 0
            except socket.error as err:
                print('Could not receive server data:', err)
                retry_count += 1
                if retry_count > self.RETRY_LIMIT:
                    print('ERROR: Amount of retries exceeded. Shutting down connection with server...')
                    self.sock.close()
                    print('Disconnected from server.')
                    os._exit(1)
                else:
                    print(f'Retrying {retry_count}/3')

    def send_data_to_server(self):
        retry_count = 0
        while True:
            try:
                data = self.recording_stream.read(VOICE_DATA_SIZE // 2)
                if self.console.mode != VoiceMode.PUSH_TO_TALK or keyboard.is_pressed('v'):
                    self.sock.sendall(VoiceMessage(data=data).encode())
                retry_count = 0
            except socket.error as err:
                print('ERROR: Could not send data to server because of socket:', err)
                retry_count += 1
                if retry_count > self.RETRY_LIMIT:
                    print('ERROR: Amount of retries exceeded. Shutting down connection with server...')
                    self.sock.close()
                    print('Disconnected from server.')
                    os._exit(1)
                else:
                    print(f'Retrying {retry_count}/3')


client = Client()
