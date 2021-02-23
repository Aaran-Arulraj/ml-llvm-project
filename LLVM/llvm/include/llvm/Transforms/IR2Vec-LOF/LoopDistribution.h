#ifndef __IR2Vec_LOOP_DISTRIBUTION_H__
#define __IR2Vec_LOOP_DISTRIBUTION_H__

#include "llvm/Transforms/IR2Vec-LOF/RDG.h"

#include "llvm/ADT/MapVector.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/OptimizationRemarkEmitter.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/Function.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;
using NodeList = SmallVector<DDGNode *, 64>;
using InstList = SmallVector<Instruction *, 64>;
using Container = StringMap<InstList>;
using Ordering = SmallVector<std::string, 10>;

static cl::opt<std::string> funcName("function", cl::Hidden, cl::Required,
                                     cl::desc("Name of the function"));

static cl::opt<unsigned int> loopID("lID", cl::Hidden, cl::Required,
                                    cl::desc("ID of the loop set by RDG pass"));

static cl::opt<std::string>
    partitionPattern("partition", cl::Hidden, cl::Required,
                     cl::desc("partition for loop distribution"));

class LoopDistribution : public FunctionPass {

private:
  NodeList topologicalWalk(DataDependenceGraph &SCCGraph);
  Ordering populatePartitions(DataDependenceGraph &SCCGraph, Loop *il,
                              std::string partition);
  Loop *cloneLoop(Loop *L, LoopInfo *LI, DominatorTree *DT,
                  ValueToValueMap &instVMap);
  void modifyCondBranch(BasicBlock *preheader, Loop *newLoop);
  void removeUnwantedSlices(SmallVector<Loop *, 5> clonedLoops,
                            SmallDenseMap<Loop *, ValueToValueMap> loopInstVMap,
                            SmallDenseMap<unsigned, Loop *> workingLoopID,
                            Ordering paritionOrder);
  bool fail(StringRef RemarkName, StringRef Message, Loop *L);
  bool doSanityChecks(Loop *L);
  MDNode *getLoopID(Loop *L) const;
  void changeLoopIDMetaData(Loop *L);

  bool distributed;
  OptimizationRemarkEmitter *ORE;
  AAResults *AA;
  ScalarEvolution *SE;
  LoopInfo *LI;
  DominatorTree *DT;
  void createContainer(DataDependenceGraph &ddg);
  void addNodeToContainer(DDGNode *node, const std::string id);
  void mergePartitionsOfContainer(std::string srcID, std::string destID);
  Container container;
  DataDependenceGraph* findSCCGraph(Loop *il, DependenceInfo DI);
  bool computeDistributionOnLoop(DataDependenceGraph *SCCGraph, Loop *il, std::string partition);
Loop* findLoop(unsigned int lid);
public:
  static char ID;
  LoopDistribution() : FunctionPass(ID) { distributed = false; }
  bool runOnFunction(Function &F) override;
  
  void computeDistribution(SmallVector<DataDependenceGraph*, 5> &SCCGraphs, SmallVector<Loop *, 5> &loops, SmallVector<std::string, 5> &dis_seqs);
   // void computeDistribution(Function &F, std::string fname, unsigned int lid, std::string partition);
  
  void getAnalysisUsage(AnalysisUsage &AU) const;
};

#endif
