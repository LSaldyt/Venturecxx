#include "sps/numerical_helpers.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include <cmath>
#include <cfloat>

using std::isfinite;

// LogLikelihoods, from Yura's Utilities.cpp
double NormalDistributionLogLikelihood(double sampled_value, double average, double sigma) {
  double loglikelihood = 0.0;
  loglikelihood -= log(sigma);
  loglikelihood -= 0.5 * log(2.0 * 3.14159265358979323846264338327950);
  double deviation = sampled_value - average;
  loglikelihood -= 0.5 * deviation * deviation / (sigma * sigma);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double GammaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //b^a * x^{a-1} * e^{-b * x} / Gamma(a)
  if (sampled_value <= 0.0) {
    return log(0.0);
  }
  double loglikelihood = alpha * log(beta);
  loglikelihood += (alpha - 1.0) * log(sampled_value);
  loglikelihood -= beta * sampled_value;
  loglikelihood -= gsl_sf_lngamma(alpha);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double InvGammaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //b^a * x^{-a-1} * e^{-b / x} / Gamma(a)
  double loglikelihood = alpha * log(beta);
  loglikelihood -= (alpha + 1.0) * log(sampled_value);
  loglikelihood -= beta / sampled_value;
  loglikelihood -= gsl_sf_lngamma(alpha);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }

  return loglikelihood;
}

double BetaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //x^{a-1} * (1-x)^{b-1} / Beta(a, b)
  double loglikelihood = 0.0;
  loglikelihood += (alpha - 1.0) * log(sampled_value);
  loglikelihood += (beta - 1.0) * log(1.0 - sampled_value);
  loglikelihood -= gsl_sf_lnbeta(alpha, beta);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double ChiSquaredDistributionLogLikelihood(double sampled_value, double nu) {
  //(x / 2)^{nu/2 - 1} * e^{-x/2} / (2 * Gamma(nu / 2))
  double loglikelihood = (0.5 * nu - 1.0) * log(0.5 * sampled_value);
  loglikelihood -= 0.5 * sampled_value;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double InvChiSquaredDistributionLogLikelihood(double sampled_value, double nu) {
  //(2x)^{-nu/2 - 1} * e^{-1/2x} / (2 * Gamma(nu / 2))
  double loglikelihood = (-0.5 * nu  - 1.0) * log(2.0 * sampled_value);
  loglikelihood -= 0.5 / sampled_value;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}
