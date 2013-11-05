#include "lkernel.h"
#include "infer/meanfield.h"
#include "trace.h"
#include "flush.h"
#include "check.h"
#include "node.h"
#include "value.h"
#include "scaffold.h"
#include "sp.h"

double MeanFieldGKernel::propose()
{
  /* Sample from the variational distribution. */
  double weightXi = trace->regen(scaffold->border,scaffold,false,nullptr,nullptr);
  return weightXi - weightRho;
}
 
void MeanFieldGKernel::accept()
{
  flushDB(rhoDB,false);
  rhoDB = nullptr;
}

void MeanFieldGKernel::reject()
{
  pair<double, OmegaDB *> xiInfo = trace->detach(scaffold->border,scaffold);
  OmegaDB * xiDB = xiInfo.second;
  assertTorus(trace,scaffold);
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  flushDB(rhoDB,true);
  flushDB(xiDB,false);
  rhoDB = nullptr;
}

void MeanFieldGKernel::destroyParameters()
{
  delete scaffold;
}

void MeanFieldGKernel::registerVariationalLKernels()
{
  for (pair<Node *, Scaffold::DRGNode> p : scaffold->drg)
  {
    Node * node = p.first;
    if (node->nodeType == NodeType::OUTPUT && 
	!scaffold->isResampling(node->operatorNode) &&
	node->sp()->hasVariationalLKernel)
    {
      scaffold->lkernels.insert({node,node->sp()->getVariationalLKernel(node)});
    }
  }
}


void MeanFieldGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  delete sparam;

  /* Now, compute variational kernels through stochastic gradient descent. */
  double stepSize = 0.05;
  size_t numIters = 50;
  registerVariationalLKernels();
  if (scaffold->lkernels.empty()) { numIters = 0; }
  double rhoWeight;

  tie(rhoWeight,rhoDB) = trace->detach(scaffold->border,scaffold);
  assertTorus(trace,scaffold);

  for (size_t i = 0; i < numIters; ++i)
  {
    map<Node *, vector<double> > gradients;

    // Regen populates the gradients
    double gain = trace->regen(scaffold->border,scaffold,false,nullptr,&gradients);

    OmegaDB * detachedDB;
    tie(ignore,detachedDB) = trace->detach(scaffold->border,scaffold);
    assertTorus(trace,scaffold);
    flushDB(detachedDB,false);

    for (pair<Node *, LKernel*> p : scaffold->lkernels)
    {
      VariationalLKernel * vk = dynamic_cast<VariationalLKernel*>(p.second);
      if (vk) { vk->updateParameters(gradients[p.first],gain,stepSize); }
    }
  }
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  OmegaDB * rhoDB2;
  tie(weightRho,rhoDB2) = trace->detach(scaffold->border,scaffold);
  flushDB(rhoDB2,true);
  assertTorus(trace,scaffold);
}
 
