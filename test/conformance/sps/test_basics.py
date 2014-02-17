import scipy.stats

from venture.test.config import get_ripl, collectSamples
from venture.test.stats import statisticalTest, reportKnownContinuous

def testEq():
  assert get_ripl().predict("(eq 1 1)")

def testCompare():
  assert get_ripl().predict("(<= 1 1)")
  assert get_ripl().predict("(< 1 2)")
  assert not get_ripl().predict("(> 1 2)")
  assert not get_ripl().predict("(>= 1 2)")

def testBasicCDFs():
  yield checkCDF, "(normal 1 1)", scipy.stats.norm(loc=1, scale=1).cdf
  yield checkCDF, "(uniform_continuous 0 1)", lambda x: x
  yield checkCDF, "(beta 1 1)", scipy.stats.beta(1, 1).cdf
  yield checkCDF, "(gamma 1 2)", scipy.stats.gamma(1, scale=1/2.0).cdf
  yield checkCDF, "(student_t 1)", scipy.stats.t(1).cdf

@statisticalTest
def checkCDF(expr, cdf):
  ripl = get_ripl()
  ripl.predict(expr)
  predictions = collectSamples(ripl, 1)
  return reportKnownContinuous(cdf, predictions, expr)
