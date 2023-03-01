#ifndef MLRA_INFERENCE_INCLUDES_MULTI_AGENT_ENV_H
#define MLRA_INFERENCE_INCLUDES_MULTI_AGENT_ENV_H

#include "topological_sort.h"
#include "MLInferenceEngine/environment.h"
#include <vector>
#include <set>
// #include "llvm/ADT/SetVector.h
// #include "llvm/CodeGen/RegisterProfile.h"

typedef std::vector<float> Observation;

#define max_node_number 600
#define IR2Vec_size 100
#define X86_action_space_size 113
#define max_usepoints_count 200
#define split_threshold 10

#define selectNodeObsSize 153601
#define selectTaskObsSize 106
#define colourNodeObsSize 216
#define splitNodeObsSize 700

class MultiAgentEnv : public Environment {
  int debug_ct=0;
  RegisterProfileMap regProfMap;

  RegisterActionSpace *registerAS;

  RegisterProfile current_node;

  unsigned edge_count;

  // int *nid_idx = new int[max_node_number]();

  // int *idx_nid = new int[max_node_number]();

  std::map<int, int> nid_idx;
  std::map<int, int> idx_nid;


  float annotations[max_node_number][3];

  unsigned splitStepCount = 0;

  // float *nodeRepersentaion[max_node_number];

  std::vector<std::vector<float>> nodeRepresentation;

  Observation *select_node_step(unsigned action);

  Observation *select_task_step(unsigned action);

  Observation *colour_node_step(unsigned action);

  void createNodeSplitMask(std::vector<float>& mask);

  void getSplitPointProperties(std::vector<float>& usepointProperties);
  
  void createNodeSelectMask(std::vector<int> &mask);

  void createAnnotations(std::vector<float> &temp_annotations);

  unsigned computeEdgesFromRP();

  void computeEdgesFlatened(std::vector<float> &edgesFlattened);

  void constructNodeVector(const SmallVector<IR2Vec::Vector, 12>& nodeMat, std::vector<float>& nodeVec);

  Observation *taskSelectionObsConstructor();

  Observation *colourNodeObsConstructor();

  Observation *splitNodeObsConstructor();

  void computeAnnotations();
  void printRegisterProfile() const;


  // void updateEdges();

public:
  Graph *graph_topology;
  
  std::vector<std::vector<int>> edges;

  std::map<unsigned, unsigned> nid_colour;

  unsigned current_node_id;

  unsigned splitPoint;

  Observation* reset(const RegisterProfileMap& regProfMap);

  Observation* step(Action action) override;

  void update_env(RegisterProfileMap *regProfMap, SmallSetVector<unsigned, 8> updatedRegIdxs);

  Observation *selectNodeObsConstructor();

  virtual Observation* split_node_step(unsigned action) = 0; 

  MultiAgentEnv(){
    edges = std::vector<std::vector<int>>(MAX_EDGE_COUNT, std::vector<int>(2));
  }
};

#endif
