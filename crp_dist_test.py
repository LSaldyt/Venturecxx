import itertools
import math
import sys

from venture.lite.crp import CRPOutputPSP
from venture.lite.crp import CRPSPAux
from venture.lite.sp_use import MockArgs
from venture.lite.utils import logsumexp

def draw_crp_samples(n, alpha):
    aux = CRPSPAux()
    args = MockArgs([], aux)
    psp = CRPOutputPSP(alpha, 0) # No dispersion
    def draw_sample():
        ans = psp.simulate(args)
        psp.incorporate(ans, args)
        return ans
    ans = [draw_sample() for _ in range(n)]
    print aux.cts()
    return ans

def log_prob_num_tables(k, n, alpha):
    # Log probability that a CRP(alpha) will seat n customers at
    # exactly k tables.
    if k > n:
        return float("-inf")
    config_denominator = sum([math.log(i + alpha) for i in range(n)])
    def log_prob_one_assignment(items):
        # items is the (ordered) list of customer numbers
        # (zero-indexed for customers beyond the first) each of whom
        # sat at an existing table.
        ans = 0
        for i in items:
            ans += math.log(i+1)
        # k customers started new tables
        ans += k * math.log(alpha)
        # Each customer had to sit somewhere
        ans -= config_denominator
        return ans
    return logsumexp([log_prob_one_assignment(items)
                      for items in itertools.combinations(range(n-1), n-k)])

def cdf_num_tables(n, alpha):
    # Returns a "massive cdf": at argument k, returns the tuple (p(<k), p(k)).
    def mcdf(k):
        return (math.exp(logsumexp([log_prob_num_tables(i, n, alpha) for
                                    i in range(k)])),
                math.exp(log_prob_num_tables(k, n, alpha)))
    return mcdf

if __name__ == '__main__':
    n = int(sys.argv[1])
    alpha = float(sys.argv[2])
    f = cdf_num_tables(n, alpha)
    for k in range(n+2):
        print k, f(k)
