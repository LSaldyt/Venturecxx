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

from nose.tools import eq_
from venture.test.config import get_ripl, on_inf_prim, gen_on_inf_prim, broken_in, collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

@gen_on_inf_prim("none")
def testDirSmoke():
  yield checkDirSmoke1, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke2, "(symmetric_dirichlet 3 4)"
  yield checkDirSmoke1, "(dirichlet (array 3 3 3 3))"
  yield checkDirSmoke2, "(dirichlet (array 3 3 3 3))"

def checkDirSmoke1(form):
  eq_(get_ripl().predict("(is_simplex %s)" % form), True)

def checkDirSmoke2(form):
  eq_(get_ripl().predict("(size %s)" % form), 4)

@on_inf_prim("none")
def testDirichletComparisonRegression():
  eq_(get_ripl().predict("(= (symmetric_dirichlet 3 2) (simplex 0.01 0.99))"), False) # As opposed to crashing

@broken_in('puma', "Puma does not define log_flip")
@statisticalTest
def testLogFlip():
  ripl = get_ripl()

  ripl.predict('(log_flip (log 0.5))', label='pid')

  predictions = collectSamples(ripl,'pid')
  ans = [(False,0.5),(True,0.5)]
  return reportKnownDiscrete(ans, predictions)

@on_inf_prim("none")
@broken_in('puma', "Puma does not accept the objects argument to Dirichlet categoricals.  Issue #430.")
def testDirMultSmoke():
  r = get_ripl()
  for form in ["(is_atom ((make_dir_mult (array 1 1 1))))",
               "(is_atom ((make_sym_dir_mult 3 2)))",
               "(is_atom ((make_uc_dir_mult (array 1 1 1))))",
               "(is_atom ((make_uc_sym_dir_mult 3 2)))",
               "(is_number ((make_dir_mult (array 1 1 1) (array 1 2 3))))",
               "(is_number ((make_sym_dir_mult 2 3 (array 1 2 3))))",
               "(is_number ((make_uc_dir_mult (array 1 1 1) (array 1 2 3))))",
               "(is_number ((make_uc_sym_dir_mult 2 3 (array 1 2 3))))",
             ]:
    eq_(r.sample(form), True)

def testCategoricalDensityWithDuplicates():
  eq_(get_ripl().evaluate("(assess 1 categorical (simplex 0.25 0.25 0.25 0.25) (array 1 2 3 1))"), math.log(0.5))
