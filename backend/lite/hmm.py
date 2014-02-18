from sp import VentureSP,SPAux
from psp import PSP, RandomPSP, TypedPSP
from request import Request
import numpy as np
import numpy.random as npr
import math
from copy import copy
from value import NumberType, RequestType

def npSampleVector(pVec): return np.mat(npr.multinomial(1,np.array(pVec)[0,:]))
def npIndexOfOne(pVec): return np.where(pVec[0] == 1)[1][0,0]
def npMakeDiag(colvec): return np.diag(np.array(colvec)[:,0])
def npNormalizeVector(vec): return vec / np.sum(vec)

class HMMSPAux(SPAux):
  def __init__(self):
    super(HMMSPAux,self).__init__()
    self.xs = [] # [ x_n ],
    self.os = {} #  { n => [o_n1, ... ,o_nK] }

  def copy(self):
    ans = HMMSPAux()
    ans.xs = copy(self.xs)
    ans.os = {k:copy(v) for (k,v) in self.os.iteritems()}
    return ans

class MakeUncollapsedHMMOutputPSP(PSP):
  def simulate(self,args):
    (p0,T,O) = args.operandValues
    # p0 comes in as a simplex but needs to become a 1-row matrix
    p0 = np.mat([p0])
    # Transposition for compatibility with CXX
    return UncollapsedHMMSP(p0,np.transpose(T),np.transpose(O))

  def description(self,name):
    return "(%s <simplex> <matrix> <matrix>) -> <SP <number> <number>>\n  Discrete-state HMM of unbounded length with discrete observations.  The inputs are the probability distribution of the first state, the transition matrix, and the observation matrix.  It is an error if the dimensionalities do not line up.  Returns observations from the HMM encoded as a stochastic procedure that takes the time step and samples a new observation at that time step." % name

class UncollapsedHMMSP(VentureSP):
  def __init__(self,p0,T,O):
    req = TypedPSP([NumberType()], RequestType(), UncollapsedHMMRequestPSP())
    output = TypedPSP([NumberType()], NumberType(), UncollapsedHMMOutputPSP(O))
    super(UncollapsedHMMSP,self).__init__(req,output)
    self.p0 = p0
    self.T = T
    self.O = O

  def constructSPAux(self): return HMMSPAux()
  def constructLatentDB(self): return {} # { n => x_n }

  # lsr: the index of the observation needed
  def simulateLatents(self,aux,lsr,shouldRestore,latentDB):
    if not aux.xs:
      if shouldRestore: aux.xs.append(latentDB[0])
      else: aux.xs.append(npSampleVector(self.p0))

    for i in range(len(aux.xs),lsr+1):
      if shouldRestore: aux.xs.append(latentDB[i])
      else: aux.xs.append(npSampleVector(aux.xs[-1] * self.T))

    assert len(aux.xs) > lsr
    return 0
    
  def detachLatents(self,aux,lsr,latentDB):
    if len(aux.xs) == lsr + 1 and not lsr in aux.os:
      if not aux.os:
        for i in range(len(aux.xs)): latentDB[i] = aux.xs[i]
        del aux.xs[:]
      else:
        maxObservation = max(aux.os)
        for i in range(len(aux.xs)-1,maxObservation,-1):
          latentDB[i] = aux.xs.pop()
        assert len(aux.xs) == maxObservation + 1
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self,aux):
    if not aux.os: return

    # forward sampling
    fs = [self.p0]
    for i in range(1,len(aux.xs)):
      f = fs[i-1] * self.T
      if i in aux.os:
        for o in aux.os[i]: 
          f = f * npMakeDiag(self.O[:,o])
        
      fs.append(npNormalizeVector(f))

    # backwards sampling
    aux.xs[-1] = npSampleVector(fs[-1])
    for i in range(len(aux.xs) - 2,-1,-1):
      index = npIndexOfOne(aux.xs[i+1])
      T_i = npMakeDiag(self.T[:,index])
      gamma = npNormalizeVector(fs[i] * T_i)
      aux.xs[i] = npSampleVector(gamma)


class UncollapsedHMMOutputPSP(RandomPSP):

  def __init__(self,O): 
    super(UncollapsedHMMOutputPSP,self).__init__()
    self.O = O

  def simulate(self,args): 
    n = int(args.operandValues[0])
    return npIndexOfOne(npSampleVector(args.spaux.xs[n] * self.O))

  def logDensity(self,value,args):
    n = int(args.operandValues[0])
    assert len(args.spaux.xs) > n
    theta = args.spaux.xs[n] * self.O
    return math.log(theta[0,value])

  def incorporate(self,value,args):
    n = int(args.operandValues[0])
    if not n in args.spaux.os: args.spaux.os[n] = []
    args.spaux.os[n].append(value)

  def unincorporate(self,value,args):
    n = int(args.operandValues[0])
    del args.spaux.os[n][args.spaux.os[n].index(value)]
    if not args.spaux.os[n]: del args.spaux.os[n]

class UncollapsedHMMRequestPSP(PSP):
  def simulate(self,args): return Request([],[int(args.operandValues[0])])


##########################################

