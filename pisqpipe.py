import sys
import socket
import threading

ADDR = 'localhost'
SEND_PORT = 8082
RECV_PORT = 8083

# win32process.beginthreadex(None, 0, threadLoop, (), 0)
# def threadLoop():
# 	"""main function for the working thread"""
# 	while True:
# 		win32event.WaitForSingleObject(event1, win32event.INFINITE)
# 		brain_turn()
# 		win32event.SetEvent(event2)

import win32api
import win32event
import win32console
import win32process
import pywintypes

def pipeOut(what):
	"""write a line to sys.stdout"""
	ret = len(what)
	print(what)
	sys.stdout.flush()

def get_line():
	return sys.stdin.readline().strip()

def listen():
	sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_recv.bind((ADDR, RECV_PORT))
	sock_recv.listen(1)
	print('Listening to %s %s' % (ADDR, RECV_PORT))
	
	conn, addr = sock_recv.accept()
	print('Accepted connection from %s %s' % (ADDR, RECV_PORT))
	while True:
		data = conn.recv(4096)
		print(data)

def main():
	"""main function for AI console application"""
	#
	handle = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
	try:
		if handle.GetConsoleMode():
			pipeOut("MESSAGE Gomoku AI should not be started directly. Please install gomoku manager (http://sourceforge.net/projects/piskvork). Then enter path to this exe file in players settings.")
	except pywintypes.error:
		pass
	
	t_recv = threading.Thread(target=listen)
	t_recv.start()

	sock_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock_send.connect((ADDR, SEND_PORT))

	while True:
		line = get_line()
		print(line)
		sock.sendall(line)

main()