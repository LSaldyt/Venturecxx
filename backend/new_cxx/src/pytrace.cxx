#include "pytrace.h"
#include "regen.h"
#include "render.h"
#include "scaffold.h"
#include "detach.h"
#include "concrete_trace.h"
#include "db.h"
#include "env.h"
#include "values.h"
#include "sp.h"
#include "mixmh.h"
#include "indexer.h"
#include "gkernel.h"
#include "gkernels/mh.h"
#include "gkernels/func_mh.h"
#include "gkernels/pgibbs.h"
#include "gkernels/egibbs.h"
#include "gkernels/slice.h"
#include <boost/foreach.hpp>

#include <boost/python/exception_translator.hpp>

PyTrace::PyTrace() : trace(new ConcreteTrace()), continuous_inference_running(false), continuous_inference_thread(NULL)
{
  trace->initialize();
}
PyTrace::~PyTrace() {}

void PyTrace::evalExpression(DirectiveID did, boost::python::object object) 
{
  VentureValuePtr exp = parseExpression(object);
  pair<double,Node*> p = evalFamily(trace.get(),
                                    exp,
                                    trace->globalEnvironment,
                                    shared_ptr<Scaffold>(new Scaffold()),
                                    shared_ptr<DB>(new DB()),
                                    shared_ptr<map<Node*,Gradient> >());
  assert(p.first == 0);
  assert(!trace->families.count(did));
  trace->families[did] = shared_ptr<Node>(p.second);
}

void PyTrace::unevalDirectiveID(DirectiveID did) 
{ 
 assert(trace->families.count(did));
 unevalFamily(trace.get(),trace->families[did].get(),shared_ptr<Scaffold>(new Scaffold()),shared_ptr<DB>(new DB()));
 trace->families.erase(did);
}

void PyTrace::observe(DirectiveID did,boost::python::object valueExp)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  trace->unpropagatedObservations[root.get()] = parseExpression(valueExp);
}

void PyTrace::unobserve(DirectiveID did)
{
  assert(trace->families.count(did));
  Node * node = trace->families[did].get();
  OutputNode * appNode = trace->getOutermostNonRefAppNode(node);
  if (trace->isObservation(node)) { unconstrain(trace.get(),appNode); trace->unobserveNode(node); }
  else
  {
    assert(trace->unpropagatedObservations.count(node));
    trace->unpropagatedObservations.erase(node);
  }
}

void PyTrace::bindInGlobalEnv(const string& sym, DirectiveID did)
{
  trace->globalEnvironment->addBinding(sym,trace->families[did].get());
}

boost::python::object PyTrace::extractPythonValue(DirectiveID did)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  VentureValuePtr value = trace->getValue(root.get());
  assert(value.get());
  return value->toPython(trace.get());
}

void PyTrace::setSeed(size_t n) {
  gsl_rng_set(trace->getRNG(), n);
}

size_t PyTrace::getSeed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


double PyTrace::getGlobalLogScore() 
{
  double ls = 0.0;
  for (set<Node*>::iterator iter = trace->unconstrainedChoices.begin();
       iter != trace->unconstrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    shared_ptr<Args> args = trace->getArgs(node);
    ls += psp->logDensity(trace->getValue(node),args);
  }
  for (set<Node*>::iterator iter = trace->constrainedChoices.begin();
       iter != trace->constrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    shared_ptr<Args> args = trace->getArgs(node);
    ls += psp->logDensity(trace->getValue(node),args);
  }
  return ls;
}

uint32_t PyTrace::numUnconstrainedChoices() { return trace->numUnconstrainedChoices(); }

// parses params and does inference
struct Inferer
{
  shared_ptr<ConcreteTrace> trace;
  shared_ptr<GKernel> gKernel;
  ScopeID scope;
  BlockID block;
  shared_ptr<ScaffoldIndexer> scaffoldIndexer;
  size_t transitions;
  bool cycle; // TODO Turn this into an enum for mixtures
  vector<shared_ptr<Inferer> > subkernels;
  
  Inferer(shared_ptr<ConcreteTrace> trace, boost::python::dict params) : trace(trace)
  {
    cycle = false;
    string kernel = boost::python::extract<string>(params["kernel"]);
    if (kernel == "mh")
    {
      gKernel = shared_ptr<GKernel>(new MHGKernel);
    }
    else if (kernel == "func_mh")
    {
      gKernel = shared_ptr<GKernel>(new FuncMHGKernel);
    }
    else if (kernel == "pgibbs")
    {
      size_t particles = boost::python::extract<size_t>(params["particles"]);
      bool inParallel  = boost::python::extract<bool>(params["in_parallel"]);
      gKernel = shared_ptr<GKernel>(new PGibbsGKernel(particles,inParallel));
    }
    else if (kernel == "gibbs")
    {
      bool inParallel  = boost::python::extract<bool>(params["in_parallel"]);
      gKernel = shared_ptr<GKernel>(new EnumerativeGibbsGKernel(inParallel));
    }
    else if (kernel == "slice")
    {
      gKernel = shared_ptr<GKernel>(new SliceGKernel);
    }
    else if (kernel == "cycle")
    {
      cycle = true;
      boost::python::list subs = boost::python::extract<boost::python::list>(params["subkernels"]);
      boost::python::ssize_t len = boost::python::len(subs);
      subkernels = vector<shared_ptr<Inferer> >(len);

      for (boost::python::ssize_t i = 0; i < len; ++i)
      {
        subkernels[i] = shared_ptr<Inferer>(new Inferer(trace, boost::python::extract<boost::python::dict>(subs[i])));
      }
    }
    else
    {
      cout << "\n***Kernel '" << kernel << "' not supported. Using MH instead.***" << endl;
      gKernel = shared_ptr<GKernel>(new MHGKernel);
    }
    
    if (!(kernel == "cycle")) {
      scope = fromPython(params["scope"]);
      block = fromPython(params["block"]);

      if (block->hasSymbol() && block->getSymbol() == "ordered_range")
      {
        VentureValuePtr minBlock = fromPython(params["min_block"]);
        VentureValuePtr maxBlock = fromPython(params["max_block"]);
        scaffoldIndexer = shared_ptr<ScaffoldIndexer>(new ScaffoldIndexer(scope,block,minBlock,maxBlock));
      }
      else
      {
        scaffoldIndexer = shared_ptr<ScaffoldIndexer>(new ScaffoldIndexer(scope,block));
      }
    }
    transitions = boost::python::extract<size_t>(params["transitions"]);
  }
  
  void infer()
  {
    if (trace->numUnconstrainedChoices() == 0) { return; }
    for (size_t i = 0; i < transitions; ++i)
    {
      if (cycle) { inferCycle(); }
      else { inferPrimitive(); inferAEKernels(); }
    }
  }

  void inferCycle()
  {
    for (size_t i = 0; i < subkernels.size(); i++)
    {
      subkernels[i]->infer();
    }
  }

  void inferPrimitive()
  {
    mixMH(trace.get(), scaffoldIndexer, gKernel);
  }

  void inferAEKernels()
  {
    for (set<Node*>::iterator iter = trace->arbitraryErgodicKernels.begin();
      iter != trace->arbitraryErgodicKernels.end();
      ++iter)
    {
      OutputNode * node = dynamic_cast<OutputNode*>(*iter);
      assert(node);
      trace->getMadeSP(node)->AEInfer(trace->getMadeSPAux(node),trace->getArgs(node),trace->getRNG());
    }
  }
};

void PyTrace::infer(boost::python::dict params)
{ 
  Inferer inferer(trace, params);
  inferer.infer();
}

boost::python::dict PyTrace::continuous_inference_status()
{
  boost::python::dict status;
  status["running"] = continuous_inference_running;
  if(continuous_inference_running) {
    status["params"] = continuous_inference_params;
  }
  return status;
}

void run_continuous_inference(shared_ptr<Inferer> inferer, bool * flag)
{
  while(*flag) { inferer->infer(); }
}

void PyTrace::start_continuous_inference(boost::python::dict params)
{
  stop_continuous_inference();
  
  continuous_inference_params = params;
  continuous_inference_running = true;
  shared_ptr<Inferer> inferer = shared_ptr<Inferer>(new Inferer(trace, params));
  
  trace->makeConsistent();
  
  continuous_inference_thread = new boost::thread(run_continuous_inference, inferer, &continuous_inference_running);
}

void PyTrace::stop_continuous_inference() {
  if(continuous_inference_running) {
    continuous_inference_running = false;
    continuous_inference_thread->join();
    delete continuous_inference_thread;
    continuous_inference_thread = NULL;
  }
}

void translateStringException(const string& err) {
  PyErr_SetString(PyExc_RuntimeError, err.c_str());
}

void translateCStringException(const char* err) {
  PyErr_SetString(PyExc_RuntimeError, err);
}

double PyTrace::makeConsistent()
{
  return trace->makeConsistent();
}

int PyTrace::numNodesInBlock(boost::python::object scope, boost::python::object block)
{
  return trace->getNodesInBlock(fromPython(scope), fromPython(block)).size();
}

boost::python::list PyTrace::dotTrace(bool colorIgnored)
{
  boost::python::list dots;
  Renderer r;

  r.dotTrace(trace,shared_ptr<Scaffold>(),false,colorIgnored);
  dots.append(r.dot);
  r.dotTrace(trace,shared_ptr<Scaffold>(),true,colorIgnored);
  dots.append(r.dot);

  set<Node *> ucs = trace->unconstrainedChoices;
  BOOST_FOREACH (Node * pNode, ucs)
    {
      set<Node*> pNodes;
      pNodes.insert(pNode);
      vector<set<Node*> > pNodesSequence;
      pNodesSequence.push_back(pNodes);

      shared_ptr<Scaffold> scaffold = constructScaffold(trace.get(),pNodesSequence,false);
      r.dotTrace(trace,scaffold,false,colorIgnored);
      dots.append(r.dot);
      r.dotTrace(trace,scaffold,true,colorIgnored);
      dots.append(r.dot);
      cout << "detaching..." << flush;
      pair<double,shared_ptr<DB> > p = detachAndExtract(trace.get(),scaffold->border[0],scaffold);
      cout << "done" << endl;
      r.dotTrace(trace,scaffold,false,colorIgnored);
      dots.append(r.dot);
      r.dotTrace(trace,scaffold,true,colorIgnored);
      dots.append(r.dot);

      cout << "restoring..." << flush;
      regenAndAttach(trace.get(),scaffold->border[0],scaffold,true,p.second,shared_ptr<map<Node*,Gradient> >());
      cout << "done" << endl;
    }

  return dots;
}

boost::python::list PyTrace::numFamilies()
{
  boost::python::list xs;
  xs.append(trace->families.size());
  for (map<Node*, shared_ptr<VentureSPRecord> >::iterator iter = trace->madeSPRecords.begin();
       iter != trace->madeSPRecords.end();
       ++iter)
    {
      if (iter->second->spFamilies->families.size()) { xs.append(iter->second->spFamilies->families.size()); }
    }
  return xs;
}

void PyTrace::freeze(DirectiveID did) 
{
  trace->freezeDirectiveID(did);
}


BOOST_PYTHON_MODULE(libpumatrace)
{
  using namespace boost::python;
  
  register_exception_translator<string>(&translateStringException);
  register_exception_translator<const char*>(&translateCStringException);

  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("set_seed", &PyTrace::setSeed)
    .def("get_seed", &PyTrace::getSeed)
    .def("numRandomChoices", &PyTrace::numUnconstrainedChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("infer", &PyTrace::infer)
    .def("dot_trace", &PyTrace::dotTrace)
    .def("makeConsistent", &PyTrace::makeConsistent)
    .def("numNodesInBlock", &PyTrace::numNodesInBlock)
    .def("numFamilies", &PyTrace::numFamilies)
    .def("freeze", &PyTrace::freeze)
    .def("continuous_inference_status", &PyTrace::continuous_inference_status)
    .def("start_continuous_inference", &PyTrace::start_continuous_inference)
    .def("stop_continuous_inference", &PyTrace::stop_continuous_inference)
    .def("stop_and_copy", &PyTrace::stop_and_copy, return_value_policy<manage_new_object>())
    ;
};
