#ifndef SP_H
#define SP_H

#include "types.h"
#include "value.h"
#include <map>

#include <gsl/gsl_rng.h>

struct SPAux;
struct LSR;
struct LatentDB;
struct PSP;
struct ApplicationNode;
struct RequestNode;
struct OutputNode;
struct Args;

struct VentureSPRef : VentureValue
{
  VentureSPRef(Node * makerNode): makerNode(makerNode) {}
  Node * makerNode;

  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;

};

struct SPFamilies
{
  SPFamilies() {}
  SPFamilies(const VentureValuePtrMap<RootOfFamily> & families): families(families) {}

  VentureValuePtrMap<RootOfFamily> families;
  bool containsFamily(FamilyID id);
  RootOfFamily getRootOfFamily(FamilyID id);
  void registerFamily(FamilyID id,RootOfFamily root);
  void unregisterFamily(FamilyID id);
};

struct SPAux
{
  virtual ~SPAux() {}
  // TODO stupid and may make bugs hard to find
  virtual shared_ptr<SPAux> clone() { return shared_ptr<SPAux>(new SPAux()); } 
  virtual boost::python::object toPython(Trace * trace) const;
};

struct SP
{
  SP(PSP * requestPSP, PSP * outputPSP);
  
  shared_ptr<PSP> requestPSP;
  shared_ptr<PSP> outputPSP;
  
  virtual shared_ptr<PSP> getPSP(ApplicationNode * node) const;

  virtual shared_ptr<LatentDB> constructLatentDB() const;
  virtual double simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const;
  virtual double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  virtual bool hasAEKernel() const { return false; }
  virtual void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args, gsl_rng * rng) const;
  
  virtual boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;
};

#endif
