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
from venture.shortcuts import *
import math
import pdb
import itertools

globalKernel = "meanfield";
globalUseGlobalScaffold = True;

def RIPL():
  return make_church_prime_ripl()

def normalizeList(seq):
  denom = sum(seq)
  if denom > 0: return [ float(x)/denom for x in seq]
  else: return [0 for x in seq]

def countPredictions(predictions, seq):
  return [predictions.count(x) for x in seq]

def rmsDifference(eps,ops): return math.sqrt(sum([ math.pow(x - y,2) for (x,y) in zip(eps,ops)]))

def printTest(testName,eps,ops):
  print "---Test: " + testName + "---"
  print "Expected: " + str(eps)
  print "Observed: " + str(ops)
  print "Root Mean Square Difference: " + str(rmsDifference(eps,ops))

def runAllTests(N):
  print "========= RunAllTests(N) ========"
  options = [ ("mh",False),
              ("mh",True),
              ("pgibbs",False),
              ("pgibbs",True),
              ("meanfield",False),
              ("meanfield",True),
              ("gibbs",False)]


  for i in range(len(options)):
    print "\n\n\n\n\n\n\n========= %d. (%s,%d) ========" % (i+1,options[i][0],options[i][1])
    global globalKernel
    global globalUseGlobalScaffold
    globalKernel = options[i][0]
    globalUseGlobalScaffold = options[i][1]
    runTests(N)

def loggingInfer(ripl,address,T):
  predictions = []
  for t in range(T):
    ripl.infer(10,kernel=globalKernel, use_global_scaffold=globalUseGlobalScaffold)
    predictions.append(ripl.report(address))
#    print predictions[len(predictions)-1]
  return predictions

def runTests(N):
  testBernoulli0(N)
  testBernoulli1(N)
  testCategorical1(N)
  testMHNormal0(N)
  testMHNormal1(N)
  testStudentT0(N)
  testMem0(N)
  testMem1(N)
  testMem2(N)
  testMem3(N)
  testSprinkler1(N)
  testSprinkler2(N)
  testGamma1(N)
  testIf1(N)
  testIf2(N)
  testBLOGCSI(N)
  testMHHMM1(N)
  testOuterMix1(N)
  testMakeSymDirMult1(N)
  testMakeSymDirMult2(N)
  testMakeUCSymDirMult1(N)
  testMakeDirMult1(N)
  testMakeBetaBernoulli1(N)
  testMap1(N)
  testMap2()
  testMap3()
  testMap4()
  testLazyHMM1(N)
  testLazyHMMSP1(N)
  testStaleAAA1(N)
  testStaleAAA2(N)
  testEval1(N)
  testEval2(N)
  testEval3(N)
  testApply1(N)
  testExtendEnv1(N)
  testList1()
  testHPYMem1(N)
  testGeometric1(N)
  testTrig1(N)
  testForget1()
  testForget2()
  testReferences1(N)
  testReferences2(N)
  testMemoizingOnAList()
  testOperatorChanging(N)
#  testObserveAPredict1(N)
#  testObserveAPredict2(N)
  testBreakMem(N)
  testHPYLanguageModel1(N) # fails
  testHPYLanguageModel2(N)
  testHPYLanguageModel3(N)
  testHPYLanguageModel4(N)
  testGoldwater1(N)

def runTests2(N):
  testGeometric1(N)



def testMakeCSP():
  ripl = RIPL()
  ripl.assume("f", "(lambda (x) (* x x))")
  ripl.predict("(f 1)")

  ripl.assume("g", "(lambda (x y) (* x y))")
  ripl.predict("(g 2 3)")

  ripl.assume("h", "(lambda () 5)")
  ripl.predict("(h)")

  print ripl.report(2)
  print ripl.report(4)
  print ripl.report(6)


def testBernoulli0(N):
  ripl = RIPL()
  ripl.assume("b", "((lambda () (bernoulli)))")
  ripl.predict("""
((biplex
  b
  (lambda () (normal 0.0 1.0))
  (lambda () ((lambda () (normal 10.0 1.0))))))
""");
  predictions = loggingInfer(ripl,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestBernoulli0---"
  print "(5.0," + str(mean) + ")"


def testBernoulli1(N):
  ripl = RIPL()
  ripl.assume("b", "((lambda () (bernoulli 0.7)))")
  ripl.predict("""
(branch
  b
  (lambda () (normal 0.0 1.0))
  (lambda () ((lambda () (normal 10.0 1.0)))))
""");
  predictions = loggingInfer(ripl,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestBernoulli1---"
  print "(3.0," + str(mean) + ")"

def testCategorical1(N):
  ripl = RIPL()
  ripl.assume("x", "(real (categorical 0.1 0.2 0.3 0.4))")
  ripl.assume("y", "(real (categorical 0.2 0.6 0.2))")
  ripl.predict("(plus x y)")

  predictions = loggingInfer(ripl,3,N)
  ps = [0.1 * 0.2,
        0.1 * 0.6 + 0.2 * 0.2,
        0.1 * 0.2 + 0.2 * 0.6 + 0.3 * 0.2,
        0.2 * 0.2 + 0.3 * 0.6 + 0.4 * 0.2,
        0.3 * 0.2 + 0.4 * 0.6,
        0.4 * 0.2]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4,5])) if N > 0 else [0 for x in range(6)]
  printTest("testCategorical1",ps,eps)

def testMHNormal0(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  ripl.predict("(normal a 1.0)")

  predictions = loggingInfer(ripl,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHNormal0---"
  print "(12.0," + str(mean) + ")"


def testMHNormal1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("b", "(normal a 1.0)")
  ripl.observe("((lambda () (normal b 1.0)))", 14.0)
  ripl.predict("""
(branch (lt a 100.0)
        (lambda () (normal (plus a b) 1.0))
        (lambda () (normal (times a b) 1.0)))
""")

  predictions = loggingInfer(ripl,4,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHNormal1---"
  print "(23.9," + str(mean) + ")"

def testStudentT0(N):
  # Modeled on testMHNormal0, but I do not know what the answer is
  # supposed to be.  However, the run not crashing says something.
  ripl = RIPL()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)")
  predictions = loggingInfer(ripl,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestStudentT0---"
  print "(2.3ish (regression)," + str(mean) + ")"

def testMem0(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (x) (bernoulli 0.5)))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.predict("(f (bernoulli 0.5))")
  ripl.infer(N, kernel="mh", use_global_scaffold=False)
  print "Passed TestMem0"


def testMem1(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("x","(f 1)")
  ripl.assume("y","(f 1)")
  ripl.assume("w","(f 2)")
  ripl.assume("z","(f 2)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = loggingInfer(ripl,7,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem1",ps,eps)

def testMem2(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((branch (bernoulli 0.5) (lambda () (lambda () 1)) (lambda () (lambda () 1)))))")
  ripl.assume("y","(g ((lambda () 0)))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = loggingInfer(ripl,8,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem2",ps,eps)

def testMem3(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (arg) (plus 1 (real (categorical 0.4 0.6)))))")
  ripl.assume("g","((lambda () (mem (lambda (y) (f (plus y 1))))))")
  ripl.assume("x","(f ((lambda () 1)))")
  ripl.assume("y","(g ((lambda () (branch (bernoulli 1.0) (lambda () 0) (lambda () 100)))))")
  ripl.assume("w","((lambda () (f 2)))")
  ripl.assume("z","(g 1)")
  ripl.assume("q","(plus 1 (real (categorical 0.1 0.9)))")
  ripl.predict('(plus x y w z q)');

  predictions = loggingInfer(ripl,8,N)
  ps = [0.4 * 0.4 * 0.1, 0.6 * 0.6 * 0.9]
  eps = [ float(x) / N for x in countPredictions(predictions, [5,10])] if N > 0 else [0,0]
  printTest("TestMem3",ps,eps)

def testSprinkler1(N):
  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(branch rain (lambda () (bernoulli 0.01)) (lambda () (bernoulli 0.4)))")
  ripl.assume("grassWet","""
(branch rain
(lambda () (branch sprinkler (lambda () (bernoulli 0.99)) (lambda () (bernoulli 0.8))))
(lambda () (branch sprinkler (lambda () (bernoulli 0.9)) (lambda () (bernoulli 0.00001)))))
""")
  ripl.observe("grassWet", True)

  predictions = loggingInfer(ripl,1,N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [True,False]))
  printTest("TestSprinkler1",ps,eps)

def testSprinkler2(N):
  # this test needs more iterations than most others, because it mixes badly
  N = N

  ripl = RIPL()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(bernoulli (branch rain (lambda () 0.01) (lambda () 0.4)))")
  ripl.assume("grassWet","""
(bernoulli (branch rain
(lambda () (branch sprinkler (lambda () 0.99) (lambda () 0.8)))
(lambda () (branch sprinkler (lambda () 0.9) (lambda () 0.00001)))))
""")
  ripl.observe("grassWet", True)

  predictions = loggingInfer(ripl,1,N)
  ps = [.3577,.6433]
  eps = normalizeList(countPredictions(predictions, [True,False]))
  printTest("TestSprinkler2 (mixes terribly)",ps,eps)

def testGamma1(N):
  ripl = RIPL()
  ripl.assume("a","(gamma 10.0 10.0)")
  ripl.assume("b","(gamma 10.0 10.0)")
  ripl.predict("(gamma a b)")

  predictions = loggingInfer(ripl,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHGamma1---"
  print "(1," + str(mean) + ")"

def testIf1(N):
  ripl = RIPL()
  ripl.assume('IF', '(lambda () branch)')
  ripl.assume('IF2', '(branch (bernoulli 0.5) IF IF)')
  ripl.predict('(IF2 (bernoulli 0.5) IF IF)')
  ripl.infer(N/10, kernel="mh", use_global_scaffold=False)
  print "Passed TestIf1()"

def testIf2(N):
  ripl = RIPL()
  ripl.assume('if1', '(branch (bernoulli 0.5) (lambda () branch) (lambda () branch))')
  ripl.assume('if2', '(branch (bernoulli 0.5) (lambda () if1) (lambda () if1))')
  ripl.assume('if3', '(branch (bernoulli 0.5) (lambda () if2) (lambda () if2))')
  ripl.assume('if4', '(branch (bernoulli 0.5) (lambda () if3) (lambda () if3))')
  ripl.infer(N/10, kernel="mh", use_global_scaffold=False)
  print "Passed TestIf2()"

def testBLOGCSI(N):
  ripl = RIPL()
  ripl.assume("u","(bernoulli 0.3)")
  ripl.assume("v","(bernoulli 0.9)")
  ripl.assume("w","(bernoulli 0.1)")
  ripl.assume("getParam","(lambda (z) (branch z (lambda () 0.8) (lambda () 0.2)))")
  ripl.assume("x","(bernoulli (branch u (lambda () (getParam w)) (lambda () (getParam v))))")

  predictions = loggingInfer(ripl,5,N)
  ps = [.596, .404]
  eps = normalizeList(countPredictions(predictions, [True, False]))
  printTest("TestBLOGCSI",ps,eps)


def testMHHMM1(N):
  ripl = RIPL()
  ripl.assume("f","""
(mem (lambda (i) (branch (eq i 0) (lambda () (normal 0.0 1.0)) (lambda () (normal (f (minus i 1)) 1.0)))))
""")
  ripl.assume("g","""
(mem (lambda (i) (normal (f i) 1.0)))
""")
  ripl.observe("(g 0)",1.0)
  ripl.observe("(g 1)",2.0)
  ripl.observe("(g 2)",3.0)
  ripl.observe("(g 3)",4.0)
  ripl.observe("(g 4)",5.0)
  ripl.predict("(f 4)")

  predictions = loggingInfer(ripl,8,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMHHMM1---"
  print "(4.3ish," + str(mean) + ")"

def testOuterMix1(N):
  ripl = RIPL()
  ripl.predict("""
(branch (bernoulli 0.5)
  (lambda ()
    (branch (bernoulli 0.5) (lambda () 2) (lambda () 3)))
  (lambda () 1))
""")

  predictions = loggingInfer(ripl,1,N)
  ps = [.5, .25,.25]
  eps = normalizeList(countPredictions(predictions, [1, 2, 3]))
  printTest("TestOuterMix1",ps,eps)


def testMakeSymDirMult1(N):
  ripl = RIPL()
  ripl.assume("f", "(make_sym_dir_mult 1.0 2)")
  ripl.predict("(f)")
  predictions = loggingInfer(ripl,2,N)
  ps = [.5, .5]
  eps = normalizeList(countPredictions(predictions, [0,1]))
  printTest("TestMakeSymDirMult1",ps,eps)


def testMakeSymDirMult2(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_sym_dir_mult a 4)")
  ripl.predict("(f)")

  for i in range(1,4):
    for j in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = loggingInfer(ripl,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeSymDirMult2",ps,eps)

def testMakeDirMult1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_dir_mult a a a a)")
  ripl.predict("(f)")

  for i in range(1,4):
    for j in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = loggingInfer(ripl,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeDirMult2",ps,eps)

def testMakeBetaBernoulli1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_beta_bernoulli a a)")
  ripl.predict("(f)")

  for j in range(20): ripl.observe("(f)", "true")

  predictions = loggingInfer(ripl,3,N)
  ps = [.25,.75]
  eps = normalizeList(countPredictions(predictions, [False,True]));
  printTest("TestMakeBetaBernoulli1",ps,eps)


def testMakeUCSymDirMult1(N):
  ripl = RIPL()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("f", "(make_uc_sym_dir_mult a 4)")
  ripl.predict("(f)")

  for i in range(1,4):
    for j in range(20):
      ripl.observe("(f)", "atom<%d>" % i)

  predictions = loggingInfer(ripl,3,N)
  ps = [.1,.3,.3,.3]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3]))
  printTest("TestMakeUCSymDirMult1",ps,eps)


def testLazyHMM1(N):
  N = N
  ripl = RIPL()
  ripl.assume("f","""
(mem
(lambda (i)
  (branch (eq i 0)
     (lambda () (bernoulli 0.5))
     (lambda () (branch (f (minus i 1))
                 (lambda () (bernoulli 0.7))
                 (lambda () (bernoulli 0.3)))))))
""")

  ripl.assume("g","""
(mem (lambda (i)
  (branch (f i)
     (lambda () (bernoulli 0.8))
     (lambda () (bernoulli 0.1)))))
""")

  ripl.observe("(g 1)",False)
  ripl.observe("(g 2)",False)
  ripl.observe("(g 3)",True)
  ripl.observe("(g 4)",False)
  ripl.observe("(g 5)",False)
  ripl.predict("(make_vector (f 0) (f 1) (f 2) (f 3) (f 4) (f 5))")

  # predictions = loggingInfer(ripl,8,N)
  # sums = [0 for i in range(6)]
  # for p in predictions: sums = [sums[i] + p[i] for i in range(6)]
  # ps = [.3531,.1327,.1796,.6925,.1796,.1327]
  # eps = [float(x) / N for x in sums] if N > 0 else [0 for x in sums]
  # printTest("testLazyHMM1 (mixes terribly)",ps,eps)

def testLazyHMMSP1(N):
  ripl = RIPL()
  ripl.assume("f","""
(make_lazy_hmm
  (make_vector 0.5 0.5)
  (make_vector
    (make_vector 0.7 0.3)
    (make_vector 0.3 0.7))
  (make_vector
    (make_vector 0.9 0.2)
    (make_vector 0.1 0.8)))
""");
  ripl.observe("(f 1)","atom<0>")
  ripl.observe("(f 2)","atom<0>")
  ripl.observe("(f 3)","atom<1>")
  ripl.observe("(f 4)","atom<0>")
  ripl.observe("(f 5)","atom<0>")
  ripl.predict("(f 6)")
  ripl.predict("(f 7)")
  ripl.predict("(f 8)")

  predictions = loggingInfer(ripl,7,N)
  ps = [0.6528, 0.3472]
  eps = normalizeList(countPredictions(predictions,[0,1]))
  printTest("testLazyHMMSP1",ps,eps)

def testStaleAAA1(N):
  ripl = RIPL()
  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(mem f)")
  ripl.assume("h", "g")
  ripl.predict("(h)")

  for i in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = loggingInfer(ripl,5,N)
  ps = [.9, .1]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestStaleAAA1",ps,eps)

def testStaleAAA2(N):
  ripl = RIPL()
  ripl.assume("a", "1.0")
  ripl.assume("f", "(make_uc_sym_dir_mult a 2)")
  ripl.assume("g", "(lambda () f)")
  ripl.assume("h", "(g)")
  ripl.predict("(h)")

  for i in range(9):
    ripl.observe("(f)", "atom<1>")

  predictions = loggingInfer(ripl,5,N)
  ps = [.9, .1]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestStaleAAA2",ps,eps)

def testMap1(N):
  ripl = RIPL()
  ripl.assume("x","(bernoulli 1.0)")
  ripl.assume("m","""(make_map (list (quote x) (quote y))
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("""(normal (plus
                           (map_lookup m (quote x))
                           (map_lookup m (quote y))
                           (map_lookup m (quote y)))
                         1.0)""")

  predictions = loggingInfer(ripl,3,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestMap1---"
  print "(20.0," + str(mean) + ")"

def testMap2():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list (quote x) (quote y))
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(map_contains m (quote x))",label="p1")
  ripl.predict("(map_contains m (quote y))",label="p2")
  ripl.predict("(map_contains m (quote z))",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")
  print "---Passed TestMap2---"

def testMap3():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list atom<1> atom<2>)
                               (list (normal 0.0 1.0) (normal 10.0 1.0)))""")
  ripl.predict("(map_contains m atom<1>)",label="p1")
  ripl.predict("(map_contains m atom<2>)",label="p2")
  ripl.predict("(map_contains m atom<3>)",label="p3")

  assert ripl.report("p1")
  assert ripl.report("p2")
  assert not ripl.report("p3")
  print "---Passed TestMap3---"

def testMap4():
  ripl = RIPL()
  ripl.assume("m","""(make_map (list (make_vector atom<1> atom<2>))
                               (list (normal 0.0 1.0)))""")
  ripl.predict("(map_contains m (make_vector atom<1> atom<2>))",label="p1")
  ripl.predict("(map_contains m atom<1>)",label="p2")
  ripl.predict("(map_contains m (make_vector atom<1>))",label="p3")

  assert ripl.report("p1")
  assert not ripl.report("p2")
  assert not ripl.report("p3")
  print "---Passed TestMap4---"

def testEval1(N):
  ripl = RIPL()
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","(quote (bernoulli 0.7))")
  ripl.predict("(eval exp globalEnv)")

  predictions = loggingInfer(ripl,3,N)
  ps = [.7, .3]
  eps = normalizeList(countPredictions(predictions, [1, 0]))
  printTest("TestEval1",ps,eps)

def testEval2(N):
  ripl = RIPL()
  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","""(quote
  (branch (bernoulli p)
        (lambda () (normal 10.0 1.0))
        (lambda () (normal 0.0 1.0)))
)""")

  ripl.assume("x","(eval exp globalEnv)")
  ripl.observe("x",11.0)

  predictions = loggingInfer(ripl,1,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestEval2---"
  print "(0.667," + str(mean) + ")"

def testEval3(N):
  ripl = RIPL()
  ripl.assume("p","(uniform_continuous 0.0 1.0)")
  ripl.assume("globalEnv","(get_current_environment)")
  ripl.assume("exp","""(quote
  (branch ((lambda () (bernoulli p)))
        (lambda () ((lambda () (normal 10.0 1.0))))
        (lambda () (normal 0.0 1.0)))
)""")

  ripl.assume("x","(eval exp globalEnv)")
  ripl.observe("x",11.0)

  predictions = loggingInfer(ripl,1,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestEval3---"
  print "(0.667," + str(mean) + ")"

def testApply1(N):
  ripl = RIPL()
  ripl.assume("apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.predict("(apply times (list (normal 10.0 1.0) (normal 10.0 1.0) (normal 10.0 1.0)))")

  predictions = loggingInfer(ripl,2,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestApply1---"
  print "(1000ish," + str(mean) + ")"


def testExtendEnv1(N):
  ripl = RIPL()
  ripl.assume("env1","(get_current_environment)")

  ripl.assume("env2","(extend_environment env1 (quote x) (normal 0.0 1.0))")
  ripl.assume("env3","(extend_environment env2 (quote x) (normal 10.0 1.0))")
  ripl.assume("exp","(quote (normal x 1.0))")
  ripl.predict("(normal (eval exp env3) 1.0)")

  predictions = loggingInfer(ripl,5,N)
  mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
  print "---TestExtendEnv1---"
  print "(10," + str(mean) + ")"



# TODO need extend_env, symbol?
def riplWithSTDLIB(ripl):
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (x) (x))")
  ripl.assume("venture_apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")
  ripl.assume("incremental_apply","""
(lambda (operator operands)
  (incremental_eval (deref (list_ref operator 3))

                    (extend_env env
				(deref (list_ref operator 2))
                                operands)))
""")
  ripl.assume("incremental_eval","""
(lambda (exp env)
  (branch
    (is_symbol exp)
    (quote (eval exp env))
    (quote
      (branch
        (not (is_pair exp))
        (quote exp)
        (branch
          (sym_eq (deref (list_ref exp 0)) (quote lambda))
	  (quote (pair env (rest exp)))
          (quote
            ((lambda (operator operands)
               (branch
                 (is_pair operator)
                 (quote (incremental_apply operator operands))
                 (quote (venture_apply operator operands))))
             (incremental_eval (deref (first exp)) env)
             (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp))))
)))))
""")
  return ripl

def testList1():
  ripl = RIPL()
  ripl.assume("x1","(list)")
  ripl.assume("x2","(pair 1.0 x1)")
  ripl.assume("x3","(pair 2.0 x2)")
  ripl.assume("x4","(pair 3.0 x3)")
  ripl.assume("f","(lambda (x) (times x x x))")
  ripl.assume("y4","(map_list f x4)")

  y4 = ripl.predict("(first y4)")
  y3 = ripl.predict("(list_ref y4 1)")
  y2 = ripl.predict("(list_ref (rest y4) 1)")
  px1 = ripl.predict("(is_pair x1)")
  px4 = ripl.predict("(is_pair x4)")
  py4 = ripl.predict("(is_pair y4)")

  assert(ripl.report(7) == 27.0);
  assert(ripl.report(8) == 8.0);
  assert(ripl.report(9) == 1.0);

  assert(not ripl.report(10));
  assert(ripl.report(11));
  assert(ripl.report(11));

  print "Passed TestList1()"

def loadPYMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
          (lambda () k)
          (lambda () (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha d)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem
    (lambda (k)
      (beta (minus 1 d)
            (plus alpha (times k d)))))))
""")

  ripl.assume("u_pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha d)))
""")

  ripl.assume("pymem","""
(lambda (alpha d base_dist)
  ((lambda (augmented_proc crp)
     (lambda () (augmented_proc (crp))))
   (mem (lambda (table) (base_dist)))
   (make_crp alpha d)))
""")

def loadDPMem(ripl):
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (branch (bernoulli (sticks k))
          (lambda () k)
          (lambda () (pick_a_stick sticks (plus k 1)))))
""")

  ripl.assume("make_sticks","""
(lambda (alpha)
  ((lambda (sticks) (lambda () (pick_a_stick sticks 1)))
   (mem
    (lambda (k)
      (beta 1 (plus alpha (times k k)))))))
""")

  ripl.assume("u_dpmem","""
(lambda (alpha base_dist)
  ((lambda (augmented_proc py)
     (lambda () (augmented_proc (py))))
   (mem (lambda (stick_index) (base_dist)))
   (make_sticks alpha)))
""")


def testDPMem1(N):
  ripl = RIPL()
  loadDPMem(ripl)

  ripl.assume("alpha","(uniform_continuous 0.1 20.0)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.5 0.5)))")
  ripl.assume("f","(u_dpmem alpha base_dist)")

  ripl.predict("(f)")
  ripl.predict("(f)")
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",1.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.observe("(normal (f) 1.0)",0.0)
  ripl.infer(N)

def observeCategories(ripl,counts):
  for i in range(len(counts)):
    for ct in range(counts[i]):
      ripl.observe("(normal (f) 1.0)",i)

def testCRP1(N,isCollapsed):
  ripl = RIPL()
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if isCollapsed: ripl.assume("f","(pymem alpha d base_dist)")
  else: ripl.assume("f","(u_pymem alpha d base_dist)")

  ripl.predict("(f)",label="pid")

  observeCategories(ripl,[2,2,5,1,0])

  predictions = loggingInfer(ripl,"pid",N)
  ps = normalizeList([3,3,6,2,1])
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4]))
  printTest("TestCRP1 (not exact)",ps,eps)

def loadHPY(ripl,topCollapsed,botCollapsed):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.1)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  if topCollapsed: ripl.assume("intermediate_dist","(pymem alpha d base_dist)")
  else: ripl.assume("intermediate_dist","(u_pymem alpha d base_dist)")
  if botCollapsed: ripl.assume("f","(pymem alpha d intermediate_dist)")
  else: ripl.assume("f","(u_pymem alpha d intermediate_dist)")

def loadPY(ripl):
  loadPYMem(ripl)
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0 0.0001)")
  ripl.assume("base_dist","(lambda () (real (categorical 0.2 0.2 0.2 0.2 0.2)))")
  ripl.assume("f","(u_pymem alpha d base_dist)")

def predictPY(N):
  ripl = RIPL()
  loadPY(ripl)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return loggingInfer(ripl,"pid",N)

def predictHPY(N,topCollapsed,botCollapsed):
  ripl = RIPL()
  loadHPY(ripl,topCollapsed,botCollapsed)
  ripl.predict("(f)",label="pid")
  observeCategories(ripl,[2,2,5,1,0])
  return loggingInfer(ripl,"pid",N)

def testHPYMem1(N):
  print "---TestHPYMem1---"
  for top in [False,True]:
    for bot in [False,True]:
      attempt = normalizeList(countPredictions(predictHPY(N,top,bot), [0,1,2,3,4]))
      print("(%s,%s): %s" % (top,bot,attempt))

def testGeometric1(N):
  ripl = RIPL()
  ripl.assume("alpha1","(gamma 5.0 2.0)")
  ripl.assume("alpha2","(gamma 5.0 2.0)")
  ripl.assume("p", "(beta alpha1 alpha2)")
  ripl.assume("geo","(lambda (p) (branch (bernoulli p) (lambda () 1) (lambda () (plus 1 (geo p)))))")
  ripl.predict("(geo p)",label="pid")

  predictions = loggingInfer(ripl,"pid",N)

  k = 7
  ps = [math.pow(2,-n) for n in range(1,k)]
  eps = normalizeList(countPredictions(predictions, range(1,k)))
  printTest("TestGeometric1",ps,eps)


def testTrig1(N):
  ripl = RIPL()
  ripl.assume("sq","(lambda (x) (* x x))")
  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("a","(sq (sin x))")
  ripl.assume("b","(sq (cos x))")
  ripl.predict("(+ a b)")
  for i in range(N/10):
    ripl.infer(10,kernel="mh",use_global_scaffold=False)
    assert abs(ripl.report(5) - 1) < .001
  print "Passed TestTrig1()"

def testForget1():
  ripl = RIPL()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id3")
  ripl.forget("id2")
  ripl.forget("id1")

def testForget2():
  ripl = RIPL()

  ripl.assume("x","(normal 0.0 1.0)")
  ripl.assume("f","(lambda (y) (normal y 1.0))")
  ripl.assume("g","(lambda (z) (normal z 2.0))")

  ripl.predict("(f 1.0)",label="id1")
  ripl.observe("(g 2.0)",3.0,label="id2")
  ripl.observe("(g 3.0)",3.0,label="id3")

  ripl.forget("id1")
  ripl.forget("id2")
  ripl.forget("id3")

  real_sivm = ripl.sivm.core_sivm.engine
  assert real_sivm.get_entropy_info()["unconstrained_random_choices"] == 1
  assert real_sivm.logscore() < 0

# This is the original one that fires an assert, when the (flip) has 0.0 or 1.0 it doesn't fail
def testReferences1(N):
  ripl = RIPL()
  ripl.assume("draw_type1", "(make_crp 1.0)")
  ripl.assume("draw_type0", "(if (flip) draw_type1 (lambda () 1))")
  ripl.assume("draw_type2", "(make_dir_mult 1 1)")
  ripl.assume("class", "(if (flip) (lambda (name) (draw_type0)) (lambda (name) (draw_type2)))")
  ripl.predict("(class 1)")
  ripl.predict("(flip)")
  predictions = loggingInfer(ripl,6,N)
  ps = normalizeList([0.5,0.5])
  eps = normalizeList(countPredictions(predictions, [True,False])) if N > 0 else [0 for i in ps]
  printTest("TestReferences1()",ps,eps)

#
def testReferences2(N):
  ripl = RIPL()
  ripl.assume("f", "(if (flip 0.5) (make_dir_mult 1 1) (lambda () 1))")
  ripl.predict("(f)")
#  ripl.predict("(flip)",label="pid")

  predictions = loggingInfer(ripl,2,N)
  ps = normalizeList([0.75,0.25])
  eps = normalizeList(countPredictions(predictions, [True,False])) if N > 0 else [0 for i in ps]
  printTest("TestReferences2()",ps,eps)

def testMemoizingOnAList():
  ripl = RIPL()
  ripl.assume("G","(mem (lambda (x) 1))")
  ripl.predict("(G (list 0))")
  print "Passed TestMemoizingOnAList()"

def testOperatorChanging(N):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda () (flip)))")
  ripl.assume("op1","(if (flip) flip (lambda () (f)))")
  ripl.assume("op2","(if (op1) op1 (lambda () (op1)))")
  ripl.assume("op3","(if (op2) op2 (lambda () (op2)))")
  ripl.assume("op4","(if (op3) op2 op1)")
  ripl.predict("(op4)")
  ripl.observe("(op4)",True)
  ripl.infer(N)
  print "Passed TestOperatorChanging()"

def testObserveAPredict0(N):
  ripl = RIPL()
  ripl.assume("f","(if (flip) (lambda () (flip)) (lambda () (flip)))")
  ripl.predict("(f)")
  ripl.observe("(f)","true")
  ripl.predict("(f)")
  predictions = loggingInfer(ripl,2,N)
  ps = normalizeList([0.75,0.25])
  eps = normalizeList(countPredictions(predictions, [True,False])) if N > 0 else [0 for i in ps]
  printTest("TestObserveAPredict0()",ps,eps)


### These tests are illegal Venture programs, and cause PGibbs to fail because
# when we detach for one slice, a node may think it owns its value, but then
# when we constrain we reclaim it and delete it, so it ends up getting deleted
# twice.

# def testObserveAPredict1(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip 0.0) (lambda () (flip)) (mem (lambda () (flip))))")
#   ripl.predict("(f)")
#   ripl.observe("(f)","true")
#   ripl.predict("(f)")
#   predictions = loggingInfer(ripl,2,N)
#   ps = normalizeList([0.75,0.25])
#   eps = normalizeList(countPredictions(predictions, [True,False])) if N > 0 else [0 for i in ps]
#   printTest("TestObserveAPredict1()",ps,eps)


# def testObserveAPredict2(N):
#   ripl = RIPL()
#   ripl.assume("f","(if (flip) (lambda () (normal 0.0 1.0)) (mem (lambda () (normal 0.0 1.0))))")
#   ripl.observe("(f)","1.0")
#   ripl.predict("(* (f) 100)")
#   predictions = loggingInfer(ripl,3,N)
#   mean = float(sum(predictions))/len(predictions) if len(predictions) > 0 else 0
#   print "---TestObserveAPredict2---"
#   print "(25," + str(mean) + ")"
#   print "(note: true answer is 50, but program is illegal and staleness is correct behavior)"


def testBreakMem(N):
  ripl = RIPL()
  ripl.assume("pick_a_stick","""
(lambda (sticks k)
  (if (bernoulli (sticks k))
      k
      (pick_a_stick sticks (plus k 1))))
""")
  ripl.assume("d","(uniform_continuous 0.4 0.41)")

  ripl.assume("f","(mem (lambda (k) (beta 1.0 (times k d))))")
  ripl.assume("g","(lambda () (pick_a_stick f 1))")
  ripl.predict("(g)")
  ripl.infer(N)

def testHPYLanguageModel1(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("G","""
(mem
  (lambda (context)
    (if (is_pair context)
        (pymem alpha d (G (rest context)))
        (pymem alpha d G_init))))
""")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((G (list %d)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list 0)))",label="pid")

  predictions = loggingInfer(ripl,"pid",N)
  ps = [0.03, 0.88, 0.03, 0.03, 0.03]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4])) if N > 0 else [0 for x in range(5)]
  printTest("testHPYLanguageModel1 (approximate)",ps,eps)

def testHPYLanguageModel2(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("H","(mem (lambda (a) (pymem alpha d G_init)))")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((H %d))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((H 0))",label="pid")

  predictions = loggingInfer(ripl,"pid",N)
  ps = [0.03, 0.88, 0.03, 0.03, 0.03]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4])) if N > 0 else [0 for x in range(5)]
  printTest("testHPYLanguageModel2 (approximate)",ps,eps)

def testHPYLanguageModel3(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("H","(mem (lambda (a) (pymem alpha d G_init)))")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((H atom<%d>))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((H atom<0>))",label="pid")

  predictions = loggingInfer(ripl,"pid",N)
  ps = [0.03, 0.88, 0.03, 0.03, 0.03]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4])) if N > 0 else [0 for x in range(5)]
  printTest("testHPYLanguageModel3 (approximate)",ps,eps)

def testHPYLanguageModel4(N):
  ripl = RIPL()
  loadPYMem(ripl)

  # 5 letters for now
  ripl.assume("G_init","(make_sym_dir_mult 0.5 5)")

  # globally shared parameters for now
  ripl.assume("alpha","(gamma 1.0 1.0)")
  ripl.assume("d","(uniform_continuous 0.0 0.01)")

  # G(letter1 letter2 letter3) ~ pymem(alpha,d,G(letter2 letter3))
  ripl.assume("G","""
(mem
  (lambda (context)
    (if (is_pair context)
        (pymem alpha d (G (rest context)))
        (pymem alpha d G_init))))
""")

  ripl.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")

  atoms = [0, 1, 2, 3, 4] * 4;

  for i in range(1,len(atoms)):
    ripl.observe("""
(noisy_true
  (atom_eq
    ((G (list atom<%d>)))
    atom<%d>)
  0.001)
""" % (atoms[i-1],atoms[i]), "true")

  ripl.predict("((G (list atom<0>)))",label="pid")

  predictions = loggingInfer(ripl,"pid",N)
  ps = [0.03, 0.88, 0.03, 0.03, 0.03]
  eps = normalizeList(countPredictions(predictions, [0,1,2,3,4])) if N > 0 else [0 for x in range(5)]
  printTest("testHPYLanguageModel4 (approximate)",ps,eps)


def testGoldwater1(N):
  v = RIPL()

  #brent = open("brent_ratner/br-phono.txt", "r").readlines()
  #brent = [b.strip().split() for b in brent]
  #brent = ["".join(i) for i in brent]
  #brent = ["aaa", "bbb", "aaa", "bbb"]
  #brent = brent[:2]
  #brent = "".join(brent)
#  brent = ["catanddog", "dogandcat", "birdandcat","dogandbird","birdcatdog"]
  brent = ["aba","ab"]

  iterations = 100
  parameter_for_dirichlet = 1
#  n = 2 #eventually implement option to set n
  alphabet = "".join(set("".join(list(itertools.chain.from_iterable(brent)))))
  d = {}
  for i in xrange(len(alphabet)): d[alphabet[i]] = i

  v.assume("parameter_for_dirichlet", str(parameter_for_dirichlet))
  v.assume("alphabet_length", str(len(alphabet)))

  v.assume("sample_phone", "(make_sym_dir_mult parameter_for_dirichlet alphabet_length)")
  v.assume("sample_word_id", "(make_crp 1.0)")

  v.assume("sample_letter_in_word", """
(mem
  (lambda (word_id pos)
    (sample_phone)))
""")
#7
  v.assume("is_end", """
(mem
  (lambda (word_id pos)
    (flip .3)))
""")

  v.assume("get_word_id","""
(mem
  (lambda (sentence sentence_pos)
    (branch (= sentence_pos 0)
        (lambda () (sample_word_id))
        (lambda ()
          (branch (is_end (get_word_id sentence (- sentence_pos 1)) (get_pos sentence (- sentence_pos 1)))
            (lambda () (sample_word_id))
            (lambda () (get_word_id sentence (- sentence_pos 1))))))))
""")

  v.assume("get_pos","""
(mem
  (lambda (sentence sentence_pos)
    (branch (= sentence_pos 0)
        (lambda () 0)
        (lambda ()
          (branch (is_end (get_word_id sentence (- sentence_pos 1)) (get_pos sentence (- sentence_pos 1)))
            (lambda () 0)
            (lambda () (+ (get_pos sentence (- sentence_pos 1)) 1)))))))
""")

  v.assume("sample_symbol","""
(mem
  (lambda (sentence sentence_pos)
    (sample_letter_in_word (get_word_id sentence sentence_pos) (get_pos sentence sentence_pos))))
""")

#  v.assume("noise","(gamma 1 1)")
  v.assume("noise",".01")
  v.assume("noisy_true","(lambda (pred noise) (flip (if pred 1.0 noise)))")


  for i in range(len(brent)): #for each sentence
    for j in range(len(brent[i])): #for each letter
      v.predict("(sample_symbol %d %d)" %(i, j))
      v.observe("(noisy_true (atom_eq (sample_symbol %d %d) atom<%d>) noise)" %(i, j,d[str(brent[i][j])]), "true")

  v.infer(N)
  print "Passed TestGoldwater1()"


def testMemHashFunction1(A,B):
  ripl = RIPL()
  ripl.assume("f","(mem (lambda (a b) (normal 0.0 1.0)))")
  for a in range(A):
    for b in range(B):
      ripl.observe("(f %d %d)" % (a,b),"0.5")
  print "Passed TestMemHashFunction(%d,%d)" % (A,B)


