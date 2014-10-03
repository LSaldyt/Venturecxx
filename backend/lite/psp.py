from utils import override
from lkernel import DefaultAAALKernel,DefaultVariationalLKernel,LKernel
from request import Request
from exception import VentureBuiltinSPMethodError

class PSP(object):
  """A Primitive Stochastic Procedure.

  PSPs are the basic units of computation in Venture.  A PSP
  represents a (potentially) stochastic process that computes a value
  conditioned on some arguments (A PSP may instead compute a set of
  requests for further evaluation by Venture -- this is how compound
  Venture procedures are implemented -- but this is an advanced
  topic).

  The PSP interface is for people wishing to extend Venture with
  bindings to additional external computations (including traditional
  foreign functions, as well as things like a custom inference method
  for a particular model type).  Users of Venture who do not wish to
  extend it need not learn the PSP interface.

  The main part of the PSP interface is about providing information
  about the stochastic process the PSP represents -- simulating from
  it, computing log densities, etc.  Generally only the ability to
  simulate is required to define a valid PSP, but implementing the
  other methods may improve efficiency and/or permit the application
  of additional inference methods to scaffolds containing the PSP in
  question.

  The PSP interface also currently contains several methods used for
  the selection of lkernels, pending the invention of a better
  mechanism.  If you don't know what lkernels are, don't worry about
  it -- the defaults will do.

  The general pattern of PSP methods is that they accept an Args
  struct (and possibly some additional arguments) and compute
  something about the stochastic process at that Args struct.  The
  main thing the Args struct contains is the list of arguments this
  stochastic process is applied to, but it also has a bunch of
  additional contextual information that can be useful for special
  PSPs.  See node.py for the definition of Args.
  """

  def simulate(self, _args):
    """Simulate this process with the given parameters and return the result."""
    raise VentureBuiltinSPMethodError("Simulate not implemented!")

  def gradientOfSimulate(self, _args, _value, _direction):
    """Return the gradient of this PSP's simulation function.  This method
    is needed only for Hamiltonian Monte Carlo.

    Specifically, the gradient of the simulation function must be with
    respect to the given direction on the output space, at the point
    given by the args struct (the input space is taken to be the full
    list of parents).  In other words, the Jacobian-vector product

      direction^T J_simulate(args).

    For PSPs with one scalar output, the direction will be a number,
    and the correct answer is the gradient of simulate multiplied by
    that number.

    The gradient should be returned as a list of the partial
    derivatives with respect to each parent node represented in the
    args.

    We circumvent problems with trying to compute derivatives of
    stochastic functions by mixing over the randomness consumed.  What
    this practically means is that the gradient to be computed is the
    gradient of the deterministic function of the arguments that is
    this process, if its randomness is fixed at some particular stream
    of bits.  The gradient will, in general, depend on what those bits
    are.  Pending a better interface for communicating it, the value
    argument of this method is the value that simulating this PSP
    outputs when using the fixed randomness with respect to which the
    gradient is to be computed.  We hope that, for sufficiently simple
    PSPs, this proxy is sufficient.

    The exact circumstances when this method is needed for HMC are
    this PSP appearing as the operator of a non-principal,
    non-absorbing scaffold node (that is, in the non-principal part of
    the DRG, or in the brush).

    """
    raise VentureBuiltinSPMethodError("Cannot compute simulation gradient of %s", type(self))

  def isRandom(self):
    """Return whether this PSP is stochastic or not.  This is important
    because only nodes whose operators are random PSPs can be
    principal.

    """
    raise VentureBuiltinSPMethodError("Do not know whether %s is random", type(self))

  def canAbsorb(self, _trace, _appNode, _parentNode):
    """Return whether this PSP, which is the operator of the given
    application node, can absorb a change to the value of the given
    parent node.

    If this returns True, then logDensity must return a finite value
    for any proposed new value of the given parent node.  canAbsorb
    calls are assumed to be cumulative: if a PSP claims to be able to
    absorb changes to two of its parents individually, that amounts to
    claiming to absorb changes to both of them simultaneously.

    """
    raise VentureBuiltinSPMethodError("Do not know whether %s can absorb", type(self))

  def logDensity(self, _value, _args):
    """Return the log-density of simulating the given value from the given args.

    If the output space is discrete, return the log-probability.

    Note: Venture does *not* ensure that the given value actually was
    simulated from the given args.  The ability to measure the density
    of other values (or of the same value at other args) is invaluable
    for many inference methods.

    Implementing this method is not strictly necessary for a valid
    PSP, but is very helpful for many purposes if the density
    information is available.  See also canAbsorb."""
    raise VentureBuiltinSPMethodError("Cannot compute log density of %s", type(self))

  def gradientOfLogDensity(self, _value, _args):
    """Return the gradient of this PSP's logDensity function.  This method
    is needed only for gradient-based methods (currently Hamiltonian
    Monte Carlo and Meanfield).

    The gradient should be returned as a 2-tuple of the partial
    derivative with respect to the value and a list of the partial
    derivatives with respect to the arguments."""
    raise VentureBuiltinSPMethodError("Cannot compute gradient of log density of %s", type(self))

  def logDensityBound(self, _value, _args):
    """Return an upper bound on the possible log density of this PSP
    holding the given values fixed.  This method is needed only for
    rejection sampling.

    Specifically, the value and any or all of the operands present in
    the Args struct may be None.  Return an upper bound on the value
    the logDensity function could take for any values substituted for
    the None arguments, but holding fixed the given non-None
    arguments.  See NormalOutputPSP for an example implementation.

    This method is used only when this PSP is the operator of an
    absorbing node under rejection sampling.  Tighter upper bounds
    lead to more efficient rejection sampling.

    TODO maybe allow the logDensityBound to return None to indicate no
    bound, and in this case do not try to absorb at this node when
    doing rejection sampling?  Or should that be a separate method
    called logDensityBounded?"""
    raise VentureBuiltinSPMethodError("Cannot compute log density bound of %s", type(self))

  def incorporate(self,value,args):
    """Register that an application of this PSP produced the given value
    at the given args.  This is relevant only if the SP needs to
    maintain statistics about results of its applications (e.g., for
    collapsed models, or for external inference schemes that need to
    maintain statistics)."""
    pass

  def unincorporate(self,value,args):
    """Unregister one instance of an application of this PSP producing the
    given value at the given args.  This is the inverse of
    incorporate."""
    pass

  def canEnumerate(self):
    """Return whether this PSP can enumerate the space of its possible
    return values.  Enumeration is used only for principal nodes in
    enumerative Gibbs.

    """
    return False

  # Returns a Python list of VentureValue objects
  def enumerateValues(self, _args):
    """Return a list of all the values this PSP can return given the
    arguments.  Enumeration is used only for principal nodes in
    enumerative Gibbs.

    For enumerative Gibbs to work, logDensity must return a finite
    number for the probability of every value returned from this
    method, given the same arguments.

    """
    raise VentureBuiltinSPMethodError("Cannot enumerate")

  def reifyLatent(self):
    """
    Return latent state of PSP. Applies to uncollapsed PSP's, e.g.
    make_beta_bernoulli, for which the latent state is the value of the
    beta random variable.
    For PSP's with no latent state (the majority), simple return None.
    """
    return None

  def description(self, _name):
    """Return a string describing this PSP.  The string may include the
    name argument, which is the symbol that the enclosing SP is bound
    to.

    """
    return None

  def childrenCanAAA(self): return False
  def getAAALKernel(self): return DefaultAAALKernel(self)

  def hasVariationalLKernel(self): return False
  def getVariationalLKernel(self,args): return DefaultVariationalLKernel(self, args)

  def hasSimulationKernel(self): return False
  def hasDeltaKernel(self): return False

  def madeSpLogDensityOfCountsBound(self, _aux):
    raise VentureBuiltinSPMethodError("Cannot rejection sample AAA procedure with unbounded log density of counts")

class DeterministicPSP(PSP):
  """Provides good default implementations of PSP methods for deterministic PSPs."""
  @override(PSP)
  def isRandom(self): return False
  @override(PSP)
  def canAbsorb(self, _trace, _appNode, _parentNode): return False
  @override(PSP)
  def logDensity(self, _value, _args): return 0
  @override(PSP)
  def gradientOfLogDensity(self, _value, args):
    return (0, [0 for _ in args.operandValues])
  @override(PSP)
  def logDensityBound(self, _value, _args): return 0

class NullRequestPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self, _args): return Request()
  @override(PSP)
  def gradientOfSimulate(self, args, _value, _direction): return [0 for _ in args.operandValues]
  @override(DeterministicPSP)
  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class ESRRefOutputPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self,args):
    assert len(args.esrNodes) ==  1
    return args.esrValues[0]

  @override(PSP)
  def gradientOfSimulate(self, args, _value, direction):
    return [0 for _ in args.operandValues] + [direction]

  @override(DeterministicPSP)
  def gradientOfLogDensity(self, _value, args):
    return (0, [0 for _ in args.operandValues + args.esrNodes])

  @override(DeterministicPSP)
  def canAbsorb(self,trace,appNode,parentNode):
    return parentNode != trace.esrParentsAt(appNode)[0] and parentNode != appNode.requestNode

class RandomPSP(PSP):
  """Provides good default implementations of (two) PSP methods for stochastic PSPs."""
  @override(PSP)
  def isRandom(self): return True
  @override(PSP)
  def canAbsorb(self, _trace, _appNode, _parentNode): return True

class TypedPSP(PSP):
  def __init__(self, psp, f_type):
    self.f_type = f_type
    self.psp = psp

  def simulate(self,args):
    return self.f_type.wrap_return(self.psp.simulate(self.f_type.unwrap_args(args)))
  def gradientOfSimulate(self, args, value, direction):
    # TODO Should gradientOfSimulate unwrap the direction and wrap the
    # answers using the gradient_type, like gradientOfLogDensity does?
    # Or do I want to use the vector space structure of gradients
    # given by the Venture values inside the Python methods?
    return self.psp.gradientOfSimulate(self.f_type.unwrap_args(args), self.f_type.unwrap_return(value), direction)
  def logDensity(self,value,args):
    return self.psp.logDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def gradientOfLogDensity(self, value, args):
    (dvalue, dargs) = self.psp.gradientOfLogDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
    return (self.f_type.gradient_type().wrap_return(dvalue), self.f_type.gradient_type().wrap_arg_list(dargs))
  def logDensityBound(self, value, args):
    return self.psp.logDensityBound(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def incorporate(self,value,args):
    return self.psp.incorporate(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def unincorporate(self,value,args):
    return self.psp.unincorporate(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def enumerateValues(self,args):
    return [self.f_type.wrap_return(v) for v in self.psp.enumerateValues(self.f_type.unwrap_args(args))]
  def isRandom(self):
    return self.psp.isRandom()
  def canAbsorb(self,trace,appNode,parentNode):
    return self.psp.canAbsorb(trace, appNode, parentNode)

  def childrenCanAAA(self):
    return self.psp.childrenCanAAA()
  def getAAALKernel(self):
    return TypedLKernel(self.psp.getAAALKernel(), self.f_type)

  def canEnumerate(self): return self.psp.canEnumerate()

  def hasVariationalLKernel(self): return self.psp.hasVariationalLKernel()
  def getVariationalLKernel(self,args):
    return TypedVariationalLKernel(self.psp.getVariationalLKernel(self.f_type.unwrap_args(args)), self.f_type)

  def hasSimulationKernel(self): return self.psp.hasSimulationKernel()
  def hasDeltaKernel(self): return self.psp.hasDeltaKernel()
  def getDeltaKernel(self,args): return TypedLKernel(self.psp.getDeltaKernel(args),self.f_type)
  # TODO Wrap the simulation and delta kernels properly (once those are tested)

  def reifyLatent(self):
    latent = self.psp.reifyLatent()
    return self.f_type.wrap_latent(latent)

  def description(self,name):
    type_names = self.f_type.names()
    signature = "\n".join(["%s :: %s" % (name, variant) for variant in type_names])
    return signature + "\n" + self.psp.description(name)

  # TODO Is this method part of the psp interface?
  def logDensityOfCounts(self,aux):
    return self.psp.logDensityOfCounts(aux)

class TypedLKernel(LKernel):
  def __init__(self, kernel, f_type):
    self.kernel = kernel
    self.f_type = f_type

  def simulate(self, trace, oldValue, args):
    return self.f_type.wrap_return(self.kernel.simulate(trace, self.f_type.unwrap_return(oldValue),
                                                        self.f_type.unwrap_args(args)))
  def weight(self, trace, newValue, oldValue, args):
    return self.kernel.weight(trace, self.f_type.unwrap_return(newValue),
                              self.f_type.unwrap_return(oldValue),
                              self.f_type.unwrap_args(args))

  def reverseWeight(self, trace, oldValue, args):
    return self.kernel.reverseWeight(trace,
                                     self.f_type.unwrap_return(oldValue),
                                     self.f_type.unwrap_args(args))

  def weightBound(self, trace, newValue, oldValue, args):
    return self.kernel.weightBound(trace, self.f_type.unwrap_return(newValue),
                                   self.f_type.unwrap_return(oldValue),
                                   self.f_type.unwrap_args(args))

class TypedVariationalLKernel(TypedLKernel):
  def gradientOfLogDensity(self, value, args):
    return self.kernel.gradientOfLogDensity(self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
  def updateParameters(self, gradient, gain, stepSize):
    return self.kernel.updateParameters(gradient, gain, stepSize)
