#include "sps/betabernoulli.h"

#include "utils.h"
#include "sprecord.h"

#include "gsl/gsl_sf_gamma.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include "sps/numerical_helpers.h"

#include <boost/math/special_functions/binomial.hpp>

VentureValuePtr MakeBetaBernoulliOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("make_beta_bernoulli", args, 2);
  
  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new BetaBernoulliOutputPSP(alpha, beta);
  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP,outputPSP),new BetaBernoulliSPAux()));
}

// BetaBernoulliOutputPSP

VentureValuePtr BetaBernoulliOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<BetaBernoulliSPAux> aux = dynamic_pointer_cast<BetaBernoulliSPAux>(args->spAux);
  double a = alpha + aux->heads;
  double b = beta + aux->tails;
  double w = a / (a + b);
  return VentureValuePtr(new VentureBool(gsl_ran_flat(rng,0.0,1.0) < w));
}

double BetaBernoulliOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<BetaBernoulliSPAux> aux = dynamic_pointer_cast<BetaBernoulliSPAux>(args->spAux);
  double a = alpha + aux->heads;
  double b = beta + aux->tails;
  double w = a / (a + b);
  if (value->getBool()) { return log(w); }
  else { return log(1-w); }
}

void BetaBernoulliOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<BetaBernoulliSPAux> aux = dynamic_pointer_cast<BetaBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads++; }
  else { aux->tails++; }
}
void BetaBernoulliOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<BetaBernoulliSPAux> aux = dynamic_pointer_cast<BetaBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads--; }
  else { aux->tails--; }
}

double BetaBernoulliOutputPSP::logDensityOfCounts(shared_ptr<SPAux> aux) const 
{
  shared_ptr<BetaBernoulliSPAux> spAux = dynamic_pointer_cast<BetaBernoulliSPAux>(aux);


  int heads = spAux->heads;
  int tails = spAux->tails;

  int N = heads + tails;
  double A = alpha + beta;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  x += gsl_sf_lngamma(alpha + heads) - gsl_sf_lngamma(alpha);
  x += gsl_sf_lngamma(beta + tails) - gsl_sf_lngamma(beta);
  return x;
}

// MakeUncollapsed

VentureValuePtr MakeUBetaBernoulliOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  double p = gsl_ran_beta(rng,alpha,beta);

  UBetaBernoulliSPAux * aux = new UBetaBernoulliSPAux(p);
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new UBetaBernoulliOutputPSP();
  return VentureValuePtr(new VentureSPRecord(new UBetaBernoulliSP(requestPSP,outputPSP),aux));
}

double MakeUBetaBernoulliOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  assert(args->operandValues.size() == 2);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();
  
  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<UBetaBernoulliSPAux> spAux = dynamic_pointer_cast<UBetaBernoulliSPAux>(spRecord->spAux);
  assert(spAux);

  return BetaDistributionLogLikelihood(spAux->p,alpha,beta);
}

// Uncollapsed SP

void UBetaBernoulliSP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const 
{ 
  assert(args->operandValues.size() == 2);
  shared_ptr<UBetaBernoulliSPAux> aux = dynamic_pointer_cast<UBetaBernoulliSPAux>(spAux);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  int heads = aux->heads;
  int tails = aux->tails;

  aux->p = gsl_ran_beta(rng,alpha + heads,beta + tails);
}

// Uncollapsed PSP

VentureValuePtr UBetaBernoulliOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<UBetaBernoulliSPAux> aux = dynamic_pointer_cast<UBetaBernoulliSPAux>(args->spAux);
  int n = gsl_ran_bernoulli(rng,aux->p);
  if (n == 0) { return VentureValuePtr(new VentureBool(false)); }
  else if (n == 1) { return VentureValuePtr(new VentureBool(true)); }
  else { assert(false); }
}

double UBetaBernoulliOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UBetaBernoulliSPAux> aux = dynamic_pointer_cast<UBetaBernoulliSPAux>(args->spAux);
  double p = aux->p;
  if (value->getBool()) { return log(p); }
  else { return log(1-p); }
}

void UBetaBernoulliOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UBetaBernoulliSPAux> aux = dynamic_pointer_cast<UBetaBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads++; }
  else { aux->tails++; }
}

void UBetaBernoulliOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UBetaBernoulliSPAux> aux = dynamic_pointer_cast<UBetaBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads--; }
  else { aux->tails--; }
}

// Auxs
SPAux* BetaBernoulliSPAux::copy_help(ForwardingMap m)  { return new BetaBernoulliSPAux(*this);  }
SPAux* UBetaBernoulliSPAux::copy_help(ForwardingMap m) { return new UBetaBernoulliSPAux(*this); }








