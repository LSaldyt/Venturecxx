# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

def isVariable(exp): return isinstance(exp,str)
def isSelfEvaluating(exp): return not isinstance(exp,list)

def isQuotation(exp):
  assert isinstance(exp,list)
  assert len(exp) > 0
  return exp[0] == "quote"

def quote(obj):
  return ["quote", obj]

def textOfQuotation(exp):
  assert len(exp) > 1
  return exp[1]

def isLambda(exp):
  assert isinstance(exp,list)
  assert len(exp) > 0
  return exp[0] == "make_csp"

def destructLambda(exp):
  import venture.lite.types as t
  assert isinstance(exp,list)
  assert len(exp) == 3
  assert isQuotation(exp[1])
  assert isQuotation(exp[2])
  params = t.ExpressionType().asPython(textOfQuotation(exp[1]))
  body = t.ExpressionType().asPython(textOfQuotation(exp[2]))
  return (params, body)

def getOperator(exp):
  assert isinstance(exp,list)
  assert len(exp) > 0
  return exp[0]

def getOperands(exp): return exp[1:]
