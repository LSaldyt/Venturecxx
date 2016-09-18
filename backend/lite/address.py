# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

  def map(self, _f):
    return self
  
  def isEmpty(self):
    return True
  
  def __contains__(self, x):
    return False
  
  def remove(self, _x):
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
  
  def isEmpty(self):
    return False
  
  def __contains__(self, x):
    if x == self.last:
      return True
    return x in self.rest
  
  def remove(self, x):
    if x == self.last:
      return self.rest
    return self.rest.remove(x).append(self.last)

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

  def asFrozenList(self):
    return tuple(map(tuple, list(self)))

  def __eq__(self, other):
    if not isinstance(other, Address):
      return False
    return self.asFrozenList() == other.asFrozenList()

  def __hash__(self):
    return hash(self.asFrozenList())

emptyAddress = Address(emptyList)

def directive_address(did):
  return Address(List(did))

def request(addr, index):
  return addr.request(index)

def extend(addr, index):
  return addr.extend(index)

def top_frame(addr):
  return addr.last

def append(loc, index):
  return loc.append(index)
