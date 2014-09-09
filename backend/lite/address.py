class EmptyList(object):
  def __iter__(self):
    return
    yield
  
  def __len__(self):
    return 0
  
  def __repr__(self):
    return str(list(self))
  
  def append(self, last):
    return List(last, self)

  def map(self, f):
    return self
  
emptyList = EmptyList()

class List(object):
  """Functional list data structure.
  Note that order is reversed from the traditional
  scheme implementation. That is, insertion (via
  append) is done at the end of the list."""
  
  def __init__(self, last, rest=emptyList):
    self.last = last
    self.rest = rest
  
  # FIXME: quadratic runtime :(
  # even python3's "yield from" doesn't work
  def __iter__(self):
    for i in self.rest:
      yield i
    yield self.last
  
  def __len__(self):
    return 1 + len(self.rest)
  
  def __repr__(self):
    return str(list(self))
  
  def append(self, last):
    return List(last, self)

  def map(self, f):
    return self.rest.map(f).append(f(self.last))

class Address(List):
  """Maintains a call stack."""
  def __init__(self, index, stack=emptyList):
    super(Address, self).__init__(index, stack)
  
  def request(self, index):
    """Make a new stack frame."""
    return Address(index, self)
  
  def extend(self, index):
    """Extend the current stack frame."""
    return Address(self.last.append(index), self.rest)
  
  def asList(self):
    """Converts to nested lists."""
    return map(list, list(self))

emptyAddress = Address(emptyList)
