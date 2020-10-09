import socket
import os
from threading import Thread
import packetparser as parser
from importlib import reload

# Part 9
# Developing a TCP Network Proxy - Pwn Adventure 3

game_servers = ["172.105.251.170", "172.105.249.25", "176.58.123.111"]

class Proxy2Server(Thread):

    def __init__(self, host, port):
        super(Proxy2Server, self).__init__()
        self.g2p = None # G2P object
        self.data = None

        self.port = port
        self.host = host
        self.serv_addr = (host, port)

        print("[p2s proxy_to({}:{})] setting up".format(self.host, self.port))
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def communicate(self):
        # 3. Receive from Among Us Server
        self.data, self.serv_addr = self.server.recvfrom(4096)
        print("[{} to P2S]: {}".format(':'.join(map(str, self.serv_addr)), self.data.hex()))
        reload(parser)
        parser.parse(self.data, self.serv_addr, self.g2p.game_addr)
        if self.data:
            # 4. Send to Among Us Client
            print("[P2S to {}]: {}".format(':'.join(map(str, self.g2p.game_addr)), self.data.hex()))
            self.g2p.game.sendto(self.data, self.g2p.game_addr) 

    def run(self):
        while True:
            self.communicate()
            
class Game2Proxy(Thread):

    def __init__(self, host, port):
        super(Game2Proxy, self).__init__()
        self.p2s = None # Proxy2Server object
        self.game_addr = None
        self.data = None

        self.port = port
        self.host = host
        
        print("[g2p proxy_from({}:{})] setting up".format(self.host, self.port))
        self.game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.game.bind((host, port))

    def comm_check(self, current_address):
        if self.game_addr != current_address:
            self.game_addr = current_address
            self.p2s.game_addr = current_address

    def communicate(self):
        if self.data:
            # 2. Send to Among Us Server
            print("[G2P to {}]: {}".format(':'.join(map(str, self.p2s.serv_addr)), self.data.hex()))
            self.p2s.server.sendto(self.data, self.p2s.serv_addr)
            reload(parser)
            parser.parse(self.data, self.game_addr, self.p2s.serv_addr)
            self.data = None
        else:
            # 1. Receive from Among Us Client
            self.data, _curr_addr = self.game.recvfrom(4096)
            self.comm_check(_curr_addr)

    def run(self):
        while True: 
            self.communicate()

class Proxy(Thread):

    def __init__(self, from_host, to_host, port):
        super(Proxy, self).__init__()
        self.from_host = from_host
        self.to_host = to_host
        self.port = port

    def run(self):
        while True:
            print( "[proxy({})] setting up".format(self.port))
            
            self.g2p = Game2Proxy(self.from_host, self.port)
            self.p2s = Proxy2Server(self.to_host, self.port)

            print( "[proxy({})] connection established".format(self.port))

            """
            1. Store object-by-reference of P2S inside G2P
            2. Initiate first communication with Among Us client
            """
            self.g2p.p2s = self.p2s
            self.g2p.communicate()
            self.g2p.start()

            """
            3. Store object-by-reference of G2P inside P2S
            """
            self.p2s.g2p = self.g2p
            self.p2s.start()

            self.g2p.join()
            self.p2s.join()

proxies = []

for game_server in game_servers:
    _server = Proxy('192.168.0.101', game_server, 22023)
    _server.start()
    proxies.append(_server)

# game_servers = []
# for port in range(3000, 3006):
#     _game_server = Proxy('0.0.0.0', '192.168.178.54', port)
#     _game_server.start()
#     game_servers.append(_game_server)
