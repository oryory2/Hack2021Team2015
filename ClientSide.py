import select
import socket
import sys
from datetime import datetime
from threading import Thread


class Client:

    def __init__(self):

        # Initializing the Square parameters
        self.name = "None"
        self.port = 13117
        self.host = ''
        self.magicCookie = 0xabcddcba
        self.messageType = 0x2
        self.serverIP = None
        self.serverPort = None
        self.stopTheGame = False
        self.serverConnected = 0

        # Initializing the UDP Socket
        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except: # socket.error:
            print("Failed to create client UDP socket")
            sys.exit()
        self.udpSocket.bind((self.host, self.port))

        # Initializing the TCP Socket
        try:
            self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:  # socket.error:
            print("Failed to create server TCP socket")
            sys.exit()

    def searchForServer(self):  # First function to run on the server side

        print("Client started, listening for offer requests...")
        while self.serverConnected < 1:
            msgFromServer, serverInfo = self.udpSocket.recvfrom(2048)  # wait for broadcast message from a Server

            # Extract the data from the ServerMsg
            self.serverIP = serverInfo[0]
            magicCookie = hex(int(msgFromServer.hex()[:8], 16))
            messageType = msgFromServer.hex()[9:10]
            self.serverPort = int(msgFromServer.hex()[10:], 16)

            # Verify all the different parameters from the Server
            if hex(self.magicCookie) != magicCookie or self.messageType != int(messageType):
                continue
            print("Received offer from " + str(self.serverIP) + ", attempting to connect...\n")
            self.connectToServer()  # Try to connect to the specific Server

        # Connected the Server successfully, and now starting to play
        self.startToPlay() #######

        # whileFlag = True
        # while whileFlag:
        #     inputOrOutput = [self.tcpSocket, sys.stdin]
        #     inReady, outReady, exceptReady = select.select(inputOrOutput, [], [])
        #
        #     for message in inReady:
        #         if message == self.tcpSocket:  # Received the message from the server before answering
        #             msg = message.recv(1024).decode()
        #             print(msg)
        #             whileFlag = False
        #             break
        #         if message == sys.stdin:  # Sent the answer to the server before the second Client or before 10 seconds passed
        #             answer = sys.stdin.readline()
        #             print("My answer is: " + answer)
        #             self.tcpSocket.sendall(bytes(answer, 'UTF-8'))



        # The game has been finished, getting the final result
        msgFromServer = self.tcpSocket.recv(1024) #######
        print(msgFromServer.decode('UTF-8')) #######

        # Closing the tcpSocket
        try:
            self.tcpSocket.shutdown(socket.SHUT_RDWR)
            self.tcpSocket.close()
        except:  # socket.error:
            print("Failed to close the socket")
            sys.exit()

        print("Server disconnected, listening for offer requests...")

        # Runs the Client once again
        self.restart()

    def connectToServer(self):

        # Try to connect to the server
        try:
            self.tcpSocket.connect((self.serverIP, self.serverPort))  # TODO: what happens if the server is not listening anymore
        except socket.error:
            print("Failed to connect to the server with IP " + str(self.serverIP))
            return

        # Sending the server the client name
        self.tcpSocket.send(bytes(self.name, 'UTF-8'))
        self.serverConnected = 1

    # Answer the math question
    def answerToServer(self):

        currentTime = datetime.now()

        while (datetime.now() - currentTime).seconds <= 10:
            answer = input('Answer as fast as you can: ')
            self.tcpSocket.send(bytes(answer, 'UTF-8'))
            return


    def startToPlay(self):

        # Receiving and printing the question from the Server
        msgFromServer = self.tcpSocket.recv(1024)
        print(msgFromServer.decode('UTF-8'))
        teamOneGameThread = Thread(target=self.answerToServer)
        teamOneGameThread.start()


    def restart(self):

        # Initializing the needed parameters
        self.serverIP = None
        self.serverPort = None
        self.serverConnected = 0

        if self.stopTheGame:  # Check if to Stop the Client

            # Closing the udpSocket
            try:
                self.udpSocket.shutdown(socket.SHUT_RDWR)
                self.udpSocket.close()
            except:  # socket.error:
                print("Failed to close the socket")
                sys.exit()

            # Closing the tcpSocket
            try:
                self.tcpSocket.shutdown(socket.SHUT_RDWR)
                self.tcpSocket.close()
            except: # socket.error:
                print("Failed to close the socket")
                sys.exit()
        else:
            self.searchForServer()  # Continue in running the Client

    def stopTheGameFunc(self):  # Function that stops the Client
        self.stopTheGame = True



if __name__ == "__main__":
    client = Client()
    client.searchForServer()