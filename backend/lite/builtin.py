import math

from sp import VentureSP
from psp import NullRequestPSP, ESRRefOutputPSP, PSP, TypedPSP

import discrete
import continuous
import dstructures
import csp
import crp
import msp
import hmm
import conditionals
import scope
import eval_sps
import value as v

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False) }

def deterministic_psp(f):
  class DeterministicPSP(PSP):
    def simulate(self,args):
      return f(*args.operandValues)
    def description(self,name):
      return "deterministic %s" % name
  return DeterministicPSP()

def deterministic(f):
  return VentureSP(NullRequestPSP(), deterministic_psp(f))

def deterministic_typed(f, args_types, return_type, variadic=False):
  return VentureSP(NullRequestPSP(), TypedPSP(args_types, return_type, deterministic_psp(f), variadic))

def binaryNum(f):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f):
  return deterministic_typed(f, [v.NumberType()], v.NumberType())

def naryNum(f):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), True)

def type_test(t):
  return deterministic(lambda thing: v.VentureBool(isinstance(thing, t)))

def builtInSPsList():
  return [ [ "plus",  naryNum(lambda *args: sum(args)) ],
           [ "minus", binaryNum(lambda x,y: x - y) ],
           [ "times", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1)) ],
           [ "div",   binaryNum(lambda x,y: x / y) ],
           [ "eq",    deterministic(lambda x,y: v.VentureBool(x.compare(y) == 0)) ],
           [ "gt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) >  0)) ],
           [ "gte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) >= 0)) ],
           [ "lt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) <  0)) ],
           [ "lte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) <= 0)) ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic_typed(lambda x:x, [v.AtomType()], v.NumberType()) ],
           # Atoms appear to be represented as Python integers
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [v.AtomType(), v.AtomType()], v.BoolType()) ],

           [ "sin", unaryNum(math.sin) ],
           [ "cos", unaryNum(math.cos) ],
           [ "tan", unaryNum(math.tan) ],
           [ "hypot", unaryNum(math.hypot) ],
           [ "exp", unaryNum(math.exp) ],
           [ "log", unaryNum(math.log) ],
           [ "pow", unaryNum(math.pow) ],
           [ "sqrt", unaryNum(math.sqrt) ],

           [ "not", deterministic_typed(lambda x: not x, [v.BoolType()], v.BoolType()) ],

           [ "is_symbol", type_test(v.VentureSymbol) ],

           [ "list", deterministic(v.pythonListToVentureList) ],
           [ "pair", deterministic(v.VenturePair) ],
           [ "is_pair", type_test(v.VenturePair) ],
           [ "first", VentureSP(NullRequestPSP(),dstructures.FirstListOutputPSP()) ],
           [ "second", VentureSP(NullRequestPSP(),dstructures.SecondListOutputPSP()) ],
           [ "rest", VentureSP(NullRequestPSP(),dstructures.RestListOutputPSP()) ],

           [ "map_list",VentureSP(dstructures.MapListRequestPSP(),dstructures.MapListOutputPSP()) ],

           [ "array", VentureSP(NullRequestPSP(),dstructures.ArrayOutputPSP()) ],
           [ "is_array", VentureSP(NullRequestPSP(),dstructures.IsArrayOutputPSP()) ],
           [ "dict", VentureSP(NullRequestPSP(),dstructures.DictOutputPSP()) ],
           [ "matrix", VentureSP(NullRequestPSP(),dstructures.MatrixOutputPSP()) ],
           [ "simplex", VentureSP(NullRequestPSP(),dstructures.SimplexOutputPSP()) ],

           [ "lookup",VentureSP(NullRequestPSP(),dstructures.LookupOutputPSP()) ],
           [ "contains",VentureSP(NullRequestPSP(),dstructures.ContainsOutputPSP()) ],
           [ "size",VentureSP(NullRequestPSP(),dstructures.SizeOutputPSP()) ],

           [ "branch", VentureSP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()) ],
           [ "biplex", VentureSP(NullRequestPSP(),conditionals.BiplexOutputPSP()) ],
           [ "make_csp", VentureSP(NullRequestPSP(),csp.MakeCSPOutputPSP()) ],

           [ "eval",VentureSP(eval_sps.EvalRequestPSP(),ESRRefOutputPSP()) ],
           [ "get_current_environment",VentureSP(NullRequestPSP(),eval_sps.GetCurrentEnvOutputPSP()) ],
           [ "get_empty_environment",VentureSP(NullRequestPSP(),eval_sps.GetEmptyEnvOutputPSP()) ],
           [ "extend_environment",VentureSP(NullRequestPSP(),eval_sps.ExtendEnvOutputPSP()) ],

           [ "mem",VentureSP(NullRequestPSP(),msp.MakeMSPOutputPSP()) ],

           [ "scope_include",VentureSP(NullRequestPSP(),scope.ScopeIncludeOutputPSP()) ],

           [ "binomial", VentureSP(NullRequestPSP(),discrete.BinomialOutputPSP()) ],           
           [ "flip",VentureSP(NullRequestPSP(),discrete.BernoulliOutputPSP()) ],
           [ "bernoulli",VentureSP(NullRequestPSP(),discrete.BernoulliOutputPSP()) ],
           [ "categorical",VentureSP(NullRequestPSP(),discrete.CategoricalOutputPSP()) ],

           [ "normal",VentureSP(NullRequestPSP(),continuous.NormalOutputPSP()) ],
           [ "uniform_continuous",VentureSP(NullRequestPSP(),continuous.UniformOutputPSP()) ],
           [ "beta",VentureSP(NullRequestPSP(),continuous.BetaOutputPSP()) ],
           [ "gamma",VentureSP(NullRequestPSP(),continuous.GammaOutputPSP()) ],
           [ "student_t",VentureSP(NullRequestPSP(),continuous.StudentTOutputPSP()) ],

           [ "dirichlet",VentureSP(NullRequestPSP(),discrete.DirichletOutputPSP()) ],
           [ "symmetric_dirichlet",VentureSP(NullRequestPSP(),discrete.SymmetricDirichletOutputPSP()) ],

           [ "make_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerCDirMultOutputPSP()) ],
           [ "make_uc_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerUDirMultOutputPSP()) ],

           [ "make_beta_bernoulli",VentureSP(NullRequestPSP(),discrete.MakerCBetaBernoulliOutputPSP()) ],
           [ "make_uc_beta_bernoulli",VentureSP(NullRequestPSP(),discrete.MakerUBetaBernoulliOutputPSP()) ],

           [ "make_sym_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerCSymDirMultOutputPSP()) ],
           [ "make_uc_sym_dir_mult",VentureSP(NullRequestPSP(),discrete.MakerUSymDirMultOutputPSP()) ],

           [ "make_crp",VentureSP(NullRequestPSP(),crp.MakeCRPOutputPSP()) ],

           [ "make_lazy_hmm",VentureSP(NullRequestPSP(),hmm.MakeUncollapsedHMMOutputPSP()) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
