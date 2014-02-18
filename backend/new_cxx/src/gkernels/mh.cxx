#include "gkernels/mh.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"

pair<Trace*,double> MHGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;

  pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = p.first;
  rhoDB = p.second;

  assertTorus(scaffold);

  double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,rhoDB,shared_ptr<map<Node*,Gradient> >());

  return make_pair(trace,xiWeight - rhoWeight);
}

void MHGKernel::accept() { }


void MHGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
