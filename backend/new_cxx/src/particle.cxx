#include "particle.h"
#include "concrete_trace.h"

Particle::Particle(ConcreteTrace * outerTrace): baseTrace(outerTrace) {  }
Particle::Particle(shared_ptr<Particle> outerParticle):
  baseTrace(outerParticle->baseTrace),
  unconstrainedChoices(outerParticle->unconstrainedChoices),
  constrainedChoices(outerParticle->constrainedChoices),
  arbitraryErgodicKernels(outerParticle->arbitraryErgodicKernels),

  families(outerParticle->families),

  scopes(outerParticle->scopes),

  esrRoots(outerParticle->esrRoots),
  numRequests(outerParticle->numRequests),

  values(outerParticle->values),
  madeSPs(outerParticle->madeSPs),

  regenCounts(outerParticle->regenCounts),

  newMadeSPFamilies(outerParticle->newMadeSPFamilies),
  newChildren(outerParticle->newChildren)

  {
    for (map<Node*, shared_ptr<SPAux> >::iterator iter = outerParticle->madeSPAuxs.begin();
      iter != outerParticle->madeSPAuxs.end();
      ++iter)
    {
      madeSPAuxs[iter->first] = iter->second->clone();
    }
  }

/* Methods */

/* Registering metadata */
void Particle::registerAEKernel(Node * node) 
{
  arbitraryErgodicKernels = arbitraryErgodicKernels.insert(node);
}

void Particle::registerUnconstrainedChoice(Node * node) 
{ 
  unconstrainedChoices = unconstrainedChoices.insert(node);
  registerUnconstrainedChoiceInScope(VentureValuePtr(new VentureSymbol("default")),
			       VentureValuePtr(new VentureNode(node)),
			       node);
}

void Particle::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  assert(block);
  if (!scopes.contains(scope)) { scopes = scopes.insert(scope,PMap<BlockID,PSet<Node*> >()); }
  if (!scopes.lookup(scope).contains(block)) 
  { 
    PMap<BlockID,PSet<Node*> > newBlock = scopes.lookup(scope).insert(block,PSet<Node*>());
    scopes = scopes.insert(scope,newBlock);
 } 
  PSet<Node*> newPNodes = scopes.lookup(scope).lookup(block).insert(node);
  scopes = scopes.insert(scope,scopes.lookup(scope).insert(block,newPNodes));
}

void Particle::registerConstrainedChoice(Node * node) 
{ 
  constrainedChoices = constrainedChoices.insert(node);
  unregisterUnconstrainedChoice(node);
}


/* Unregistering metadata */
void Particle::unregisterUnconstrainedChoice(Node * node) 
{ 
  assert(unconstrainedChoices.contains(node));
  unconstrainedChoices = unconstrainedChoices.remove(node);
  unregisterUnconstrainedChoiceInScope(VentureValuePtr(new VentureSymbol("default")),
				 VentureValuePtr(new VentureNode(node)),
				 node);
}

void Particle::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{
  PSet<Node*> newPNodes = scopes.lookup(scope).lookup(block).remove(node);
  scopes = scopes.insert(scope,scopes.lookup(scope).insert(block,newPNodes));

  if (scopes.lookup(scope).lookup(block).size() == 0)
  { 
    scopes = scopes.insert(scope,scopes.lookup(scope).remove(block));
  }
  if (scopes.lookup(scope).size() == 0)
  {
    scopes = scopes.remove(scope);
  }
}

/* Regen mutations */
void Particle::addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) 
{
  // Note: this mutates, because it never crosses a particle
  assert(baseTrace->getESRParents(outputNode).empty());
  if (!esrRoots.contains(outputNode)) { esrRoots = esrRoots.insert(outputNode,vector<RootOfFamily>()); }
  esrRoots.lookup(outputNode).push_back(esrRoot);
}

void Particle::reconnectLookup(LookupNode * lookupNode) { assert(false); }
void Particle::incNumRequests(RootOfFamily root) 
{
  if (!numRequests.contains(root)) { numRequests = numRequests.insert(root,baseTrace->getNumRequests(root)); }
  numRequests = numRequests.insert(root,numRequests.lookup(root) + 1);
}
void Particle::incRegenCount(shared_ptr<Scaffold> scaffold,Node * node) 
{
  if (!regenCounts.contains(node)) { regenCounts = regenCounts.insert(node,0); }
  regenCounts = regenCounts.insert(node,regenCounts.lookup(node) + 1);
}

void Particle::addChild(Node * node, Node * child) 
{ 
  if (!newChildren.contains(node)) { newChildren = newChildren.insert(node,PSet<Node*>()); }
  newChildren = newChildren.insert(node, newChildren.lookup(node).insert(child)); 
}


/* Primitive getters */
gsl_rng * Particle::getRNG() { return baseTrace->getRNG(); }

VentureValuePtr Particle::getValue(Node * node) 
{ 
  if (values.contains(node)) { return values.lookup(node); }
  else { return baseTrace->getValue(node); }
}

shared_ptr<SP> Particle::getMadeSP(Node * makerNode)
{
  if (madeSPs.contains(makerNode)) { return madeSPs.lookup(makerNode); }
  else { return baseTrace->getMadeSP(makerNode); }
}

shared_ptr<SPAux> Particle::getMadeSPAux(Node * makerNode)
{
  if (!madeSPAuxs.count(makerNode))
  {
    if (baseTrace->getMadeSPAux(makerNode))
    {
      madeSPAuxs[makerNode] = baseTrace->getMadeSPAux(makerNode)->clone();
    }
    else { return shared_ptr<SPAux>(); }
  }
  return madeSPAuxs[makerNode];
}


vector<RootOfFamily> Particle::getESRParents(Node * node) 
{
  if (esrRoots.contains(node)) { return esrRoots.lookup(node); }
  else { return baseTrace->getESRParents(node); }
}

int Particle::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) 
{ 
  assert(baseTrace->getRegenCount(scaffold,node) == 0);
  if (regenCounts.contains(node)) { return regenCounts.lookup(node); }
  else { return baseTrace->getRegenCount(scaffold,node); }
}

VentureValuePtr Particle::getObservedValue(Node * node) { assert(false); }


/* Primitive setters */
void Particle::setValue(Node * node, VentureValuePtr value) 
{ 
  assert(!baseTrace->getValue(node)); // TODO might not work
  values = values.insert(node,value);
}

void Particle::clearValue(Node * node)  { setValue(node,VentureValuePtr()); }


void Particle::setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord) 
{ 
  madeSPs = madeSPs.insert(makerNode,spRecord->sp);
  madeSPAuxs[makerNode] = spRecord->spAux;
  newMadeSPFamilies = newMadeSPFamilies.insert(makerNode,PMap<FamilyID,RootOfFamily>());
}


void Particle::setMadeSP(Node * makerNode,shared_ptr<SP> sp) 
{ 
  assert(!madeSPs.contains(makerNode));
  assert(!baseTrace->getMadeSP(makerNode));
  madeSPs = madeSPs.insert(makerNode,sp);
}

void Particle::setMadeSPAux(Node * makerNode,shared_ptr<SPAux> spAux) 
{ 
  assert(!madeSPAuxs.count(makerNode));
  assert(!baseTrace->getMadeSPAux(makerNode));
  madeSPAuxs[makerNode] = spAux;
}


/* SPFamily operations */
void Particle::registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot) 
{ 
  if (!newMadeSPFamilies.contains(makerNode))
  {
    newMadeSPFamilies = newMadeSPFamilies.insert(makerNode,PMap<FamilyID,RootOfFamily>());
  }
  newMadeSPFamilies = newMadeSPFamilies.insert(makerNode,newMadeSPFamilies.lookup(makerNode).insert(id,esrRoot));    
}

bool Particle::containsMadeSPFamily(Node * makerNode, FamilyID id) 
{ 
  if (newMadeSPFamilies.contains(makerNode))
  {
    if (newMadeSPFamilies.lookup(makerNode).contains(id)) { return true; }
  }
  else if (baseTrace->getMadeSPFamilies(makerNode)->containsFamily(id)) { return true; }
  return false;
}

RootOfFamily Particle::getMadeSPFamilyRoot(Node * makerNode, FamilyID id) 
{ 
  if (newMadeSPFamilies.contains(makerNode) && newMadeSPFamilies.lookup(makerNode).contains(id))
  {
    return newMadeSPFamilies.lookup(makerNode).lookup(id);
  }
  else
  {
    return baseTrace->getMadeSPFamilyRoot(makerNode,id);
  }
}

/* Inference (computing reverse weight) */
int Particle::numBlocksInScope(ScopeID scope) { return scopes.lookup(scope).size() + baseTrace->numBlocksInScope(scope); }

void Particle::commit()
{
  // note that we do not call registerUnconstrainedChoice() because it in turn calls registerUnconstrainedChoiceInScope()
  vector<Node*> ucs = unconstrainedChoices.keys();
  baseTrace->unconstrainedChoices.insert(ucs.begin(), ucs.end());
  
  // note that we do not call registerConstrainedChoice() because it in turn calls unregisterUnconstrainedChoice()
  vector<Node*> ccs = constrainedChoices.keys();
  baseTrace->constrainedChoices.insert(ccs.begin(), ccs.end());

  // probably could call the appropriate register methods here
  vector<Node*> aes = arbitraryErgodicKernels.keys();
  baseTrace->arbitraryErgodicKernels.insert(aes.begin(), aes.end());
  
  vector<pair<Node*, VentureValuePtr> > valueItems = values.items();
  baseTrace->values.insert(valueItems.begin(), valueItems.end());
  
  vector<pair<Node*, shared_ptr<SP> > > madeSPItems = madeSPs.items();
  for (size_t madeSPIndex = 0; madeSPIndex < madeSPItems.size(); ++madeSPIndex)
  {
    pair<Node*, shared_ptr<SP> > madeSPItem = madeSPItems[madeSPIndex];
    baseTrace->setMadeSPRecord(madeSPItem.first, shared_ptr<VentureSPRecord>(new VentureSPRecord(madeSPItem.second)));
  }
  
  // this iteration includes "default"
  vector<pair<ScopeID,PMap<BlockID,PSet<Node*> > > > scopeItems = scopes.items();
  for (size_t scopeIndex = 0; scopeIndex < scopeItems.size(); ++scopeIndex)
  {
    pair<ScopeID,PMap<BlockID,PSet<Node*> > >& scopeItem = scopeItems[scopeIndex];
    vector<pair<BlockID,PSet<Node*> > > blockItems = scopeItem.second.items();
    
    for (size_t blockIndex = 0; blockIndex < blockItems.size(); ++blockIndex)
    {
      pair<BlockID,PSet<Node*> >& blockItem = blockItems[blockIndex];
      vector<Node*> nodes = blockItem.second.keys();
      
      for (size_t nodeIndex = 0; nodeIndex < nodes.size(); ++nodeIndex)
      {
        baseTrace->registerUnconstrainedChoiceInScope(scopeItem.first, blockItem.first, nodes[nodeIndex]);
      }
    }
  }
  
  vector<pair<Node*, vector<RootOfFamily> > > esrItems = esrRoots.items();
  for (size_t esrIndex = 0; esrIndex < esrItems.size(); ++esrIndex)
  {
    pair<Node*, vector<RootOfFamily> >& esrItem = esrItems[esrIndex];
    baseTrace->setESRParents(esrItem.first, esrItem.second);
  }
  
  vector<pair<RootOfFamily, int> > numRequestsItems = numRequests.items();
  for (size_t numRequestsIndex = 0; numRequestsIndex < numRequestsItems.size(); ++numRequestsIndex)
  {
    pair<RootOfFamily, int>& numRequestsItem = numRequestsItems[numRequestsIndex];
    baseTrace->setNumRequests(numRequestsItem.first, numRequestsItem.second);
  }
  
  vector<pair<Node*, PMap<FamilyID,RootOfFamily> > > newMadeSPFamiliesItems = newMadeSPFamilies.items();
  for (size_t newMadeSPFamiliesIndex = 0; newMadeSPFamiliesIndex < newMadeSPFamiliesItems.size(); ++newMadeSPFamiliesIndex)
  {
    pair<Node*, PMap<FamilyID,RootOfFamily> >& newMadeSPFamilyItem = newMadeSPFamiliesItems[newMadeSPFamiliesIndex];
    baseTrace->addNewMadeSPFamilies(newMadeSPFamilyItem.first, newMadeSPFamilyItem.second);
  }
  
  vector<pair<Node*, PSet<Node*> > > newChildrenItems = newChildren.items();
  for (size_t newChildrenIndex = 0; newChildrenIndex < newChildrenItems.size(); ++newChildrenIndex)
  {
    pair<Node*, PSet<Node*> >& newChildrenItem = newChildrenItems[newChildrenIndex];
    baseTrace->addNewChildren(newChildrenItem.first, newChildrenItem.second);
  }
  
  vector<pair<Node*, shared_ptr<SPAux> > > madeSPAuxItems(madeSPAuxs.begin(), madeSPAuxs.end());
  for (size_t madeSPAuxIndex = 0; madeSPAuxIndex < madeSPAuxItems.size(); ++madeSPAuxIndex)
  {
    pair<Node*, shared_ptr<SPAux> > madeSPAuxItem = madeSPAuxItems[madeSPAuxIndex];
    baseTrace->setMadeSPAux(madeSPAuxItem.first, madeSPAuxItem.second);
  }
}

/* The following should never be called on particles */


RootOfFamily Particle::popLastESRParent(OutputNode * outputNode) { assert(false); throw "should never be called"; }
void Particle::disconnectLookup(LookupNode * lookupNode) { assert(false); throw "should never be called"; }
void Particle::decNumRequests(RootOfFamily root) { assert(false); throw "should never be called"; }
void Particle::decRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); throw "should never be called"; }
void Particle::removeChild(Node * node, Node * child) { assert(false); throw "should never be called"; }
void Particle::unregisterAEKernel(Node * node) { assert(false); throw "should never be called"; }

void Particle::unregisterConstrainedChoice(Node * node) { assert(false); throw "should never be called"; }
set<Node*> Particle::getChildren(Node * node) { assert(false); throw "should never be called"; }
int Particle::getNumRequests(RootOfFamily root) { assert(false); throw "should never be called"; }

void Particle::destroyMadeSPRecord(Node * makerNode) { assert(false); }
void Particle::unregisterMadeSPFamily(Node * makerNode,FamilyID id) { assert(false); }

/* Probably called */
bool Particle::isMakerNode(Node * node) { assert(false); }
bool Particle::isConstrained(Node * node) { assert(false); }
bool Particle::isObservation(Node * node) { assert(false); }


/* Probably not called */
void Particle::setChildren(Node * node,set<Node*> children) { assert(false); }
void Particle::setESRParents(Node * node,const vector<RootOfFamily> & esrRoots) { assert(false); }

void Particle::setNumRequests(RootOfFamily node,int num) { assert(false); }
