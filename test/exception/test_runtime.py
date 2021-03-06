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

from nose.tools import raises

from venture.exception import VentureException
from venture.test.config import broken_in
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.errors import assert_ripl_annotation_succeeds

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testSymbolNotFound():
  ripl = get_ripl()
  assert_ripl_annotation_succeeds(ripl.predict, 'a')

# Not @broken_in('puma') because nowadays the Engine catches this as a label collision
@on_inf_prim("none")
@raises(VentureException)
def testDoubleAssume():
  ripl = get_ripl()
  ripl.assume('a', 1)
  ripl.assume('a', 1)

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testNoSPRef():
  ripl = get_ripl()
  assert_ripl_annotation_succeeds(ripl.predict, '(1 + 1)')

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testLambda():
  ripl = get_ripl()
  ripl.assume('err', '(lambda () a)')
  assert_ripl_annotation_succeeds(ripl.predict, '(err)')

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testLargeStack():
  ripl = get_ripl()
  ripl.assume('f', '(lambda (i) (if (= i 0) a (f (- i 1))))')
  assert_ripl_annotation_succeeds(ripl.predict, '(f 20)')

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testTooFewArgs():
  ripl = get_ripl()
  assert_ripl_annotation_succeeds(ripl.predict, '(-)')

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testTooManyArgs():
  ripl = get_ripl()
  assert_ripl_annotation_succeeds(ripl.predict, '(- 1 1 1)')

@broken_in('puma', "Puma does not report error addresses")
@on_inf_prim("none")
def testExceptionAnnotated():
  ripl = get_ripl()
  assert_ripl_annotation_succeeds(ripl.predict, 'a')
