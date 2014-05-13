import math
import scipy.stats as stats
from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples, ignore_inference_quality
from nose import SkipTest
from testconfig import config

def testPGibbsBlockingMHHMM1():
  yield checkPGibbsBlockingMHHMM1, True
  yield checkPGibbsBlockingMHHMM1, False

@statisticalTest
def checkPGibbsBlockingMHHMM1(mutate):
  """The point of this is that it should give reasonable results in very few transitions but with a large number of particles."""
  ripl = get_ripl()

  ripl.assume("x0","(scope_include 0 0 (normal 0.0 1.0))")
  ripl.assume("x1","(scope_include 0 1 (normal x0 1.0))")
  ripl.assume("x2","(scope_include 0 2 (normal x1 1.0))")
  ripl.assume("x3","(scope_include 0 3 (normal x2 1.0))")
  ripl.assume("x4","(scope_include 0 4 (normal x3 1.0))")

  ripl.assume("y0","(normal x0 1.0)")
  ripl.assume("y1","(normal x1 1.0)")
  ripl.assume("y2","(normal x2 1.0)")
  ripl.assume("y3","(normal x3 1.0)")
  ripl.assume("y4","(normal x4 1.0)")

  ripl.observe("y0",1.0)
  ripl.observe("y1",2.0)
  ripl.observe("y2",3.0)
  ripl.observe("y3",4.0)
  ripl.observe("y4",5.0)
  ripl.predict("x4",label="pid")

  if ignore_inference_quality():
    infer = {"kernel":"pgibbs","transitions":2,"scope":0,"block":"ordered","particles":3, "with_mutation":mutate}
  else:
    infer = {"kernel":"pgibbs","transitions":10,"scope":0,"block":"ordered","particles":20, "with_mutation":mutate}

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(4.382, 0.786)")


def testPGibbsDynamicScope1():
  yield checkPGibbsDynamicScope1, True
  yield checkPGibbsDynamicScope1, False

@statisticalTest
def checkPGibbsDynamicScope1(mutate):
  ripl = get_ripl()
  
  ripl.assume("transition_fn", "(lambda (x) (normal x 1.0))")
  ripl.assume("observation_fn", "(lambda (y) (normal y 1.0))")

  ripl.assume("initial_state_fn", "(lambda () (normal 0.0 1.0))")
  ripl.assume("f","""
(mem (lambda (t)
  (scope_include 0 t (if (= t 0) (initial_state_fn) (transition_fn (f (- t 1)))))))
""")  

  ripl.assume("g","(mem (lambda (t) (observation_fn (f t))))")

  ripl.observe("(g 0)",1.0)
  ripl.observe("(g 1)",2.0)
  ripl.observe("(g 2)",3.0)
  ripl.observe("(g 3)",4.0)
  ripl.observe("(g 4)",5.0)

  ripl.predict("(f 4)","pid")

  if ignore_inference_quality():
    infer = {"kernel":"pgibbs","transitions":2,"scope":0,"block":"ordered","particles":3, "with_mutation":mutate}
  else:
    infer = {"kernel":"pgibbs","transitions":10,"scope":0,"block":"ordered","particles":20, "with_mutation":mutate}

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(4.382, 0.786)")

@statisticalTest
def testPGibbsDynamicScopeInterval():
  ripl = get_ripl()

  ripl.assume("transition_fn", "(lambda (x) (normal x 1.0))")
  ripl.assume("observation_fn", "(lambda (y) (normal y 1.0))")

  ripl.assume("initial_state_fn", "(lambda () (normal 0.0 1.0))")
  ripl.assume("f","""
(mem (lambda (t)
  (scope_include 0 t (if (= t 0) (initial_state_fn) (transition_fn (f (- t 1)))))))
""")  

  ripl.assume("g","(mem (lambda (t) (observation_fn (f t))))")

  ripl.observe("(g 0)",1.0)
  ripl.observe("(g 1)",2.0)
  ripl.observe("(g 2)",3.0)
  ripl.observe("(g 3)",4.0)
  ripl.observe("(g 4)",5.0)

  ripl.predict("(f 4)","pid")

  P = 3 if ignore_inference_quality() else 8
  T = 2 if ignore_inference_quality() else 10

  infer = "(cycle ((pgibbs 0 (ordered_range 0 3) %d %d) (pgibbs 0 (ordered_range 1 4) %d %d)) 1)" % (P,P,T,T)

  predictions = collectSamples(ripl,"pid",infer=infer)
  cdf = stats.norm(loc=390/89.0, scale=math.sqrt(55/89.0)).cdf
  return reportKnownContinuous(cdf, predictions, "N(4.382, 0.786)")

def testFunnyHMM():
  ripl = get_ripl()
  
  ripl.assume("hypers", "(mem (lambda (t) (scope_include 0 t (normal 0 1))))")
  ripl.assume("init", "0")
  ripl.assume("next", "(lambda (state delta) (+ state delta))")
  ripl.assume("get_state",
    """(mem (lambda (t)
          (if (= t 0) init
            (next (get_state (- t 1)) (hypers t)))))""")
  ripl.assume("obs", "(mem (lambda (t) (normal (get_state t) 1)))")
  
  for t in range(1, 5):
    ripl.observe("(obs %d)" % t, t)
  
  ripl.infer({"kernel":"pgibbs","transitions":2,"scope":0,"block":"ordered","particles":3, "with_mutation":False})

