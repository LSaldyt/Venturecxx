"""Venture values.

The design currently lives at
https://docs.google.com/document/d/1URnJh5hNJ___-dwzIpca5Y2h-Mku1n5zjpGCiFBcUHM/edit
"""
import operator
from numbers import Number
import numpy as np
import hashlib

from mlens import MLens
import ensure_numpy as enp
from request import Request # TODO Pull that file in here?
from exception import VentureValueError, VentureTypeError
import serialize

# TODO Define reasonable __str__ and/or __repr__ methods for all the
# values and all the types.

class VentureValue(object):
  ### "natural" representation and conversions
  def getNumber(self): raise VentureTypeError("Cannot convert %s to number" % type(self))
  def getInteger(self): raise VentureTypeError("Cannot convert %s to integer" % type(self))
  def getProbability(self): raise VentureTypeError("Cannot convert %s to probability" % type(self))
  def getAtom(self): raise VentureTypeError("Cannot convert %s to atom" % type(self))
  def getBool(self): raise VentureTypeError("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise VentureTypeError("Cannot convert %s to symbol" % type(self))
  def getForeignBlob(self): raise VentureTypeError("Cannot convert %s to foreign blob" % type(self))
  def getPair(self): raise VentureTypeError("Cannot convert %s to pair" % type(self))
  # Convention for containers: if the elt_type argument is None,
  # return a Python container of VentureValue objects.  Otherwise,
  # apply the transformation given by the given type to the elements.
  def getArray(self, _elt_type=None): raise VentureTypeError("Cannot convert %s to array" % type(self))
  def getSimplex(self): raise VentureTypeError("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise VentureTypeError("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise VentureTypeError("Cannot convert %s to matrix" % type(self))
  def getSymmetricMatrix(self): raise VentureTypeError("Cannot convert %s to symmetric matrix" % type(self))
  def getSP(self): raise VentureTypeError("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise VentureTypeError("Cannot convert %s to environment" % type(self))

  ### Stack representation
  def asStackDict(self, _trace): raise Exception("Cannot convert %s to a stack dictionary" % type(self))
  @staticmethod
  def fromStackDict(thing):
    if isinstance(thing, list):
      # TODO Arrays or lists?
      return VentureArray([VentureValue.fromStackDict(v) for v in thing])
    else:
      return stackable_types[thing["type"]].fromStackDict(thing)

  ### Comparison
  def compare(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.compareSameType(other)
    if venture_types.index(st) < venture_types.index(ot) : return -1
    else: return 1 # We already checked for equality
  def compareSameType(self, _): raise Exception("Cannot compare %s" % type(self))
  def equal(self, other):
    st = type(self)
    ot = type(other)
    if st == ot:
      return self.equalSameType(other)
    else:
      return False
  def equalSameType(self, other): return self.compareSameType(other) == 0

  ### Generic container methods
  def lookup(self, _): raise VentureTypeError("Cannot look things up in %s" % type(self))
  def lookup_grad(self, _index, _direction):
    raise VentureTypeError("Cannot compute gradient of looking things up in %s" % type(self))
  def contains(self, _): raise VentureTypeError("Cannot look for things in %s" % type(self))
  def length(self): raise VentureTypeError("Cannot measure length of %s" % type(self))

  def __eq__(self, other):
    if isinstance(other, VentureValue):
      return self.equal(other)
    else:
      return False

  # Some Venture value types form a natural vector space over reals,
  # so overload addition, subtraction, and multiplication by scalars.
  # def __add__(self, other), and also __radd__, __neg__, __sub__,
  # __mul__, __rmul__, and dot

  def expressionFor(self):
    return [{"type":"symbol", "value":"quote"}, self.asStackDict(None)]

@serialize.register
class VentureNumber(VentureValue):
  def __init__(self,number):
    assert isinstance(number, Number)
    self.number = float(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureNumber(%s)" % self.number
    else:
      return "VentureNumber(uninitialized)"
  def getNumber(self): return self.number
  def getInteger(self): return int(self.number)
  def getProbability(self):
    if 0 <= self.number and self.number <= 1:
      return self.number
    else: # TODO Do what?  Clip to [0,1]?  Raise?
      raise VentureTypeError("Probability out of range %s" % self.number)
  def getBool(self): return self.number
    
  def asStackDict(self, _trace=None): return {"type":"number","value":self.number}
  @staticmethod
  def fromStackDict(thing): return VentureNumber(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(self.number + other.number)
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(other.number + self.number)
  def __neg__(self):
    return VentureNumber(-self.number)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureNumber(self.number - other.number)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureNumber(self.number * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureNumber(other * self.number)
  def dot(self, other):
    assert isinstance(other, VentureNumber)
    return self.number * other.number
  def map_real(self, f):
    return VentureNumber(f(self.number))
  def real_lenses(self):
    class NumberLens(MLens):
      # Poor man's closure: pass the relevant thing from the lexical
      # scope directly.
      def __init__(self, vn):
        self.vn = vn
      def get(self):
        return self.vn.number
      def set(self, new):
        assert isinstance(new, Number)
        self.vn.number = new
    return [NumberLens(self)]
  def expressionFor(self): return self.number

@serialize.register
class VentureInteger(VentureValue):
  def __init__(self,number):
    assert isinstance(number, Number)
    self.number = int(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureInteger(%s)" % self.number
    else:
      return "VentureInteger(uninitialized)"
  def getInteger(self): return self.number
  def getNumber(self): return float(self.number)
  def asStackDict(self, _trace=None): return {"type":"integer","value":self.number}
  @staticmethod
  def fromStackDict(thing): return VentureInteger(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def expressionFor(self): return self.number

@serialize.register
class VentureProbability(VentureValue):
  def __init__(self, number):
    assert isinstance(number, Number)
    assert 0 <= number and number <= 1
    self.number = float(number)
  def __repr__(self):
    if hasattr(self, "number"):
      return "VentureProbability(%s)" % self.number
    else:
      return "VentureProbability(uninitialized)"
  def getNumber(self): return self.number
  def getProbability(self): return self.number
  def asStackDict(self, _trace=None): return {"type":"probability","value":self.number}
  @staticmethod
  def fromStackDict(thing): return VentureProbability(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.number, other.number)
  def __hash__(self): return hash(self.number)
  def expressionFor(self):
    return [{"type":"symbol", "value":"probability"}, self.number]
  def real_lenses(self):
    class NumberLens(MLens):
      # Poor man's closure: pass the relevant thing from the lexical
      # scope directly.
      def __init__(self, vn):
        self.vn = vn
      def get(self):
        return self.vn.number
      def set(self, new):
        assert isinstance(new, Number)
        self.vn.number = new
    return [NumberLens(self)]

def stupidCompare(thing, other):
  # number.__cmp__(other) works for ints but not floats.  Guido, WTF!?
  # strings don't have __cmp__ either? or lists?
  if thing < other: return -1
  elif thing > other: return 1
  else: return 0

def lexicographicBoxedCompare(thing, other):
  if len(thing) < len(other): return -1
  if len(thing) > len(other): return 1

  # else same length
  for x,y in zip(thing,other):
    if x.compare(y) != 0: return x.compare(y)

  return 0

def lexicographicUnboxedCompare(thing, other):
  if len(thing) < len(other): return -1
  if len(thing) > len(other): return 1

  # else same length
  for x,y in zip(thing,other):
    if stupidCompare(x,y) != 0: return stupidCompare(x,y)

  return 0

def lexicographicMatrixCompare(thing, other):
  ct_thing = reduce(operator.mul, np.shape(thing), 1)
  ct_other = reduce(operator.mul, np.shape(other), 1)
  if ct_thing == 0 and ct_other == 0: return 0
  shape_cmp = lexicographicUnboxedCompare(np.shape(thing), np.shape(other))
  if not shape_cmp == 0: return shape_cmp

  # else shame shape
  if np.array_equal(thing, other): return 0
  # Hack for finding the first discrepant element, via
  # http://stackoverflow.com/questions/432112/is-there-a-numpy-function-to-return-the-first-index-of-something-in-an-array
  diffs = np.array(thing - other)
  diff_indexes = np.nonzero(diffs)
  first_diff = diffs[diff_indexes[0][0]][diff_indexes[0][0]]
  return stupidCompare(first_diff, 0)

def sequenceHash(seq):
  return reduce(lambda res, item: res * 37 + item, [hash(i) for i in seq], 1)

@serialize.register
class VentureAtom(VentureValue):
  def __init__(self,atom):
    assert isinstance(atom, Number)
    self.atom = atom
  def __repr__(self): return "Atom(%s)" % self.atom
  def getNumber(self): return self.atom
  def getAtom(self): return self.atom
  def getBool(self): return self.atom
  def asStackDict(self, _trace): return {"type":"atom","value":self.atom}
  @staticmethod
  def fromStackDict(thing): return VentureAtom(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.atom, other.atom)
  def __hash__(self): return hash(self.atom)
  def expressionFor(self): return [{"type":"symbol", "value":"quote"}, self] # TODO Is this right?

@serialize.register
class VentureBool(VentureValue):
  def __init__(self,boolean):
    assert isinstance(boolean, bool) or isinstance(boolean, np.bool_)
    self.boolean = boolean
  def __repr__(self): return "Bool(%s)" % self.boolean
  def getBool(self): return self.boolean
  def getNumber(self):
    # TODO This horrible thing permits adding the outputs of bernoulli
    # trials as well as dispatching on them.  Or should flip and
    # bernoulli be different SPs?
    return self.boolean
  def asStackDict(self, _trace): return {"type":"boolean","value":self.boolean}
  @staticmethod
  def fromStackDict(thing): return VentureBool(thing["value"])
  def compareSameType(self, other):
    return stupidCompare(self.boolean, other.boolean)
  def __hash__(self): return hash(self.boolean)
  def expressionFor(self):
    return {"type":"symbol", "value":"true"} if self.boolean else {"type":"symbol", "value":"false"}

@serialize.register
class VentureSymbol(VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def __repr__(self): return "Symbol(%s)" % self.symbol
  def getSymbol(self): return self.symbol
  def asStackDict(self, _trace): return {"type":"symbol","value":self.symbol}
  @staticmethod
  def fromStackDict(thing): return VentureSymbol(thing["value"])
  def compareSameType(self, other): return stupidCompare(self.symbol, other.symbol)
  def __hash__(self): return hash(self.symbol)
  def expressionFor(self): return [{"type":"symbol", "value":"quote"}, self.asStackDict(None)]

class VentureForeignBlob(VentureValue):
  # TODO Think about the interaction of foreign blobs with trace
  # copying and serialization
  def __init__(self, datum): self.datum = datum

  def getForeignBlob(self): return self.datum

  def asStackDict(self, _trace=None):
    return {"type":"blob", "value":self.datum}
  @staticmethod
  def fromStackDict(thing): return VentureForeignBlob(thing["value"])

@serialize.register
class VentureNil(VentureValue):
  def __init__(self): pass
  def __repr__(self): return "Nil"

  def asStackDict(self, _trace): return {"type":"list", "value":[]}
  @staticmethod
  def fromStackDict(_): return VentureNil()

  def compareSameType(self, _): return 0 # All Nils are equal
  def __hash__(self): return 0

  def lookup(self, index):
    raise VentureValueError("Index out of bounds: too long by %s" % index)
  def contains(self, _obj): return False
  def size(self): return 0

  def expressionFor(self):
    return [{"type":"symbol", "value":"list"}]

  def asPythonList(self, _elt_type=None): return []

@serialize.register
class VenturePair(VentureValue):
  def __init__(self,(first,rest)):
    # TODO Maybe I need to be careful about tangent and cotangent
    # spaces after all.  A true pair needs to have a venture value
    # inside; a pair that represents the cotangent of something needs
    # to have cotangents; but cotangents permit symbolic zeros.
    if not first == 0: assert isinstance(first, VentureValue)
    if not rest == 0:  assert isinstance(rest, VentureValue)
    self.first = first
    self.rest = rest
  def __repr__(self):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return "VentureList(%r)" % list_
    else:
      return "VentureList(%r . %r)" % (list_, tail)

  def getPair(self): return (self.first,self.rest)
  def getArray(self, elt_type=None):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return VentureArray(list_).getArray(elt_type)
    else:
      raise Exception("Cannot convert an improper list to array")

  def asStackDict(self, trace):
    (list_, tail) = self.asPossiblyImproperList()
    if tail is None:
      return {"type":"list", "value":[v.asStackDict(trace) for v in list_]}
    else:
      return {"type":"improper_list", "value": self}
  @staticmethod
  def fromStackDict(thing):
    if thing["type"] == "improper_list":
      return thing["value"]
    else:
      return pythonListToVentureList(*[VentureValue.fromStackDict(v) for v in thing["value"]])

  def compareSameType(self, other):
    fstcmp = self.first.compare(other.first)
    if fstcmp != 0: return fstcmp
    else: return self.rest.compare(other.rest)
  def __hash__(self):
    return hash(self.first) + 37*hash(self.rest)

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in an array" % index)
    if ind < 1: # Equivalent to truncating for positive floats
      return self.first
    else:
      return self.rest.lookup(VentureNumber(ind - 1))
  def lookup_grad(self, index, direction):
    if direction == 0: return 0
    if index == 0: return VenturePair((direction, 0))
    return VenturePair((0, self.rest.lookup_grad(index - 1, direction)))
  def contains(self, obj): # Treat the list as a set
    if obj.equal(self.first):
      return True
    elif not isinstance(self.rest, VenturePair):
      # Notably, this means I am not checking whether the obj is the
      # last member of an improper list.
      return False
    else:
      return self.rest.contains(obj)
  def size(self): # Really, length
    return 1 + self.rest.size()

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((self.first + other.first, self.rest + other.rest))
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((other.first + self.first, other.rest + self.rest))
  def __neg__(self):
    return VenturePair((-self.first, -self.rest))
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VenturePair((self.first - other.first, self.rest - other.rest))
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VenturePair((self.first * other, self.rest * other))
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VenturePair((other * self.first, other * self.rest))

  def expressionFor(self):
    return [{"type":"symbol", "value":"pair"}, self.first.expressionFor(), self.rest.expressionFor()]

  def asPythonList(self, elt_type=None):
    if elt_type is not None:
      return [elt_type.asPython(self.first)] + self.rest.asPythonList(elt_type)
    else:
      return [self.first] + self.rest.asPythonList()
  def asPossiblyImproperList(self):
    if isinstance(self.rest, VenturePair):
      (sublist, tail) = self.rest.asPossiblyImproperList()
      return ([self.first] + sublist, tail)
    elif isinstance(self.rest, VentureNil):
      return ([self.first], None)
    else:
      return ([self.first], self.rest)

def pythonListToVentureList(*l):
  return reduce(lambda t, h: VenturePair((h, t)), reversed(l), VentureNil())

@serialize.register
class VentureArray(VentureValue):
  """Venture arrays are heterogeneous, with O(1) access and O(n) copy."""
  def __init__(self, array): self.array = array
  def __repr__(self):
    return "VentureArray(%s)" % self.array
  def getArray(self, elt_type=None):
    if elt_type is None: # No conversion
      return self.array
    else:
      return [elt_type.asPython(v) for v in self.array]

  def compareSameType(self, other):
    return lexicographicBoxedCompare(self.array, other.array)
  def __hash__(self): return sequenceHash(self.array)

  def asStackDict(self,trace):
    # TODO Are venture arrays reflected as lists to the stack?
    # TODO Are stack lists lists, or are they themselves type tagged?
    return {"type":"list","value":[v.asStackDict(trace) for v in self.array]}
  @staticmethod
  def fromStackDict(thing):
    return VentureArray([VentureValue.fromStackDict(v) for v in thing["value"]])

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in an array" % index)
    if 0 <= int(ind) and int(ind) < len(self.array):
      return self.array[int(ind)]
    else:
      raise VentureValueError("Index out of bounds: %s" % index)
  def lookup_grad(self, index, direction):
    return VentureArray([direction if i == index else 0 for (_,i) in enumerate(self.array)])
  def contains(self, obj):
    # Not Python's `in` because I need to use custom equality
    # TODO I am going to have to overload the equality for dicts
    # anyway, so might as well eventually use `in` here.
    return any(obj.equal(li) for li in self.array)
  def size(self): return len(self.array)

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([x + y for (x,y) in zip(self.array, other.array)])
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([y + x for (x,y) in zip(self.array, other.array)])
  def __neg__(self):
    return VentureArray([-x for x in self.array])
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureArray([x - y for (x,y) in zip(self.array, other.array)])
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArray([x * other for x in self.array])
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArray([other * x  for x in self.array])
  def dot(self, other):
    return sum([x.dot(y) for (x,y) in zip(self.array, other.array)])
  def map_real(self, f):
    return VentureArray([x.map_real(f) for x in self.array])

  def expressionFor(self):
    return [{"type":"symbol", "value":"array"}] + [v.expressionFor() for v in self.array]

  def asPythonList(self, elt_type=None):
    return self.getArray(elt_type)

@serialize.register
class VentureArrayUnboxed(VentureValue):
  """Venture arrays of unboxed objects are homogeneous, with O(1) access and O(n) copy."""
  def __init__(self, array, elt_type):
    assert isinstance(elt_type, VentureType)
    self.elt_type = elt_type
    self.array = enp.ensure_numpy_if_possible(elt_type, array)
  def __repr__(self):
    return "VentureArrayUnboxed(%s)" % self.array

  # This method produces results that are at least Python-boxed
  def getArray(self, elt_type=None):
    if elt_type is None: # Convert to VentureValue
      return [self.elt_type.asVentureValue(v) for v in self.array]
    else:
      # TODO What I really need here is the function that converts
      # from the Python representation of self.elt_type to the Python
      # representation of elt_type, with an optimization if that
      # function is the identity.
      assert elt_type == self.elt_type
      return self.array

  def compareSameType(self, other):
    return lexicographicUnboxedCompare(self.array, other.array)
  def __hash__(self): return sequenceHash(self.array)

  def asStackDict(self,_trace=None):
    return {"type":"array_unboxed", "subtype":self.elt_type, "value":self.array}
  @staticmethod
  def fromStackDict(thing):
    return VentureArrayUnboxed(thing["value"], thing["subtype"])

  def lookup(self, index):
    try:
      ind = index.getNumber()
    except VentureTypeError:
      raise VentureValueError("Looking up non-number %r in an array" % index)
    if 0 <= int(ind) and int(ind) < len(self.array):
      return self.elt_type.asVentureValue(self.array[int(ind)])
    else:
      raise VentureValueError("Index out of bounds: %s" % index)
  def lookup_grad(self, index, direction):
    # TODO Really this should be an unboxed array of the gradient
    # types of the elements, with generic zeroes.
    return VentureArray([direction if i == index else 0 for (_,i) in enumerate(self.array)])
  def contains(self, obj):
    return any(obj.equal(self.elt_type.asVentureValue(li)) for li in self.array)
  def size(self): return len(self.array)

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.add, self.array, self.elt_type, other.array, other.elt_type))
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.add, other.array, other.elt_type, self.array, self.elt_type))
  def __neg__(self):
    return VentureArrayUnboxed(enp.map(operator.neg, self.array, self.elt_type), self.elt_type)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureArrayUnboxed(*enp.map2(operator.sub, self.array, self.elt_type, other.array, other.elt_type))
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArrayUnboxed(enp.map(lambda x: x * other, self.array, self.elt_type), self.elt_type)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureArrayUnboxed(enp.map(lambda x: other * x, self.array, self.elt_type), self.elt_type)
  def dot(self, other):
    return enp.dot(self.array, self.elt_type, other.array, other.elt_type)
  def map_real(self, f):
    # TODO Ascertain whether self.elt_type represents a real number or not
    return VentureArrayUnboxed(enp.map(f, self.array, self.elt_type), self.elt_type)

  def asPythonList(self, elt_type=None):
    return self.getArray(elt_type)

@serialize.register
class VentureSimplex(VentureValue):
  """Simplexes are homogeneous unboxed arrays of probabilities.  They
are also supposed to sum to 1, but we are not checking that.

  """
  def __init__(self,simplex): self.simplex = simplex
  def __repr__(self):
    return "VentureSimplex(%s)" % self.simplex
  def getSimplex(self): return self.simplex
  def compareSameType(self, other):
    # The Python ordering is lexicographic first, then by length, but
    # I think we want lower-d simplexes to compare less than higher-d
    # ones regardless of the point.
    return lexicographicUnboxedCompare(self.simplex, other.simplex)
  def __hash__(self):
    return sequenceHash(self.simplex)
  def asStackDict(self, _trace=None):
    # TODO As what type to reflect simplex points to the stack?
    return {"type":"simplex", "value":self.simplex}
  @staticmethod
  def fromStackDict(thing): return VentureSimplex(thing["value"])
  def lookup(self, index):
    return ProbabilityType().asVentureValue(self.simplex[index.getNumber()])
  def contains(self, obj):
    # Homogeneous; TODO make it return False instead of exploding for non-numeric objects.
    return obj.getNumber() in self.simplex
  def size(self): return len(self.simplex)
  def expressionFor(self):
    return [{"type":"symbol", "value":"simplex"}] + self.simplex

@serialize.register
class VentureDict(VentureValue):
  def __init__(self,d): self.dict = d

  def getDict(self): return self.dict

  def asStackDict(self, _trace):
    # TODO Difficult to reflect as a Python dict because the keys
    # would presumably need to be converted to stack dicts too, which
    # is a problem because they need to be hashable.
    return {"type":"dict", "value":self}
  @staticmethod
  def fromStackDict(thing): return thing["value"]

  def equalSameType(self, other):
    return len(set(self.dict.iteritems()) ^ set(other.dict.iteritems())) == 0

  def lookup(self, key):
    return self.dict[key]
  def contains(self, key):
    return key in self.dict
  def size(self): return len(self.dict)

  def expressionFor(self):
    (keys, vals) = zip(*self.dict.iteritems())
    return [{"type":"symbol", "value":"dict"},
            [{"type":"symbol", "value":"list"}] + [k.expressionFor() for k in keys],
            [{"type":"symbol", "value":"list"}] + [v.expressionFor() for v in vals]]

# 2D array of numbers backed by a numpy array object
@serialize.register
class VentureMatrix(VentureValue):
  def __init__(self,matrix): self.matrix = np.array(matrix)
  def __repr__(self):
    return "VentureMatrix(%s)" % self.matrix

  def getMatrix(self): return self.matrix
  def getSymmetricMatrix(self):
    if matrixIsSymmetric(self.matrix):
      return self.matrix
    else:
      raise VentureTypeError("Matrix is not symmetric %s" % self.matrix)

  def compareSameType(self, other):
    return lexicographicMatrixCompare(self.matrix, other.matrix)
  def __hash__(self):
    # From http://stackoverflow.com/questions/5386694/fast-way-to-hash-numpy-objects-for-caching
    b = self.matrix.view(np.uint8)
    return hash(hashlib.sha1(b).hexdigest())

  def asStackDict(self, _trace):
    return {"type":"matrix", "value":self.matrix}
  @staticmethod
  def fromStackDict(thing): return VentureMatrix(thing["value"])

  def __add__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(self.matrix + other.matrix)
  def __radd__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(other.matrix + self.matrix)
  def __neg__(self):
    return VentureMatrix(-self.matrix)
  def __sub__(self, other):
    if other == 0:
      return self
    else:
      return VentureMatrix(self.matrix - other.matrix)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureMatrix(self.matrix * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureMatrix(other * self.matrix)
  def dot(self, other):
    assert isinstance(other, VentureMatrix)
    return np.sum(np.multiply(self.matrix, other.matrix))
  def map_real(self, f):
    return VentureMatrix(np.vectorize(f)(self.matrix))

  def expressionFor(self):
    return [{"type":"symbol", "value":"matrix"},
            [{"type":"symbol", "value":"list"}] + [[{"type":"symbol", "value":"list"}] + [v for v in row] for row in self.matrix]]

@serialize.register
class VentureSymmetricMatrix(VentureMatrix):
  def __init__(self, matrix):
    self.matrix = matrix
    assert matrixIsSymmetric(matrix)

  def __add__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(self.matrix + other.matrix)
    else:
      return VentureMatrix(self.matrix + other.matrix)
  def __radd__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(other.matrix + self.matrix)
    else:
      return VentureMatrix(other.matrix + self.matrix)
  def __neg__(self):
    return VentureSymmetricMatrix(-self.matrix)
  def __sub__(self, other):
    if other == 0:
      return self
    if isinstance(other, VentureSymmetricMatrix):
      return VentureSymmetricMatrix(self.matrix - other.matrix)
    else:
      return VentureMatrix(self.matrix - other.matrix)
  def __mul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureSymmetricMatrix(self.matrix * other)
  def __rmul__(self, other):
    # Assume other is a scalar
    assert isinstance(other, Number)
    return VentureSymmetricMatrix(other * self.matrix)
  def map_real(self, f):
    candidate = np.vectorize(f)(self.matrix)
    return VentureSymmetricMatrix( (candidate + candidate.T)/2 )

def matrixIsSymmetric(matrix):
  return np.allclose(matrix.transpose(), matrix)

@serialize.register
class SPRef(VentureValue):
  def __init__(self,makerNode): self.makerNode = makerNode
  def asStackDict(self,trace):
    return {"type":"sp","value":trace.madeSPAt(self.makerNode).show(trace.madeSPAuxAt(self.makerNode))}
  
  @staticmethod
  def fromStackDict(thing): return thing["value"]
  # SPRefs are intentionally not comparable until we decide otherwise

## SPs and Environments as well
## Not Requests, because we do not reflect on them

venture_types = [
  VentureNumber, VentureInteger, VentureProbability, VentureAtom, VentureBool,
  VentureSymbol, VentureForeignBlob, VentureNil, VenturePair,
  VentureArray, VentureArrayUnboxed, VentureSimplex, VentureDict, VentureMatrix, SPRef]
  # Break load order dependency by not adding SPs and Environments yet

stackable_types = {
  "number": VentureNumber,
  "real": VentureNumber,
  "integer": VentureInteger,
  "probability": VentureProbability,
  "atom": VentureAtom,
  "boolean": VentureBool,
  "symbol": VentureSymbol,
  "blob": VentureForeignBlob,
  "list": VenturePair,
  "improper_list": VenturePair,
  "vector": VentureArray,
  "array": VentureArray,
  "array_unboxed": VentureArrayUnboxed,
  "simplex": VentureSimplex,
  "dict": VentureDict,
  "matrix": VentureMatrix,
  "SP": SPRef, # As opposed to VentureSP?
  }

def registerVentureType(t, name = None):
  if t in venture_types: pass
  else:
    venture_types.append(t)
    if name is not None:
      stackable_types[name] = t

### Venture Types

class VentureType(object):
  def asPythonNoneable(self, vthing):
    if vthing is None:
      return None
    else:
      return self.asPython(vthing) # Function will be added by inheritance pylint:disable=no-member
  def distribution(self, base, **kwargs):
    return base(self.name()[1:-1], **kwargs) # Strip the angle brackets

# TODO Is there any way to make these guys be proper singleton
# objects?

class AnyType(VentureType):
  """The type object to use for parametric types -- does no conversion."""
  def __init__(self, type_name=None):
    self.type_name = type_name
  def asVentureValue(self, thing):
    assert isinstance(thing, VentureValue)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, VentureValue)
    return thing
  def __contains__(self, vthing): return isinstance(vthing, VentureValue)
  def name(self):
    if self.type_name is None:
      return "<object>"
    else:
      return self.type_name
  def distribution(self, base, **kwargs):
    return base("object", **kwargs)

# This is a prototypical example of the classes I am autogenerating
# below, for legibility.  I could have removed this and added "Number"
# to the list in the for.
class NumberType(VentureType):
  def asVentureValue(self, thing): return VentureNumber(thing)
  def asPython(self, vthing): return vthing.getNumber()
  def __contains__(self, vthing): return isinstance(vthing, VentureNumber)
  def name(self): return "<number>"

def standard_venture_type(typename):
  return """
class %sType(VentureType):
  def asVentureValue(self, thing): return Venture%s(thing)
  def asPython(self, vthing): return vthing.get%s()
  def __contains__(self, vthing): return isinstance(vthing, Venture%s)
  def name(self): return "<%s>"
""" % (typename, typename, typename, typename, typename.lower())

for typestring in ["Integer", "Probability", "Atom", "Bool", "Symbol", "ForeignBlob", "Array", "Simplex", "Dict", "Matrix", "SymmetricMatrix"]:
  # Exec is appropriate for metaprogramming, but indeed should not be used lightly.
  # pylint: disable=exec-used
  exec(standard_venture_type(typestring))

class CountType(VentureType):
  def asVentureValue(self, thing):
    assert 0 <= thing
    return VentureInteger(thing)
  def asPython(self, vthing):
    ans = vthing.getInteger()
    if 0 <= ans:
      return ans
    else:
      # TODO: Or what?  Clip to 0?
      raise VentureTypeError("Count is not positive %s" % self.number)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureInteger) and 0 <= vthing.getInteger()
  def name(self): return "<count>"

class PositiveType(VentureType):
  def asVentureValue(self, thing):
    assert 0 < thing
    return VentureNumber(thing)
  def asPython(self, vthing):
    ans = vthing.getNumber()
    if 0 < ans:
      return ans
    else:
      # TODO: Or what?  Can't even clip to 0!
      raise VentureTypeError("Number is not positive %s" % ans)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureNumber) and 0 < vthing.getNumber()
  def name(self): return "<positive>"

class NilType(VentureType):
  def asVentureValue(self, _thing):
    # TODO Throw an error if not null-like?
    return VentureNil()
  def asPython(self, _vthing):
    # TODO Throw an error if not nil?
    return []
  def __contains__(self, vthing): return isinstance(vthing, VentureNil)
  def name(self): return "()"
  def distribution(self, base, **kwargs):
    return base("nil", **kwargs)

class PairType(VentureType):
  def __init__(self, first_type=None, second_type=None):
    # TODO Do I want to do automatic conversions if the types are
    # given, or not?
    self.first_type = first_type
    self.second_type = second_type
  def asVentureValue(self, thing): return VenturePair(thing)
  def asPython(self, vthing): return vthing.getPair()
  def __contains__(self, vthing): return isinstance(vthing, VenturePair)
  def name(self):
    if self.first_type is None and self.second_type is None:
      return "<pair>"
    first_name = self.first_type.name() if self.first_type else "<object>"
    second_name = self.second_type.name() if self.second_type else "<object>"
    return "<pair %s %s>" % (first_name, second_name)
  def distribution(self, base, **kwargs):
    first_dist = self.first_type.distribution(base, **kwargs) if self.first_type else None
    second_dist = self.second_type.distribution(base, **kwargs) if self.second_type else None
    return base("pair", first_dist=first_dist, second_dist=second_dist, **kwargs)

class ListType(VentureType):
  """A Venture list is either a VentureNil or a VenturePair whose
second field is a Venture list.  I choose that the corresponding
Python object is a list of VentureValue objects (this is consistent
with the Any type doing no conversion).

In Haskell type notation:

data List = Nil | Pair Any List
"""
  def asVentureValue(self, thing):
    return pythonListToVentureList(*thing)
  def asPython(self, thing):
    return thing.asPythonList()
  def __contains__(self, vthing):
    return isinstance(vthing, VentureNil) or (isinstance(vthing, VenturePair) and vthing.rest in self)
  def name(self): return "<list>"

class HomogeneousListType(VentureType):
  """Type objects for homogeneous lists.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture lists.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, subtype):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
  def asVentureValue(self, thing):
    return pythonListToVentureList(*[self.subtype.asVentureValue(t) for t in thing])
  def asPython(self, vthing):
    return vthing.asPythonList(self.subtype)
  def __contains__(self, vthing):
    return vthing in ListType and all([v in self.subtype for v in vthing.asPythonList()])
  def name(self): return "<list %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("list", elt_dist=self.subtype.distribution(base, **kwargs), **kwargs)

class HomogeneousArrayType(VentureType):
  """Type objects for homogeneous arrays.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture arrays.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, subtype):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
  def asVentureValue(self, thing):
    return VentureArray([self.subtype.asVentureValue(v) for v in thing])
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)
  def __contains__(self, vthing):
    return isinstance(vthing, VentureArray) and all([v in self.subtype for v in vthing.getArray()])
  def name(self): return "<array %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("array", elt_dist=self.subtype.distribution(base, **kwargs), **kwargs)

class ArrayUnboxedType(VentureType):
  """Type objects for arrays of unboxed values.  Perforce homogeneous."""
  def __init__(self, subtype):
    assert isinstance(subtype, VentureType)
    self.subtype = subtype
  def asVentureValue(self, thing):
    return VentureArrayUnboxed(thing, self.subtype)
  def asPython(self, vthing):
    return vthing.getArray(self.subtype)
  def __contains__(self, vthing):
    # TODO Need a more general element type compatibility check
    return isinstance(vthing, VentureArrayUnboxed) and vthing.elt_type == self.subtype
  def name(self): return "<array %s>" % self.subtype.name()
  def distribution(self, base, **kwargs):
    return base("array_unboxed", elt_type=self.subtype, **kwargs)

class ExpressionType(VentureType):
  """A Venture expression is either a Venture self-evaluating object
(bool, number, integer, atom), or a Venture symbol, or a Venture array of
Venture Expressions.  Note: I adopt the convention that, to
distinguish them from numbers, Venture Atoms will be represented in
Python as VentureAtom objects for purposes of this type.

Note 2: Consumers of expressions should also be able to consume lists
of expressions, but the Python-side representation of expressions does
not distinguish the representation of lists and arrays.  So
round-tripping from Venture to Python and back will not be the
identity function, but should still be idempotent.

Note 3: The same discussion applies to other nice types like
VentureSPs.

In Haskell type notation:

data Expression = Bool | Number | Integer | Atom | Symbol | Array Expression
"""
  def asVentureValue(self, thing):
    if isinstance(thing, bool) or isinstance(thing, np.bool_):
      return VentureBool(thing)
    if isinstance(thing, int):
      return VentureInteger(thing)
    if isinstance(thing, Number):
      return VentureNumber(thing)
    if isinstance(thing, VentureAtom):
      return thing
    if isinstance(thing, str):
      return VentureSymbol(thing)
    if hasattr(thing, "__getitem__"): # Already not a string
      return VentureArray([self.asVentureValue(v) for v in thing])
    else:
      raise Exception("Cannot convert Python object %r to a Venture Expression" % thing)

  def asPython(self, thing):
    if isinstance(thing, VentureBool):
      return thing.getBool()
    if isinstance(thing, VentureInteger):
      return thing.getInteger()
    if isinstance(thing, VentureNumber):
      return thing.getNumber()
    if isinstance(thing, VentureAtom):
      return thing # Atoms are valid elements of expressions
    if isinstance(thing, VentureSymbol):
      return thing.getSymbol()
    if isinstance(thing, VentureArray):
      return thing.getArray(self)
    if isinstance(thing, VenturePair) or isinstance(thing, VentureNil):
      return thing.asPythonList(self)
    # Many other things are represented as themselves now. TODO Restrict this to self-evaluatings?
    return thing

  def name(self): return "<exp>"

class HomogeneousDictType(VentureType):
  """Type objects for homogeneous dicts.  Right now, the homogeneity
  is not captured in the implementation, in that on the Venture side
  such data is still stored as heterogenous Venture dicts.  This type
  does, however, encapsulate the necessary wrapping and unwrapping."""
  def __init__(self, keytype, valtype):
    assert isinstance(keytype, VentureType)
    assert isinstance(valtype, VentureType)
    self.keytype = keytype
    self.valtype = valtype
  def asVentureValue(self, thing):
    return VentureDict(dict([(self.keytype.asVentureValue(key), self.valtype.asVentureValue(val)) for (key, val) in thing.iteritems()]))
  def asPython(self, vthing):
    return dict([(self.keytype.asPython(key), self.valtype.asPython(val)) for (key, val) in vthing.getDict().iteritems()])
  def __contains__(self, vthing):
    return isinstance(vthing, VentureDict) and all([k in self.keytype and v in self.valtype for (k,v) in vthing.getDict().iteritems()])
  def name(self): return "<dict %s %s>" % (self.keytype.name(), self.valtype.name())
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("dict", key_dist=self.keytype.distribution(base, **kwargs),
                val_dist=self.valtype.distribution(base, **kwargs), **kwargs)

class HomogeneousMappingType(VentureType):
  """Type objects for all Venture mappings.  Dicts are the only fully
  generic mappings, but Venture also treats arrays and lists as
  mappings from integers to values, and environments as mappings from
  symbols to values.  This type is purely advisory and does not do any
  conversion."""
  def __init__(self, keytype, valtype):
    assert isinstance(keytype, VentureType)
    assert isinstance(valtype, VentureType)
    self.keytype = keytype
    self.valtype = valtype
  def asVentureValue(self, thing):
    return thing
  def asPython(self, vthing):
    return vthing
  def name(self): return "<mapping %s %s>" % (self.keytype.name(), self.valtype.name())
  def distribution(self, base, **kwargs):
    # TODO Is this splitting what I want?
    return base("mapping", key_dist=self.keytype.distribution(base, **kwargs),
                val_dist=self.valtype.distribution(base, **kwargs), **kwargs)

class RequestType(VentureType):
  """A type object for Venture's Requests.  Requests are not Venture
  values in the strict sense, and reflection is not permitted on them.
  This type exists to permit requester PSPs to be wrapped in the
  TypedPSP wrapper."""
  def __init__(self, name="<request>"):
    # Accept a name to report in the documentation because the
    # synthesizer is not clever enough to properly compose
    # descriptions of SPs from descriptions of their PSPs.
    self._name = name
  def asVentureValue(self, thing):
    assert isinstance(thing, Request)
    return thing
  def asPython(self, thing):
    assert isinstance(thing, Request)
    return thing
  def name(self): return self._name
