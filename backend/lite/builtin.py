import math
import numpy as np

from sp import VentureSP, SPType
from psp import NullRequestPSP, ESRRefOutputPSP, DeterministicPSP, TypedPSP

import discrete
import dirichlet
import continuous
import csp
import crp
import cmvn
import msp
import hmm
import conditionals
import scope
import eval_sps
import value as v
import env

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def no_request(output): return VentureSP(NullRequestPSP(), output)

def esr_output(request): return VentureSP(request, ESRRefOutputPSP())

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(output, SPType(args_types, return_type, **kwargs)))

def func_psp(f, descr=None, sim_grad=None):
  class FunctionPSP(DeterministicPSP):
    def __init__(self, descr):
      self.descr = descr
      self.sim_grad = sim_grad
      if self.descr is None:
        self.descr = "deterministic %s"
    def simulate(self,args):
      return f(args)
    def gradientOfSimulate(self, args, _value, direction):
      # Don't need the value if the function is deterministic, because
      # it consumes no randomness.
      if self.sim_grad:
        return self.sim_grad(args, direction)
      else:
        raise Exception("Cannot compute simulation gradient of %s", self.descr)
    def description(self,name):
      return self.descr % name
  return FunctionPSP(descr)

def typed_func_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(func_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def typed_func(*args, **kwargs):
  return no_request(typed_func_psp(*args, **kwargs))

# TODO This should actually be named to distinguish it from the
# previous version, which accepts the whole args object (where this
# one splats the operand values).
def deterministic_psp(f, descr=None, sim_grad=None):
  def new_grad(args, direction):
    return sim_grad(args.operandValues, direction)
  return func_psp(lambda args: f(*args.operandValues), descr, sim_grad=(new_grad if sim_grad else None))

def deterministic_typed_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(deterministic_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def deterministic(f, descr=None, sim_grad=None):
  return no_request(deterministic_psp(f, descr, sim_grad))

def deterministic_typed(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr, sim_grad), args_types, return_type, **kwargs)

def binaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType(), descr=descr)

def binaryNumS(output):
  return typed_nr(output, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), descr=descr)

def unaryNumS(f):
  return typed_nr(f, [v.NumberType()], v.NumberType())

def naryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), variadic=True, sim_grad=sim_grad, descr=descr)

def zero_gradient(args, _direction):
  return [0 for _ in args]

def binaryPred(f, descr=None):
  return deterministic_typed(f, [v.AnyType(), v.AnyType()], v.BoolType(), sim_grad=zero_gradient, descr=descr)

def type_test(t):
  return deterministic_typed(lambda thing: thing in t, [v.AnyType()], v.BoolType(),
                             sim_grad = zero_gradient,
                             descr="%s returns true iff its argument is a " + t.name())

def grad_times(args, direction):
  assert len(args) == 2, "Gradient only available for binary multiply"
  return [direction*args[1], direction*args[0]]

def builtInSPsList():
  return [ [ "add",  naryNum(lambda *args: sum(args),
                              sim_grad=lambda args, direction: [direction for _ in args],
                              descr="%s returns the sum of all its arguments") ],
           [ "sub", binaryNum(lambda x,y: x - y,
                                "%s returns the difference between its first and second arguments") ],
           [ "mul", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1),
                              sim_grad=grad_times,
                              descr="%s returns the product of all its arguments") ],           
           [ "div",   binaryNum(lambda x,y: x / y,
                                "%s returns the quotient of its first argument by its second") ],
           [ "eq",    binaryPred(lambda x,y: x.compare(y) == 0,
                                 descr="%s compares its two arguments for equality") ],
           [ "gt",    binaryPred(lambda x,y: x.compare(y) >  0,
                                 descr="%s returns true if its first argument compares greater than its second") ],
           [ "gte",   binaryPred(lambda x,y: x.compare(y) >= 0,
                                 descr="%s returns true if its first argument compares greater than or equal to its second") ],
           [ "lt",    binaryPred(lambda x,y: x.compare(y) <  0,
                                 descr="%s returns true if its first argument compares less than its second") ],
           [ "lte",   binaryPred(lambda x,y: x.compare(y) <= 0,
                                 descr="%s returns true if its first argument compares less than or equal to its second") ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic_typed(lambda x:x, [v.AtomType()], v.NumberType(),
                                          "%s returns the identity of its argument atom as a number") ],
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [v.AtomType(), v.AtomType()], v.BoolType(),
                                            "%s tests its two arguments, which must be atoms, for equality") ],

           [ "sin", unaryNum(math.sin, "Returns the %s of its argument") ],
           [ "cos", unaryNum(math.cos, "Returns the %s of its argument") ],
           [ "tan", unaryNum(math.tan, "Returns the %s of its argument") ],
           [ "hypot", binaryNum(math.hypot, "Returns the %s of its arguments") ],
           [ "exp", unaryNum(math.exp, "Returns the %s of its argument") ],
           [ "log", unaryNum(math.log, "Returns the %s of its argument") ],
           [ "pow", binaryNum(math.pow, "%s returns its first argument raised to the power of its second argument") ],
           [ "sqrt", unaryNum(math.sqrt, "Returns the %s of its argument") ],

           [ "not", deterministic_typed(lambda x: not x, [v.BoolType()], v.BoolType(),
                                        "%s returns the logical negation of its argument") ],

           [ "is_symbol", type_test(v.SymbolType()) ],
           [ "is_atom", type_test(v.AtomType()) ],

           [ "list", deterministic_typed(lambda *args: args, [v.AnyType()], v.ListType(), variadic=True,
                                         descr="%s returns the list of its arguments") ],
           [ "pair", deterministic_typed(lambda a,d: (a,d), [v.AnyType(), v.AnyType()], v.PairType(),
                                         descr="%s returns the pair whose first component is the first argument and whose second component is the second argument") ],
           [ "is_pair", type_test(v.PairType()) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType(),
                                          "%s returns the first component of its argument pair") ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType(),
                                         "%s returns the second component of its argument pair") ],
           [ "second", deterministic_typed(lambda p: p[1].first, [v.PairType(second_type=v.PairType())], v.AnyType(),
                                           "%s returns the first component of the second component of its argument") ],


           [ "array", deterministic_typed(lambda *args: np.array(args), [v.AnyType()], v.ArrayType(), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="%s returns an array initialized with its arguments") ],

           [ "vector", deterministic_typed(lambda *args: np.array(args), [v.AnyType()], v.ArrayType(), variadic=True,
                                          sim_grad=lambda args, direction: direction.getArray(),
                                          descr="%s currently a pseudonym for array") ],

           [ "is_array", type_test(v.ArrayType()) ],
           [ "dict", deterministic_typed(lambda keys, vals: dict(zip(keys, vals)),
                                         [v.HomogeneousListType(v.AnyType("k")), v.HomogeneousListType(v.AnyType("v"))],
                                         v.HomogeneousDictType(v.AnyType("k"), v.AnyType("v")),
                                         descr="%s returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length.") ],
           [ "is_dict", type_test(v.DictType()) ],
           [ "matrix", deterministic_typed(np.array,
                                           [v.HomogeneousListType(v.HomogeneousListType(v.NumberType()))],
                                           v.MatrixType(),
                                           "%s returns a matrix formed from the given list of rows.  It is an error if the given list is not rectangular.") ],
           [ "is_matrix", type_test(v.MatrixType()) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [v.ProbabilityType()], v.SimplexType(), variadic=True,
                                            descr="%s returns the simplex point given by its argument coordinates.") ],
           [ "is_simplex", type_test(v.SimplexType()) ],

           [ "lookup", deterministic_typed(lambda xs, x: xs.lookup(x),
                                           [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v")), v.AnyType("k")],
                                           v.AnyType("v"),
                                           sim_grad=lambda args, direction: [args[0].lookup_grad(args[1], direction), 0],
                                           descr="%s looks the given key up in the given mapping and returns the result.  It is an error if the key is not in the mapping.  Lists and arrays are viewed as mappings from indices to the corresponding elements.  Environments are viewed as mappings from symbols to their values.") ],
           [ "contains", deterministic_typed(lambda xs, x: xs.contains(x),
                                             [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v")), v.AnyType("k")],
                                             v.BoolType(),
                                             descr="%s reports whether the given key appears in the given mapping or not.") ],
           [ "size", deterministic_typed(lambda xs: xs.size(),
                                         [v.HomogeneousMappingType(v.AnyType("k"), v.AnyType("v"))],
                                         v.NumberType(),
                                         "%s returns the number of elements in the given collection (lists and arrays work too)") ],

           [ "branch", esr_output(conditionals.branch_request_psp()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType(),
                                           sim_grad=lambda args, direc: [0, direc, 0] if args[0] else [0, 0, direc],
                                           descr="%s returns either its second or third argument.")],
           [ "make_csp", typed_nr(csp.MakeCSPOutputPSP(),
                                  [v.HomogeneousArrayType(v.SymbolType()), v.ExpressionType()],
                                  v.AnyType("a compound SP")) ],

           [ "get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                   descr="%s returns the lexical environment of its invocation site") ],
           [ "get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                 descr="%s returns the empty environment") ],
           [ "is_environment", type_test(env.EnvironmentType()) ],
           [ "extend_environment", typed_nr(eval_sps.ExtendEnvOutputPSP(),
                                            [env.EnvironmentType(), v.SymbolType(), v.AnyType()],
                                            env.EnvironmentType()) ],
           [ "eval",esr_output(TypedPSP(eval_sps.EvalRequestPSP(),
                                        SPType([v.ExpressionType(), env.EnvironmentType()],
                                               v.RequestType("<object>")))) ],

           [ "mem",typed_nr(msp.MakeMSPOutputPSP(),
                            [SPType([v.AnyType("a")], v.AnyType("b"), variadic=True)],
                            SPType([v.AnyType("a")], v.AnyType("b"), variadic=True)) ],

           [ "scope_include",typed_nr(scope.ScopeIncludeOutputPSP(),
                                      # These are type-restricted in Venture, but the actual PSP doesn't care.
                                      [v.AnyType("<scope>"), v.AnyType("<block>"), v.AnyType()],
                                      v.AnyType()) ],

           [ "scope_exclude",typed_nr(scope.ScopeExcludeOutputPSP(),
                                      # These are type-restricted in Venture, but the actual PSP doesn't care.
                                      [v.AnyType("<scope>"), v.AnyType()],
                                      v.AnyType()) ],

           [ "binomial", typed_nr(discrete.BinomialOutputPSP(), [v.CountType(), v.ProbabilityType()], v.CountType()) ],
           [ "flip", typed_nr(discrete.FlipOutputPSP(), [v.ProbabilityType()], v.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [v.ProbabilityType()], v.NumberType(), min_req_args=0) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [v.SimplexType(), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "uniform_discrete",binaryNumS(discrete.UniformDiscreteOutputPSP()) ],
           [ "poisson", typed_nr(discrete.PoissonOutputPSP(), [v.PositiveType()], v.CountType()) ],
                      
           [ "normal", typed_nr(continuous.NormalOutputPSP(), [v.NumberType(), v.NumberType()], v.NumberType()) ], # TODO Sigma is really non-zero, but negative is OK by scaling
           [ "uniform_continuous",binaryNumS(continuous.UniformOutputPSP()) ],
           [ "beta", typed_nr(continuous.BetaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.ProbabilityType()) ],
           [ "gamma", typed_nr(continuous.GammaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.PositiveType()) ],
           [ "student_t", typed_nr(continuous.StudentTOutputPSP(), [v.PositiveType(), v.NumberType(), v.NumberType()], v.NumberType(), min_req_args=1 ) ],
           [ "inv_gamma", typed_nr(continuous.InvGammaOutputPSP(), [v.PositiveType(), v.PositiveType()], v.PositiveType()) ],

           [ "multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.SymmetricMatrixType()], v.HomogeneousArrayType(v.NumberType())) ],
           [ "inv_wishart", typed_nr(continuous.InverseWishartPSP(), [v.SymmetricMatrixType(), v.PositiveType()], v.SymmetricMatrixType())],
           [ "wishart", typed_nr(continuous.WishartPSP(), [v.SymmetricMatrixType(), v.PositiveType()], v.SymmetricMatrixType())],
           
           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [v.PositiveType(), v.PositiveType()], SPType([], v.BoolType())) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [v.PositiveType(), v.PositiveType()], SPType([], v.BoolType())) ],

           [ "dirichlet",typed_nr(dirichlet.DirichletOutputPSP(), [v.HomogeneousArrayType(v.PositiveType())], v.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(dirichlet.SymmetricDirichletOutputPSP(), [v.PositiveType(), v.CountType()], v.SimplexType()) ],

           [ "make_dir_mult",typed_nr(dirichlet.MakerCDirMultOutputPSP(), [v.HomogeneousArrayType(v.PositiveType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(dirichlet.MakerUDirMultOutputPSP(), [v.HomogeneousArrayType(v.PositiveType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(dirichlet.MakerCSymDirMultOutputPSP(), [v.PositiveType(), v.CountType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(dirichlet.MakerUSymDirMultOutputPSP(), [v.PositiveType(), v.CountType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [v.NumberType(),v.NumberType()], SPType([], v.AtomType()), min_req_args = 1) ],
           [ "make_cmvn",typed_nr(cmvn.MakeCMVNOutputPSP(),
                                  [v.HomogeneousArrayType(v.NumberType()),v.NumberType(),v.NumberType(),v.MatrixType()],
                                  SPType([], v.MatrixType())) ],

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [v.SimplexType(), v.MatrixType(), v.MatrixType()], SPType([v.NumberType()], v.NumberType())) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
