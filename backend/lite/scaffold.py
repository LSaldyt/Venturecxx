from node import ConstantNode, LookupNode, RequestNode, OutputNode
from value import SPRef
from omegadb import OmegaDB
from detach import unapplyPSP
from regen import applyPSP

class Scaffold(object):
  def __init__(self,setsOfPNodes=None,regenCounts=None,absorbing=None,aaa=None,border=None,lkernels=None,brush=None):
    self.setsOfPNodes = setsOfPNodes if setsOfPNodes else [] # [Set Node]
    self.regenCounts = regenCounts if regenCounts else {} # {Node:Int}
    self.absorbing = absorbing if absorbing else set() # Set Node
    self.aaa = aaa if aaa else set() # Set Node
    self.border = border if border else [] # [[Node]]
    self.lkernels = lkernels if lkernels else {} # {Node:LKernel}
    self.brush = brush if brush else set() # Set Node

  def getPrincipalNodes(self):
    # Return a list so that repeated traversals have the same order
    return [n for n in set.union(*self.setsOfPNodes)]
  def getRegenCount(self,node): return self.regenCounts[node]
  def incrementRegenCount(self,node): self.regenCounts[node] += 1
  def decrementRegenCount(self,node): self.regenCounts[node] -= 1
  def isResampling(self,node): return node in self.regenCounts
  def isAbsorbing(self,node): return node in self.absorbing
  def isAAA(self,node): return node in self.aaa
  def hasLKernel(self,node): return node in self.lkernels
  def getLKernel(self,node): return self.lkernels[node]
  def getPNode(self):
    assert len(self.setsOfPNodes) == 1
    pnodes = []
    for pnode in self.setsOfPNodes[0]: pnodes.append(pnode)
    assert len(pnodes) == 1
    return pnodes[0]
  def isBrush(self, node): return node in self.brush

  def show(self):
    print "---Scaffold---"
    print "# pnodes: " + str(len(self.getPrincipalNodes()))
    print "# absorbing nodes: " + str(len(self.absorbing))
    print "# aaa nodes: " + str(len(self.aaa))
    print "border lengths: " + str([len(segment) for segment in self.border])
    print "# lkernels: " + str(len(self.lkernels))

  def showMore(self):
    print "---Scaffold---"
    print "pnodes: " + str(self.getPrincipalNodes())
    print "absorbing nodes: " + str(self.absorbing)
    print "aaa nodes: " + str(self.aaa)
    print "borders: " + str(self.border)
    print "lkernels: " + str(self.lkernels)

"""
When subsampled_mh is called, there will exist broken deterministic relationships in the trace.
For example, in the program:
[assume mu (normal 0 1)]
[assume x (lambda () (normal mu 1))]
[observe (x) 0.1]
[observe (x) 0.2]
...
N observations
...
After mu is updated. If a subsampled scaffold only include the first n observations,
the lookup nodes for mu in the remaining N-n observations will have a stale value.
At a second call to infer, these inconsistency may cause a problem.

updateValuesAtScaffold updates all the nodes in a newly constructed scaffold by
calling updateValueAtNode for each node. The main idea is that:
Assume all the random output nodes have the latest values and the problem is in
the nodes with determnistic dependency on their parents.
For every node that cannot absorb, update the value of all its parents, and then
unapplyPSP and apply PSP. For a request node, compare its old Request with the new
request. If they are different, unevalRequests and evalRequests to generate new
ESRs. When a new ESR is generated, return True. Otherwise return false.
"""
#FIXME(Yutian): At regen phase in proposal, value should also be updated. This will
#involve changing the regen method.
def updateValuesAtScaffold(trace,scaffold,updatedNodes):
  # for every node in the scaffold (resampling, brush, border) update values.
  # return true if any node gets a new value.
  hasNewEsr = False
  #for node in scaffold.brush:
  #  hasNewEsr |= updateValueAtNode(trace, scaffold, node, updatedNodes)
  for node in scaffold.regenCounts:
    hasNewEsr |= updateValueAtNode(trace, scaffold, node, updatedNodes)
  #for borderList in scaffold.border:
  #  for node in borderList:
  #    hasNewEsr |= updateValueAtNode(trace, scaffold, node, updatedNodes)

  return hasNewEsr

def updateValueAtNode(trace, scaffold, node, updatedNodes):
  # Return True if a new value is assigned.
  if node in updatedNodes:
    return False

  # Strong assumption! Only consider resampling nodes in the scaffold.
  if not scaffold.isResampling(node):
    return False

  hasNewEsr = False
  if isinstance(node, ConstantNode):
    return False
  elif isinstance(node, LookupNode):
    hasNewEsr |= updateValueAtNode(trace, scaffold, node.sourceNode, updatedNodes)
    trace.setValueAt(node, trace.valueAt(node.sourceNode))
  elif isinstance(node, RequestNode):
    return False
  else: # OutputNode.
    # Assume SPRef and AAA nodes are always updated.
    psp = trace.pspAt(node)
    if isinstance(trace.valueAt(node), SPRef) or psp.childrenCanAAA():
      pass

    canAbsorb = True
    for parent in trace.parentsAt(node):
      if not psp.canAbsorb(trace, node, parent):
        hasNewEsr |= updateValueAtNode(trace, scaffold, parent, updatedNodes)
        canAbsorb = False

    # Assume AAA node is always updated
    if not canAbsorb:
      #DEBUG
      #scaffold = Scaffold()
      #omegaDB = OmegaDB()
      #oldValue = trace.valueAt(node)
      # DEBUG
      #unapplyPSP(trace, node, scaffold, omegaDB)
      #applyPSP(trace,node,scaffold,False,omegaDB,{})
      updateValue(trace, node)
      #print "Regen output node", oldValue, trace.valueAt(node), psp

  #hasNewEsr = False
  #if isinstance(node, ConstantNode):
  #  pass
  #elif isinstance(node, LookupNode):
  #  hasNewEsr |= updateValueAtNode(trace, scaffold, node.sourceNode, updatedNodes)
  #  trace.setValueAt(node, trace.valueAt(node.sourceNode))
  #else: # Application Node.
  #  psp = trace.pspAt(node)
  #  canAbsorb = True
  #  for parent in trace.parentsAt(node):
  #    canAbsorb &= psp.canAbsorb(trace, node, parent)
  #  # Assume AAA node is always updated
  #  if not canAbsorb and not psp.childrenCanAAA():
  #    # psp can not absorb for all the paretns
  #    for parent in trace.definiteParentsAt(node):
  #      hasNewEsr |= updateValueAtNode(trace, scaffold, parent, updatedNodes)

  #    # Update esrParent value after update the value of the request node.
  #    if isinstance(node, OutputNode):
  #      for esrParent in trace.esrParentsAt(node):
  #        hasNewEsr |= updateValueAtNode(trace, scaffold, esrParent, updatedNodes)

  #    # Regen value.
  #    if isinstance(node, RequestNode):
  #      # FIXME: only checked the value of esrs (in string)
  #      # FIXME: psp is unapplied before unevalRequests, and the args of psp may not be the same as they were used for applyPSP. Problem for AAA?
  #      #DEBUG
  #      #print "Regen request node", psp

  #      #scaffold = Scaffold()
  #      #omegaDB = OmegaDB()
  #      #old_request = trace.valueAt(node)
  #      ##DEBUG
  #      #spf = trace.spFamiliesAt(node)
  #      #for esr in old_request.esrs:
  #      #  if esr.id not in spf.families:
  #      #    print "strange"

  #      #unapplyPSP(trace, node, scaffold, omegaDB)
  #      #applyPSP(trace,node,scaffold,False,omegaDB,{})
  #      #new_request = trace.valueAt(node)

  #      ##DEBUG
  #      #spf = trace.spFamiliesAt(node)
  #      #for esr in new_request.esrs:
  #      #  if esr.id not in spf.families:
  #      #    print "strange"

  #      #eq_request = len(old_request.esrs) == len(new_request.esrs)
  #      #if eq_request:
  #      #  for i in range(len(old_request.esrs)):
  #      #    if not old_request.esrs[i].id == new_request.esrs[i].id:
  #      #      eq_request = False
  #      #      break
  #      #if not eq_request:
  #      #  #DEBUG
  #      #  old_request_str = str(old_request.esrs)
  #      #  new_request_str = str(new_request.esrs)
  #      #  print "not equal request", old_request_str, new_request_str
  #      #  trace.setValueAt(node, old_request)
  #      #  unevalRequests(trace, node, scaffold, omegaDB, compute_gradient)
  #      #  trace.setValueAt(node, new_request)
  #      #  evalRequests(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  #      #  hasNewEsr |= True
  #      pass
  #    else: # OutputNode
  #      if not isinstance(trace.valueAt(node), SPRef):
  #        #DEBUG
  #        scaffold = Scaffold()
  #        omegaDB = OmegaDB()
  #        #oldValue = trace.valueAt(node)
  #        # DEBUG
  #        #unapplyPSP(trace, node, scaffold, omegaDB)
  #        #applyPSP(trace,node,scaffold,False,omegaDB,{})
  #        updateValue(trace, node, scaffold, omegaDB)
  #        #print "Regen output node", oldValue, trace.valueAt(node), psp

  updatedNodes.add(node)
  return hasNewEsr

# DEBUG, for cprofiler only
def updateValue(trace, node):
  scaffold = Scaffold()
  omegaDB = OmegaDB()
  unapplyPSP(trace, node, scaffold, omegaDB)
  applyPSP(trace,node,scaffold,False,omegaDB,{})


def constructScaffold(trace,setsOfPNodes,useDeltaKernels = False, deltaKernelArgs = None, updateValue = False, updatedNodes = None):
  if updatedNodes is None:
    updatedNodes = set()
  while True:
    cDRG,cAbsorbing,cAAA = set(),set(),set()
    indexAssignments = {}
    assert isinstance(setsOfPNodes,list)
    for i in range(len(setsOfPNodes)):
      assert isinstance(setsOfPNodes[i],set)
      extendCandidateScaffold(trace,setsOfPNodes[i],cDRG,cAbsorbing,cAAA,indexAssignments,i)

    brush = findBrush(trace,cDRG)
    drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
    border = findBorder(trace,drg,absorbing,aaa)
    regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush)
    lkernels = loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs)
    borderSequence = assignBorderSequnce(border,indexAssignments,len(setsOfPNodes))
    scaffold = Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels,brush)
    if not updateValue or not updateValuesAtScaffold(trace,scaffold,updatedNodes):
      break
  return scaffold

def addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  if node in aaa: aaa.remove(node)
  drg.add(node)
  q.extend([(n,False,node) for n in trace.childrenAt(node)])
  indexAssignments[node] = i

def addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i):
  assert not node in drg
  assert not node in aaa
  absorbing.add(node)
  indexAssignments[node] = i

def addAAANode(drg,aaa,absorbing,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  drg.add(node)
  aaa.add(node)
  indexAssignments[node] = i


def extendCandidateScaffold(trace,pnodes,drg,absorbing,aaa,indexAssignments,i):
  q = [(pnode,True,None) for pnode in pnodes]

  while q:
    node,isPrincipal,parentNode = q.pop()
    if node in drg and not node in aaa:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    elif isinstance(node,LookupNode) or node.operatorNode in drg:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)
    # TODO temporary: once we put all uncollapsed AAA procs into AEKernels, this line won't be necessary
    elif node in aaa:
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)      
    elif (not isPrincipal) and trace.pspAt(node).canAbsorb(trace,node,parentNode):
      addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i)
    elif trace.pspAt(node).childrenCanAAA(): 
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    else: 
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i)


def findBrush(trace,cDRG):
  disableCounts = {}
  disabledRequests = set()
  brush = set()
  for node in cDRG:
    if isinstance(node,RequestNode):
      disableRequests(trace,node,disableCounts,disabledRequests,brush)
  return brush

def disableRequests(trace,node,disableCounts,disabledRequests,brush):
  if node in disabledRequests: return
  disabledRequests.add(node)
  for esrParent in trace.esrParentsAt(node.outputNode):
    if not esrParent in disableCounts: disableCounts[esrParent] = 0
    disableCounts[esrParent] += 1
    if disableCounts[esrParent] == esrParent.numRequests:
      disableFamily(trace,esrParent,disableCounts,disabledRequests,brush)

def disableFamily(trace,node,disableCounts,disabledRequests,brush):
  if node in brush: return
  brush.add(node)
  if isinstance(node,OutputNode):
    brush.add(node.requestNode)
    disableRequests(trace,node.requestNode,disableCounts,disabledRequests,brush)
    disableFamily(trace,node.operatorNode,disableCounts,disabledRequests,brush)
    for operandNode in node.operandNodes: 
      disableFamily(trace,operandNode,disableCounts,disabledRequests,brush)

def removeBrush(cDRG,cAbsorbing,cAAA,brush):
  drg = cDRG - brush
  absorbing = cAbsorbing - brush
  aaa = cAAA - brush
  assert aaa.issubset(drg)
  assert not drg.intersection(absorbing)
  return drg,absorbing,aaa

def hasChildInAorD(trace,drg,absorbing,node):
  kids = trace.childrenAt(node)
  return kids.intersection(drg) or kids.intersection(absorbing)

def findBorder(trace,drg,absorbing,aaa):
  border = absorbing.union(aaa)
  for node in drg - aaa:
    if not hasChildInAorD(trace,drg,absorbing,node): border.add(node)
  return border

def maybeIncrementAAARegenCount(trace,regenCounts,aaa,node):
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode in aaa: 
    regenCounts[value.makerNode] += 1

def computeRegenCounts(trace,drg,absorbing,aaa,border,brush):
  regenCounts = {}
  for node in drg:
    if node in aaa:
      regenCounts[node] = 1 # will be added to shortly
    elif node in border:
      regenCounts[node] = len(trace.childrenAt(node)) + 1
    else:
      regenCounts[node] = len(trace.childrenAt(node))
  
  if aaa:
    for node in drg.union(absorbing):
      for parent in trace.parentsAt(node):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,parent)

    for node in brush:
      if isinstance(node,OutputNode):
        for esrParent in trace.esrParentsAt(node):
          maybeIncrementAAARegenCount(trace,regenCounts,aaa,esrParent)
      elif isinstance(node,LookupNode):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,node.sourceNode)

  return regenCounts

def loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs):
  lkernels = { node : trace.pspAt(node).getAAALKernel() for node in aaa}
  if useDeltaKernels:
    for node in drg - aaa:
      if not isinstance(node,OutputNode): continue
      if node.operatorNode in drg: continue
      for o in node.operandNodes:
        if o in drg: continue
      if trace.pspAt(node).hasDeltaKernel(): lkernels[node] = trace.pspAt(node).getDeltaKernel(deltaKernelArgs)
  return lkernels

def assignBorderSequnce(border,indexAssignments,numIndices):
  borderSequence = [[] for _ in range(numIndices)]
  for node in border:
    borderSequence[indexAssignments[node]].append(node)
  return borderSequence
