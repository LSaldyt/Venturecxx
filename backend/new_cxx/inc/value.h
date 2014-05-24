#ifndef VALUE_H
#define VALUE_H

#include "Eigen/Dense"
#include "types.h"
#include "srs.h"


#include <boost/python/object.hpp>
#include <boost/python/dict.hpp>
#include <boost/unordered_map.hpp>

using Eigen::MatrixXd;
using Eigen::VectorXd;

struct HashVentureValuePtr;
struct VentureValuePtrsEqual;

// Problem: C++ does not admit templated type aliases.
// We would have wanted one for clarity and keystrokes:
//   template <typename T>
//   typedef public boost::unordered_map<VentureValuePtr, T, HashVentureValuePtr, VentureValuePtrsEqual> VentureValuePtrMap;
// but that requires C++11.

// Using an empty inherited class is not so good; in particular, the
// assignment operator we get (either by inheritance or
// autogeneration, who knows?) does not seem to work right.
// template <typename T>
// class VentureValuePtrMap : public boost::unordered_map<VentureValuePtr, T, HashVentureValuePtr, VentureValuePtrsEqual> {};

// We can cover the general case by using a templated struct as a
// namespace, but there are some problems with using this in other
// templates.
template <typename T>
struct VentureValuePtrMap {
  typedef typename boost::unordered_map<VentureValuePtr, T, HashVentureValuePtr, VentureValuePtrsEqual> Type;
};

// Solution: cover the cases we actually use with specific typedefs.
typedef boost::unordered_map<VentureValuePtr, int, HashVentureValuePtr, VentureValuePtrsEqual> MapVVPtrInt;
typedef boost::unordered_map<VentureValuePtr, VentureValuePtr, HashVentureValuePtr, VentureValuePtrsEqual> MapVVPtrVVPtr;
typedef boost::unordered_map<VentureValuePtr, RootOfFamily, HashVentureValuePtr, VentureValuePtrsEqual> MapVVPtrRootOfFamily;

struct SPAux;
struct Trace;

// TODO AXCH
// We need to be more consistent about whether this unboxes
struct VentureValue
{
  virtual bool hasDouble() const; // TODO hack for operator<
  virtual double getDouble() const;

  virtual bool hasInt() const;
  virtual long getInt() const;
  virtual int getAtom() const;
  virtual bool isBool() const;
  virtual bool getBool() const;
  virtual bool hasSymbol() const;
  virtual const string & getSymbol() const;

  virtual string asExpression() const;

  virtual bool hasArray() const { return false; }
  virtual vector<VentureValuePtr> getArray() const;
  virtual bool isNil() const { return false; }
  
  virtual const VentureValuePtr& getFirst() const;
  virtual const VentureValuePtr& getRest() const;
  
  virtual const Simplex& getSimplex() const;
  virtual const MapVVPtrVVPtr& getDictionary() const;

  virtual VectorXd getVector() const;
  virtual MatrixXd getMatrix() const;
  
  virtual const vector<ESR>& getESRs() const;
  virtual const vector<shared_ptr<LSR> >& getLSRs() const;

  bool hasNode() const { return false; }
  virtual Node * getNode() const;

  virtual shared_ptr<SPAux> getSPAux() const;

  /* for containers */
  virtual VentureValuePtr lookup(VentureValuePtr index) const;
  virtual bool contains(VentureValuePtr index) const;
  virtual int size() const;
  
  virtual boost::python::dict toPython(Trace * trace) const;

  /* for unordered_maps */
  virtual bool equals(const VentureValuePtr & other) const;
  virtual bool equalsSameType(const VentureValuePtr & other) const;
  virtual size_t hash() const;
  
  virtual string toString() const { return "Unknown VentureValue"; };

  virtual bool operator<(const VentureValuePtr & rhs) const;
  virtual bool ltSameType(const VentureValuePtr & rhs) const;

  virtual VentureValue* copy_help(ForwardingMap* m) { return this; }

  virtual ~VentureValue() {}
};



inline bool operator==(const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return lhs->equals(rhs); }
inline bool operator!=(const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return !operator==(lhs,rhs);}
inline bool operator< (const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return lhs->operator<(rhs); }
inline bool operator> (const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return  operator< (rhs,lhs);}
inline bool operator<=(const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return !operator> (lhs,rhs);}
inline bool operator>=(const VentureValuePtr& lhs, const VentureValuePtr& rhs){ return !operator< (lhs,rhs);}

/* for unordered map */
struct VentureValuePtrsEqual
{
  bool operator() (const VentureValuePtr& a, const VentureValuePtr& b) const
  {
    return a->equals(b);
  }
};

struct HashVentureValuePtr
{
  size_t operator() (const VentureValuePtr& a) const
  {
    return a->hash();
  }
};

struct VentureValuePtrsLess
{
  bool operator() (const VentureValuePtr& a, const VentureValuePtr& b) const
  {
    return a < b;
  }
};

#endif
