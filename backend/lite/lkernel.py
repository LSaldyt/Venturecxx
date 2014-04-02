import numbers
from abc import ABCMeta, abstractmethod
from sp import VentureSP
from value import VentureValue
import sys
import math

class LKernel(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,trace,oldValue,args): pass
  def weight(self, _trace, _newValue, _oldValue, _args): return 0
  def reverseWeight(self,trace,oldValue,args):
    return self.weight(trace,oldValue,None,args)
  def gradientOfReverseWeight(self, _trace, _value, args): return (0, [0 for _ in args.operandValues])
  def weightBound(self, _trace, _newValue, _oldValue, _args):
    # An upper bound on the value of weight over the variation
    # possible by changing the values of everything in the arguments
    # whose value is None.  Useful for rejection sampling.
    raise Exception("Cannot rejection sample with weight-unbounded LKernel of type %s" % type(self))

class DefaultAAALKernel(LKernel):
  def __init__(self,makerPSP): self.makerPSP = makerPSP
  def simulate(self,trace,oldValue,args): return self.makerPSP.simulate(args)
  def weight(self,_trace,newValue,_oldValue,args):
    assert isinstance(newValue,VentureSP)
    return newValue.outputPSP.logDensityOfCounts(args.madeSPAux)
  def weightBound(self, _trace, _newValue, _oldValue, args):
    # Going through the maker here because the new value is liable to
    # be None when computing bounds for rejection, but the maker
    # should know enough about its possible values future to answer my
    # question.
    return self.makerPSP.madeSpLogDensityOfCountsBound(args.madeSPAux)

class DeterministicLKernel(LKernel):
  def __init__(self,psp,value):
    self.psp = psp
    self.value = value
    assert isinstance(value, VentureValue)

  def simulate(self,trace,oldValue,args): return self.value
  def weight(self, _trace, newValue, _oldValue, args):
    answer = self.psp.logDensity(newValue,args)
    assert isinstance(answer, numbers.Number)
    return answer
  def gradientOfReverseWeight(self, _trace, newValue, args):
    return self.psp.gradientOfLogDensity(newValue, args.operandValues)

######## Variational #########

class VariationalLKernel(LKernel):
  def gradientOfLogDensity(self, _value, _args): return 0
  def updateParameters(self,gradient,gain,stepSize): pass

class DefaultVariationalLKernel(VariationalLKernel):
  def __init__(self,psp,args):
    self.psp = psp
    self.parameters = args.operandValues
    self.parameterScopes = psp.getParameterScopes()

  def simulate(self,trace,oldValue,args):
    return self.psp.simulateNumeric(self.parameters)

  def weight(self, _trace, newValue, _oldValue, args):
    ld = self.psp.logDensityNumeric(newValue,args.operandValues)
    proposalLD = self.psp.logDensityNumeric(newValue,self.parameters)
    w = ld - proposalLD
    assert not math.isinf(w) and not math.isnan(w)
    return w

  def gradientOfLogDensity(self, value, _args):
    # Ignore the derivative of the value because we do not care about it
    (_, grad) = self.psp.gradientOfLogDensity(value, self.parameters)
    return grad

  def updateParameters(self,gradient,gain,stepSize):
    # TODO hacky numerical stuff
    minFloat = -sys.float_info.max
    maxFloat = sys.float_info.max
    for i in range(len(self.parameters)):
      self.parameters[i] += gradient[i] * gain * stepSize
      if self.parameters[i] < minFloat: self.parameters[i] = minFloat
      if self.parameters[i] > maxFloat: self.parameters[i] = maxFloat
      if self.parameterScopes[i] == "POSITIVE_REAL" and \
         self.parameters[i] < 0.1: self.parameters[i] = 0.1
      assert not math.isinf(self.parameters[i]) and not math.isnan(self.parameters[i])
