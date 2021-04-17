from ggnn import constructGraph
from topologicalSort import Graph
import random
import utils
import os
import logging
logger = logging.getLogger('distributeEnv.py') 
class DistributeLoopEnv:

    def __init__(self, config):
        self.action_space = None
        self.ggnn = None
        self.graph = None
        self.topology = None # Have the graph formed from adjency list using dependence edges only.
        self.cur_node = None
        self.mode = config.mode
        
        
        # self.loopcost_cache = utils.load_precomputed_loopcost() 
        # self.second_loopcost_cache = set()
        
    # TODO
    def reward_formula(self, value):
        reward = 0
        return reward


    def getReward_Static(self, action):
       
        home_dir = self.home_dir
        method_name = self.functionName
        # loop_id = self.loopId
        ll_file_name = self.fileName
        # fun_id = self.fun_id
        
        logging.info('')
        # ipc to llvm splill cost function for reward
        spillcost = 0
        reward = self.reward_formula(spillcost)  

        return reward

    def getReward(self, action):
        return self.getReward_Static(action)


    def step(self, action):
        if self.ggnn is None:
            raise Exception()
        
        reg_allocated, nodeChoosen = action
        self.cur_node = nodeChoosen
        
        # add the node to the visited list
        self.topology.UpdateVisitList(nodeChoosen)
       
        
        # node_id =  self.ggnn.idx_nid[nodeChoosen]
        
        # logging.info('DLOOP merge {cur_node} with {nodeChoosen}'.format(cur_node=self.cur_node, nodeChoosen=nodeChoosen))
        

        self.ggnn.updateAnnotation(action)
        
        # update the graph representations
        next_hidden_state = self.ggnn.propagate()
        reward = 0
        done = False
        
        # possible_next_nodes = self.topology.findAllVertaxWithZeroWeights()
        
        reward = self.getReward(action)
  
        if self.topology.length() ==  nodeChoosen +1:
            done = True
            return (next_hidden_state[nodeChoosen], nodeChoosen), reward, done

        # next_hidden_state = next_hidden_state[possible_next_nodes]

        next_node = nodeChoosen+1 
        next_obs = next_hidden_state[next_node]
        adj_colors = topology.getColorOfVisitedAdjNodes(next_node)
        return (next_obs, next_node, adj_colors), reward, done 
    
    # input graph : jsonnx
    # return the state of the graph, all the possible starting nodes
    def reset_env(self, graph, path):
        attr = utils.getllFileAttributes(path)
        self.path = path
        self.graph = graph
        self.fileName = graph['graph'][1][1]['FileName'].strip('\"') 
        self.functionName = graph['graph'][1][1]['Function'].strip('\"')
        # self.loopId = attr['LOOP_ID']
        self.home_dir = attr['HOME_DIR']
        # self.fun_id = attr['FUN_ID']
        self.num_nodes = len(self.graph['nodes'])
        
        self.cur_node = None
        

        hidden_state, self.topology, self.ggnn = constructGraph(self.graph)
        
        # Consider Node with index with node with index 0
        obs= hidden_state[0]
        adj_colors = topology.getColorOfVisitedAdjNodes(0)
        return ( obs, 0, adj_colors)



