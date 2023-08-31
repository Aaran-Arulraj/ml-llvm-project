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

BUFFER_SIZE = int(2e5)  # replay buffer size
BATCH_SIZE = 64         # minibatch size
GAMMA = 0.99            # discount factor
TAU = 1e-3              # for soft update of target parameters
LR = 5e-4               # learning rate 
UPDATE_EVERY = 4        # how often to update the network

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def generate_actions(next_loops):
    mask = []
    for a in next_loops:
        mask.append(a*2)
        mask.append(a*2+1)
    return mask

def lexographic_actions(focusNode, valid_actions):
    mask=[]
    for node in valid_actions:
        if  node % 2== 1 and node > 2*focusNode:
            mask.append(node)
        elif node % 2 == 0:
            mask.append(node)
    return mask

def applymask(focusNode, next_loops, enable_lexographical_constraint):
    masked_action = generate_actions(next_loops)
    if enable_lexographical_constraint:
        masked_action = lexographic_actions(focusNode, masked_action)
    return masked_action

class Agent():
    """Interacts with and learns from the environment."""

    def __init__(self, config, seed):
        """Initialize an Agent object.
        
        Params
        ======
            state_size (int): dimension of each state
            action_size (int): dimension of each action
            seed (int): random seed
        """
        random.seed(seed)
        state_size = config.state_size
        action_size = config.action_space
        self.enable_lexographical_constraint=config.enable_lexographical_constraint
        # Q-Network
        self.qnetwork_local = QNetwork(state_size, action_size, seed).to(device)
        self.qnetwork_target = QNetwork(state_size, action_size, seed).to(device)
        self.optimizer = optim.Adam(self.qnetwork_local.parameters(), lr=LR)

        # Replay memory
        self.memory = ReplayBuffer(action_size, BUFFER_SIZE, BATCH_SIZE, seed, config)
        # Initialize time step (for updating every UPDATE_EVERY steps)
        self.t_step = 0
        self.updateDone = 0
        self.writer = SummaryWriter(os.path.join(config.distributed_data, 'log/tensorboard'))    
    
    def step(self, state, action, reward, next_state, done, action_mask=None, next_action_mask=None):
        # Save experience in replay memory
        self.memory.add(state, action, reward, next_state, done, action_mask=action_mask, next_action_mask=next_action_mask)
        
        action_mask_flag = self.memory.action_mask_flag
        # Learn every UPDATE_EVERY time steps.
        self.t_step = (self.t_step + 1) % UPDATE_EVERY
        if self.t_step == 0:
            # If enough samples are available in memory, get random subset and learn
            if len(self.memory) > BATCH_SIZE:
                experiences = self.memory.sample()
                self.learn(experiences, GAMMA, action_mask_flag=action_mask_flag)

    def act(self, state, topology, focusNode, eps=0.):
        """Returns actions for given state as per current policy.
        
        Params
        ======
            state (array_like): current state
            eps (float): epsilon, for epsilon-greedy action selection
        """
        next_loops = topology.findAllVertaxWithZeroWeights()
        
        # n transition As per the SCC * 2 decscsion  

        masked_action = applymask(focusNode, next_loops, self.enable_lexographical_constraint) 

        logging.info("valid action space for the state : {}".format(masked_action))

        # logging.info("DLOOP state type : {}, {}".format(type(state), state.shape))
        state = torch.from_numpy(state).float() # .unsqueeze(0)
        # logging.info('{} {}'.format(state.shape, type(state)))
        state = state.to(device)
        self.qnetwork_local.eval()
        with torch.no_grad():
            

            action_values = self.qnetwork_local(state)
            masked_action_space = action_values[masked_action]
            action_values = masked_action_space

            logging.info('action_values : {}'.format(action_values))
            # TODO Mask for each state via SCC
        self.qnetwork_local.train()

        # Epsilon-greedy action selection
        if random.random() > eps:
            return masked_action[np.argmax(action_values.cpu().data.numpy())], masked_action
        else:
            return random.choice(masked_action), masked_action

            # return random.choice(np.arange(self.action_size))

    def learn(self, experiences, gamma, action_mask_flag):
        """Update value parameters using given batch of experience tuples.

        Params
        ======
            experiences (Tuple[torch.Tensor]): tuple of (s, a, r, s', done) tuples 
            gamma (float): discount factor
        """

        if action_mask_flag:
            states, action_mask, actions, rewards, next_states, next_action_mask, dones = experiences
            # Get max predicted Q values (for next states) from target model
            logging.info('dqn_agent:learn():  nezt_action_mask:', next_action_mask)

            Q_targets_next = self.qnetwork_target(next_states).detach()
            
            # logging.info('!!!!!!!!!!!!!!!!!!!! Q_targets_next ', Q_targets_next.shape, Q_targets_next[0])
            # Q_targets_next = torch.from_numpy(np.vstack([Q_targets_next[mask].max(1)[0] if len(mask) > 0 else 0 for mask in next_action_mask])).float().to(device).unsqueeze(1)* (1 - dones)
            Q_targets_next = torch.stack([Q_targets_next[i][mask].max(0)[0] if len(mask) > 0 else Q_targets_next[i].max(0)[0]*0 for i, mask in enumerate(next_action_mask)], dim=0).unsqueeze(1)* (1 - dones)
        else:
            states, actions, rewards, next_states, dones = experiences
            # Get max predicted Q values (for next states) from target model
            Q_targets_next = self.qnetwork_target(next_states).detach().max(1)[0].unsqueeze(1)* (1 - dones)

        # Compute Q targets for current states 
        Q_targets = rewards + (gamma * Q_targets_next )

        # Get expected Q values from local model
        Q_expected = self.qnetwork_local(states).gather(1, actions)

        # Compute loss
        loss = F.mse_loss(Q_expected, Q_targets)
        self.updateDone+=1
        self.writer.add_scalar('train/loss', loss, self.updateDone)
        # Minimize the loss
        self.optimizer.zero_grad()
        loss.backward()
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

    def __init__(self, action_size, buffer_size, batch_size, seed, config):
        """Initialize a ReplayBuffer object.

        Params
        ======
            action_size (int): dimension of each action
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
            seed (int): random seed
        """
        self.action_size = action_size
        self.memory = deque(maxlen=buffer_size)  
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
        random.seed(seed)
        self.action_mask_flag = False
        self.enable_lexographical_constraint = config.enable_lexographical_constraint
    
    def add(self, state, action, reward, next_state, done, action_mask=None, next_action_mask=None):
        """Add a new experience to memory."""

        if action_mask is not None:
            e = self.experience((state,action_mask), action, reward, (next_state,next_action_mask), done)
            self.action_mask_flag=True
        else:
            e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)
    
    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)
        
        if self.action_mask_flag:
            states = torch.from_numpy(np.vstack([e.state[0] for e in experiences if e is not None])).float().to(device)
            action_mask = [e.state[1] for e in experiences if e is not None]

            next_states = torch.from_numpy(np.vstack([e.next_state[0] for e in experiences if e is not None])).float().to(device)
            next_action_mask = [applymask(e.next_state[1][0], e.next_state[1][1], self.enable_lexographical_constraint) for e in experiences  if e is not None] 
            
            actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).long().to(device)
            rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
            dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)
            
            return (states, action_mask, actions,  rewards, next_states, next_action_mask, dones)

        else:
            states = torch.from_numpy(np.vstack([e.state for e in experiences if e is not None])).float().to(device)
            next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(device)
            actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).long().to(device)
            rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
            dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)
            return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)
