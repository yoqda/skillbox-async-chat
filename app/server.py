#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def is_unic_login(self, login: str):
        unic = True
        for client in self.server.clients:
            if login == client.login:
                unic = False
                break
        return unic

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if self.is_unic_login(login):
                    self.login = login
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(f"Логин {login} уже занят. Попробуйте другой\n".encode())
                    self.transport.close()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def send_history(self):
        for msg in self.server.last_10_messages:
            self.transport.write(
                f"{msg[0]}: {msg[1]}".encode()
            )

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"
        if len(self.server.last_10_messages) == 10:
            self.server.last_10_messages = self.server.last_10_messages[1:]

        self.server.last_10_messages.append([self.login, content])

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    last_10_messages: list

    def __init__(self):
        self.clients = []
        self.last_10_messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

