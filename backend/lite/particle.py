from nose.tools import assert_equal,assert_is_none,assert_is_instance
from wttree import PMap, PSet
from trace import Trace

class Particle(Trace):

  # The trace is expected to be a torus, with the chosen scaffold
  # already detached, or a particle.
  def __init__(self,trace):
    if type(trace) is Particle: self.initFromParticle(trace)
    elif type(trace) is Trace: self.initFromTrace(trace)
    else: raise Exception("Must init particle from trace or particle")

  # Note: using "copy()" informally for both legit_copy and persistent_copy
  def initFromParticle(self,particle):
    self.base = particle.base    

    # (1) Persistent stuff
    self.rcs = particle.rcs
    self.ccs = particle.ccs
    self.aes = particle.aes

    self.values = particle.values
    self.madeSPs = particle.madeSPs

    self.scopes = particle.scopes # pmap => pmap => pset
    self.esrParents = particle.esrParents
    self.numRequests = particle.numRequests
    self.regenCounts = particle.regenCounts
    self.newMadeSPFamilies = particle.newMadeSPFamilies # pmap => pmap => node
    self.newChildren = particle.newChildren

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = { node : spaux.copy() for node,spaux in particle.madeSPAuxs.iteritems() }

  def initFromTrace(self,trace):
    self.base = trace

    # (1) Persistent stuff
    self.rcs = PSet()
    self.ccs = PSet()
    self.aes = PSet()

    self.values = PMap()
    self.madeSPs = PMap()

    self.scopes = PMap()
    self.esrParents = PMap()
    self.numRequests = PMap()
    self.regenCounts = PMap()
    self.newMadeSPFamilies = PMap()
    self.newChildren = PMap()

    # (2) Maps to things that change outside of particle methods
    self.madeSPAuxs = {}


#### Random choices and scopes

  def registerRandomChoice(self,node):
    self.rcs = self.rcs.insert(node)
    self.registerRandomChoiceInScope("default",node,node)

  def registerAEKernel(self,node): 
    self.aes = self.aes.insert(node)

  def registerConstrainedChoice(self,node): 
    self.ccs = self.ccs.insert(node)
    self.unregisterRandomChoice(node)

  def unregisterRandomChoice(self,node): 
    assert node in self.rcs
    self.rcs = self.rcs.delete(node)
    self.unregisterRandomChoiceInScope("default",node,node)

  def registerRandomChoiceInScope(self,scope,block,node):
    if not scope in self.scopes: self.scopes = self.scopes.insert(scope,PMap())
    if not block in self.scopes.lookup(scope): self.scopes = self.scopes.adjust(scope,lambda blocks: blocks.insert(block,PSet()))
    self.scopes = self.scopes.adjust(scope,lambda blocks: blocks.adjust(block,lambda pnodes: pnodes.insert(node)))

  def unregisterRandomChoiceInScope(self,scope,block,node):
    self.scopes = self.scopes.adjust(scope,lambda blocks: blocks.adjust(block,lambda pnodes: pnodes.delete(node)))
    if not len(self.scopes.lookup(scope).lookup(block)): self.scopes = self.scopes.adjust(scope,lambda blocks: blocks.delete(block))
    if not len(self.scopes.lookup(scope)): self.scopes = self.scopes.delete(scope)

#### Misc

  def valueAt(self,node): 
    if node in self.values: return self.values.lookup(node)
    else: 
      return self.base.valueAt(node)

  def setValueAt(self,node,value): 
    assert_is_none(self.base.valueAt(node))
    self.values = self.values.insert(node,value)

  def madeSPAt(self,node):
    if node in self.madeSPs: return self.madeSPs.lookup(node)
    else: return self.base.madeSPAt(node)

  def setMadeSPAt(self,node,sp): 
    assert not node in self.madeSPs
    assert self.base.madeSPAt(node) is None
    self.madeSPs = self.madeSPs.insert(node,sp)

  def esrParentsAt(self,node): 
    if node in self.esrParents: return self.esrParents.lookup(node)
    else: return self.base.esrParentsAt(node)

  def appendEsrParentAt(self,node,parent):
    assert not self.base.esrParentsAt(node)
    if not node in self.esrParents: self.esrParents = self.esrParents.insert(node,[])
    self.esrParents.lookup(node).append(parent)

  def regenCountAt(self,scaffold,node): 
    assert self.base.regenCountAt(scaffold,node) == 0
    if node in self.regenCounts: return self.regenCounts.lookup(node)
    else: return self.base.regenCountAt(scaffold,node)

  def incRegenCountAt(self,scaffold,node): 
    if not node in self.regenCounts: self.regenCounts = self.regenCounts.insert(node,0)
    self.regenCounts = self.regenCounts.adjust(node,lambda rc: rc + 1)

  def incRequestsAt(self,node):
    if not node in self.numRequests: self.numRequests = self.numRequests.insert(node,self.base.numRequestsAt(node))
    self.numRequests = self.numRequests.adjust(node,lambda nr: nr + 1)

  def addChildAt(self,node,child):
    if not node in self.newChildren: self.newChildren = self.newChildren.insert(node,[])
    self.newChildren.lookup(node).append(child)

### SPFamilies

  def containsSPFamilyAt(self,node,id): 
    makerNode = self.spRefAt(node).makerNode
    if makerNode in self.newMadeSPFamilies:
      assert_is_instance(self.newMadeSPFamilies.lookup(makerNode),PMap)
      if id in self.newMadeSPFamilies.lookup(makerNode): 
        return True
    elif self.base.madeSPFamiliesAt(makerNode).containsFamily(id): return True
    return False

  def initMadeSPFamiliesAt(self,node): 
    assert not node in self.newMadeSPFamilies
    assert node.madeSPFamilies is None
    self.newMadeSPFamilies = self.newMadeSPFamilies.insert(node,PMap())

  def registerFamilyAt(self,node,esrId,esrParent): 
    makerNode = self.spRefAt(node).makerNode
    if not makerNode in self.newMadeSPFamilies: self.newMadeSPFamilies = self.newMadeSPFamilies.insert(makerNode,PMap())
    self.newMadeSPFamilies = self.newMadeSPFamilies.adjust(makerNode,lambda ids: ids.insert(esrId,esrParent))


  def madeSPFamilyAt(self,node,esrId): 
    if node in self.newMadeSPFamilies and esrId in self.newMadeSPFamilies.lookup(node): 
      return self.newMadeSPFamilies.lookup(node).lookup(esrId)
    else: 
      return self.base.madeSPFamilyAt(node,esrId)

  def spFamilyAt(self,node,esrId): 
    makerNode = self.spRefAt(node).makerNode
    return self.madeSPFamilyAt(makerNode,esrId)
 
### Regular maps

  def madeSPAuxAt(self,node):
    if not node in self.madeSPAuxs: 
      if self.base.madeSPAuxAt(node) is not None:
        self.madeSPAuxs[node] = self.base.madeSPAuxAt(node).copy()
      else: return None
    return self.madeSPAuxs[node]

  def setMadeSPAuxAt(self,node,aux):
    assert not node in self.madeSPAuxs
    assert self.base.madeSPAuxAt(node) is None
    self.madeSPAuxs[node] = aux

### Miscellaneous bookkeeping
  def numBlocksInScope(self,scope): return len(self.scopes.lookup(scope)) + self.base.numBlocksInScope(scope)

### Commit
  def commit(self): 
    # note that we do not call registerRandomChoice() because it in turn calls registerRandomChoiceInScope()
    for node in self.rcs: self.base.rcs.add(node)

    # note that we do not call registerConstrainedChoice() because it in turn calls unregisterRandomChoice()
    for node in self.ccs: self.base.ccs.add(node)

    for node in self.aes: self.base.registerAEKernel(node)

    for (node,value) in self.values.iteritems(): 
      self.base.setValueAt(node,value)
    for (node,madeSP) in self.madeSPs.iteritems(): self.base.setMadeSPAt(node,madeSP)

    # this iteration includes "default"
    for (scope,blocks) in self.scopes.iteritems():
      for (block,pnodes) in blocks.iteritems():
        for pnode in pnodes:
          self.base.registerRandomChoiceInScope(scope,block,pnode)
          
    for (node,esrParents) in self.esrParents.iteritems(): self.base.setEsrParentsAt(node,esrParents)
    for (node,numRequests) in self.numRequests.iteritems(): self.base.setNumRequestsAt(node,numRequests)
    for (node,newMadeSPFamilies) in self.newMadeSPFamilies.iteritems(): self.base.addNewMadeSPFamilies(node,newMadeSPFamilies)
    for (node,newChildren) in self.newChildren.iteritems(): self.base.addNewChildren(node,newChildren)

    for (node,spaux) in self.madeSPAuxs.iteritems(): self.base.setMadeSPAuxAt(node,spaux)

################### Methods that should never be called on particles
  def unregisterFamilyAt(self,node,esrId): raise Exception("Should not be called on a particle")
  def popEsrParentAt(self,node): raise Exception("Should not be called on a particle")
  def childrenAt(self,node): raise Exception("Should not be called on a particle")
  def removeChildAt(self,node,child): raise Exception("Should not be called on a particle")
  def decRequestsAt(self,node): raise Exception("Should not be called on a particle")
  def unregisterAEKernel(self,node): raise Exception("Should not be called on a particle")
  def unregisterConstrainedChoice(self,node): raise Exception("Should not be called on a particle")
  def decRegenCountAt(self,scaffold,node): raise Exception("Should never be called on a particle")
  def numRequestsAt(self,node): raise Exception("Should not be called on a particle")

