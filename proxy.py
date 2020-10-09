import socket
import os
from threading import Thread
import packetparser as parser
from importlib import reload

# Part 9
# Developing a TCP Network Proxy - Pwn Adventure 3

REAL_SERVER_IP = "172.105.251.170"

class Proxy2Server(Thread):

    def __init__(self, host, port):
        super(Proxy2Server, self).__init__()
        self.name = "P2S"
        self.port = port
        self.host = host
        self.game_addr = None
        self.serv_addr = (host, port)

        print("[p2s proxy_to({}:{})] setting up".format(self.host, self.port))
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game = None

    # run in thread
    def run(self):
        while True:
            # 3. Receive from Among Us Server
            self.data, self.serv_addr = self.server.recvfrom(1024)
            print("[{} to P2S]: {}".format(':'.join(map(str, self.serv_addr)), self.data.hex()))

            # reload(parser)
            # parser.parse(self.data, self.serv_addr, self.game_addr)

            if self.data:
                # 4. Send to Among Us Client
                print("[P2S to {}]: {}".format(':'.join(map(str, self.game_addr)), self.data.hex()))
                self.game.sendto(self.data, self.game_addr) 

class Game2Proxy(Thread):

    def __init__(self, host, port):
        super(Game2Proxy, self).__init__()
        self.name = "G2P"
        self.port = port
        self.host = host
        self.game_addr = None
        self.serv_addr = None

        print("[g2p proxy_from({}:{})] setting up".format(self.host, self.port))
        self.game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.game.bind((host, port))
        self.server = None

        # 1. Waiting for first data from Among Us Client
        self.data, self.game_addr = self.game.recvfrom(1024)

    def run(self):
        while True:
            if self.data:
                # 2. Send to Among Us Server
                print("[G2P to {}]: {}".format(':'.join(map(str, self.serv_addr)), self.data.hex()))
                self.server.sendto(self.data, self.serv_addr)

                # reload(parser)
                # parser.parse(self.data, self.game_addr, self.serv_addr)

                self.data = None
            else:
                # 1. Receive from Among Us Client
                self.data, self.game_addr = self.game.recvfrom(1024)
                
class Proxy(Thread):

    def __init__(self, from_host, to_host, port):
        super(Proxy, self).__init__()
        self.from_host = from_host
        self.to_host = to_host
        self.port = port

    def run(self):
        while True:
            print( "[proxy({})] setting up".format(self.port))
            
            # waiting for a client
            self.g2p = Game2Proxy(self.from_host, self.port)
            self.p2s = Proxy2Server(self.to_host, self.port)

            print( "[proxy({})] connection established".format(self.port))

            self.g2p.server = self.p2s.server
            self.g2p.serv_addr = self.p2s.serv_addr
            self.g2p.start()

            self.p2s.game = self.g2p.game
            self.p2s.game_addr = self.g2p.game_addr
            self.p2s.start()

            self.g2p.join()
            self.p2s.join()


master_server = Proxy('192.168.0.101', REAL_SERVER_IP, 22023)
master_server.start()

# game_servers = []
# for port in range(3000, 3006):
#     _game_server = Proxy('0.0.0.0', '192.168.178.54', port)
#     _game_server.start()
#     game_servers.append(_game_server)
