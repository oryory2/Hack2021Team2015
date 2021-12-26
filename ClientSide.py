import msvcrt
import socket
import sys

stopTheGame = False


class Client:

    def _init_(self):
        self.name = "None"
        self.port = 13117
        self.host = ''
        self.magicCookie = 0xabcddcba
        self.messageType = 0x2
        self.serverIP = None
        self.serverPort = None
        self.serverConnected = 0

        # initializing the UDP Socket
        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error:
            print("Failed to create client UDP socket")
            sys.exit()
        self.udpSocket.bind((self.host, self.port))

        # initializing the TCP Socket
        try:
            self.tcpSocket = socket.socket(family=socket.AF_INET, Type=socket.SOCK_STREAM)
        except socket.error:
            print("Failed to create server TCP socket")
            sys.exit()

    def startClient(self):
        print("Client started, listening for offer requests...")

        while self.serverConnected < 1:
            msgFromServer, serverInfo = self.udpSocket.recvfrom(2048)
            self.serverIP = serverInfo[0]
            magicCookie = hex(int(msgFromServer.hex()[:8], 16))
            messageType = msgFromServer.hex()[9:10]
            self.serverPort = int(msgFromServer.hex()[10:], 16)

            # TODO: need to understand if needed or not
            if hex(self.magicCookie) != magicCookie or self.messageType != int(messageType):
                continue

            print("Received offer from " + serverInfo[0] + ", attempting to connect...\n")
            self.connectToServer()

        self.startToPlay()

        # End game message
        msgFromServer = self.tcpSocket.recv(1024)
        print(msgFromServer.decode('UTF-8'))

        try:
            self.tcpSocket.shutdown(socket.SHUT_RDWR)
            self.tcpSocket.close()
        except socket.error:
            print("Failed to close the socket")
            sys.exit()

        print("Server disconnected, listening for offer requests...")

        self.restart()

    def connectToServer(self):
        try:  # TODO: what happens if the server is not listening anymore
            self.tcpSocket.connect((self.serverIP, self.serverPort))
        except socket.error:
            print("Failed to connect to the server with IP " + self.serverIP)
            return

        # sending the server client's name
        self.tcpSocket.send(bytes(self.name), 'UTF-8')
        self.serverConnected = 1

    def startToPlay(self):
        msgFromServer = self.tcpSocket.recv(1024)
        print(msgFromServer.decode('UTF-8'))

        # TODO: understand the msvcrt.getch()
        # TODO: what happens if the other player answered first

        answer = msvcrt.getch('Answer as fast as you can: ')
        self.tcpSocket.send(answer)

    def restart(self):
        self.serverIP = None
        self.serverPort = None
        self.serverConnected = 0

        if stopTheGame:
            # Closing the udpSocket
            try:
                self.udpSocket.shutdown(socket.SHUT_RDWR)
                self.udpSocket.close()
            except socket.error:
                print("Failed to close the socket")
                sys.exit()

            # Closing the tcpSocket
            try:
                self.tcpSocket.shutdown(socket.SHUT_RDWR)
                self.tcpSocket.close()
            except socket.error:
                print("Failed to close the socket")
                sys.exit()
        else:
            self.startToPlay()

    def stopTheGameFunc(self):
        stopTheGame = True
