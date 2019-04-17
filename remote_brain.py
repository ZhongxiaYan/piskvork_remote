import socket
import sys
import threading
import time
import click

class Brain:
	def __init__(self, stdin, addr, recv, send):
		if stdin:
			self.recv = lambda: sys.stdin.readline().strip()
			self.send = lambda msg: print(msg, flush=True)
		else:
			sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock_recv.bind((addr, recv))
			sock_recv.listen(1)
			print('Listening to %s %s' % (addr, recv))
			
			sock_recv, _ = sock_recv.accept()
			file_recv = sock_recv.makefile()
			print('Accepted connection from %s %s' % (addr, recv))
			
			def recv_fn():
				msg = file_recv.readline().strip()
				print('RECV: %s' % msg, flush=True)
				return msg
			self.recv = recv_fn

			sock_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock_send.connect((addr, send))
			print('Sending to %s %s' % (addr, send))
			
			def send_fn(msg):
				print('SEND: %s' % msg, flush=True)
				sock_send.sendall(msg.encode('utf-8'))
			self.send = send_fn

		# conditional variables
		self.let_turn_start = threading.Event()
		self.let_turn_end = threading.Event()
		self.let_turn_end.set()

		t_worker = threading.Thread(target=self.worker_loop, daemon=True)
		t_worker.start()

		self.info_init()

		self.loop()
	
	def brain_init(self):
		"""create the board and call self.send("OK") or self.send("ERROR Maximal board size is ..")"""
		raise NotImplementedError

	def brain_restart(self):
		"""delete old board, create new board, call self.send("OK")"""
		raise NotImplementedError

	def brain_turn(self):
		"""choose your move and call do_mymove(x,y), 0 <= x < self.width, 0 <= y < self.height"""
		raise NotImplementedError

	def brain_my(self, x, y):
		"""put your move to the board"""
		raise NotImplementedError

	def brain_opponents(self, x, y):
		"""put opponent's move to the board"""
		raise NotImplementedError

	def brain_block(self, x, y):
		"""square [x,y] belongs to a winning line (when info_continuous is 1)"""
		raise NotImplementedError

	def brain_takeback(self, x, y):
		"""clear one square, return value: 0: success, 1: not supported, 2: error"""
		raise NotImplementedError

	def brain_end(self):
		"""delete temporary files, free resources"""
		raise NotImplementedError



	### methods that don't need to be overriden

	def info_init(self):
		"""the board size"""
		self.width, self.height = None, None
		"""time for one turn in milliseconds"""
		self.info_timeout_turn = 30000
		"""total time for a game"""
		self.info_timeout_match = 1000000000
		"""left time for a game"""
		self.info_time_left = 1000000000
		"""maximum memory in bytes, zero if unlimited"""
		self.info_max_memory = 0
		"""0: human opponent, 1: AI opponent, 2: tournament, 3: network tournament"""
		self.info_game_type = 1
		"""0: five or more stones win, 1: exactly five stones win"""
		self.info_exact5 = 0
		"""0: gomoku, 1: renju"""
		self.info_renju = 0
		"""0: single game, 1: continuous"""
		self.info_continuous = 0
		"""return from brain_turn when terminate_ai > 0"""
		self.terminate_ai = None
		"""time at the beginning of turn"""
		self.start_time = None
		"""folder for persistent files"""
		self.data_folder = ""

		self.info_text = 'Remote AI'
	
	def do_mymove(self, x, y):
		self.brain_my(x, y)
		self.send("{},{}".format(x,y))

	def check_coord(self, x, y):
		return 0 <= x < self.width and 0 <= y < self.height

	def loop(self):
		while True:
			line = self.recv()
			if not line:
				break
			self.do_command(line)

	def worker_loop(self):
		"""main function for the working thread"""
		while True:
			self.let_turn_start.wait()
			self.let_turn_start.clear()
			self.brain_turn()
			self.let_turn_end.set()

	def turn(self):
		"""start thinking"""
		self.terminate_ai = 0
		self.let_turn_end.clear()
		self.let_turn_start.set() # lets worker thread run brain_turn

	def stop(self):
		"""stop thinking"""
		self.terminate_ai = 1
		self.let_turn_end.wait()

	def start(self):
		self.start_time = time.time()
		self.stop()

	def do_command(self, line):
		cmd, *rest = line.lower().split(' ')

		if cmd == 'info':
			if len(rest) != 2:
				return
			# info <subcmd> value
			# subcmd can be max_memory, timeout_match, timeout_turn, time_left, game_type, rule, folder
			subcmd, value = rest
			if subcmd not in ['max_memory', 'timeout_match', 'timeout_turn', 'time_left', 'game_type', 'rule', 'folder']:
				return
			if subcmd != 'folder':
				value = int(value)
			if subcmd == 'rule':
				self.info_exact5 = value & 1
				self.info_continuous = (value >> 1) & 1
				self.info_renju = (value >> 2) & 1
			else:
				setattr(self, 'info_' + subcmd, value)

		elif cmd == 'start':
			try:
				dim = int(rest[0])
				if dim < 5:
					raise ValueError('Board width and height must be >= 5')
				self.height = self.width = dim
				self.start()
				self.brain_init()
			except (IndexError, ValueError) as e:
				print(e)
				self.send('ERROR bad START parameter')

		elif cmd == 'restart':
			self.start()
			self.brain_restart()
		
		elif cmd == 'turn':
			self.start()
			try:
				x, y = map(int, rest[0].split(','))
				if not self.check_coord(x, y):
					raise ValueError('Out of bounds')
				self.brain_opponents(x, y)
				self.turn()
			except (IndexError, ValueError) as e:
				print(e)
				self.send("ERROR bad coordinates")
		
		elif cmd == 'play':
			self.start()
			try:
				x, y = map(int, rest[0].split(','))
				if not self.check_coord(x, y):
					raise ValueError('Out of bounds')
				self.do_mymove(x, y)
			except (IndexError, ValueError) as e:
				print(e)
				self.send("ERROR bad coordinates")
		
		elif cmd == 'begin':
			self.start()
			self.turn()
		
		elif cmd == 'about':
			self.send(self.info_text)

		elif cmd == 'end':
			self.stop()
			self.brain_end()
		
		elif cmd == 'board':
			self.start()
			try:
				subcmd = self.recv().lower()
				while subcmd != 'done':
					x, y, who = map(int, subcmd.split(','))
					if not self.check_coord(x, y):
						raise ValueError('Out of bounds')
					if who == 1:
						self.brain_my(x, y)
					elif who == 2:
						self.brain_opponents(x, y)
					elif who == 3:
						self.brain_block(x, y)
					else:
						raise ValueError('Who must be 1, 2, or 3')
					subcmd = self.recv().lower()
			except (IndexError, ValueError) as e:
				print(e)
				self.send("ERROR x,y,who or DONE expected after BOARD")
			self.turn()
		
		elif cmd == 'takeback':
			self.start()
			try:
				x, y = map(int, rest[0].split(','))
				e = self.brain_takeback(x, y)
				self.send('OK' if e == 0 else 'UNKNOWN')
			except (IndexError, ValueError) as e:
				print(e)
				self.send('ERROR bad coordinates')
		
		else:
			self.send('UNKNOWN command %s' % cmd)

@click.command()
@click.option('--stdin/--no-stdin', default=False)
@click.option('--addr', default='localhost')
@click.option('--recv', default=8082, help='Receive port for socket')
@click.option('--send', default=8083, help='Send port for socket')
def main(stdin, addr, recv, send):
	Brain(stdin, addr, recv, send)
