import sys
import socket
import threading

import win32console
import pywintypes

ADDR = 'localhost'
SEND_PORT = 8082
RECV_PORT = 8083

def pipe_out(msg):
	print(msg)
	sys.stdout.flush()

def get_line():
	return sys.stdin.readline().strip()

def listen():
	sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_recv.bind((ADDR, RECV_PORT))
	sock_recv.listen(1)
	# print('Listening to %s %s' % (ADDR, RECV_PORT))
	
	conn, addr = sock_recv.accept()
	# print('Accepted connection from %s %s' % (ADDR, RECV_PORT))
	while True:
		data = conn.recv(4096)
		if not data:
			break
		pipe_out(data.decode())

def main():
	handle = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
	try:
		if handle.GetConsoleMode():
			pipe_out("MESSAGE Gomoku AI should not be started directly. Please install gomoku manager (http://sourceforge.net/projects/piskvork). Then enter path to this exe file in players settings.")
	except pywintypes.error:
		pass

	t_recv = threading.Thread(target=listen)
	t_recv.start()

	sock_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_send.connect((ADDR, SEND_PORT))
	# print('Sending to %s %s' % (ADDR, SEND_PORT))

	while True:
		line = get_line()
		sock_send.sendall(line.encode('utf-8'))

if __name__ == '__main__':
	main()