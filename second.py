import socket

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

port = 8000
if is_port_open(port):
    print(f"Port {port} is open")
else:
    print(f"Port {port} is closed")
