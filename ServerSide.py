import random
import time
from multiprocessing.pool import ThreadPool
import socket
import sys
import _thread
import multiprocessing
from threading import Thread
from typing import Type
from datetime import time, datetime



#  TODO: handle exception of failed message



class Server:

    def _init_(self):

        # Initializing the Square parameters
        self.uPortNumber = 13117
        self.tPortNumber = 12312  # TODO: check what should be the port number
        self.host = ''
        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.teamOneAddress = None
        self.teamTwoAddress = None
        self.answerOne = None
        self.answerTwo = None
        self.answer = None
        self.answerOneTime = None
        self.answerTwoTime = None
        self.stopTheGame = False
        self.teamsTable = {}
        self.magicCookie = 0xabcddcba
        self.messageType = 0x2
        self.clientsConnected = 0

        # Initializing the UDP Socket
        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except socket.error:
            print("Failed to create server UDP socket")
            sys.exit()

        try:
            self.ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            print("Hostname server couldn't be resolved")
            sys.exit()

        # Initializing the TCP Socket
        try:
            self.tcpSocket = socket.socket(family=socket.AF_INET, Type=socket.SOCK_STREAM)
        except socket.error:
            print("Failed to create server TCP socket")
            sys.exit()
        self.tcpSocket.bind((self.host, self.tPortNumber))



    def acceptingClients(self):  # First function to run on the server side

        self.tcpSocket.listen(2)

        # Creating the different ServerMsgs
        startMsg = "Server started, listening on IP address " + str(self.ip)
        magicCookieInBytes = self.magicCookie.to_bytes(byteorder='big', length=4)
        messageTypeInBytes = self.message_type.to_bytes(byteorder='big', length=1)
        tcpPortNumberInBytes = self.tcp_port.to_bytes(byteorder='big', length=2)
        broadMsg = magicCookieInBytes + messageTypeInBytes + tcpPortNumberInBytes

        print(startMsg)

        # Starting to send the broadcastMsg
        broadcastThread = Thread(target=self.broadcastMsg(broadMsg), daemon=True)
        broadcastThread.start()

        # Wait for two Clients to connect the Server
        while self.clientsConnected < 2:

            if self.clientsConnected == 0:
                self.teamOneSocket, self.teamOneAddress = self.tcpSocket.accept()  # Wait for the first Client to connect
                self.teamOneName = self.teamOneSocket.recv(1024).decode('UTF-8')  # receive the TeamName of the first Team
                self.clientsConnected = self.clientsConnected + 1

            else:
                self.teamTwoSocket, self.teamTwoAddress = self.tcpSocket.accept()  # Wait for the second Client to connect
                self.teamTwoName = self.teamTwoSocket.recv(1024).decode('UTF-8')  # receive the TeamName of the second Team
                self.clientsConnected = self.clientsConnected + 1
        self.startTheGame()


    def broadcastMsg(self, msg):  # Function to send the broadcastMsg via UDP transport
        while self.clientsConnected != 2:
            self.udpSocket.sendto(msg, ('255.255.255.255', self.uPortNumber))  # TODO correct the broadcast dest ip
            time.sleep(1)  # Wait one second between messages

    def startTheGame(self):

        time.sleep(10)  # wait 10 seconds until the start of the game
        print("The Game has been started!")

        # Creating the math question
        numOne = random.randint(0, 100)
        numTwo = random.randint(0, 100)

        randomMathOperator = random.randint(0, 1)
        if randomMathOperator > 0.5:
            mathMsg = "How much is " + str(numOne) + " + " + str(numTwo) + "?"
            result = numOne + numTwo
        else:
            mathMsg = "How much is " + str(numOne) + " - " + str(numTwo) + "?"
            result = numOne - numTwo

        # Welcome the two Teams and ask the math question
        self.teamOneSocket.sendall("Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n ""Teams: \n 1. " + str(self.teamOneName) + "\n2. " + str(self.teamTwoName) + "\n ====== \nPlease answer the following question as fast as you can:\n" + mathMsg)
        self.teamTwoSocket.sendall("Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n ""Teams: \n 1. " + str(self.teamOneName) + "\n2. " + str(self.teamTwoName) + "\n ====== \nPlease answer the following question as fast as you can:\n" + mathMsg)

        # Creating two Threads that will take answer from the two Clients
        teamOneGameThread = Thread(target=self.getAnswerFromTeam(self.teamOneSocket, 1), daemon=True)
        teamTwoGameThread = Thread(target=self.getAnswerFromTeam(self.teamTwoSocket, 2), daemon=True)

        teamOneGameThread.start()
        teamTwoGameThread.start()

        teamOneGameThread.join()
        teamTwoGameThread.join()

        if self.answerOne is not None and self.answerTwo is not None:
            deltaTime = (datetime.strptime(self.answerOneTime, '%H:%M') - datetime.strptime(self.answerTwoTime, '%H:%M'))/12


            if deltaTime.seconds < 0:  # teamOne answered first

                if self.answerOne is not None:
                    if result == self.answerOne:  # The first Team has won
                        self.printResultWin(self.teamOneName, result)
                        self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)

                    else:  # The second Team has won
                        self.printResultWin(self.teamTwoName, result)
                        self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)

            elif deltaTime.seconds > 0:  # teamTwo answered first

                if result == self.answerTwo:  # The second Team has won
                    self.printResultWin(self.teamTwoName, result)
                    self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)

                else:  # The first Team has won
                    self.printResultWin(self.teamOneName, result)
                    self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)
            else:
                # Draw
                self.printResultDraw(result)
                self.updateTeamsTable_draw()

        if self.answerOne is not None:  # teamOne answered first

            if result == self.answerOne:  # The first Team has won
                self.printResultWin(self.teamOneName, result)
                self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)

            else:  # The second Team has won
                self.printResultWin(self.teamTwoName, result)
                self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)

        elif self.answerTwo is not None:  # teamTwo answered first

            if result == self.answerTwo:  # The second Team has won
                self.printResultWin(self.teamTwoName, result)
                self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)

            else:  # The first Team has won
                self.printResultWin(self.teamOneName, result)
                self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)

        else:  # Draw - none of the teams answered on time
            self.printResultDraw(result)
            self.updateTeamsTable_draw()

        bestTeamsMSG = self.showBestTeams()

        print(bestTeamsMSG)

        self.teamOneSocket.send(bytes(bestTeamsMSG), 'UTF-8')
        self.teamTwoSocket.send(bytes(bestTeamsMSG), 'UTF-8')


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

        # Runs the Server once again
        self.restartServer()


    def updateTeamsTable_win(self, winnerTeam, loserTeam):
        if winnerTeam in self.teamsTable:
            self.teamsTable[winnerTeam] = (self.teamsTable[winnerTeam][0] + 1, self.teamsTable[winnerTeam][1] + 1)  # (gamesPlayed, gamesWon)
        else:
            self.teamsTable[winnerTeam] = (1, 1)
        if loserTeam in self.teamsTable:
            self.teamsTable[loserTeam] -= (self.teamsTable[loserTeam][0] + 1, self.teamsTable[loserTeam][1])  # (gamesPlayed, gamesWon)
        else:
            self.teamsTable[loserTeam] = (1, 0)


    def updateTeamsTable_draw(self):
        if self.teamOneName in self.teamsTable:
            self.teamsTable[self.teamOneName] = (self.teamsTable[self.teamOneName][0] + 1, self.teamsTable[self.teamOneName][1])  # (gamesPlayed, gamesWon)
        else:
            self.teamsTable[self.teamOneName] = (1, 0)
        if self.teamTwoName in self.teamsTable:
            self.teamsTable[self.teamTwoName] = (self.teamsTable[self.teamTwoName][0] + 1, self.teamsTable[self.teamTwoName][1])  # (gamesPlayed, gamesWon)
        else:
            self.teamsTable[self.teamTwoName] = (1, 0)


    def printResultWin(self, winnerTeam, result):  # not Draw

        print("Game Over!\nThe correct answer was " + str(result) + "!\nCongratulations to the winner: " + winnerTeam)
        self.teamOneSocket.sendall(
            "Game Over!\nThe correct answer was " + str(result) + "!\nCongratulations to the winner: " + winnerTeam)
        self.teamTwoSocket.sendall(
            "Game Over!\nThe correct answer was " + str(result) + "!\nCongratulations to the winner: " + winnerTeam)



    def printResultDraw(self, result):  # Draw

        print("Game Over!\nThe correct answer was " + str(result) + "!\nNone of the team answered on time, so there is a Draw!")
        self.teamOneSocket.sendall(
            "Game Over!\nThe correct answer was " + str(result) + "!\nNone of the team answered on time, so there is a Draw!")
        self.teamTwoSocket.sendall(
            "Game Over!\nThe correct answer was " + str(result) + "!\nNone of the team answered on time, so there is a Draw!")



    def getAnswerFromTeam(self, teamSocket, teamNumber):

        teamSocket.setblocking(False)
        stopper = time.time()

        while not self.answer and stopper <= 10:  # While none of both teams has answered, and 10 second didn't pass yet
            try:
                teamAnswer = teamSocket.recv(1024)
            except:
                pass

            if teamAnswer is not None:  # The team has answered
                self.answer = True
                if teamNumber == 1:  # teamOne has answered
                    self.answerOne = teamAnswer
                    self.answerOneTime = datetime.now()
                if teamNumber == 2:  # teamTwo has answered
                    self.answerTwo = teamAnswer
                    self.answerTwoTime = datetime.now()


    def restartServer(self):

        print("Game over, sending out offer requests...")

        # Initializing the needed parameters
        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.teamOneAddress = None
        self.teamTwoAddress = None
        self.answerOne = None
        self.answerTwo = None
        self.clientsConnected = 0

        if self.stopTheGame:  # Check if to Stop the Server

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
            self.acceptingClients()  # Continue in running the server

    def stopTheGameFunc(self):  # Function that stops the Client
        self.stopTheGame = True



    def showBestTeams(self):
        sortedDict = sorted(self.teamsTable, lambda x: (x[1]/x[0]))
        teamsList = sortedDict.keys()

        #Win percentage of the teams
        team1 = ((sortedDict[teamsList[0]][1]/sortedDict[teamsList[0]][0])*100)
        team2 = ((sortedDict[teamsList[1]][1]/sortedDict[teamsList[1]][0])*100)
        team3 = ((sortedDict[teamsList[2]][1]/sortedDict[teamsList[2]][0])*100)

        return ("The top 3 teams on the server are:\n1. " + teamsList[0] + " - win percentages: " + team1 + "\n2. " +
         teamsList[1] + " - win percentages: " + team2 + "\n3. " + teamsList[2] + " - win percentages: " + team3)


