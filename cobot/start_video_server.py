import tkinter as tk
import time
from video_server import *

def main():

    while True:
        server = None
        try:
            print("starting server")
            server = Video_Server()
            server.bind()

            server.listen()
            while server.running:
                time.sleep(1)
        finally:
            print("Attempting to close server...")
            if server:
                server.stop()
                server.close()
    

if __name__ == "__main__":
    main()

