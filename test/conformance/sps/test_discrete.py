from nose.tools import eq_
from venture.test.config import get_ripl

def testDirSmoke():
  yield checkDirSmoke1, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke2, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke1, "(dirichlet (array 3 3 3 3))"
  yield checkDirSmoke2, "(dirichlet (array 3 3 3 3))"

def checkDirSmoke1(form):
  eq_(get_ripl().predict("(is_simplex %s)" % form), True)

def checkDirSmoke2(form):
  eq_(get_ripl().predict("(size %s)" % form), 4)
