# Copyright (c) 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import math

from venture.test.stats import statisticalTest
from venture.test.stats import reportKnownGaussian
from venture.test.config import get_ripl, on_inf_prim, broken_in, collectSamples, default_num_transitions_per_sample

def custom_mh_ripl():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("custom_mh", """\
(lambda (scope block)
  (do (subproblem <- (select scope block)) ; really, select by availability of log densities
      (rho_weight_and_rho_db <- (detach subproblem))
      (xi_weight <- (regen subproblem))
      (let ((rho_weight (first rho_weight_and_rho_db))
            (rho_db (rest rho_weight_and_rho_db)))
        (if (< (log (uniform_continuous 0 1)) (- xi_weight rho_weight))
            pass ; accept
            (do (detach subproblem) ; reject
                (restore subproblem rho_db))))))
""")
  return ripl

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
def testDetachRegenSmoke():
  ripl = custom_mh_ripl()
  ripl.assume("x", "(normal 0 1)")
  old = ripl.sample("x")
  ripl.infer("(custom_mh default all)")
  assert not old == ripl.sample("x")

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
@statisticalTest
def testDetachRegenInference():
  ripl = custom_mh_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.observe("(normal x 1)", 2)
  predictions = collectSamples(ripl, "x", infer="(repeat %d (custom_mh default all))" % default_num_transitions_per_sample())
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)

def gaussian_drift_mh_ripl():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("gaussian_drift_mh", """\
(lambda (scope block sigma)
  (do (subproblem <- (select scope block))
      (values <- (get_current_values subproblem))
      (let ((move (lambda (value) (normal value sigma))) ; gaussian drift proposal kernel
            (new_values (mapv move values)))
        (do (rho_weight_and_rho_db <- (detach_for_proposal subproblem))
            (xi_weight <- (regen_with_proposal subproblem new_values))
            (let ((rho_weight (first rho_weight_and_rho_db))
                  (rho_db (rest rho_weight_and_rho_db)))
              (if (< (log (uniform_continuous 0 1)) (- xi_weight rho_weight))
                  pass ; accept
                  (do (detach subproblem) ; reject
                      (restore subproblem rho_db))))))))
""")
  return ripl

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
@broken_in("mite", "Does not support regen_with_proposal yet")
def testCustomProposalSmoke():
  ripl = gaussian_drift_mh_ripl()
  ripl.assume("x", "(normal 0 1)")
  old = ripl.sample("x")
  ripl.infer("(repeat 5 (gaussian_drift_mh default all 0.1))")
  assert not old == ripl.sample("x")

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
@broken_in("mite", "Does not support regen_with_proposal yet")
@statisticalTest
def testCustomProposalInference():
  ripl = gaussian_drift_mh_ripl()
  ripl.assume("x", "(normal 0 1)")
  ripl.observe("(normal x 1)", 2)
  predictions = collectSamples(ripl, "x", infer="(repeat %d (gaussian_drift_mh default all 0.5))" % default_num_transitions_per_sample())
  return reportKnownGaussian(1, math.sqrt(0.5), predictions)

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
@broken_in("mite", "Does not support regen_with_proposal yet")
def testDetachForProposalDoesNotMutateScaffold():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.assume("x", "(normal 0 1)")
  old = ripl.sample("x")
  ripl.infer("""\
(do (subproblem <- (select default all))
    (detach_for_proposal subproblem)
    (regen subproblem))
""")
  assert not old == ripl.sample("x")
