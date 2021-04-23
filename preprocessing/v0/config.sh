PWD=`pwd`
HOME=`realpath ${PWD}/../..`

BUILD_TYPE="_release"

LLVM_BUILD="${HOME}/llvm-project/build${BUILD_TYPE}"
echo "LLVM Build used for the data generation: ${LLVM_BUILD}"
[[ ! -d ${LLVM_BUILD} ]] && echo "LLVM build directory does not exist" && exit

INP_DIR=${HOME}/data/SPEC_NEW_UNLINK_Ind_iv_REL_AsrtON
echo "Input data directory path: ${INP_DIR}"
[[ ! -d ${INP_DIR} ]] && echo "Input directory does not exist" && exit

LL_FLR_NAME=level-O0-llfiles
INP_TYPE=llfiles

WD=${INP_DIR}/G_O3_1
echo "${WD}: Run to check the effect of added new ID if loopid not found in rdg on data"

USE_MCA=
# USE_MCA=" -use-mca "
TIME_OUT= # "timeout --kill-after=2m 2m "


REMARKS=

OPT_PASSES_SEQ="-O3 "

echo "Pass seq used to generate data : ${SSA_PASSES_SEQ}"
${LLVM_BUILD}/bin/llvm-as < /dev/null | ${LLVM_BUILD}/bin/clang ${OPT_PASSES_SEQ}  -mllvm -regalloc=mlra -debug-pass=Arguments ../../sample/bublesort.c
echo "\n"
${LLVM_BUILD}/bin/llvm-as < /dev/null | ${LLVM_BUILD}/bin/opt ${OPT_PASSES_SEQ}  -regalloc=mlra -debug-pass=Arguments
echo "\n"
${LLVM_BUILD}/bin/llvm-as < /dev/null | ${LLVM_BUILD}/bin/llc ${OPT_PASSES_SEQ}  -regalloc=mlra -debug-pass=Arguments

