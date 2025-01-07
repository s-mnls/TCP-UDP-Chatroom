# to run in terminal: python server.py
# to run in terminal: python client.py --name
from chatroom import ClientTCP
import argparse
from chatroom import ServerTCP
server = ServerTCP(12345)
server.accept_client()



