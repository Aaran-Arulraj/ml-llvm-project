#include "llvm/CodeGen/RegisterProfile.h"
#include <llvm/ADT/MapVector.h>
#include <llvm/ADT/SmallVector.h>
#include <map>
#include <stdio.h>

#define max_edge_count 30000

class Graph {
public:
  llvm::SmallVector<unsigned, 8> getColorOfVisitedAdjNodes(unsigned node_idx);
  llvm::SmallVector<unsigned, 8> getAdjNodes(unsigned node_idx);
  void get_eligibleNodes(std::vector<int>& eligibleNodes);
  void UpdateColorVisitedNode(unsigned node_idx, unsigned colour);
  bool all_discovered();
  Graph(int edges[][2], const RegisterProfileMap &regProfMap);
  llvm::SmallVector<bool, 8> discovered;
  void UpdateVisitList(unsigned node_idx);

private:
  llvm::SmallMapVector<unsigned, llvm::SmallVector<unsigned, 8>, 16>
      adjacencyList;
  unsigned node_number;
  // llvm::SmallVector<unsigned, 8> indegree;
  llvm::SmallVector<int, 8> colored;
};

class RegisterActionSpace {

public:
  static std::vector<std::string> supported_regclasses;
  static std::map<std::string, std::vector<int>> suppcls_regs_normalize_map;
  static std::vector<int> ac_sp_normlize;
  static std::map<int, int> normal_org_map;
  static std::map<int, int> org_normal_map;
  static std::map<std::string, std::vector<int>> overlaps;
  llvm::SmallVector<unsigned, 8>
  maskActionSpace(llvm::StringRef regclass,
                  llvm::SmallVector<unsigned, 8> adj_colors);
};