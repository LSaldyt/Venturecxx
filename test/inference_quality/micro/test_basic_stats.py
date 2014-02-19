import math
import scipy.stats as stats
from nose import SkipTest

from venture.test.stats import statisticalTest, reportKnownContinuous, reportKnownMeanVariance, reportKnownDiscrete
from venture.test.config import get_ripl, collectSamples, collect_iid_samples

@statisticalTest
def testBernoulliIfNormal1():
  "A simple program with bernoulli, if, and normal applications in the brush"
  ripl = get_ripl()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(if b (normal 0.0 1.0) (normal 10.0 1.0))")
  predictions = collectSamples(ripl,2)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous(cdf, predictions, "0.3*N(0,1) + 0.7*N(10,1)")

@statisticalTest
def testBernoulliIfNormal2():
  "A simple program with bernoulli, if, and an absorbing application of normal"
  if not collect_iid_samples(): raise SkipTest("This test should not pass without reset.")

  ripl = get_ripl()
  ripl.assume("b", "(bernoulli 0.3)")
  ripl.predict("(normal (if b 0.0 10.0) 1.0)")
  predictions = collectSamples(ripl,2)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous(cdf, predictions, "0.3*N(0,1) + 0.7*N(10,1)")

@statisticalTest
def testNormalWithObserve1():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
#  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1)
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def testNormalWithObserve2a():
  "Checks the posterior distribution on a Gaussian given an unlikely observation.  The difference between this and 1 is an extra predict, which apparently has a deleterious effect on mixing."
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,1,infer="mixes_slowly")
  cdf = stats.norm(loc=12, scale=math.sqrt(0.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(0.5))")

@statisticalTest
def testNormalWithObserve2b():
  "Checks the posterior distribution on a Gaussian given an unlikely observation"
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.observe("(normal a 1.0)", 14.0)
  # Posterior for a is normal with mean 12, precision 2
  ripl.predict("(normal a 1.0)")

  predictions = collectSamples(ripl,3,infer="mixes_slowly")
  cdf = stats.norm(loc=12, scale=math.sqrt(1.5)).cdf
  return reportKnownContinuous(cdf, predictions, "N(12,sqrt(1.5))")

@statisticalTest
def testNormalWithObserve3():
  "Checks the posterior of a Gaussian in a Linear-Gaussian-BN"
  raise SkipTest("I do not know the right answer.  See issue https://app.asana.com/0/9277419963067/9797699085006")
  ripl = get_ripl()
  ripl.assume("a", "(normal 10.0 1.0)")
  ripl.assume("b", "(normal a 1.0)")
  # Prior for b is normal with mean 10, variance 2 (precision 1/2)
  ripl.observe("(normal b 1.0)", 14.0)
  # Posterior for b is normal with mean 38/3, precision 3/2 (variance 2/3)
  # Likelihood of a is normal with mean 0, variance 2 (precision 1/2)
  # Posterior for a is normal with mean 34/3, precision 3/2 (variance 2/3)
  ripl.predict("""
(if (lt a 100.0)
  (normal (plus a b) 1.0)
  (normal (times a b) 1.0))
""")

  predictions = collectSamples(ripl,4,infer="mixes_slowly")
  # Unfortunately, a and b are (anti?)correlated now, so the true
  # distribution of the sum is mysterious to me
  cdf = stats.norm(loc=24, scale=math.sqrt(7.0/3.0)).cdf
  return reportKnownContinuous(cdf, predictions, "approximately N(24,sqrt(7/3))")

@statisticalTest
def testStudentT1():
  "Simple program involving simulating from a student_t"
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  predictions = collectSamples(ripl,1)

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara, predictions)

@statisticalTest
def testStudentT2():
  "Simple program involving simulating from a student_t"
  ripl = get_ripl()
  ripl.assume("a", "(student_t 1.0)")
  ripl.observe("(normal a 1.0)", 3.0)
  ripl.predict("(normal a 1.0)")
  predictions = collectSamples(ripl,3,infer="mixes_slowly")

  # Posterior of a is proprtional to
  def postprop(a):
    return stats.t(1).pdf(a) * stats.norm(loc=3).pdf(a)
  import scipy.integrate as integrate
  (normalize,_) = integrate.quad(postprop, -10, 10)
  def posterior(a): return postprop(a) / normalize
  (meana,_) = integrate.quad(lambda x: x * posterior(x), -10, 10)
  (meanasq,_) = integrate.quad(lambda x: x * x * posterior(x), -10, 10)
  vara = meanasq - meana * meana
  return reportKnownMeanVariance(meana, vara + 1.0, predictions)


@statisticalTest
def testSprinkler1():
  "Classic Bayes-net example, with no absorbing when proposing to 'rain'"
  ripl = get_ripl()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(if rain (bernoulli 0.01) (bernoulli 0.4))")
  ripl.assume("grassWet","""
(if rain
  (if sprinkler (bernoulli 0.99) (bernoulli 0.8))
  (if sprinkler (bernoulli 0.9)  (bernoulli 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1)
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testSprinkler2():
  "Classic Bayes-net example, absorbing at 'sprinkler' when proposing to 'rain'"
  # this test needs more iterations than most others, because it mixes badly
  ripl = get_ripl()
  ripl.assume("rain","(bernoulli 0.2)")
  ripl.assume("sprinkler","(bernoulli (if rain 0.01 0.4))")
  ripl.assume("grassWet","""
(bernoulli
 (if rain
   (if sprinkler 0.99 0.8)
   (if sprinkler 0.9 0.00001)))
""")
  ripl.observe("grassWet", True)

  predictions = collectSamples(ripl,1,infer="mixes_slowly")
  ans = [(True, .3577), (False, .6433)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testBLOGCSI1():
  "Context-sensitive Bayes-net taken from BLOG examples"
  ripl = get_ripl()
  ripl.assume("u","(bernoulli 0.3)")
  ripl.assume("v","(bernoulli 0.9)")
  ripl.assume("w","(bernoulli 0.1)")
  ripl.assume("getParam","(lambda (z) (if z 0.8 0.2))")
  ripl.assume("x","(bernoulli (if u (getParam w) (getParam v)))")

  predictions = collectSamples(ripl,5)
  ans = [(True, .596), (False, .404)]
  return reportKnownDiscrete(ans, predictions)

@statisticalTest
def testGeometric1():
  "Geometric written with bernoullis and ifs, with absorbing at the condition."
  ripl = get_ripl()
  ripl.assume("p","(if (flip) 0.5 0.5)")
  ripl.assume("geo","(lambda (p) (if (bernoulli p) 1 (plus 1 (geo p))))")
  ripl.predict("(geo p)",label="pid")

  predictions = collectSamples(ripl,"pid")

  k = 128
  ans = [(n,math.pow(2,-n)) for n in range(1,k)]
  return reportKnownDiscrete(ans, predictions)
