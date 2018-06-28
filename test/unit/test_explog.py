# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from nose.tools import assert_raises

from venture.lite.utils import exp
from venture.lite.utils import expm1
from venture.lite.utils import log
from venture.lite.utils import log1p
from venture.lite.utils import logsumexp
from venture.lite.utils import xlogx

def relerr(expected, actual):
  if expected == 0:
    return 0 if actual == 0 else 1
  else:
    return abs((actual - expected)/expected)

def test_log():
  inf = float('inf')
  nan = float('nan')
  assert log(0) == -inf
  assert log(1) == 0
  assert relerr(1, log(2.718281828)) < 1e-8
  assert log(+inf) == +inf
  assert math.isnan(log(nan))

def test_log1p():
  inf = float('inf')
  nan = float('nan')
  assert log1p(-1) == -inf
  assert log1p(0) == 0
  assert relerr(1, log1p(1.718281828)) < 1e-8
  assert log1p(+inf) == +inf
  assert relerr(1e-20, log1p(1e-20)) < 1e-16
  assert math.isnan(log1p(nan))

def test_exp():
  inf = float('inf')
  nan = float('nan')
  assert exp(-inf) == 0
  assert exp(0) == 1
  assert relerr(2.718281828, exp(1)) < 1e-8
  assert exp(+inf) == +inf
  assert math.isnan(exp(nan))

def test_expm1():
  inf = float('inf')
  nan = float('nan')
  assert expm1(-inf) == -1
  assert expm1(0) == 0
  assert relerr(1.718281828, expm1(1)) < 1e-8
  assert expm1(+inf) == +inf
  assert relerr(1e-20, expm1(1e-20)) < 1e-16
  assert math.isnan(expm1(nan))

def test_xlogx():
  inf = float('inf')
  nan = float('nan')
  assert_raises(ValueError, lambda: xlogx(-inf))
  assert_raises(ValueError, lambda: xlogx(-1))
  assert xlogx(+inf) == +inf
  assert xlogx(0) == 0
  assert xlogx(1) == 0
  assert relerr(2.718281828, xlogx(2.718281828)) < 1e-8
  assert math.isnan(xlogx(nan))

def test_logsumexp():
  inf = float('inf')
  nan = float('nan')
  assert_raises(OverflowError,
    lambda: math.log(sum(map(math.exp, list(range(1000))))))
  assert relerr(999.4586751453871, logsumexp(list(range(1000)))) < 1e-15
  assert logsumexp([]) == -inf
  assert logsumexp([-1000.]) == -1000.
  assert logsumexp([-1000., -1000.]) == -1000. + math.log(2.)
  assert relerr(math.log(2.), logsumexp([0., 0.])) < 1e-15
  assert logsumexp([-inf, 1]) == 1
  assert logsumexp([-inf, -inf]) == -inf
  assert logsumexp([+inf, +inf]) == +inf
  assert math.isnan(logsumexp([-inf, +inf]))
  assert math.isnan(logsumexp([nan, inf]))
  assert math.isnan(logsumexp([nan, -3]))
