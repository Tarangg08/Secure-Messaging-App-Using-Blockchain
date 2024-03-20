import json
import os
import random
import socket
import string
import sys
import threading
import tkinter as tk
from io import StringIO
from tkinter import messagebox

from art import text2art
from colorama import Fore

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'BlockChain'))
import BlockChain

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'AES_Crypto'))
# Initialize colorama
from colorama import init

import AES_Crypto

init()

# Run BlockChain
blockchain = BlockChain.Blockchain()
genesisBlock = blockchain.head

# Random String for Generating Key and GroupId
def randomString(stringLength=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

# Server Class
class Server:
    port = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connections = []

    def __init__(self, port):
        self.port = port
        self.sock.bind(('0.0.0.0', int(port)))
        self.sock.listen(1)

    def sendBroadcast(self):
        while True:
            try:
                data = bytes(input(""), 'utf-8')
                if data == "exit":
                    print("Closing Server")
                    os.kill(os.getpid(), 9)
            except EOFError as error:
                print("Closing Server")
                os.kill(os.getpid(), 9)

    def handler(self, c, a):
        while True:
            try:
                data = c.recv(1024)
            except Exception as error:
                print(str(a[0]) + ':' + str(a[1]) + " disconnected")
                self.connections.remove(c)
                c.close()
                break
            block = BlockChain.Block(data.decode('utf-8'))
            blockchain.mine(block)
            for connection in self.connections:
                connection.send(bytes(str(block.data), 'utf-8'))
            if not data:
                print(str(a[0]) + ':' + str(a[1]) + " disconnected")
                self.connections.remove(c)
                c.close()
                break

    def run(self):
        iThread = threading.Thread(target=self.sendBroadcast)
        iThread.daemon = True
        iThread.start()
        os.system('cls')
        os.system('clear')
        print("//////////// Welcome to ///////////////////")
        print(text2art("MY BLOCK CHAT"))
        print("SERVER running on port " + str(socket.gethostbyname(socket.gethostname())) + ":" + str(self.port))
        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=self.handler, args=(c, a))
            cThread.daemon = True
            cThread.start()
            self.connections.append(c)
            print(str(a[0]) + ':' + str(a[1]) + " connected")

# Client Class
class Client:
    key_aes = ''
    name = ''
    groupId = ''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def sendMsg(self):
        while True:
            try:
                private_msg = input("")
                if private_msg == "exit":
                    print("Closing Connection")
                    os.kill(os.getpid(), 9)
                secret_key = self.key_aes
                data = {
                    "groupId": str(self.groupId),
                    "sender": str(self.name),
                    "msg": str(AES_Crypto.AESCipher(secret_key).encrypt(private_msg).decode('utf-8'))
                }
                jsonData = json.dumps(data)
                self.sock.send(bytes(jsonData, "utf-8"))
            except EOFError as error:
                print("Closing Connection")
                os.kill(os.getpid(), 9)

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.root = tk.Tk()
        self.root.title("Chat App")
        self.root.geometry("300x150")

        label = tk.Label(self.root, text="Enter your name:")
        label.pack()

        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()

        self.mode_var = tk.IntVar()
        self.mode_var.set(1)

        mode_label = tk.Label(self.root, text="Choose mode:")
        mode_label.pack()

        create_button = tk.Radiobutton(self.root, text="Create Room", variable=self.mode_var, value=1)
        create_button.pack()

        join_button = tk.Radiobutton(self.root, text="Join Room", variable=self.mode_var, value=2)
        join_button.pack()

        submit_button = tk.Button(self.root, text="Submit", command=self.submit)
        submit_button.pack()

        self.root.mainloop()

    def submit(self):
        self.name = self.name_entry.get()
        self.root.destroy()

        if self.mode_var.get() == 1:
            self.create_room()
        else:
            self.join_room()

    def create_room(self):
        self.key_aes = randomString(20).upper()
        self.groupId = randomString(10).upper()
        messagebox.showinfo("Room Details",
                            f"Group ID: {self.groupId}\nSecret Key: {self.key_aes}\nShare these details with others.")
        self.initiate_chat()

    def join_room(self):
        self.groupId = input("Enter Group ID: ")
        self.key_aes = input("Enter Secret Key: ")
        self.initiate_chat()

    def initiate_chat(self):
        self.sock.connect((self.address, int(self.port)))  # Establish socket connectionprint(Fore.LIGHTYELLOW_EX)
        print("////////// WELCOME TO CHAT ROOM ///////////")
        print(" CHAT ROOM Group_id : " + self.groupId + " Started!!!")
        print(" You are : " + self.name)
        print("///////////////////////////////////////////")
        print(Fore.LIGHTGREEN_EX)
        iThread = threading.Thread(target=self.sendMsg)
        iThread.daemon = True
        iThread.start()
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                newBlock = json.loads(data.decode("utf-8"))
                groupId = newBlock["groupId"]
                sender = newBlock["sender"]
                msg = newBlock["msg"]
                if groupId == self.groupId:
                    print(str(sender) + " : " + str(AES_Crypto.AESCipher(self.key_aes).decrypt(msg).decode('utf-8')))
            except Exception as e:
                print("Error receiving data:", e)


if __name__ == "__main__":
    print("==========================")
    print("Welcome to the Chat App!")
    print("==========================")
    print("1. Start as Server")
    print("2. Start as Client")
    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        port = input("Enter port number to run the server: ")
        server = Server(port)
        server.run()
    elif choice == "2":
        address = input("Enter server address: ")
        port = input("Enter server port: ")
        client = Client(address, port)
