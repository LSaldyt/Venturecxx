# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import math

from nose.tools import assert_almost_equal
from scipy import stats

from venture.lite import types as t
from venture.lite.psp import LikelihoodFreePSP
from venture.lite.sp_help import typed_nr
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim

@on_inf_prim("none")
def test_global_logscore():
    ripl = get_ripl()
    for _ in range(100):
        ripl.observe('(flip (exactly 0.5))', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()[0]
    logscore_true = -100*math.log(2)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_global_logscore_coupled():
    ripl = get_ripl()
    ripl.assume('f', '(exactly (make_beta_bernoulli 1.0 1.0))')
    for _ in range(100):
        ripl.observe('(f)', 'true')
    ripl.infer('(incorporate)')
    logscore = ripl.get_global_logscore()[0]
    logscore_true = -math.log(101)
    assert_almost_equal(logscore, logscore_true)

@on_inf_prim("none")
def test_logscore_likelihood_free():
    "Shouldn't break in the presence of likelihood-free SP's"
    ripl = setup_likelihood_free()
    for _ in range(100):
        ripl.observe('(flip)', 'true')
    ripl.infer('(incorporate)')
    ripl.predict('(test1 0)')
    ripl.predict('(test2 0)')
    ripl.get_global_logscore()

def setup_likelihood_free():
    class TestPSP1(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues()[0]
            return x + stats.distributions.norm.rvs()
    tester1 = typed_nr(TestPSP1(), [t.NumberType()], t.NumberType())

    class TestPSP2(LikelihoodFreePSP):
        def simulate(self, args):
            x = args.operandValues()[0]
            return x + stats.distributions.bernoulli(0.5).rvs()
    tester2 = typed_nr(TestPSP2(), [t.NumberType()], t.NumberType())
    ripl = get_ripl()
    ripl.bind_foreign_sp('test1', tester1)
    ripl.bind_foreign_sp('test2', tester2)
    return ripl
