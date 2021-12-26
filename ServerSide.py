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
        self.stopTheGame = 10
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


    def acceptingClients(self):  # first function to run on the server side

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

        # Closing the first tcpSocket
        try:
            self.teamOneSocket.shutdown(socket.SHUT_RDWR)
            self.teamOneSocket.close()
        except socket.error:
            print("Failed to close the socket")
            sys.exit()

        # Closing the second tcpSocket
        try:
            self.teamTwoSocket.shutdown(socket.SHUT_RDWR)
            self.teamTwoSocket.close()
        except socket.error:
            print("Failed to close the socket")
            sys.exit()

        self.restartServer()




    def restartServer(self):

        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.teamOneAddress = None
        self.teamTwoAddress = None
        self.answerOne = None
        self.answerTwo = None
        self.clientsConnected = 0
        self.stopTheGame = self.stopTheGame - 1

        if self.stopTheGame == 0:  # stop the server

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
            self.acceptingClients()  # continue in running the server


    def getAnswerFromTeam(self, teamSocket, teamNumber):
        teamAnswer = teamSocket.recv(1024)
        #  TODO stop the second Thread
        #  TODO stop the game if 10 sec was passed without a answer

        if teamNumber == 1:
            self.answerOne = teamAnswer
        if teamNumber == 2:
            self.answerTwo = teamAnswer






