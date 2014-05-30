# Copyright (c) 2013, MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
import random

from venture.exception import VentureException
from venture.lite.utils import simulateCategorical, sampleLogCategorical

# Thin wrapper around Trace
# TODO: merge with CoreSivm?

class Engine(object):

  def __init__(self, name="phony", Trace=None):
    self.name = name
    self.Trace = Trace
    self.traces = [Trace()]
    self.weights = [0]
    self.directiveCounter = 0
    self.directives = {}

  def getDistinguishedTrace(self): 
    assert self.traces
    return self.traces[0]

  def nextBaseAddr(self):
    self.directiveCounter += 1
    return self.directiveCounter

  # TODO Move this into stack.
  def desugarLambda(self,datum):
    if type(datum) is list and type(datum[0]) is dict and datum[0]["value"] == "lambda":
      ids = [{"type" : "symbol","value" : "quote"}] + [datum[1]]
      body = [{"type" : "symbol","value" : "quote"}] + [self.desugarLambda(datum[2])]
      return [{"type" : "symbol", "value" : "make_csp"},ids,body]
    elif type(datum) is list: return [self.desugarLambda(d) for d in datum]
    else: return datum

  def assume(self,id,datum):
    baseAddr = self.nextBaseAddr()

    exp = self.desugarLambda(datum)

    for trace in self.traces:
      trace.eval(baseAddr,exp)
      trace.bindInGlobalEnv(id,baseAddr)

    self.directives[self.directiveCounter] = ["assume",id,datum]

    return (self.directiveCounter,self.getDistinguishedTrace().extractValue(baseAddr))

  def predict(self,datum):
    baseAddr = self.nextBaseAddr()
    for trace in self.traces:
      trace.eval(baseAddr,self.desugarLambda(datum))

    self.directives[self.directiveCounter] = ["predict",datum]

    return (self.directiveCounter,self.getDistinguishedTrace().extractValue(baseAddr))

  def observe(self,datum,val):
    baseAddr = self.nextBaseAddr()

    for trace in self.traces:
      trace.eval(baseAddr,self.desugarLambda(datum))
      logDensity = trace.observe(baseAddr,val)

      # TODO check for -infinity? Throw an exception?
      if logDensity == float("-inf"):
        raise VentureException("invalid_constraint", "Observe failed to constrain",
                               expression=datum, value=val)

    self.directives[self.directiveCounter] = ["observe",datum,val]
    return self.directiveCounter

  def forget(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot forget a non-existent directive id",
                             argument="directive_id", directive_id=directiveId)
    directive = self.directives[directiveId]
    for trace in self.traces:
      if directive[0] == "observe": trace.unobserve(directiveId)
      trace.uneval(directiveId)
      if directive[0] == "assume": trace.unbindInGlobalEnv(directive[1])

    del self.directives[directiveId]

  def freeze(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot freeze a non-existent directive id",
                             argument="directive_id", directive_id=directiveId)
    # TODO Record frozen state for reinit_inference_problem?  What if
    # the replay is done with a different number of particles than the
    # original?  Where do the extra values come from?
    for trace in self.traces:
      trace.freeze(directiveId)

  def report_value(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot report a non-existent directive id",
                             argument=directiveId)
    return self.getDistinguishedTrace().extractValue(directiveId)

  def report_raw(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument",
                             "Cannot report raw value of a non-existent directive id",
                             argument=directiveId)
    return self.getDistinguishedTrace().extractRaw(directiveId)

  def clear(self):
    for trace in self.traces: del trace
    self.directiveCounter = 0
    self.directives = {}
    self.traces = [self.Trace()]
    self.weights = [1]
    self.ensure_rng_seeded_decently()

  def ensure_rng_seeded_decently(self):
    # Frobnicate the trace's random seed because Trace() resets the
    # RNG seed from the current time, which sucks if one calls this
    # method often.
    self.set_seed(random.randint(1,2**31-1))

  # TODO There should also be capture_inference_problem and
  # restore_inference_problem (Analytics seems to use something like
  # it)
  def reinit_inference_problem(self, num_particles=None):
    """Blow away all the traces and rebuild from the stored directives.

The goal is to resample from the prior.  May have the unfortunate
effect of renumbering the directives, if some had been forgotten."""
    worklist = sorted(self.directives.iteritems())
    self.clear()
    if num_particles is not None:
      self.infer("(resample %d)" % num_particles)
    for (_,dir) in worklist:
      self.replay(dir)

  def replay(self,directive):
    if directive[0] == "assume":
      self.assume(directive[1], directive[2])
    elif directive[0] == "observe":
      self.observe(directive[1], directive[2])
    elif directive[0] == "predict":
      self.predict(directive[1])
    else:
      assert False, "Unkown directive type found %r" % directive

  def incorporate(self):
    for i,trace in enumerate(self.traces):
      self.weights[i] += trace.makeConsistent()

  def infer(self,params=None):
    if params is None:
      params = {}
    self.set_default_params(params)

    self.incorporate()    
    if 'command' in params and params['command'] == "resample":
      P = params['particles']
      newTraces = [None for p in range(P)]
      for p in range(P):
        parent = sampleLogCategorical(self.weights) # will need to include or rewrite
        newTraces[p] = self.traces[parent].stop_and_copy()
        if self.name != "lite":
          newTraces[p].set_seed(random.randint(1,2**31-1))
      self.traces = newTraces
      self.weights = [0 for p in range(P)]

    elif 'command' in params and params['command'] == "incorporate": pass

    elif params['kernel'] == "cycle":
      if 'subkernels' not in params:
        raise Exception("Cycle kernel must have things to cycle over (%r)" % params)
      for _ in range(params["transitions"]):
        for k in params["subkernels"]:
          self.infer(k)
    elif params["kernel"] == "mixture":
      for _ in range(params["transitions"]):
        self.infer(simulateCategorical(params["weights"], params["subkernels"]))
    else: # A primitive infer expression
      #import pdb; pdb.set_trace()
      for trace in self.traces: trace.infer(params)
  
  # TODO put all inference param parsing in one place
  def set_default_params(self,params):
    if 'kernel' not in params:
      params['kernel'] = 'mh'
    if 'scope' not in params:
      params['scope'] = "default"
    if 'block' not in params:
      params['block'] = "one"
    if 'with_mutation' not in params:
      params['with_mutation'] = True
    if 'transitions' not in params:
      params['transitions'] = 1
    else:
      # FIXME: Kludge. If removed, test_infer (in
      # python/test/ripl_test.py) fails, and if params are printed,
      # you'll see a float for the number of transitions
      params['transitions'] = int(params['transitions'])
    
    if "particles" in params:
      params["particles"] = int(params["particles"])
    if "in_parallel" not in params:
      params['in_parallel'] = True
    if params['kernel'] in ['cycle', 'mixture']:
      if 'subkernels' not in params:
        params['subkernels'] = []
      if params['kernel'] == 'mixture' and 'weights' not in params:
        params['weights'] = [1 for _ in params['subkernels']]
      for p in params['subkernels']:
        self.set_default_params(p)
  
  def get_logscore(self, did): return self.getDistinguishedTrace().getDirectiveLogScore(did)
  def logscore(self): return self.getDistinguishedTrace().getGlobalLogScore()

  def get_entropy_info(self):
    return { 'unconstrained_random_choices' : self.getDistinguishedTrace().numRandomChoices() }

  def get_seed(self):
    return self.getDistinguishedTrace().get_seed() # TODO is this what we want?

  def set_seed(self, seed):
    self.getDistinguishedTrace().set_seed(seed) # TODO is this what we want?

  def continuous_inference_status(self):
    return self.getDistinguishedTrace().continuous_inference_status() # awkward

  def start_continuous_inference(self, params):
    self.set_default_params(params)
    for trace in self.traces: trace.start_continuous_inference(params)

  def stop_continuous_inference(self):
    for trace in self.traces: trace.stop_continuous_inference()

  def save(self, fname, extra=None):
    if extra is None:
      extra = {}
    extra['directives'] = self.directives
    extra['directiveCounter'] = self.directiveCounter
    return self.getDistinguishedTrace().save(fname, extra)

  def load(self, fname):
    trace, extra = self.Trace.load(fname)
    self.traces = [trace]
    self.directives = extra['directives']
    self.directiveCounter = extra['directiveCounter']
    return extra

  # TODO: Add methods to inspect/manipulate the trace for debugging and profiling
