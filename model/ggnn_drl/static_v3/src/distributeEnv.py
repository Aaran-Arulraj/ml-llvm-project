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
        # self.obs = None
        # self.cur_action_space = None
        self.ggnn = None
        # self.obs = None
        # self.next_obs = None
        self.graph = None
        # self.hidden_size = 300
        # self.n_steps = 10
        # self.num_nodes = 40 # this value to estimate
        self.topology = None # Have the graph formed from adjency list using dependence edges only.
        self.cur_node = None
        
        self.distribution = ""
        self.startNode= None
        # self.discovered = []
        
        self.mode = config.mode
        self.config = config
        if self.mode != 'inference':
            if config.loop_cost:
                filename = 'loopcost_p{}.csv'.format(config.post_pass_key)
            else:
                filename = 'mcacost_p{}.csv'.format(config.post_pass_key)
            filepath = os.path.join(config.dataset, filename)
            self.loopcost_cache = utils.load_precomputed_cost(filepath)
            self.distributed_data = config.distributed_data
            self.second_loopcost_cache = set()
        
        # cols = list(self.loopcost_cache.index.names) + list(self.loopcost_cache.columns)
        # lastrow = self.loopcost_cache.iloc[-1,:]
        # self.second_loopcost_cache = pd.DataFrame(data=[list(lastrow.name)+list(lastrow)], columns=cols)
    
    def reward_formula(self, distributedLoopCost, OriginalLoopCost):
        reward = 0
        speedup = 0
        if distributedLoopCost !=0 and OriginalLoopCost != 0:
            speedup = (OriginalLoopCost - distributedLoopCost)/OriginalLoopCost
            reward = speedup
            # if reward <= 0:
            #     reward = reward - 0.5
            # else:
            #     reward = reward + 5
            # if reward < -5:
            #     logging.warning('reward={} < -5 so rplace by -5'.format(reward))
            #     reward=-5
        else:
            logging.warning('distributedLoopCost or Original LoopCost is Zero ....., reward={}'.format(reward))

        return reward, speedup

    def getReward_NoDistribution(self):
       
        home_dir = self.home_dir
        method_name = self.functionName
        loop_id = self.loopId
        ll_file_name = self.fileName
        fun_id = self.fun_id
        
        reward=0
        key = (ll_file_name, method_name, int(loop_id), 'INLINE')   
        
        isFound = False
        try:
            if self.mode == 'train':
                record = self.loopcost_cache.iloc[self.loopcost_cache.index.get_loc(key)]
                baselineLoopCost=record['baseline_cost']
                ourLoopCost = record['our_cost']
                reward, speedup = self.reward_formula(ourLoopCost, baselineLoopCost)
                logging.info('ll_filename|baselineLoopCost|ourLoopCost|reward|speedup|distributeSeq|IML {} {} {} {} {} {}'.format(ll_file_name, baselineLoopCost, ourLoopCost, reward, speedup, 'NoDistribution', self.path.split('/')[-1]))
                logging.info('******Cache Found the data point******')
                isFound=True
        except:
            logging.warning('Index not found in the cache.. key={}'.format(key))
        
        if not isFound:
            meta_ssa_r_dir = os.path.join(home_dir, 'llfiles/meta_ssa_r')
            meta_ssa_r_file_path = os.path.join(meta_ssa_r_dir, ll_file_name)

            meta_ssa_inline_r_dir = os.path.join(home_dir, 'llfiles/meta_ssa_inline_r')
            meta_ssa_inline_r_file_path = os.path.join(meta_ssa_inline_r_dir, ll_file_name)
            
            if self.config.loop_cost:
                logging.info('Get the loop_cost metric for baseline loop')
                baselineLoopCost = utils.getLoopCost(meta_ssa_r_file_path, loop_id, method_name)
                logging.info('Get the loop_cost metric for transformed loop')
                ourLoopCost = utils.getLoopCost(meta_ssa_inline_r_file_path, loop_id, method_name)
            else:
                logging.info('Get the mca_cost metric for original loop')
                baselineLoopCost = utils.getMCACost(meta_ssa_r_file_path, loop_id, method_name)
                logging.info('Get the mca_cost metric for transformed loop')
                ourLoopCost = utils.getMCACost(meta_ssa_inline_r_file_path, loop_id, method_name)

            reward, speedup = self.reward_formula(ourLoopCost, baselineLoopCost)  
            self.second_loopcost_cache.add(key + (ourLoopCost, baselineLoopCost,))
            
            logging.info('***Key added to the cache***')
            logging.info('ll_filename|baselineLoopCost|ourLoopCost|reward|speedup|distributeSeq|IML {} {} {} {} {} {}'.format(ll_file_name, baselineLoopCost, ourLoopCost, reward, speedup, 'NoDistribution', self.path.split('/')[-1]))

        return reward

    def getReward(self):
       
        home_dir = self.home_dir
        method_name = self.functionName
        loop_id = self.loopId
        ll_file_name = self.fileName
        fun_id = self.fun_id
        
        reward=0
        # key = "{filename}_{function_name}_{loopid}_{disSeq}".format(filename=ll_file_name, function_name=method_name, loopid=loop_id, disSeq=self.distribution)   
        key = (ll_file_name, method_name, int(loop_id), '|'.join([ ','.join(sorted(seqdis.split(','))) for seqdis in self.distribution.split('|')]))   
        
        isFound = False
        try:
            if self.mode == 'train':
                record = self.loopcost_cache.iloc[self.loopcost_cache.index.get_loc(key)]
                OriginalLoopCost=record['Undsitributed Cost']
                distributedLoopCost = record['Distributed cost']
                reward, speedup = self.reward_formula(distributedLoopCost, OriginalLoopCost)
                logging.info('ll_filename|OriginalLoopCost|distributedLoopCost|reward|speedup|distributeSeq|RDG {} {} {} {} {} {}'.format(ll_file_name, OriginalLoopCost, distributedLoopCost, reward, speedup, self.distribution, self.path.split('/')[-1]))
                logging.info('******Cache Found the data point******')
                isFound=True
        except:
            logging.warning('Index not found in the cache.. key={}'.format(key))
        
        if not isFound:
            meta_ssa_dir = os.path.join(home_dir, 'llfiles/meta_ssa')
            meta_ssa_file_path = os.path.join(meta_ssa_dir, ll_file_name)
            input_file_path = meta_ssa_file_path
            
            if self.mode == 'test':
                LL_DIR_CONST='llfiles'
                dist_ll_dir=os.path.join(self.distributed_data, LL_DIR_CONST)
                if not os.path.exists(dist_ll_dir):
                    os.makedirs(dist_ll_dir)
                dist_llfile = os.path.join(dist_ll_dir, ll_file_name)
                
                Is_exist=os.path.exists(dist_llfile)
                if Is_exist:
                	input_file_path = dist_llfile
            
            distributed_llfile = utils.call_distributionPass( input_file_path, self.distribution, method_name, fun_id, loop_id, self.distributed_data)
            speedup=0
            if distributed_llfile is None:
                logging.info('warning:distributed file  not generated...., reward={}'.format(reward))
            else:
                if self.config.loop_cost:
                    logging.info('Get the loop_cost metric for original loop')
                    OriginalLoopCost = utils.getLoopCost(meta_ssa_file_path, loop_id, method_name)
                    logging.info('Get the loop_cost metric for distributed loop')
                    distributedLoopCost = utils.getLoopCost(distributed_llfile, loop_id, method_name)
                else:
                    logging.info('Get the mca_cost metric for original loop')
                    OriginalLoopCost = utils.getMCACost(meta_ssa_file_path, loop_id, method_name)
                    logging.info('Get the mca_cost metric for distributed loop')
                    distributedLoopCost = utils.getMCACost(distributed_llfile, loop_id, method_name)
                reward, speedup = self.reward_formula(distributedLoopCost, OriginalLoopCost)  
                # Remove, it is occupies a lot of space
                if self.mode != 'test':
                    os.remove(distributed_llfile)
                # update the cache 
                # self.second_loopcost_cache.append(list(key) + [ distributedLoopCost, OriginalLoopCost])
                self.second_loopcost_cache.add(key + (distributedLoopCost, OriginalLoopCost,))
                
                # costly operation
                # self.loopcost_cache.loc[key,['Distributed cost', 'Undsitributed Cost']] = [ distributedLoopCost, OriginalLoopCost]
                
                logging.info('***Key added to the cache***')
                logging.info('ll_filename|OriginalLoopCost|distributedLoopCost|reward|speedup|distributeSeq|RDG {} {} {} {} {} {}'.format(ll_file_name, OriginalLoopCost, distributedLoopCost, reward, speedup, self.distribution, self.path.split('/')[-1]))

        return reward

    def init_distribution_state(self, graph, path=None):
        self.cur_node = None
        if self.mode != 'inference':
            attr = utils.getllFileAttributes(path)
            self.loopId = attr['LOOP_ID']
            self.home_dir = attr['HOME_DIR']
            self.fun_id = attr['FUN_ID']
            self.path = path
        
        self.distribution = ""
        self.graph = graph
        self.fileName = graph['graph'][1][1]['FileName'].strip('\"') 
        self.functionName = graph['graph'][1][1]['Function'].strip('\"')
        self.num_nodes = len(self.graph['nodes'])

        self.hidden_state, self.topology, self.ggnn = constructGraph(self.graph)
        possibleStartNodes = self.topology.findAllVertaxWithZeroWeights()
        
        # hs --> hidden state
        possibleStartNodes_hs = self.hidden_state[possibleStartNodes]
        
        obs= (possibleStartNodes_hs, possibleStartNodes)
        return obs, self.topology, None

    
    def inline_step(self, action):
        filename = os.path.split(self.path)
        if action == 0:
            noninline_rdg_file = os.path.join(dataset, 'graphs/RDG/json/{}'.format(filename))
            if os.path.exists(noninline_rdg_file):
                with open(noninline_rdg_file) as f:
                    graph = json.load(f)
                next_state = init_distribution_state(graph, noninline_rdg_file)
                reward = 0
                done =False
                
            else:
                reward = 0
                done = True
                next_state = self.state 
        else:
            inline_rdg_file = os.path.join(dataset, 'graphs/INLINE_RDG/json/{}'.format(filename))
            if os.path.exists(inline_rdg_file):
                with open(inline_rdg_file) as f:
                    graph = json.load(f)
                next_state = init_distribution_state(graph, inline_rdg_file)
                reward =0
                done = False
            else:
                with open(inline_rdg_file) as f:
                    graph = json.load(f)

                next_state = init_inline_state(graph)
                reward = getReward_NoDistribution()
                done = True

            return next_state, reward, done



    def step(self, action):
        if self.ggnn is None:
            raise Exception()
        
        nodeChoosen, merge_distribute = action
        
        # add the node to the visited list
        self.topology.UpdateVisitList(nodeChoosen)
       
        
        node_id =  self.ggnn.idx_nid[nodeChoosen]
        
        if merge_distribute is not None:
            self.ggnn.mpAfterDisplacement(nodeChoosen)
            
            if merge_distribute == 1:
                self.distribution = "{},{}".format(self.distribution, node_id)
                self.ggnn.addPairEdge(self.cur_node, nodeChoosen)
                logging.info('DLOOP merge {cur_node} with {nodeChoosen}'.format(cur_node=self.cur_node, nodeChoosen=nodeChoosen))
            else:
                self.distribution = "{}|{}".format(self.distribution,node_id)
                logging.info('DLOOP distribute{cur_node} with {nodeChoosen}'.format(cur_node=self.cur_node, nodeChoosen=nodeChoosen))
        else:
            self.ggnn.mpAfterDisplacement(nodeChoosen, True)
            self.distribution = node_id
           
        next_hidden_state = self.ggnn.propagate()
        reward = 0
        done = False
        # all the nodes re visted the calculate the rewards by calling distribution pass
        possibleStartNodes = self.topology.findAllVertaxWithZeroWeights()
        if len(possibleStartNodes) == 0 :
            if self.mode != 'inference':
                reward = self.getReward()
            done = True
            next_hidden_state = next_hidden_state[nodeChoosen]
        else:
            # hs --> hidden state
            next_hidden_state = next_hidden_state[possibleStartNodes]

        self.cur_node = nodeChoosen
        next_obs = (next_hidden_state, possibleStartNodes)
        return next_obs, reward, done, self.distribution, nodeChoosen 
    
    # input graph : jsonnx
    # return the state of the graph, all the possible starting nodes
    def init_inline_state(self, graph):
        nodes = graph['nodes']
        inline_state = []
        for idx, node in enumerate(nodes):
            nodeId = node['id']
            nodeVec = list(map(float, node['label'].strip("\"").split(', ')))
            inline_state.append(nodeVec)
        return inline_state

    def reset_env(self, graph, path=None):
        self.cur_node = None
        if self.mode != 'inference':
            attr = utils.getllFileAttributes(path)
            self.loopId = attr['LOOP_ID']
            self.home_dir = attr['HOME_DIR']
            self.fun_id = attr['FUN_ID']
            self.path = path
        
        self.distribution = ""
        self.graph = graph
        self.fileName = graph['graph'][1][1]['FileName'].strip('\"') 
        self.functionName = graph['graph'][1][1]['Function'].strip('\"')
        
        
        self.state = init_inline_state(self.graph)
        self.num_nodes = len(self.state)
        return self.state



