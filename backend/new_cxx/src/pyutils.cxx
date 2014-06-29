#include "pyutils.h"
#include "values.h"

#include <iostream>

using std::cout;
using std::endl;

VentureValuePtr parseSimplex(boost::python::object value)
{
  boost::python::extract<boost::python::list> getList(value);
  if (!getList.check()) { throw "Simplex point must be a list."; }
  
  boost::python::list l = getList();
  
  boost::python::ssize_t len = boost::python::len(l);
  Simplex s;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    s.push_back(boost::python::extract<double>(l[i]));
  }
  
  return VentureValuePtr(new VentureSimplex(s));
}

VentureValuePtr parseList(boost::python::object value)
{
  boost::python::extract<boost::python::list> getList(value);
  if (!getList.check()) throw "Not a list: " + boost::python::str(value);
  boost::python::list l = getList();
  
  boost::python::ssize_t len = boost::python::len(l);
  vector<VentureValuePtr> v;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    v.push_back(parseValue(boost::python::extract<boost::python::dict>(l[i])));
  }
  
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr parseVector(boost::python::object value)
{
  boost::python::extract<boost::python::list> getList(value);
  if (!getList.check()) throw "Not a list: " + boost::python::str(value);
  boost::python::list l = getList();

  boost::python::ssize_t len = boost::python::len(l);
  VectorXd v(len);

  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    VentureValuePtr val = parseValue(boost::python::extract<boost::python::dict>(l[i]));
    v[i] = val->getDouble();
  }

  return VentureValuePtr(new VentureVector(v));
}

VentureValuePtr parseTuple(boost::python::object value)
{
  boost::python::extract<boost::python::tuple> getTuple(value);
  if (!getTuple.check()) throw "Not a tuple: " + boost::python::str(value);
  boost::python::tuple t = getTuple();
  
  boost::python::ssize_t len = boost::python::len(t);
  vector<VentureValuePtr> v;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    v.push_back(fromPython(t[i]));
  }
  
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr parseDict(boost::python::object value)
{
  boost::python::extract<boost::python::dict> getDict(value);
  if (!getDict.check()) { throw "Dict must be a dict."; }
  
  boost::python::dict d = getDict();
  
  boost::python::ssize_t len = boost::python::len(d);
  boost::python::list keys = d.keys();
  boost::python::list vals = d.values();

  MapVVPtrVVPtr m;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    VentureValuePtr k = fromPython(keys[i]);
    boost::python::extract<boost::python::dict> v(vals[i]);
    m[k] = parseValue(v);
  }
  
  return VentureValuePtr(new VentureDictionary(m));
}

VentureValuePtr fromPython(boost::python::object o)
{
  boost::python::extract<string> s(o);
  if (s.check()) { return VentureValuePtr(new VentureSymbol(s)); }
  
  boost::python::extract<int> i(o);
  if (i.check()) { return VentureValuePtr(new VentureNumber(i)); }
  
  boost::python::extract<double> d(o);
  if (d.check()) { return VentureValuePtr(new VentureNumber(d)); }

  boost::python::extract<bool> b(o);
  if (b.check()) { return VentureValuePtr(new VentureBool(b)); }

  boost::python::extract<boost::python::list> l(o);
  if (l.check()) { return parseList(l); }
  
  boost::python::extract<boost::python::tuple> t(o);
  if (t.check()) { return parseTuple(t); }
  
  boost::python::extract<boost::python::dict> dict(o);
  if (dict.check()) { return parseDict(dict); }

  throw "Failed to parse python object: " + boost::python::str(o);
}

VentureValuePtr parseValue(boost::python::dict d)
{
  string type = boost::python::extract<string>(d["type"]);
  boost::python::object value = d["value"];

  if (type == "boolean") { return VentureValuePtr(new VentureBool(boost::python::extract<bool>(value))); }
  else if (type == "number") { return VentureValuePtr(new VentureNumber(boost::python::extract<double>(value))); }
  else if (type == "real") { return VentureValuePtr(new VentureNumber(boost::python::extract<double>(value))); }
  else if (type == "integer") { return VentureValuePtr(new VentureNumber(boost::python::extract<double>(value))); }
  else if (type == "probability") { return VentureValuePtr(new VentureNumber(boost::python::extract<double>(value))); }
  else if (type == "symbol") { return VentureValuePtr(new VentureSymbol(boost::python::extract<string>(value))); }
  else if (type == "atom") { return VentureValuePtr(new VentureAtom(boost::python::extract<uint32_t>(value))); }
  else if (type == "simplex") { return parseSimplex(value); }
  else if (type == "array") { return parseList(value); }
  else if (type == "vector") { return parseVector(value); }
  else if (type == "dict") { return parseDict(value); }
  else { throw "Unknown type '" + type + "'"; }
}

VentureValuePtr parseExpression(boost::python::object o)
{
  boost::python::extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return VentureValuePtr(parseValue(getDict())); }
  
  boost::python::extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
  
  vector<VentureValuePtr> exp;
  
  boost::python::ssize_t L = boost::python::len(l);
  
  for(boost::python::ssize_t i=0; i<L; ++i)
  {
    exp.push_back(parseExpression(l[i]));
  }
  return VentureValuePtr(new VentureArray(exp));
}
