#ifndef DISCRETE_PSPS_H
#define DISCRETE_PSPS_H

#include "psp.h"
#include "args.h"

struct BernoulliOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};


#endif
