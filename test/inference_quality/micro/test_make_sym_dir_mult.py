# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from nose import SkipTest

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import gen_on_inf_prim
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.config import rejectionSampling
from venture.test.config import skipWhenRejectionSampling
from venture.test.config import skipWhenSubSampling
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

############## (1) Test SymDirMult AAA

#
@gen_on_inf_prim("any")
def testMakeSymDirMult1():
  for maker in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMult1, maker

@statisticalTest
def checkMakeSymDirMult1(maker):
  """Extremely simple program, with an AAA procedure when uncollapsed"""
  ripl = get_ripl()
  ripl.assume("f", "(%s 1.0 2)" % maker)
  ripl.predict("(f)", label="pid")
  predictions = collectSamples(ripl, "pid")
  ans = [(0, .5), (1, .5)]
  return reportKnownDiscrete(ans, predictions)

@gen_on_inf_prim("any")
def testMakeSymDirMultAAA():
  for maker in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMultAAA, maker

@statisticalTest
def checkMakeSymDirMultAAA(maker):
  """Simplest program with collapsed AAA"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker)
  ripl.predict("(f)", label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirMultFlip():
  """AAA where the SP flips between collapsed and uncollapsed."""
  for maker_1 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultFlip, maker_1, maker_2

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
def checkMakeSymDirMultFlip(maker_1, maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 4)" % (maker_1, maker_2))
  ripl.predict("(f)", label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirMultBrushObserves():
  """AAA where the SP flips between collapsed and uncollapsed, and
     there are observations in the brush."""
  for maker_1 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultBrushObserves, maker_1, maker_2

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
def checkMakeSymDirMultBrushObserves(maker_1, maker_2):
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "((if (lt a 10) %s %s) a 2)" % (maker_1, maker_2))
  ripl.predict("(f)", label="pid")

  return checkDirichletMultinomialBrush(ripl, "pid")

@skipWhenRejectionSampling("Observes resimulations of unknown code")
@skipWhenSubSampling(
  "The current implementation of subsampling can't handle this scaffold shape")
@statisticalTest
@on_inf_prim("any")
def testMakeSymDirMultNative():
  """AAA where the SP flips between collapsed, uncollapsed, and native"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
# Might be collapsed, uncollapsed, or uncollapsed in Venture
  ripl.assume("f", """
((if (lt a 9.5)
     make_sym_dir_mult
     (if (lt a 10.5)
         make_uc_sym_dir_mult
         (lambda (alpha k)
           ((lambda (theta) (lambda () (categorical theta)))
            (symmetric_dirichlet alpha k)))))
 a 4)
""")
  ripl.predict("(f)", label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirMultAppControlsFlip():
  for maker_1 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    for maker_2 in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
      yield checkMakeSymDirMultAppControlsFlip, maker_1, maker_2

@statisticalTest
def checkMakeSymDirMultAppControlsFlip(maker_1, maker_2):
  """Two AAA SPs with same parameters, where their applications control
which are applied"""
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s a 4)" % maker_1)
  ripl.assume("g", "(%s a 4)" % maker_2)
  ripl.predict("(f)", label="pid")
  ripl.predict("(g)")
  for _ in range(5): ripl.observe("(g)", "atom<1>")
  ripl.predict("(if (eq (f) atom<1>) (g) (g))")
  ripl.predict("(if (eq (g) atom<1>) (f) (f))")
  return checkDirichletMultinomialAAA(ripl, "pid", infer="mixes_slowly")

@gen_on_inf_prim("any")
def testMakeDirMult1():
  for maker in ["make_dir_mult", "make_uc_dir_mult"]:
    yield checkMakeDirMult1, maker

@statisticalTest
def checkMakeDirMult1(maker):
  if rejectionSampling() and maker == "make_dir_mult":
    raise SkipTest("Is the log density of counts bounded for "
                   "collapsed beta bernoulli?  Issue: "
                   "https://app.asana.com/0/9277419963067/10623454782852")
  ripl = get_ripl()

  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(%s (array a a a a))" % maker)
  ripl.predict("(f)", label="pid")
  return checkDirichletMultinomialAAA(ripl, "pid")

@gen_on_inf_prim("any")
def testMakeSymDirMultWeakPrior():
  for maker in ["make_sym_dir_mult", "make_uc_sym_dir_mult"]:
    yield checkMakeSymDirMultWeakPrior, maker

@statisticalTest
def checkMakeSymDirMultWeakPrior(maker):
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(%s a 2)" % maker)
  ripl.predict("(f)", label="pid")

  return checkDirichletMultinomialWeakPrior(ripl, "pid")


#### (2) Staleness

# This section should not hope to find staleness, since all backends should
# assert that a makerNode has been regenerated before applying it.
# Therefore this section should try to trigger that assertion.

@on_inf_prim("any")
@statisticalTest
def testStaleAAA_MSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)", label="pid")

  return checkDirichletMultinomialWeakPrior(ripl, "pid")

@on_inf_prim("any")
@statisticalTest
def testStaleAAA_CSP():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)", label="pid")

  return checkDirichletMultinomialWeakPrior(ripl, "pid")

@on_inf_prim("any")
@statisticalTest
@broken_in("puma",
           "Need to port records to Puma for references to work.  Issue #224")
def testStaleAAA_Madness():
  ripl = get_ripl()

  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("f2_maker", "(lambda () f)")
  ripl.assume("f2", "(f2_maker)")
  ripl.assume("xs", "(array (ref f) (ref f2))")
  ripl.assume("f3", "(deref (lookup xs 1))")
  ripl.assume("ys", """(dict (array (quote aaa) (quote bbb))
                             (array (ref f3) (ref f3)))""")
  ripl.assume("g", """(deref (if (flip) (lookup ys (quote aaa))
                                        (lookup ys (quote bbb))))""")
  ripl.predict("(g)", label="pid")

  return checkDirichletMultinomialWeakPrior(ripl, "pid")


#### Helpers

def checkDirichletMultinomialAAA(ripl, label, infer=None):
  for i in range(1, 4):
    for _ in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = collectSamples(ripl, label, infer=infer)
  ans = [(0, .1), (1, .3), (2, .3), (3, .3)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletMultinomialBrush(ripl, label):
  for _ in range(10): ripl.observe("(f)", "atom<1>")
  for _ in range(10): ripl.observe("""
(if (lt a 10.0)
  (f)
  (f))""", "atom<1>")

  predictions = collectSamples(ripl, label)
  ans = [(0, .25), (1, .75)]
  return reportKnownDiscrete(ans, predictions)

def checkDirichletMultinomialWeakPrior(ripl, label):
  for _ in range(8):
    ripl.observe("(f)", "atom<1>")

  predictions = collectSamples(ripl, label, infer="mixes_slowly")
  ans = [(1, .9), (0, .1)]
  return reportKnownDiscrete(ans, predictions)
