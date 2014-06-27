from venture.test.config import get_ripl
from nose.tools import assert_equal, assert_less
import numpy as np

def testgetDirectiveLogScore():
    ripl = get_ripl()
    ripl.assume('x', '(scope_include (quote dummy) 0 (normal 0 1))', label="x")
    trace = ripl.sivm.core_sivm.engine.getDistinguishedTrace()
    # can't give string directive id for a trace; find number of
    # directive by label
    directive_id = ripl.sivm.label_dict["x"]
    logscore_venture = trace.getDirectiveLogScore(directive_id)
    val = ripl.report(directive_id)
    logscore_true = -0.5*np.log(2*np.pi) - 0.5*val*val

    assert_equal(logscore_venture, logscore_true)
