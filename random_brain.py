import numpy as np

import remote_brain
from remote_brain import Brain, main

class RandomBrain(Brain):
	def info_init(self):
		super().info_init()
		self.info_text = 'name="pbrain-pyrandom", author="Jan Stransky", version="1.0", country="Czech Republic", www="https://github.com/stranskyjan/pbrain-pyrandom"'

	def brain_init(self):
		self.board = [[0 for i in range(self.height)] for j in range(self.width)]
		self.send('OK')

	def brain_restart(self):
		self.brain_init()
	
	def is_free(self, x, y):
		return self.check_coord(x, y) and self.board[x][y] == 0

	def brain_my(self, x, y):
		if self.is_free(x, y):
			self.board[x][y] = 1
		else:
			self.send('ERROR my move [%s,%s]' % (x, y))
	
	def brain_opponents(self, x, y):
		if self.is_free(x, y):
			self.board[x][y] = 2
		else:
			self.send('ERROR opponent\'s move [%s,%s]' % (x, y))
	
	def brain_block(self, x, y):
		if self.is_free(x, y):
			self.board[x][y] = 3
		else:
			self.send('ERROR winning move [%s,%s]' % (x, y))
	
	def brain_takeback(self, x, y):
		if self.check_coord(x, y) and self.board[x][y] != 0:
			self.board[x][y] = 0
			return 0
		return 2
	
	def brain_turn(self):
		if self.terminate_ai:
			return
		i = 0
		while True:
			x = np.random.randint(0, self.width)
			y = np.random.randint(0, self.height)
			i += 1
			if self.terminate_ai:
				return
			if self.is_free(x, y):
				break
		if i > 1:
			self.send('DEBUG %s coordinates didn\'t hit an empty field' % i)
		self.do_mymove(x, y)
	
	def brain_end(self):
		pass

remote_brain.Brain = RandomBrain

if __name__ == '__main__':
	main()
