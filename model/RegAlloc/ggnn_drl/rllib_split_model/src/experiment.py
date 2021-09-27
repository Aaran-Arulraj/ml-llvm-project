"""Example of a custom experiment wrapped around an RLlib trainer."""
import argparse
from tqdm import tqdm
import os
import json
import glob
import time
import numpy as np
from typing import Dict as type_dict
import psutil
import gc

import ray
from ray import tune
from ray.tune import function
from ray.rllib.agents import ppo
from ray.rllib.agents.dqn.simple_q_torch_policy import SimpleQTorchPolicy

from ray.rllib.agents.callbacks import DefaultCallbacks
from ray.rllib.env import BaseEnv
from ray.rllib.evaluation import MultiAgentEpisode, RolloutWorker
from ray.rllib.policy import Policy
from ray.rllib.policy.sample_batch import SampleBatch

from gym.spaces import Discrete, Box, Dict
from simple_q import SimpleQTrainer, DEFAULT_CONFIG
# from env import GraphColorEnv, set_config
from multiagentEnv import HierarchicalGraphColorEnv
from register_action_space import RegisterActionSpace
from ray.rllib.models import ModelCatalog
from model import SelectTaskNetwork, SelectNodeNetwork, ColorNetwork, SplitNodeNetwork
import logging

parser = argparse.ArgumentParser()
parser.add_argument("--train-iterations", type=int, default=10)

checkpoint = None
def experiment(config):
    iterations = config.pop("train-iterations")
    global checkpoint
    train_results = {}
    # config["env_config"]["path"] = path
    train_agent = SimpleQTrainer(config=config, env=HierarchicalGraphColorEnv)
    print('------------------------ aegent --------------------------------- ', train_agent)
    # Train
    
    # train_agent = SimpleQTrainer(config=config, env=GraphColorEnv)
    if checkpoint is not None:
        train_agent.restore(checkpoint)            

    for i in range(iterations):
        train_results = train_agent.train()
        # auto_garbage_collect()
        if i == iterations - 1 or train_results['episodes_total']%100 == 0:
            checkpoint = train_agent.save(tune.get_trial_dir())
            # print("***************Checkpoint****************", checkpoint)
        tune.report(**train_results)
        if train_results['episodes_total'] > 9:
            print("Traning Ended")
            checkpoint = train_agent.save(tune.get_trial_dir())
            break
    train_agent.stop()

    # Manual Eval
    # config["num_workers"] = 0
    # eval_agent = SimpleQTrainer(config=config, env=HierarchicalGraphColorEnv)
    # eval_agent.restore(checkpoint)
    # env = eval_agent.workers.local_worker().env

    # obs = env.reset()
    # done = False
    # eval_results = {"eval_reward": 0, "eval_eps_length": 0}
    # while not done:
    #     action = eval_agent.compute_action(obs, policy_id="select_node_policy")
    #     next_obs, reward, done, info = env.step(action)
    #     eval_results["eval_reward"] += reward
    #     eval_results["eval_eps_length"] += 1
    # results = {**train_results, **eval_results}
    # tune.report(results)

def auto_garbage_collect(pct=50.0):
    """
    auto_garbage_collection - Call the garbage collection if memory used is greater than 80% of total available memory.
                              This is called to deal with an issue in Ray not freeing up used memory.

        pct - Default value of 80%.  Amount of memory in use that triggers the garbage collection call.
    """
    if psutil.virtual_memory().percent >= pct:
        gc.collect()
    return

class MyCallbacks(DefaultCallbacks):
    def  on_episode_start(self, *, worker: RolloutWorker, base_env: BaseEnv,
                       policies: type_dict[str, Policy], episode: MultiAgentEpisode,
                       env_index: int, **kwargs):
        # print("Env object", base_env.get_unwrapped())
        if base_env.get_unwrapped()[0].server_pid is not None:
            episode.hist_data["server_pid"] = [base_env.get_unwrapped()[0].server_pid.pid]
        else:
            episode.hist_data["server_pid"] = [0]
    
    def on_sample_end(self, *, worker: "RolloutWorker", samples: SampleBatch,
                    **kwargs):
        print("Sample Batch size is {} bytes".format(samples.size_bytes()))



if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger(__file__)
    log_level=logging.DEBUG
    # if args.log_level == 'WARN':
    #     log_level=logging.WARNING
    # elif args.log_level == 'INFO':
    #     log_level=logging.INFO
    if os.path.exists('running.log'):
        os.remove('running.log')

    logging.basicConfig(filename='running.log', format='%(thread)d - %(threadName)s - %(levelname)s - %(filename)s - %(message)s', level=log_level)
    logging.info('Starting training')
    logging.info(args)



    ray.init(object_store_memory=10000000000)
    config = DEFAULT_CONFIG.copy()
    config["train-iterations"] = args.train_iterations

    config["env"] = HierarchicalGraphColorEnv    
    config["callbacks"] = MyCallbacks

    ModelCatalog.register_custom_model("select_node_model", SelectNodeNetwork)
    ModelCatalog.register_custom_model("select_task_model", SelectTaskNetwork)
    ModelCatalog.register_custom_model("colour_node_model", ColorNetwork)
    ModelCatalog.register_custom_model("split_node_model", SplitNodeNetwork)

    box_obs = Box(
            -100000.0, 100000.0, shape=(config["env_config"]["state_size"], ), dtype=np.float32)
    box_obs_select_node = Box(
            -100000.0, 100000.0, shape=(config["env_config"]["max_number_nodes"], config["env_config"]["state_size"]), dtype=np.float32)

    obs_colour_node = Dict({
        "action_mask": Box(0, 1, shape=(config["env_config"]["action_space_size"],)),
        "node_properties": Box(-100000.0, 100000.0, shape=(3,)), 
        "state": box_obs
        })
    obs_select_node = Dict({
        "spill_weights": Box(-100000.0, 100000.0, shape=(config["env_config"]["max_number_nodes"],)), 
        "action_mask": Box(0, 1, shape=(config["env_config"]["max_number_nodes"],)),
        "state": box_obs_select_node
        }) 
    obs_select_task = Dict({
        "node_properties": Box(-100000.0, 100000.0, shape=(4,)), 
        "state": box_obs
        })
    
    obs_node_spliting = Dict({
        "usepoint_properties": Box(-100000.0, 100000.0, shape=(config["env_config"]["max_usepoint_count"], 2)), 
        "action_mask": Box(0, 1, shape=(config["env_config"]["max_usepoint_count"],)),
        "state": box_obs
        }) 
    
    def policy_mapping_fn(agent_id, episode=None, **kwargs):
        if agent_id.startswith("select_node_agent"):
            return "select_node_policy"
        elif agent_id.startswith("select_task_agent"):
            return "select_task_policy"
        elif agent_id.startswith("colour_node_agent"):
            return "colour_node_policy"
        else:
            return "split_node_policy"


    policies = {
        "select_node_policy": (None, obs_select_node,
                                Discrete(config["env_config"]["max_number_nodes"]), {
                                    "gamma": 0.9,
                                    "model": {
                                        "custom_model": "select_node_model",
                                        "custom_model_config": {
                                            "state_size": config["env_config"]["state_size"],
                                            "fc1_units": 64,
                                            "fc2_units": 64
                                        },
                                    },
                                }),
        "select_task_policy": (None, obs_select_task,
                                Discrete(2), {
                                    "gamma": 0.9,
                                    "model": {
                                        "custom_model": "select_task_model",
                                        "custom_model_config": {
                                            "state_size": config["env_config"]["state_size"],
                                            "fc1_units": 64,
                                            "fc2_units": 64
                                        },
                                    },
                                }),
        "colour_node_policy": (None, obs_colour_node,
                                Discrete(config["env_config"]["action_space_size"]), {
                                    "gamma": 0.9,
                                    "model": {
                                        "custom_model": "colour_node_model",
                                        "custom_model_config": {
                                            "state_size": config["env_config"]["state_size"],
                                            "fc1_units": 64,
                                            "fc2_units": 64
                                        },
                                    },
                                }),
        "split_node_policy": (None, obs_node_spliting,
                                Discrete(config["env_config"]["max_usepoint_count"]), {
                                    "gamma": 0.9,
                                    "model": {
                                        "custom_model": "split_node_model",
                                        "custom_model_config": {
                                            "state_size": config["env_config"]["state_size"],
                                            "fc1_units": 64,
                                            "fc2_units": 64
                                        },
                                    },
                                }),
    }

    config["multiagent"] = {
        "policies" : policies,
        "policy_mapping_fn": function(policy_mapping_fn)
    }

    # file_count = 0
    start_time = time.time()
    # for path in tqdm (training_graphs, desc="Running..."): # Number of the iterations        
        # set_config(path)
        # config["env_config"]["path"] = path
    tune.run(
        experiment,
        config=config,
        resources_per_trial=SimpleQTrainer.default_resource_request(config))
        # resources_per_trial={"cpu": 16, "gpu": 2})
        # file_count += 1
    print("Total time in seconds is: ", (time.time() - start_time))
