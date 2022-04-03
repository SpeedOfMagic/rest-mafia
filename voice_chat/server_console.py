import os

from protocol import ShutdownMessage
from client_manager import ClientManager


class ServerConsole:
    HELP_TEXT = '''
You can use this console to type one or more of the following commands:
help - print this message text
shutdown - shutdown this server
disconnect {client_id} - disconnect client by client_id
'''

    client_manager: ClientManager

    def __init__(self, client_manager):
        self.client_manager = client_manager

    def console_help(self):
        print(self.HELP_TEXT)

    def shutdown(self):
        print('Disconnecting clients')
        client_ids = list(self.client_manager.clients.items())
        for client_id, client in client_ids:
            client.sock.sendall(ShutdownMessage().encode())
            self.client_manager.disconnect_client(client_id)
        print('Shutting down the server')
        os._exit(0)

    def disconnect(self, client_id: int):
        self.client_manager.disconnect_client(client_id)
        print(f'Disconnected client with client_id={client_id}')

    def start(self):
        self.console_help()
        while True:
            cmd = input().strip()
            if cmd == 'help':
                self.console_help()
            elif cmd.startswith('disconnect'):
                client_id = int(cmd.removeprefix('disconnect '))
                self.disconnect(client_id)
            elif cmd == 'shutdown':
                self.shutdown()
            else:
                print(f'Unrecognized command: "{cmd}"')
