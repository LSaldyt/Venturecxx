# Copyright (c) 2013, 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
import resource

from venture import parser
from venture import ripl
from venture import sivm
from venture import server

# Raise Python's recursion limit, per
# http://log.brandonthomson.com/2009/07/increase-pythons-recursion-limit.html
# The reason to do this is that Venture is not tail recursive, and the
# repeat inference function are written as recursive functions in
# Venture.

# Try to increase max stack size from 8MB to 512MB
(soft, hard) = resource.getrlimit(resource.RLIMIT_STACK)
if hard > -1:
    new_soft = max(soft, min(2**29, hard))
else:
    new_soft = max(soft, 2**29)
resource.setrlimit(resource.RLIMIT_STACK, (new_soft, hard))
# Set a large recursion depth limit
sys.setrecursionlimit(max(10**6, sys.getrecursionlimit()))

def make_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object.

Traces models in the default backend.  See `venture.ripl.ripl.Ripl` for what
you can do with it."""
    return backend().make_ripl(*args, **kwargs)

def make_lite_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object that traces models in the Lite backend."""
    return Lite().make_ripl(*args, **kwargs)

def make_puma_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object that traces models in the Puma backend."""
    return Puma().make_ripl(*args, **kwargs)

def make_church_prime_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object that parses input in the abstract syntax."""
    return backend().make_church_prime_ripl(*args, **kwargs)

def make_lite_church_prime_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object that parses input in the abstract syntax and traces models in the Lite backend."""
    return Lite().make_church_prime_ripl(*args, **kwargs)

def make_puma_church_prime_ripl(*args, **kwargs):
    """Construct and return a VentureScript RIPL object that parses input in the abstract syntax and traces models in the Puma backend."""
    return Puma().make_church_prime_ripl(*args, **kwargs)

def make_ripl_rest_server():
    """Return a VentureScript REST server object backed by a default RIPL."""
    r = backend().make_combined_ripl()
    return server.RiplRestServer(r)

def make_ripl_rest_client(base_url):
    """Return a VentureScript REST client object pointed at the given URL."""
    return ripl.RiplRestClient(base_url)

def _seed(seed):
    return random.randint(1, 2**31 - 1) if seed is None else seed
def _kwseed(kwargs):
    if 'seed' in kwargs:
        return kwargs.pop('seed')
    else:
        return random.randint(1, 2**31 - 1)

class Backend(object):
    """Base class representing a model backend.

See `Lite` and `Puma`."""
    def trace_constructor(self): pass
    def make_engine(self, persistent_inference_trace=True, seed=None):
        from venture.engine import engine
        seed = _seed(seed)
        return engine.Engine(self, seed, persistent_inference_trace)
    def make_core_sivm(self, persistent_inference_trace=True, seed=None):
        seed = _seed(seed)
        return sivm.CoreSivm(self.make_engine(persistent_inference_trace,
                                              seed))
    def make_venture_sivm(self, persistent_inference_trace=True, seed=None):
        seed = _seed(seed)
        return sivm.VentureSivm(self.make_core_sivm(persistent_inference_trace,
                                                    seed))
    def make_church_prime_ripl(self, **kwargs):
        return self.make_ripl(init_mode="church_prime", **kwargs)
    def make_venture_script_ripl(self, **kwargs):
        return self.make_ripl(init_mode="venture_script", **kwargs)
    def make_combined_ripl(self, persistent_inference_trace=True, seed=None,
                           **kwargs):
        seed = _seed(seed)
        v = self.make_venture_sivm(persistent_inference_trace, seed)
        parser1 = parser.ChurchPrimeParser.instance()
        parser2 = parser.VentureScriptParser.instance()
        modes = {"church_prime": parser1, "venture_script": parser2}
        r = ripl.Ripl(v, modes, **kwargs)
        r.set_mode("church_prime")
        r.backend_name = self.name()
        return r
    def make_ripl(self, init_mode="venture_script", **kwargs):
        r = self.make_combined_ripl(**kwargs)
        r.set_mode(init_mode)
        return r
    def make_ripl_rest_server(self, **kwargs):
        return server.RiplRestServer(self.make_combined_ripl(**kwargs))

class Lite(Backend):
    """An instance of this class represents the Lite backend."""
    def trace_constructor(self):
        from venture.lite import trace
        return trace.Trace
    def name(self): return "lite"

class Puma(Backend):
    """An instance of this class represents the Puma backend."""
    def trace_constructor(self):
        from venture.puma import trace
        return trace.Trace
    def name(self): return "puma"

class Mite(Backend):
    """An instance of this class represents the Mite backend."""
    def make_combined_ripl(self, *args, **kwargs):
        import venture.mite
        r = super(Mite, self).make_combined_ripl(*args, **kwargs)
        r.execute_program_from_file(venture.mite.__path__[0] + '/prelude.vnt')
        return r
    def make_engine(self, persistent_inference_trace=True, seed=None):
        from venture.mite import engine
        seed = _seed(seed)
        assert persistent_inference_trace
        return engine.Engine(self, seed)
    def trace_constructor(self):
        from venture.mite import trace
        return trace.Trace
    def name(self): return "mite"

def backend(name = "puma"):
    """Return a backend by name: 'lite' or 'puma'."""
    if name == "lite":
        return Lite()
    if name == "puma":
        return Puma()
    if name == "mite":
        return Mite()
    raise Exception("Unknown backend %s" % name)
