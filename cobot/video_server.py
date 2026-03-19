import socket, pickle, cv2, struct, imutils, subprocess, re, time
import threading, queue
def main():
    server = Video_Server()
    a
class Video_Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ip = None
        self.interface_list = None
        self.port = 25666
        self.get_ip()

        self.running = False
        self.capture_thread = None
        self.encode_thread = None
        self.transmit_thread = None

        self.socket_address = (self.ip, self.port)


        self.frame_queue = None
        self.encoded_queue = None

        print(self.ip)

    def close(self):
        self.server_socket.close()
        #self.vid.release()
        self.client_socket.close()
        self.clear()

    def bind(self):

        self.server_socket.bind(self.socket_address)
        
    def clear(self):
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get(block=False)
                self.frame_queue.task_done()
            except self.frame_queue.Empty:
                break

        while not self.encoded_queue.empty():
            try:
                self.encoded_queue.get(block=False)
                self.encoded_queue.task_done()
            except self.encoded_queue.Empty:
                break               

    def listen(self):

        self.server_socket.listen(1)
        print("Listening at: ", self.socket_address)


        while True:
            self.frame_queue = queue.Queue(maxsize=10)
            self.encoded_queue = queue.Queue(maxsize=10)
            self.running = True
            print("listening")

            self.client_socket, addr = self.server_socket.accept()


            print(f"Connection establisted to {addr}.")


            self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.encode_thread = threading.Thread(target=self._encode_frames, daemon=True)
            self.transmit_thread = threading.Thread(target=self._transmit_frames, daemon=True)

            self.capture_thread.start()
            self.encode_thread.start()
            self.transmit_thread.start()


            print("cleaning up threads")
            self.capture_thread.join()
            self.encode_thread.join()
            self.transmit_thread.join()
            print("done listening")
            self.client_socket.close()
            self.clear()

    def _capture_frames(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print("Could not capture video!")
            self.running = False
            self.clear()
            cap.release()
            return
        
        frame_count = 0

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                self.frame_queue.put(frame, block=False)
                frame_count += 1
                if frame_count % 360 == 0:
                    print(f"Captured {frame_count} frames.")
            except queue.Full:
                print("Queue is full " + f"count = {frame_count}")
                continue

        cap.release()
        print("Capture thread stopped")
        self.running = False


    def _encode_frames(self):
        encode_count = 0

        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)

                encode_opts = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                result, encoded_frame = cv2.imencode('.jpg', frame, encode_opts)

                if result:
                    data = encoded_frame.tobytes()

                try:
                    self.encoded_queue.put(data, block=False)
                    encode_count += 1

                    if encode_count % 360 == 0:
                        print(f"Encoded {encode_count} frames.")

                except queue.Full:
                    self.encoded_queue.queue.clear()
                    print("encoding queue is full")
                    
                    continue

            except queue.Empty:
                continue

        print("encode thread stopping")
        self.running = False
                    
    def _transmit_frames(self):
        transmit_count = 0

        while self.running:
            try:
                data = self.encoded_queue.get(timeout=1)

                message_size = struct.pack("Q", len(data))

                try:
                    self.client_socket.sendall(message_size+data)
                    transmit_count += 1

                    if transmit_count % 360 == 0:
                        print(f"transmitted {transmit_count} frames.")
                    
                except (BrokenPipeError, ConnectionResetError) as e:
                    print(f"Connection lost: {e}")
                    self.running = False
                    break

                except (Exception) as e:
                    print(f"Unknown error {e} occurred.")

            except queue.Empty:
                print("empty encoded wqueue")
                continue
        
        print("transmit thread stopping")
        self.running = False

    def stop(self):
        print("Stopping ...")

        self.running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2)

        if self.encode_thread:
            self.encode_thread.join(timeout=2)

        if self.transmit_thread:
            self.transmit_thread.join(timeout=2)


        if self.client_socket:
            self.client_socket.close()

        if self.server_socket:
            self.server_socket.close()

        print("Stopped!")

    def get_interfaces(self):
        command = "ls /sys/class/net"

        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        interface_list = result.stdout.split()
        interface_list.remove("lo")
        
        return interface_list


    def get_ip(self):
        self.ip = ""
        interface_list = self.get_interfaces()

        for interface in interface_list:
            if len(self.ip) > 1:
                return
            self.get_ip_address(interface)
            
            if len(self.ip) < 1:
                self.get_ip_fallback(interface)

        if len(self.ip) < 1:
            return 0
        else:
            return 1

    def get_ip_address(self,interface):
        command = f"ifconfig | grep {interface} | grep inet"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        except:
            return -1
        #ip = '192.1.23.300'
        ip_address = re.findall(r'[0-9]+(?:\.[0-9]+){3}',result.stdout)

        if len(ip_address) > 1:
            self.ip = ip_address[0]
            return 1
        else:
            return 0

    def get_ip_fallback(self, interface):
        command = f"ip addr | grep {interface} | grep inet"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        except:
            return -1

        ip_address = re.findall(r'[0-9]+(?:\.[0-9]+){3}',result.stdout)

        if len(ip_address) > 1:
            self.ip = ip_address[0]
            return 1
        else:
            return 0

if __name__ == "__main__":
    main()
