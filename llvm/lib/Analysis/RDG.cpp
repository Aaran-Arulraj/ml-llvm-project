#include "llvm/IR/Function.h"
#include "llvm/Analysis/RDG.h"
#include "llvm/Pass.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/InitializePasses.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/DependenceGraphBuilder.h"
#include "llvm/Analysis/DDG.h"
#include "llvm/Analysis/DependenceAnalysis.h"
#include "llvm/ADT/Statistic.h"
#include "llvm/Analysis/AliasAnalysis.h"
#include "llvm/ADT/SCCIterator.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/Support/GraphWriter.h"
#include "llvm/Analysis/LoopAccessAnalysis.h"
#include "llvm/Analysis/LoopAnalysisManager.h"
// #include "llvm/Support/Debug.h"

// #include "llvm/IR/Dominators.h"
// #include "llvm/Analysis/ScalarEvolution.h"
// #include "llvm/Analysis/ScalarEvolutionExpander.h"
// #include "llvm/Analysis/ScalarEvolutionExpressions.h"

// #include "llvm/ADT/StringExtras.h"

#define DEBUG_Type "RDG"

using namespace llvm;


RDGWrapperPass::RDGWrapperPass() : FunctionPass(ID) {
  initializeRDGWrapperPassPass(*PassRegistry::getPassRegistry());
}

char RDGWrapperPass::ID = 0;
// static RegisterPass<RDGWrapperPassPass> X("RDG", "Build ReducedDependenceGraph", true, true);
INITIALIZE_PASS_BEGIN(RDGWrapperPass, "RDG", "Build ReducedDependenceGraph", true, true)
// INITIALIZE_PASS_DEPENDENCY(LoopInfoWrapperPass)
INITIALIZE_PASS_END(RDGWrapperPass, "RDG", "Build ReducedDependenceGraph", true, true)

void RDGWrapperPass::PrintDotFile(DataDependenceGraph &G, std::string Filename){
	// Code to generate DOT File to store RDG

	std::error_code EC;
	raw_fd_ostream File (Filename.c_str(), EC, sys::fs::F_Text);
	int x = 0;

	if(!EC){
		File << "digraph G {\n";
		for(auto *N : G){
			x++;
			InstructionListType IList;
			N->collectInstructions([] (const Instruction *I) {return true;}, IList);
			std::string str = "";
			int tmp = 0;
			for(Instruction *II : IList){
				tmp++;
				// Instruction *Inst = dyncast<Instruction>(II);
				std::string s;
				llvm::raw_string_ostream(s) << *II;
				if(tmp>1){
					str = str + "\n";
				}
				str = str + s;
			}

			File << x << " [label=\"" << str << "\"];\n";
			
			NodeNumber.insert(std::make_pair(N, x));
		}
			
		for(auto *N : G){
			// for(auto *d : G){
			// 	if(&N == &d){
			// 		continue;
			// 	}
			// }
			for (auto &E : N->getEdges()){
				// errs()<< "Edgelabel: " << (*E).getKind() << "\n";
				File << NodeNumber.find(N)->second << " -> " 
						<< NodeNumber.find(&E->getTargetNode())->second 
						<<"[label=\"  " << (*E).getKind() << "\"];\n";
					//  <<"[label=\"\\E\"];\n";
			}
				// if(!N->hasEdgeTo(*d)){
				// 	File << NodeNumber.find(N)->second << " -> " << NodeNumber.find(d)->second << ";\n";
				// }
			// }
		}
		File << "}";
	}
	else{
		errs() << "error opening file for writing! \n";
	}
}

void RDGWrapperPass::BuildRDG_DI(DataDependenceGraph &G){}

void RDGWrapperPass::BuildRDG_LAI(DataDependenceGraph &G, DependenceInfo &DI, const LoopAccessInfo &LAI){
	const auto alldependences = LAI.getDepChecker().getDependences();
		
	if(alldependences == nullptr){
		errs() << "######################\n";
		// DEBUG(dbgs() << "LAI dependences is a nullptr.\n");
		// return false;
	}
	// DEBUG(dbgs() << "Number of dependenes from LLVM: " << alldependences->size() << "\n");	

	errs() << "+++++++++++++++++++++++++++++ " << alldependences->size() << "\n";

	bool ControlDependence = false;
	for(auto dep : *alldependences){
		errs() << "$$$$$$$$$$$$$$$$$$$$$\n";
		// errs() << "dep: " << &dep << "\n";
		Instruction *Src, *Dst;
		if(dep.Type == MemoryDepChecker::Dependence::DepType::Forward ||
			dep.Type == MemoryDepChecker::Dependence::DepType::ForwardButPreventsForwarding){
				Src = dep.getSource(LAI);
				Dst = dep.getDestination(LAI);
		}

		if(dep.Type == MemoryDepChecker::Dependence::DepType::Backward ||
			dep.Type == MemoryDepChecker::Dependence::DepType::BackwardVectorizable ||
			dep.Type == MemoryDepChecker::Dependence::DepType::BackwardVectorizableButPreventsForwarding){
				Dst = dep.getSource(LAI);
				Src = dep.getDestination(LAI);
		}

		if(dep.Type == MemoryDepChecker::Dependence::DepType::Unknown){
			Src = dep.getSource(LAI);
			Dst = dep.getDestination(LAI);
		}

		if(Src->getParent() != Dst->getParent()){
			// DEBUG(dbgs() << "Ignoring a dependence from LLVM.\n");
			continue;
		}

		errs() << "Src: " << *Src << "    " << "Dst: " << *Dst << "\n";

		int count = 0;
		SmallPtrSet<NodeType *, 4> SrcNodeList;
		SmallPtrSet<NodeType *, 4> DstNodeList;
		NodeType *SrcNode, *DstNode;

		for(NodeType *N : G){
			InstructionListType InstList;
			N->collectInstructions([](const Instruction *I) { return true; }, InstList);

			for(Instruction *II : InstList){
				if(Src == II){
					SrcNode = N;
					SrcNodeList.insert(N);
				}

				if(Dst == II){
					DstNode = N;
					DstNodeList.insert(N);
				}
			}
		}

		for(NodeType *SrcIt : SrcNodeList){
			for(NodeType *DstIt : DstNodeList){
				if(SrcIt == DstIt){
					SrcNodeList.erase(SrcIt);
					DstNodeList.erase(DstIt);
				}
			}
		}

		for(NodeType *SrcIt : SrcNodeList){
			for(NodeType *DstIt : DstNodeList){
				errs() << "src node: " << *SrcIt << "\n";
				errs() << "dst node: " << *DstIt << "\n";
				DDGBuilder(G, DI, BBList).createMemoryEdge(*SrcIt, *DstIt);
			}
		}

		for(NodeType *SrcIt : SrcNodeList){
			errs() << "SrcNodeList: " << *SrcIt << "\n";
		}

		for(NodeType *DstIt : DstNodeList){
			errs() << "DstNodeList: " << *DstIt << "\n";
		}
	}
}

bool RDGWrapperPass::runOnFunction(Function &F){
	raw_ostream &operator<<(raw_ostream &OS, const DataDependenceGraph &G);
	
	AAResults &AA = getAnalysis<AAResultsWrapperPass>().getAAResults();
	ScalarEvolution &SE = getAnalysis<ScalarEvolutionWrapperPass>().getSE();
	LoopInfo &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();

	DependenceInfo DI = DependenceInfo(&F, &AA, &SE, &LI);

	// using InstructionListType = SmallVector<Instruction *, 2>;

	// using EdgeType = DDGEdge *;
	// using EdgeListTy = SetVector<EdgeType *>;
	// EdgeListTy el;

	int loopNum = 0;
	for(LoopInfo::iterator i = LI.begin(), e = LI.end(); i != e; ++i){
		loopNum++;
		Loop *L = *i;

		DataDependenceGraph G = DataDependenceGraph(*L, LI, DI);
		DataDependenceGraph G1 = DataDependenceGraph(*L, LI, DI);

		L->dump();

		auto *LAA = &getAnalysis<LoopAccessLegacyAnalysis>();

		const LoopAccessInfo &LAI = LAA->getInfo(L);

		BuildRDG_LAI(G1, DI, LAI);

			// for(DGIterator SrcIt = G.begin(), eIt = G.end(); SrcIt!=eIt; ++SrcIt){
			// 	InstructionListType SrcList;

		///////////////////////////////////////////////////////////////////////////////////////////////////
		//## DependenceGraphBuilder API ##
		///////////////////////////////////////////////////////////////////////////////////////////////////
		// DataDependenceGraph G = DataDependenceGraph(*L, LI, DI);

		// DDGBuilder(G, DI, BBList).populate();

		std::string Filename1 = "DDG_" + F.getName().str() + "_Loop" + std::to_string(loopNum) + ".dot";
		errs() << "Writing " + Filename1 + "\n";

		PrintDotFile(G, Filename1);

		std::string Filename2 = "DDG_New_" + F.getName().str() + "_Loop" + std::to_string(loopNum) + ".dot";
		errs() << "Writing " + Filename2 + "\n";

		PrintDotFile(G1, Filename2);
	}
	return false;

}

void RDGWrapperPass::getAnalysisUsage(AnalysisUsage &AU) const {
	AU.addRequired<LoopInfoWrapperPass>();
	AU.addRequired<ScalarEvolutionWrapperPass>();
	AU.addRequired<AAResultsWrapperPass>();
	// AU.addRequired<LoopAccessInfo>();
    AU.addRequired<LoopAccessLegacyAnalysis>();
    // AU.addRequired<ScalarEvolutionWrapperPass>();
    // AU.addRequired<DominatorTreeWrapperPass>();
	// AU.addRequired<ProfileSummaryInfoWrapperPass>();
	AU.setPreservesAll();
}


