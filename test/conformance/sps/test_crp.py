from nose.tools import eq_
from venture.test.config import get_ripl

# TODO AXCH why is this a test? Why shouldn't it be legal to start at 0?
def testCRPSmoke():
  eq_(get_ripl().predict("((make_crp 1.0))"), 1)
