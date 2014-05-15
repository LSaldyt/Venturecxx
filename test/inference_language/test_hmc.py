import math
import scipy.stats as stats
from nose import SkipTest
from testconfig import config
from venture.test.stats import statisticalTest, reportKnownContinuous, reportSameContinuous
from venture.test.config import get_ripl, collectSamples

@statisticalTest
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1,infer="(hmc default one 0.05 20 10)")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

def testMVGaussSmoke():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  yield checkMVGaussSmoke, "(mh default one 1)"
  yield checkMVGaussSmoke, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkMVGaussSmoke(infer):
  """Confirm that projecting a multivariate Gaussian to one dimension
  results in a univariate Gaussian."""
  ripl = get_ripl()
  ripl.assume("vec", "(multivariate_normal (array 1 2) (matrix (list (list 1 0.5) (list 0.5 1))))")
  ripl.assume("x", "(lookup vec 0)")
  predictions = collectSamples(ripl,2,infer=infer)
  cdf = stats.norm(loc=1, scale=1).cdf
  return reportKnownContinuous(cdf, predictions, "N(1,1)")

def testForceBrush1():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  yield checkForceBrush1, "(mh default one 2)"
  yield checkForceBrush1, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkForceBrush1(infer):
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.predict("(if (< x 100) (normal x 1) (normal 100 1))")
  predictions = collectSamples(ripl,2,infer=infer)
  cdf = stats.norm(loc=0, scale=math.sqrt(2)).cdf
  return reportKnownContinuous(cdf, predictions, "N(0,sqrt(2))")

def testForceBrush2():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  yield checkForceBrush2, "(mh default one 5)"
  yield checkForceBrush2, "(hmc default one 0.05 20 10)"

@statisticalTest
def checkForceBrush2(infer):
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.predict("(if (< x 0) (normal 0 1) (normal 100 1))")
  predictions = collectSamples(ripl,2,infer=infer)
  cdf = lambda x: 0.5*stats.norm(loc=0, scale=1).cdf(x) + 0.5*stats.norm(loc=100, scale=1).cdf(x)
  return reportKnownContinuous(cdf, predictions, "N(0,1)/2 + N(100,1)/2")

@statisticalTest
def testForceBrush3():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))")
  preds_mh = collectSamples(ripl, 2, infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reset()
  preds_hmc = collectSamples(ripl, 2, infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@statisticalTest
def testForceBrush4():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))")
  ripl.predict("(normal y 1)")
  preds_mh = collectSamples(ripl, 3, infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reset()
  preds_hmc = collectSamples(ripl, 3, infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@statisticalTest
def testForceBrush5():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.assume("y", "(if (< x 0) (normal x 1) (normal (+ x 10) 1))")
  ripl.observe("y", 8)
  preds_mh = collectSamples(ripl, 1, infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reset()
  preds_hmc = collectSamples(ripl, 1, infer="(hmc default one 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@statisticalTest
def testMoreElaborate():
  """Confirm that HMC still works in the presence of brush.  Do not,
  however, mess with the possibility that the principal nodes that HMC
  operates over may themselves be in the brush."""
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("x", "(scope_include (quote param) 0 (uniform_continuous -10 10))")
  ripl.assume("y", "(scope_include (quote param) 1 (uniform_continuous -10 10))")
  ripl.assume("xout", """
(if (< x 0)
    (normal x 1)
    (normal x 2))""")
  ripl.assume("out", "(multivariate_normal (array xout y) (matrix (list (list 1 0.5) (list 0.5 1))))")
  # TODO Unexpectedly serious problem: how to observe a data structure?
  # Can't observe coordinatewise because observe is not flexible
  # enough.  For this to work we would need observations of splits.
  # ripl.observe("(lookup out 0)", 0)
  # ripl.observe("(lookup out 1)", 0)
  # Can't observe through the ripl literally because the string
  # substitution (!) is not flexible enough.
  # ripl.observe("out", [0, 0])
  v = [{"type": "real", "value": 0}, {"type": "real", "value": 0}]
  ripl.sivm.execute_instruction({"instruction":"observe","expression":"out","value":{"type":"list","value":v}})

  preds_mh = collectSamples(ripl, 1, infer="(mh default one 10)")
  ripl.sivm.core_sivm.engine.reset()
  preds_hmc = collectSamples(ripl, 1, infer="(hmc param all 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)

@statisticalTest
def testMoveMatrix():
  if config["get_ripl"] != "lite": raise SkipTest("HMC only implemented in Lite.  Issue: https://app.asana.com/0/11192551635048/9277449877754")
  ripl = get_ripl()
  ripl.assume("mu", "(array 0 0)")
  ripl.assume("scale", "(matrix (list (list 2 1) (list 1 2)))")
  ripl.assume("sigma", "(wishart scale 4)")
  ripl.assume("out", "(multivariate_normal mu sigma)")
  v = [{"type": "real", "value": 1}, {"type": "real", "value": 1}]
  ripl.sivm.execute_instruction({"instruction":"observe","expression":"out","value":{"type":"list","value":v}})

  preds_mh = collectSamples(ripl, 3, infer="(mh default one 30)")
  ripl.sivm.core_sivm.engine.reset()
  preds_hmc = collectSamples(ripl, 3, infer="(hmc default all 0.1 20 10)")
  return reportSameContinuous(preds_mh, preds_hmc)
