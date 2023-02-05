import sys
sys.path.append('/home/cs20btech11024/repos/ML-Register-Allocation/ml-llvm-tools/llvm-grpc/Python-Utilities')
import RegisterAllocationInference_pb2_grpc, RegisterAllocationInference_pb2

from concurrent import futures
import grpc
import sys
import traceback
import json
import ray
import os
# sys.path.append(os.path.realpath('../../model/RegAlloc/ggnn_drl/rllib_split_model/src'))
sys.path.append('/home/cs20btech11024/repos/ML-Register-Allocation/model/RegAlloc/ggnn_drl/rllib_split_model/src')
# import inference
import rollout as inference
# import register_action_space
# import env
from argparse import Namespace
# logging = 
class service_server(RegisterAllocationInference_pb2_grpc.RegisterAllocationInferenceServicer):

    def __init__(self):
        # model_path = '/home/cs18mtech11030/ray_results/experiment_2021-07-24_17-11-31/experiment_HierarchicalGraphColorEnv_16ff3_00000_0_2021-07-24_17-11-31/checkpoint_000001/checkpoint-1'
        # model_path = '/home/cs18mtech11030/ray_results/model/experiment_2021-08-06_09-58-35/experiment_HierarchicalGraphColorEnv_c3fda_00000_0_2021-08-06_09-58-36/checkpoint_000005/checkpoint-5'
        # model_path = '/home/cs18mtech11030/ray_results/model/experiment_2021-08-06_23-02-18/experiment_HierarchicalGraphColorEnv_3f58c_00000_0_2021-08-06_23-02-18/checkpoint_000010/checkpoint-10'
        # model_path = '/home/cs18mtech11030/ray_results/model/experiment_2021-08-09_16-11-00/experiment_HierarchicalGraphColorEnv_49c97_00000_0_2021-08-09_16-11-01/checkpoint_000100/checkpoint-100'
        # model_path = '/home/venkat/ray_results/split_model/experiment_2021-09-05_01-20-13/experiment_HierarchicalGraphColorEnv_521df_00000_0_2021-09-05_01-20-14/checkpoint_000040/checkpoint-40'
        # self.inference_model = inference.Inference(model_path)
        # model_path = '/home/venkat/ray_results/split_model/experiment_2021-09-09_22-09-20/experiment_HierarchicalGraphColorEnv_7b793_00000_0_2021-09-09_22-09-21/checkpoint_001969/checkpoint-1969'
        # model_path = '/home/venkat/ray_results/split_model/experiment_2021-10-21_12-22-45/experiment_HierarchicalGraphColorEnv_7f0ef_00000_0_2021-10-21_12-22-45/checkpoint_001575/checkpoint-1575'
        # model_path = '/home/venkat/ray_results/split_model/X86models/checkpoint_001156/checkpoint-1156'
        #model_path = '/home/venkat/ray_results/split_model/X86models/checkpoint_001274/checkpoint-1274'
        #model_path = '/home/venkat/ray_results/experiment_2022-03-12_13-28-43/experiment_HierarchicalGraphColorEnv_3c7aa_00000_0_2022-03-12_13-28-43/checkpoint_004010/checkpoint-4010'
        # model_path = '/home/venkat/ray_results/X86_C5_200kEps_16_06_22/checkpoint-10219' # used for debuginh runtime and compile time issues
        # model_path = '/home/venkat/ray_results/X86_C1_200kEps_17-07-22/checkpoint-19700'
        model_path = '/home/cs20btech11024/ray_results/table5/checkpoint-10716'
        #model_path = '/home/venkat/ray_results/split_model/home/cs17m20p100001/ray_results/experiment_2022-01-04_21-47-31/experiment_HierarchicalGraphColorEnv_d1a8f_00000_0_2022-01-04_21-47-32/checkpoint_001500/checkpoint-1500'
        args = {'no_render' : True, 'checkpoint' : model_path, 'run' : 'PPO' , 'env' : '' , 'config' : {}, 'video_dir' : '', 'steps' : 0, 'episodes' : 0, 'arch' : 'X86'}
        args = Namespace(**args)
        self.inference_model = inference.RollOutInference(args)

#     def getColouring(self, request, context):
#         
#         try:
#             inter_graphs = request.payload.decode("utf-8")
#             
#             model_path = '/home/cs18mtech11030/ray_results/experiment_2021-07-24_17-11-31/experiment_HierarchicalGraphColorEnv_16ff3_00000_0_2021-07-24_17-11-31/checkpoint_000001/checkpoint-1'
#             # model_path = os.path.abspath(model_path)    
#             print(inter_graphs)
#             inter_graph_list = []
#             if type(inter_graphs) is not list:
#                 inter_graph_list.append(inter_graphs)
#             # print(inter_graph_list)
#             color_data_list = inference.allocate_registers(inter_graph_list, model_path)
#             color_data = color_data_list[0]
#             # print("Color Data", color_data)
#             # color_data_bt = bytes(color_data, 'utf-8')
#             color_data_bt = json.dumps(color_data).encode('utf-8')
#             reply=RegisterAllocationInference_pb2.ColorData(payload=color_data_bt)
#             print('replying.....', reply) 
#             return reply
#         except:
#             print('Error')
#             traceback.print_exc()
#             raise
    #TODO
    '''
    def setGraph(self, request, context):
        try:
            inter_graphs = request.payload.decode("utf-8")
            
            # model_path = os.path.abspath(model_path)    
            # print(inter_graphs)
            inter_graph_list = []
            if type(inter_graphs) is not list:
                inter_graph_list.append(inter_graphs)
            # print(inter_graph_list)
            self.inference_model.setGraphInEnv(inter_graph_list)
            action = self.inference_model.compute_action()
            # color_data = color_data_list[0]
            # print("Color Data", color_data)
            # color_data_bt = bytes(color_data, 'utf-8')
            # color_data_bt = json.dumps(color_data).encode('utf-8')

            
            reply=RegisterAllocationInference_pb2.Data(message="Split", regidx=regidx, payload=Split_id)
            reply=RegisterAllocationInference_pb2.Data(message="Color", colorData=color_data_bt)
            reply=RegisterAllocationInference_pb2.Data(message="Exit")

            print('replying.....', reply) 
            return reply
        except:
            print('Error')
            traceback.print_exc()
            raise
    '''
    #TODO
    def getInfo(self, request, context):
        try:
            print('------Hi--------- isnew {} '.format(request.new))
            # print(request)
            # print('******************************************')
            # graph = request.graph
            # print(graph)
            inter_graphs = request# graph.decode("utf-8")           
            # print(inter_graphs)
            # if inter_graphs is not None and  inter_graphs !="":
            
            # if not inter_graphs.result:
            #     print('Nothing to update')
            #     return RegisterAllocationInference_pb2.Data(message="Exit")
            
            assert len(inter_graphs.regProf) > 0, "Graphs has no nodes"

            if inter_graphs.new:
                             # model_path = os.path.abspath(model_path)
                # print(inter_graphs)
                inter_graph_list = []
                if type(inter_graphs) is not list:
                    inter_graph_list.append(inter_graphs)
                # print(inter_graph_list)
                self.inference_model.setGraphInEnv(inter_graph_list)
                status = self.inference_model.setGraphInEnv(inter_graph_list)
                if status is None:
                    print("Exiting from inference")
                    return RegisterAllocationInference_pb2.Data(message="Exit")
            elif inter_graphs.result:
                # exit()
                # self.inference_model.update_obs(request, self.inference_model.env.virtRegId, self.inference_model.env.split_point)
                if not self.inference_model.update_obs(request):
                    print("Current split failed")
                    self.inference_model.setCurrentNodeAsNotVisited()
                # else:
                self.inference_model.updateSelectNodeObs()
                # print('stopping for spliting check, enter to continue...')
                # stop = input()
                # if stop == 0:
                #     exit()
            else:
                # print("LLVM responce", inter_graphs)
                self.inference_model.setCurrentNodeAsNotVisited()
                self.inference_model.updateSelectNodeObs()
                print("Inside else; doing nothing here")
            action, count = self.inference_model.compute_action()
            # action, count = self.inference_model.evaluate()
            # print('action= {}, count={}'.format(action,count))
            select_node_agent = "select_node_agent_{}".format(count)
            select_task_agent = "select_task_agent_{}".format(count)
            split_agent = "split_node_agent_{}".format(count)
            # color_agent = "colour_node_agent_{}".format(count)
            color_agent = "colour_node_agent_id"

            if self.inference_model.getLastTaskDone() == 1:
                reply=RegisterAllocationInference_pb2.Data(message="Split", regidx=action[select_node_agent], payload=action[split_agent])
            elif self.inference_model.getLastTaskDone() == 0:
                print("Returned colour map is:", action[color_agent])
                reply=RegisterAllocationInference_pb2.Data(message="Color", color=action[color_agent], funcName=request.funcName)
            else:
                reply=RegisterAllocationInference_pb2.Data(message="Exit")
            # print('------Bye-----' , reply)
            print('------Bye-----')
            return reply
        except:
            print('Error')
            # print(request)
            print('Error')
            traceback.print_exc()
            reply=RegisterAllocationInference_pb2.Data(message="Split", regidx=0, payload=0)
            return reply
      

class Server:

    @staticmethod

    def run():
        ray.init()

        server=grpc.server(futures.ThreadPoolExecutor(max_workers=20),options = [
                    ('grpc.max_send_message_length', 200*1024*1024), #50MB
                            ('grpc.max_receive_message_length', 200*1024*1024) #50MB
                                ])

        RegisterAllocationInference_pb2_grpc.add_RegisterAllocationInferenceServicer_to_server(service_server(),server)

        server.add_insecure_port('localhost:' + str(sys.argv[1]))

        server.start()
        print("Server Running")
        
        server.wait_for_termination()

if __name__ == '__main__' :
    assert(len(sys.argv) == 2)
    Server.run()
