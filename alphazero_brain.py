from u import *
from expres.src.config import Config

import remote_brain
from remote_brain import Brain, main

az_dir = Path('../alphazero')
sys.path.append(az_dir)

from model import Model
import mcts
from mcts import MCTSNode
import util
from util import *
mcts.config = util.config = config = Config(az_dir / 'results_small').load()
config.device = 'cuda'
config.mcts_eps = 0

model = Model(config).set_state(config.load_max_model_state(min_epoch=-1))
def evaluator(state):
	with torch.no_grad():
		v, p = model.fit_batch((np.array([state]),), train=False)
		return v, p[0]

class AlphaZero(Brain):
	def info_init(self):
		super().info_init()
		self.info_text = 'name="pbrain-alphazero", author="Zhongxia Yan", version="0.0", country="USA", www="https://github.com/ZhongxiaYan/gomoku_ai"'

	def set_mcts(self, state):
		self.head = MCTSNode(state, evaluator=evaluator)

	def brain_init(self):
		self.set_mcts(np.zeros((2, config.board_dim, config.board_dim), dtype=np.float32))
		self.send('OK')

	def brain_restart(self):
		self.brain_init()
	
	def step_mcts(self, x, y):
		print('Moved %s,%s' % (x, y))
		move = (y, x)
		index = move_to_index(move)
		head = self.head
		if index in head.next:
			self.head = head.next[index]
		else:
			new_state = step_state(head.state, move)
			self.set_mcts(new_state)

	brain_my = brain_opponents = step_mcts

	def brain_takeback(self, x, y):
		state = self.head.state
		state[:, y, x] = 0
		self.set_mcts(state)
		return 0
	
	def brain_turn(self):
		if self.terminate_ai:
			return
		head = self.head
		for _ in tqdm(range(config.eval_mcts_iterations)):
			head.select()
		index = head.N.argmax()
		(y, x) = index_to_move(index)
		self.do_mymove(x, y)
	
	def brain_end(self):
		sys.exit(0)

remote_brain.Brain = AlphaZero

if __name__ == '__main__':
	main()
