import random

import cv2
import socket
import struct
import numpy as np
import threading
import queue
import time


class VideoReceiver:
    def __init__(self, server_ip, port=25666):
        self.server_ip = server_ip
        self.port = port

        # Queues for thread communication
        self.encoded_queue = queue.Queue(maxsize=10)  # Encoded frame data
        self.decoded_queue = queue.Queue(maxsize=10)  # Decoded frames

        # Threading control
        self.running = False
        self.receive_thread = None
        self.decode_thread = None
        self.idx = random.randint(0, 10)

#self.display_thread = None

        # Socket
        self.client_socket = None

    def start(self):
       # try:
      #      cv2.namedWindow(f"Receiving{self.idx}", cv2.WINDOW_NORMAL)
     #   except:
     #       print("WTF")
        """Start all threads"""
        self.running = True

        # Connect to server
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.port))
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)
            print(f"Connected to {self.server_ip}:{self.port}")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        # Start threads
        self.receive_thread = threading.Thread(target=self._receive_frames, daemon=True)
        self.decode_thread = threading.Thread(target=self._decode_frames, daemon=True)
      #  self.display_thread = threading.Thread(target=self._display_frames, daemon=True)

        self.receive_thread.start()
        self.decode_thread.start()

    def _receive_frames(self):
        """Thread 1: Receive encoded frames from socket"""
        print("Receive thread started")
        data = b""
        payload_size = struct.calcsize("Q")
        receive_count = 0

        while self.running:
            try:
                # Receive message size
                while len(data) < payload_size:
                    packet = self.client_socket.recv(4096)
                    if not packet:
                        print("Connection closed by server")
                        self.running = False
                        break
                    data += packet

                if not self.running:
                    break

                # Unpack message size
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                # Receive frame data
                while len(data) < msg_size:
                    remaining = msg_size - len(data)
                    chunk_size = min(65536, remaining)
                    packet = self.client_socket.recv(chunk_size)
                    if not packet:
                        self.running = False
                        break
                    data += packet

                if not self.running:
                    break

                # Extract frame data
                frame_data = data[:msg_size]
                data = data[msg_size:]

                try:
                    # Non-blocking put
                    self.encoded_queue.put(frame_data, block=False)
                    receive_count += 1
                    if receive_count % 100 == 0:
                        print(f"Received {receive_count} frames")
                except queue.Full:
                    # Drop frame if queue is full
                    pass

            except Exception as e:
                print(f"Error in receive thread: {e}")
                self.running = False
                break

        print("Receive thread stopped")

    def _decode_frames(self):
        """Thread 2: Decode JPEG frames"""
        print("Decode thread started")
        decode_count = 0

        while self.running:
            try:
                # Get encoded frame with timeout
                frame_data = self.encoded_queue.get(timeout=1)

                # Decode frame
                frame = cv2.imdecode(
                    np.frombuffer(frame_data, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )

                if frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    while not self.decoded_queue.empty():
                        try:
                            self.decoded_queue.get_nowait()
                        except queue.Empty:
                            break

                    self.decoded_queue.put(frame_rgb, block=False)
                    
            except queue.Empty:
                continue

        print("Decode thread stopped")

    def get_frame(self):
        try:
            return self.decoded_queue.get(block=False)
        except queue.Empty:
            return None

    def is_running(self):
        return self.running



    def _display_frames(self):
        """Thread 3: Display decoded frames"""
        print("Display thread started")
        display_count = 0
        while self.running:

            try:
                # Get decoded frame with timeout
                frame = self.decoded_queue.get(block=False)

                # Display frame
                cv2.imshow(f"Receiving{self.idx}", frame)
                display_count += 1

                if display_count % 100 == 0:
                    print(f"Displayed {display_count} frames")

                # Check for quit key
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quit key pressed")
                    self.running = False
                    break

            except queue.Empty:
                # Still need waitKey for window updates
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                    break
            except Exception as e:
                print(str(e))
                self.running = False
                break

        print("Display thread stopped")
        


    def stop(self):
        """Stop all threads and cleanup"""
        print("Stopping video receiver...")
        self.running = False

        # Wait for threads to finish
        if self.receive_thread:
            self.receive_thread.join(timeout=10)
        if self.decode_thread:
            self.decode_thread.join(timeout=10)

        # Close socket
        if self.client_socket:
            self.client_socket.close()

        print("Video receiver stopped")
