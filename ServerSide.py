from multiprocessing.pool import ThreadPool
import socket
import sys
import _thread
import multiprocessing
from typing import Type


pool = ThreadPool(2) # initilizing ThreadPool with 2 threads
runServerFlag = 2 # start the game only after the value is 0


    
def serverStrategy(clientSocket):
    
    while(runServerFlag < 2):
        # wait for the secound client to connect
        a = 5
    # start the game



    
def startServer():
    # initilize the wanted parameters
    try:
        localIp = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        print("Hostname couldn't be resolved")
        sys.exit

    loclPort = 2015
    bufferSize = 1024

    msgFromServer = "Server started, listening on ip address " + str(localIp) # Message of the server

    # Create the first UDP socket
    try:
        udpServerSocket = socket.socket(family=socket.AF_INET, Type = socket.SOCK_DGRAM)

    except socket.error:
        print("Failed to create UDP socket")
        sys.exit()
        

    # bind the socket to a specific address and ip

    udpServerSocket.bind(localIp, loclPort)
    udpServerSocket.settimeout(1)

    print(msgFromServer)

    # change this while!!!

    while(runServerFlag > 0):
        if runServerFlag == 2:
            message1, address1 = udpServerSocket.recvfrom(bufferSize)
            runServerFlag = 1
        else:
            message2, address2 = udpServerSocket.recvfrom(bufferSize)
            runServerFlag = 0

    try:
        tcpServerSocketOne = socket.socket(family=socket.AF_INET, Type = socket.SOCK_STREAM)
    except socket.error:
        print("Failed to create TCP socket")
        sys.exit()

    currentPortNumber = loclPort + 1
    tcpServerSocketOne.bind(localIp, currentPortNumber)

    newPortNumber = str.encode(currentPortNumber)

    udpServerSocket.sendto(newPortNumber, address1)
    udpServerSocket.sendto(newPortNumber, address2)

    tcpServerSocketOne.listen(2)
    while(runServerFlag < 2):
        (clientSocKet, address) = tcpServerSocketOne.accept()
        pool.run(serverStrategy(clientSocKet))
        runServerFlag += 1
       # if runServerFlag == 2:
