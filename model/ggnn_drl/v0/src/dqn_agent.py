import numpy as np
import random
from collections import namedtuple, deque
from model import QNetwork
import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
import os
import logging
# from torch.nn.parallel import DistributedDataParallel as DDP

logger = logging.getLogger('dqn_agent.py') 

BUFFER_SIZE = int(20000)  # replay buffer size
BATCH_SIZE = 64         # minibatch size
GAMMA = 0.99            # discount factor
TAU = 1e-3              # for soft update of target parameters
LR = 1e-3               # learning rate 
UPDATE_EVERY = 4        # how often to update the network

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# def generate_actions(next_loops):
#     mask = []
#     for a in next_loops:
#         mask.append(a*2)
#         mask.append(a*2+1)
#     return mask
# 
# def lexographic_actions(focusNode, valid_actions):
#     mask=[]
#     for node in valid_actions:
#         if  node % 2== 1 and node > 2*focusNode:
#             mask.append(node)
#         elif node % 2 == 0:
#             mask.append(node)
#     return mask
# 
# def applymask(focusNode, next_loops, enable_lexographical_constraint):
#     masked_action = generate_actions(next_loops)
#     if enable_lexographical_constraint:
#         masked_action = lexographic_actions(focusNode, masked_action)
#     return masked_action

class Agent():
    """Interacts with and learns from the environment."""

    def __init__(self, config, seed):
        """Initialize an Agent object.
        
        Params
        ======
            state_size (int): dimension of each state
            seed (int): random seed
        """
        # random.seed(seed)
        state_size = config.state_size
        # Q-Network
        self.qnetwork_local = QNetwork(state_size,  seed=seed).to(device)
        self.qnetwork_target = QNetwork(state_size, seed=seed).to(device)
        
        self.optimizer = optim.Adam(self.qnetwork_local.parameters(), lr=LR)

        # Replay memory
        self.memory = ReplayBuffer(BUFFER_SIZE, BATCH_SIZE, seed, config)
        # Initialize time step (for updating every UPDATE_EVERY steps)
        self.t_step = 0
        self.updateDone = 0
        self.writer = SummaryWriter(os.path.join(config.distributed_data, 'log/tensorboard'))    

    def step(self, state, action, reward, next_state, done):
        # Save experience in replay memory
        self.memory.add(state, action, reward, next_state, done)
        
        # Learn every UPDATE_EVERY time steps.
        self.t_step = (self.t_step + 1) % UPDATE_EVERY
        if self.t_step == 0:
            # If enough samples are available in memory, get random subset and learn
            if len(self.memory) > BATCH_SIZE:
                experiences = self.memory.sample()
                self.learn(experiences, GAMMA)

    def act(self, state, topology,eps=0.):
        """Returns actions for given state as per current policy.
        
        Params
        ======
            state (array_like): current state
            eps (float): epsilon, for epsilon-greedy action selection
        """
        state, nodeChoosen,adj_colors = state

        logging.info("DLOOP state type : {}, {}".format(type(state), state.shape))
        state = torch.from_numpy(state).float() # .unsqueeze(0)
        logging.info("shape={} and type={}".format(state.shape, type(state)))
        
        # Epsilon-greedy action selection
        if random.random() > eps:
            logging.info('EXP: Model decision')
            state = state.to(device)
            self.qnetwork_local.eval()
            with torch.no_grad():
                # assign a color to the node
                out = self.qnetwork_local(state)
                if len(adj_colors) > 0:
                    out = out[adj_colors]
                _, actions = self.getMaxQvalueAndActions(out)
                # action_values = masked_action_space
            self.qnetwork_local.train()

        else:
            logging.info('EXP: Random ')
            action_space = np.arange(25)
            if len(adj_colors) > 0:
                action_space = action_space[adj_colors]
            
            actions = random.choice(action_space)
            
        return actions

    def getMaxQvalueAndActions(self, out):
        color_out = out
        
        action, action_Qvalue = torch.argmax(action_out, dim=1), torch.max(action_out, dim=1)

        QMax = action_Qvalue

        return QMax, action
 
    def getMaxQvalue(self, next_state):
        next_state = torch.from_numpy(next_state).float().to(device)
        out = self.qnetwork_target(next_state)
        # TODO:: Add a check for masking
        QMax, _ = self.getMaxQvalueAndActions(out)
        return QMax
 
 
    def getQvalueForAction(self, state, action):
        try:
            
            # logging.info(state.shape, type(state))

            state = torch.from_numpy(state).float().to(device)
            
            out = self.qnetwork_local(state)
            Qvalue = out[action]

            return Qvalue
        except:
            logging.error('Error int getQvalueForAction')
            for s in state:
                logging.error("{} {}".format(type(s), s))
            raise

    def learn(self, experiences, gamma):
        """Update value parameters using given batch of experience tuples.

        Params
        ======
            experiences (Tuple[torch.Tensor]): tuple of (s, a, r, s', done) tuples 
            gamma (float): discount factor
        """
        states, actions, rewards, next_states, dones = experiences

        # Get max predicted Q values (for next states) from target model
        # Q_targets_next = self.qnetwork_target(next_states, start).detach().max(1)[0].unsqueeze(1)
        # Q_targets_next = self.qnetwork_target(next_states, start)[0].detach().unsqueeze(1)
        

        Q_targets_next = torch.stack([self.getMaxQvalue(next_state) for next_state in next_states]).detach().unsqueeze(1)
        # logging.info('V2: Q_targets_shape : ', Q_targets_next.shape)
        # Compute Q targets for current states 
        Q_targets = rewards + (gamma * Q_targets_next * (1 - dones))

        # Get expected Q values from local model
        # Q_expected = self.qnetwork_local(states, start).gather(1, actions)

        Q_expected = torch.stack([ self.getQvalueForAction(state,  action) for state, action in zip(states, actions)]).squeeze(2)
 
        # Trans_Qvalue,_ = self.qnetwork_local.transitionNet(states)
        # Qvalue1 = Trans_Qvalue.gather(1, actions1)
        
        # Distribute_Qvalue,_ = self.distributeNet(states[actions1])
        # This might cause issue in None
        # Qvalue2 = Distribute_Qvalue.gather(1, actions2)

        # Q_expected = torch.sum(torch.cat((Qvalue1, Qvalue2),dim=1),dim=1)



        # Compute loss
        # logging.info('Q_expected', Q_expected.shape)
        # logging.info('Q_targets', Q_targets.shape)
        loss = F.mse_loss(Q_expected, Q_targets)
        self.updateDone = self.updateDone +1
        self.writer.add_scalar("Loss/train", loss, self.updateDone)
        # Minimize the loss
        self.optimizer.zero_grad()
        loss.backward()
        # TODO TODO
        for param in self.qnetwork_local.parameters():
           param.grad.data.clamp_(-1, 1)

        self.optimizer.step()

        # ------------------- update target network ------------------- #
        self.soft_update(self.qnetwork_local, self.qnetwork_target, TAU)                     

    def soft_update(self, local_model, target_model, tau):
        """Soft update model parameters.
        θ_target = τ*θ_local + (1 - τ)*θ_target

        Params
        ======
            local_model (PyTorch model): weights will be copied from
            target_model (PyTorch model): weights will be copied to
            tau (float): interpolation parameter 
        """
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau*local_param.data + (1.0-tau)*target_param.data)


class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, buffer_size, batch_size, seed, config):
        """Initialize a ReplayBuffer object.

        Params
        ======
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
            seed (int): random seed
        """
        self.memory = deque(maxlen=buffer_size)  
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
        # random.seed(seed)
        self.action_mask_flag = False
    
    def add(self, state, action, reward, next_state, done):
        """Add a new experience to memory."""
        e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)
    
    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)
        
        # State has two sub tiem vectord for possible candiadate node and current node number
        #  Fix the fix for the dimension miss match....

        # states = torch.from_numpy(np.vstack([e.state[0] for e in experiences if e is not None])).float().to(device)
        states = [e.state[0] for e in experiences if e is not None]
        
        # focusNodes = torch.from_numpy(np.vstack([e.state[1] if e.state[0] is not None else -1 for e in experiences if e is not None])).float().to(device)
        # logging.info([e.state[1] for e in experiences if e is not None]) 
        # action1 has the node index selected
        # action2 corresponds to merge or distribute decision.
        # logging.info([e.action[0] for e in experiences if e is not None]) 
        # logging.info([e.action[1] for e in experiences if e is not None]) 
        actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).long().to(device)

        rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)

        #  Fix the fix for the dimension miss match....
        # next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(device)
        next_states = [e.next_state for e in experiences if e is not None]
        
        dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)
  
        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)
