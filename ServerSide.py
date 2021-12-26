import random
import time
from multiprocessing.pool import ThreadPool
import socket
import sys
import _thread
import multiprocessing
from threading import Thread
from typing import Type


class Server:

    def __init__(self):

        # initializing the Square parameters
        self.uPortNumber = 2015
        self.tPortNumber = 12312
        self.host = ''
        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.teamOneAddress = None
        self.teamTwoAddress = None
        self.answerOne = None
        self.answerTwo = None
        self.magicCookie = 0xabcddcba
        self.messageType = 0x2
        self.clientsConnected = 0


        # initializing the UDP Socket
        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except socket.error:
            print("Failed to create UDP socket")
            sys.exit()

        try:
            self.ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            print("Hostname couldn't be resolved")
            sys.exit()

        # initializing the TCP Socket
        try:
            self.tcpSocket = socket.socket(family=socket.AF_INET, Type=socket.SOCK_STREAM)
        except socket.error:
            print("Failed to create TCP socket")
            sys.exit()
        self.tcpSocket.bind((self.host, self.tPortNumber))



    def broadcastMsg(self, msg):
        while self.clientsConnected != 2:
            self.udpSocket.sendto(msg, ('255.255.255.255', self.uPortNumber))  # TODO correct the broadcast dest ip
            time.sleep(1)  # send the broadcastMsg every 1 second


    def acceptingClients(self):

        self.tcpSocket.listen(2)  # server start listening

        startMsg = "Server started, listening on IP address " + self.ip
        magicCookieInBytes = self.magicCookie.to_bytes(byteorder='big', length=4)
        messageTypeInBytes = self.message_type.to_bytes(byteorder='big', length=1)
        tcpPortNumberInBytes = self.tcp_port.to_bytes(byteorder='big', length=2)
        broadMsg = magicCookieInBytes + messageTypeInBytes + tcpPortNumberInBytes


        print(startMsg)
        broadcastThread = Thread(target=self.broadcastMsg(broadMsg), daemon=True)
        broadcastThread.start()

        while self.clientsConnected < 2:
            if self.clientsConnected == 0:
                self.teamOneSocket, self.teamOneAddress = self.tcpSocket.accept()
                self.teamOneName = self.teamOneSocket.recv(1024).decode('UTF-8')  # receive the TeamName of the first Team
                self.clientsConnected = self.clientsConnected + 1

            else:  # the second Client connected to the server
                self.teamTwoSocket, self.teamTwoAddress = self.tcpSocket.accept()
                self.teamTwoName = self.teamTwoSocket.recv(1024).decode('UTF-8')  # receive the TeamName of the second Team
                self.clientsConnected = self.clientsConnected + 1
        self.startTheGame()


    def startTheGame(self):

        time.sleep(10)  # wait 10 seconds until the start of the game
        print("The Game has been started!")
        numOne = random.randint(0, 100)
        numTwo = random.randint(0, 100)

        randomMathOperator = random.randint(0, 1)
        if randomMathOperator > 0.5:
            mathMsg = "How much is " + numOne + " + " + numTwo + "?"
            result = numOne + numTwo
        else:
            mathMsg = "How much is " + numOne + " - " + numTwo + "?"
            result = numOne - numTwo


        # Welcome the two Teams
        self.teamOneSocket.sendall("Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n "
                                   "Teams: \n 1. " + self.teamOneName + "\n2. " + self.teamTwoName)
        self.teamTwoSocket.sendall("Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n "
                                   "Teams: \n 1. " + self.teamOneName + "\n2. " + self.teamTwoName)

        #  Ask the math question
        self.teamOneSocket.sendall("Please answer the following question as fast as you can:\n" + mathMsg)
        self.teamTwoSocket.sendall("Please answer the following question as fast as you can:\n" + mathMsg)


        teamOneGameThread = Thread(target=self.getAnswerFromTeam(self.teamOneSocket, 1), daemon=True)
        teamTwoGameThread = Thread(target=self.getAnswerFromTeam(self.teamTwoSocket, 2), daemon=True)

        teamOneGameThread.start()
        teamTwoGameThread.start()

        teamOneGameThread.join()
        teamTwoGameThread.join()

        if self.answerOne is not None:
            if result == self.answerOne:  # the first Team has won
                print("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)
                self.teamOneSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)
                self.teamTwoSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)

            else:  # the second Team has won
                print("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)
                self.teamOneSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)
                self.teamTwoSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)


        elif self.answerTwo is not None:
            if result == self.answerOne:  # the second Team has won
                print("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)
                self.teamOneSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)
                self.teamTwoSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamTwoName)

            else:  # the first Team has won
                print("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)
                self.teamOneSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)
                self.teamTwoSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nCongratulations to the winner: " + self.teamOneName)

        else:  # Draw
            print("Game Over!\nThe correct answer was " + result + "!\nNone of the team answered on time, so there is a Draw!")
            self.teamOneSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nNone of the team answered on time, so there is a Draw!")
            self.teamTwoSocket.sendall("Game Over!\nThe correct answer was " + result + "!\nNone of the team answered on time, so there is a Draw!")











    def getAnswerFromTeam(self, teamSocket, teamNumber):
        teamAnswer = teamSocket.recv(1024)
        #  TODO stop the second Thread
        #  TODO stop the game if 10 sec was passed without a answer

        if teamNumber == 1:
            self.answerOne = teamAnswer
        if teamNumber == 2:
            self.answerTwo = teamAnswer





# pool = ThreadPool(2)  # initializing ThreadPool with 2 threads
# runServerFlag = 2  # start the game only after the value is 0
#
#
#
# def serverStrategy(clientSocket):
#
#     while runServerFlag < 2:  # wait for the second client to connect
#         a = 5
#     # start the game
#
#
# def startServer():
#
#     #  initialize the wanted parameters
#     try:
#         localIp = socket.gethostbyname(socket.gethostname())
#     except socket.gaierror:
#         print("Hostname couldn't be resolved")
#         sys.exit
#
#     localPort = 2015  # server socket port number
#     bufferSize = 1024
#
#     # Create the first UDP socket
#     try:
#         udpServerSocket = socket.socket(family=socket.AF_INET, Type=socket.SOCK_DGRAM)
#
#     except socket.error:
#         print("Failed to create UDP socket")
#         sys.exit()
#
#
#     # bind the socket to a specific address and ip
#
#     udpServerSocket.bind(localIp, localPort)
#     udpServerSocket.settimeout(1)
#
#     msgFromServer = "Server started, listening on ip address " + str(localIp)  # Message of the server
#     print(msgFromServer) ######## brodcast including magic coockie.....port(tcp)
#
#
#     while runServerFlag > 0:
#         if runServerFlag == 2:
#             message1, address1 = udpServerSocket.recvfrom(bufferSize)
#             runServerFlag = 1
#         else:
#             message2, address2 = udpServerSocket.recvfrom(bufferSize)
#             runServerFlag = 0
#
#     try:
#         tcpServerSocketOne = socket.socket(family=socket.AF_INET, Type=socket.SOCK_STREAM)
#     except socket.error:
#         print("Failed to create TCP socket")
#         sys.exit()
#
#     currentPortNumber = localPort + 1
#     tcpServerSocketOne.bind(localIp, currentPortNumber)
#
#     newPortNumber = str.encode(currentPortNumber)
#
#     udpServerSocket.sendto(newPortNumber, address1)
#     udpServerSocket.sendto(newPortNumber, address2)
#
#     tcpServerSocketOne.listen(2)
#     while runServerFlag < 2:
#         (clientSocKet, address) = tcpServerSocketOne.accept()
#         pool.run(serverStrategy(clientSocKet))
#         runServerFlag += 1
#        # if runServerFlag == 2
