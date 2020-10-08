import socket
import os
from threading import Thread

# Part 9
# Developing a TCP Network Proxy - Pwn Adventure 3

REAL_SERVER_IP = "172.105.251.170"

class Proxy2Server(Thread):

    def __init__(self, host, port):
        super(Proxy2Server, self).__init__()
        self.port = port
        self.host = host
        self.p2saddr = (host, port)
        self.g2paddr = None

        print("[p2s proxy_to({}:{})] setting up".format(self.host, self.port))
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game = None

    # run in thread
    def run(self):
        while True:
            data, data_from = self.server.recvfrom(1024) # recvfrom(among us server)
            print("[{} to P2S]: {}".format(data_from, data))
            if data:
                print("[P2S to {}]: {}".format(self.g2paddr, data))
                self.game.sendto(data, self.g2paddr) # sendto(fakenet/among us client)

class Game2Proxy(Thread):

    def __init__(self, host, port):
        super(Game2Proxy, self).__init__()
        self.port = port
        self.host = host
        self.g2paddr = (host, port)
        self.p2saddr = None

        print("[g2p proxy_from({}:{})] setting up".format(self.host, self.port))
        self.game = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.game.bind(self.g2paddr)
        self.server = None

        self.data, _ = self.game.recvfrom(1024)

    def run(self):
        while True:
            if self.data:
                # sendto(among us server)
                print("[G2P to {}]: {}".format(self.p2saddr, self.data))
                self.server.sendto(self.data, self.p2saddr) 
                self.data = None
            else:
                # recvfrom(fakenet/among us client)
                self.data, _ = self.game.recvfrom(1024)
                
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
            self.g2p.p2saddr = self.p2s.p2saddr

            self.p2s.game = self.g2p.game
            self.p2s.g2paddr = self.g2p.g2paddr

            self.g2p.start()
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
