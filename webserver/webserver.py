#import socket module
from socket import *
import sys # In order to terminate the program

serverSocket = socket(AF_INET, SOCK_STREAM)
#Prepare a server socket
serverPort = 6789
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

while True:
    #Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()
    
    try:
        message = connectionSocket.recv(1024).decode()
        filename = message.split()[1]
        f = open(filename[1:])
        outputdata = f.read()
        f.close()
        
        #Send one HTTP header line into socket
        connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
        connectionSocket.send("Content-Type: text/html\r\n".encode())
        connectionSocket.send("\r\n".encode())
        
        #Send the content of the requested file to the client
        connectionSocket.send(outputdata.encode())
        connectionSocket.close()
        
    except IOError:
        #Send response message for file not found
        error_response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
        error_body = "<html><head></head><body><h1>404 Not Found</h1></body></html>"
        connectionSocket.send(error_response.encode())
        connectionSocket.send(error_body.encode())
        
        #Close client socket
        connectionSocket.close()

serverSocket.close()
sys.exit()  #Terminate the program after sending the corresponding data