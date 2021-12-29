import random
from datetime import datetime
import time
import socket
import sys
from threading import Thread


# Text colors
blueColor = '\033[96m'  # blue
yellowColor = '\033[92m'  # yellow
failColor = '\033[96m'  # red


class Server:

    def __init__(self, tcpPort):

        # Initializing the Square parameters
        self.uPortNumber = 13117
        self.tPortNumber = tcpPort
        self.host = ''
        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.answerOne = None
        self.answerTwo = None
        self.answer = None
        self.stopTheGame = False
        self.teamsTable = {}
        self.magicCookie = 0xabcddcba
        self.messageType = 0x2
        self.clientsConnected = 0

        # Creating the broadcastMsg
        magicCookieInBytes = self.magicCookie.to_bytes(byteorder='big', length=4)
        messageTypeInBytes = self.messageType.to_bytes(byteorder='big', length=1)
        tcpPortNumberInBytes = self.tPortNumber.to_bytes(byteorder='big', length=2)
        self.broadMsg = magicCookieInBytes + messageTypeInBytes + tcpPortNumberInBytes

        # Initializing the different sockets

        # UDP Socket
        try:
            self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except:
            print(failColor + "Failed to create server UDP socket")
            sys.exit()

        try:
            self.ip = socket.gethostbyname(socket.gethostname())
        except:
            print(failColor + "Hostname server couldn't be resolved")
            sys.exit()

        # TCP Socket
        try:
            self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print(failColor + "Failed to create server TCP socket")
            sys.exit()

        # Bind the tcp socket with the server host/port
        self.tcpSocket.bind((self.host, self.tPortNumber))



    # First function to run on the server side
    def acceptingClients(self):

        self.tcpSocket.listen(2)

        # Print the listening message
        print(blueColor + "Server started, listening on IP address " + str(self.ip))

        # Starting to send the broadcastMsg
        broadcastThread = Thread(target=self.broadcastMsg)
        broadcastThread.start()

        # Wait for two Clients to connect the Server
        while self.clientsConnected < 2:
            if self.clientsConnected == 0:
                self.teamOneSocket, addressOne = self.tcpSocket.accept()  # Wait for the first Client to connect
                self.teamOneName = self.teamOneSocket.recv(1024).decode(
                    'UTF-8')  # receive the TeamName of the first Team
                self.clientsConnected = self.clientsConnected + 1
                print(yellowColor + "First client connected..")
            else:
                self.teamTwoSocket, addressTwo = self.tcpSocket.accept()  # Wait for the second Client to connect
                self.teamTwoName = self.teamTwoSocket.recv(1024).decode(
                    'UTF-8')  # receive the TeamName of the second Team
                self.clientsConnected = self.clientsConnected + 1
                print(yellowColor + "Second client connected..")
        self.startTheGame()



    # Function to send the broadcastMsg via UDP transport
    def broadcastMsg(self):
        while self.clientsConnected != 2:
            self.udpSocket.sendto(self.broadMsg, ('255.255.255.255', self.uPortNumber))
            time.sleep(1)  # Wait one second between messages



    # Function that runs after the two Clients connected to the Server
    def startTheGame(self):

        time.sleep(10)  # wait 10 seconds until the start of the game

        #  Check the connection with the Clients
        self.checkConnection()

        # Start the game
        print(blueColor + "The Game has been started!")

        # Creating the math question
        numOne = random.randint(0, 5)
        numTwo = random.randint(0, 4)

        tempOne = numOne
        tempTwo = numTwo

        numOne = max(tempOne, tempTwo)
        numTwo = min(tempOne, tempTwo)

        randomMathOperator = random.randint(0, 1)
        if randomMathOperator > 0.5:
            mathMsg = "How much is " + str(numOne) + " + " + str(numTwo) + "?"
            result = numOne + numTwo
        else:
            mathMsg = "How much is " + str(numOne) + " - " + str(numTwo) + "?"
            result = numOne - numTwo

        # Welcome the two Teams and ask the math question
        self.teamOneSocket.sendall(bytes(
            "Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n""Teams: \n1. " + str(
                self.teamOneName) + "\n2. " + str(
                self.teamTwoName) + "\n ====== \nPlease answer the following question as fast as you can:\n" + mathMsg,
            'UTF-8'))
        self.teamTwoSocket.sendall(bytes(
            "Welcome to the tournament of BGU Quick Maths.. get ready, the game is going to begin shortly..\n""Teams: \n1. " + str(
                self.teamOneName) + "\n2. " + str(
                self.teamTwoName) + "\n ====== \nPlease answer the following question as fast as you can:\n" + mathMsg,
            'UTF-8'))

        # Creating two Threads that will take answer from the two Clients
        teamOneGameThread = Thread(target=self.getAnswerFromTeam, args=(self.teamOneSocket, 1,))
        teamTwoGameThread = Thread(target=self.getAnswerFromTeam, args=(self.teamTwoSocket, 2,))

        teamOneGameThread.start()
        teamTwoGameThread.start()

        teamOneGameThread.join()
        teamTwoGameThread.join()

        #  Check the connection with the Clients

        self.checkConnection()

        # teamOne answered first
        if self.answerOne is not None:
            ans = self.answerOne.decode('UTF-8')[0]
            if result == int(ans):  # The first Team has won
                self.printResultWin(self.teamOneName, result)
                self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)

            else:  # The second Team has won
                self.printResultWin(self.teamTwoName, result)
                self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)


        # teamTwo answered first
        elif self.answerTwo is not None:

            ans = self.answerTwo.decode('UTF-8')[0]
            if result == int(ans):  # The second Team has won
                self.printResultWin(self.teamTwoName, result)
                self.updateTeamsTable_win(self.teamTwoName, self.teamOneName)

            else:  # The first Team has won
                self.printResultWin(self.teamOneName, result)
                self.updateTeamsTable_win(self.teamOneName, self.teamTwoName)


        # Draw - none of the teams answered on time
        else:
            self.printResultDraw(result)
            self.updateTeamsTable_draw()

        # Prints the best three teams on the server until now (by the win percentage)
        self.showBestTeams()

        # Closing sockets and restart the server
        self.closeSocketsAndRestart()



    # Function that getting an answer from each client (runs two times in parallel (two threads))
    def getAnswerFromTeam(self, teamSocket, teamNumber):

        teamSocket.setblocking(False)
        t0 = datetime.now()

        while (datetime.now() - t0).seconds <= 10 and self.answer is None:  # While none of both teams has answered, and 10 second didn't pass yet
            try:
                teamAnswer = teamSocket.recv(1024)
            except:
                continue

            if teamAnswer != None:  # The team has answered
                if teamNumber == 1:  # teamOne has answered
                    self.answerOne = teamAnswer
                    self.answer = teamAnswer
                    return
                if teamNumber == 2:  # teamTwo has answered
                    self.answerTwo = teamAnswer
                    self.answer = teamAnswer
                    return



    def printResultWin(self, winnerTeam, result):  # Print the result of the match (not Draw)

        print(blueColor + "Game Over!\nThe correct answer was " + str(
            result) + "!\nCongratulations to the winner: " + winnerTeam)
        self.teamOneSocket.sendall(bytes(
            "Game Over!\nThe correct answer was " + str(result) + "!\nCongratulations to the winner: " + str(
                winnerTeam), 'UTF-8'))
        self.teamTwoSocket.sendall(bytes(
            "Game Over!\nThe correct answer was " + str(result) + "!\nCongratulations to the winner: " + str(
                winnerTeam), 'UTF-8'))



    def printResultDraw(self, result):  # Print the result of the match (Draw)

        print(blueColor + "Game Over!\nThe correct answer was " + str(
            result) + "!\nNone of the team answered on time, so there is a Draw!")
        self.teamOneSocket.sendall(bytes("Game Over!\nThe correct answer was " + str(
            result) + "!\nNone of the team answered on time, so there is a Draw!", 'UTF-8'))
        self.teamTwoSocket.sendall(bytes("Game Over!\nThe correct answer was " + str(
            result) + "!\nNone of the team answered on time, so there is a Draw!", 'UTF-8'))



    # Function that updating the TeamsTable in case of a win of one Team
    def updateTeamsTable_win(self, winnerTeam, loserTeam):
        if winnerTeam in self.teamsTable:
            self.teamsTable[winnerTeam] = (self.teamsTable[winnerTeam][0] + 1, self.teamsTable[winnerTeam][1] + 1, (self.teamsTable[winnerTeam][1] + 1)/(self.teamsTable[winnerTeam][0] + 1))  # (gamesPlayed, gamesWon, win ratio)
        else:
            self.teamsTable[winnerTeam] = (1, 1, 1)
        if loserTeam in self.teamsTable:
            self.teamsTable[loserTeam] = (self.teamsTable[loserTeam][0] + 1, self.teamsTable[loserTeam][1], (self.teamsTable[loserTeam][1])/(self.teamsTable[loserTeam][0] + 1))  # (gamesPlayed, gamesWon, win ratio)
        else:
            self.teamsTable[loserTeam] = (1, 0, 0)



    # Function that updating the TeamsTable in case of a draw between the teams
    def updateTeamsTable_draw(self):
        if self.teamOneName in self.teamsTable:
            self.teamsTable[self.teamOneName] = (self.teamsTable[self.teamOneName][0] + 1, self.teamsTable[self.teamOneName][1], (self.teamsTable[self.teamOneName][1])/(self.teamsTable[self.teamOneName][0] + 1))  # (gamesPlayed, gamesWon, win ratio)
        else:
            self.teamsTable[self.teamOneName] = (1, 0, 0)

        if self.teamTwoName in self.teamsTable:
            self.teamsTable[self.teamTwoName] = (self.teamsTable[self.teamTwoName][0] + 1, self.teamsTable[self.teamTwoName][1], (self.teamsTable[self.teamTwoName][1])/(self.teamsTable[self.teamTwoName][0] + 1))  # (gamesPlayed, gamesWon, win ratio)
        else:
            self.teamsTable[self.teamTwoName] = (1, 0, 0)



    # Function that shows the best three teams played on the server until now (by number of wins)
    def showBestTeams(self):

        sortedLst = sorted(self.teamsTable.items(), key=lambda tup: tup[1][2], reverse=True)

        if len(sortedLst) == 1:
            print(yellowColor + "The best teams on the server are:\n1. " + str(sortedLst[0][0]) + " - win ratio: " + str(100 * sortedLst[0][1][2]) + "%")

        elif len(sortedLst) == 2:
            print(yellowColor + "The best teams on the server are:\n1. " + str(sortedLst[0][0]) + " - win ratio: " + str(100 * sortedLst[0][1][2]) + "%" + "\n2. " +
                  str(sortedLst[1][0]) + " - win ratio: " + str(100 * sortedLst[1][1][2]) + "%")
        else:
            print(yellowColor + "The best teams on the server are:\n1. " + str(sortedLst[0][0]) + " - win ratio: " + str(100 * sortedLst[0][1][2]) + "%" + "\n2. " + str(sortedLst[1][0]) + " - win ratio: " + str(100 * sortedLst[1][1][2]) + "%" + "\n3. " + str(sortedLst[2][0]) + " - win ratio: " + str(100 * sortedLst[2][1][2]) + "%")



    # Function for handling Clients that disconnect from the server
    def checkConnection(self):
        oneDisconnected = False
        TwoDisconnected = False

        try:
            self.teamOneSocket.sendall("".encode())
        except:
            oneDisconnected = True
        try:
            self.teamTwoSocket.sendall("".encode())
        except:
            TwoDisconnected = True

        if oneDisconnected and TwoDisconnected:  # Both Clients disconnected from the server
            print(failColor + "Both Teams disconnected, restarting Server..")
            self.closeSocketsAndRestart()

        if oneDisconnected:
            print(failColor + "Team " + str(self.teamOneName) + " has disconnected from the server, Team " + str(
                self.teamTwoName) + " won the match")
            self.closeSocketsAndRestart()

        if TwoDisconnected:
            print(failColor + "Team " + str(self.teamTwoName) + " has disconnected from the server, Team " + str(
                self.teamOneName) + " won the match")
            self.closeSocketsAndRestart()



    # Function for handling the server state in case of disconnected client
    def closeSocketsAndRestart(self):

        # Closing the first tcpSocket
        try:
            self.teamOneSocket.shutdown(socket.SHUT_RDWR)
            self.teamOneSocket.close()
        except:
            print(failColor + "Failed to close the socket")
            sys.exit()

        # Closing the second tcpSocket
        try:
            self.teamTwoSocket.shutdown(socket.SHUT_RDWR)
            self.teamTwoSocket.close()
        except:
            print(failColor + "Failed to close the socket")
            sys.exit()

        # Runs the Server once again
        self.restartServer()



    # Function for restarting the server
    def restartServer(self):

        print(blueColor + "Game over, sending out offer requests...")

        # Initializing the needed parameters
        self.teamOneName = None
        self.teamTwoName = None
        self.teamOneSocket = None
        self.teamTwoSocket = None
        self.answerOne = None
        self.answerTwo = None
        self.answer = None
        self.clientsConnected = 0

        if self.stopTheGame:  # Check if to Stop the Server

            # Closing the udpSocket
            try:
                self.udpSocket.shutdown(socket.SHUT_RDWR)
                self.udpSocket.close()
            except:
                print(failColor + "Failed to close the socket")
                sys.exit()

            # Closing the tcpSocket
            try:
                self.tcpSocket.shutdown(socket.SHUT_RDWR)
                self.tcpSocket.close()
            except:
                print(failColor + "Failed to close the socket")
                sys.exit()
        else:
            self.acceptingClients()  # Continue in running the server



    # Function that stops the Server
    def stopTheGameFunc(self):
        self.stopTheGame = True


if __name__ == "__main__":
    server = Server(1255)
    server.acceptingClients()
