#!/usr/bin/python

# From here:
# http://docs.python.org/2/extending/building.html#building

# Just build as a Python library: python setup.py build
# Build and install to the system: sudo python setup.py build install

from distutils.core import setup, Extension
from os import path
import itertools

#src_dir = "backend/cxx/src"
#src_files = []

#def find_cxx(agg, dirname, fnames):
#    for f in fnames:
#        if f.endswith(".cxx"):
#            agg.append(path.join(dirname, f))
#
#path.walk(src_dir, find_cxx, src_files)
#print(src_files)

src_files = [
    "src/value.cxx",
    "src/node.cxx",
    "src/env.cxx",
    "src/builtin.cxx",
    "src/trace.cxx",
    "src/rcs.cxx",
    "src/regen.cxx",
    "src/detach.cxx",
    "src/flush.cxx",
    "src/lkernel.cxx",
    "src/infer/gkernel.cxx",
    "src/infer/mh.cxx",
    "src/infer/gibbs.cxx",
    "src/utils.cxx",
    "src/check.cxx",
    "src/sp.cxx",
    "src/scaffold.cxx",
    "src/sps/stathelpers.cxx",
    "src/sps/csp.cxx",
    "src/sps/mem.cxx",
    "src/sps/real.cxx",
    "src/sps/count.cxx",
    "src/sps/bool.cxx",
    "src/sps/continuous.cxx",
    "src/sps/discrete.cxx",
    "src/sps/cond.cxx",
    "src/sps/vector.cxx",
    "src/sps/list.cxx",
    "src/sps/map.cxx",
    "src/sps/envs.cxx",
    "src/sps/eval.cxx",
    "src/sps/pycrp.cxx",
    "src/sps/makesymdirmult.cxx",
    "src/sps/makeucsymdirmult.cxx",
    "src/sps/makelazyhmm.cxx",
    "src/pytrace.cxx",
]
src_files = ["backend/cxx/" + f for f in src_files]

inc_dirs = ['inc/', 'inc/sps/', 'inc/infer/']
inc_dirs = ["backend/cxx/" + d for d in inc_dirs]

ext_modules = []
packages=["venture","venture.sivm","venture.ripl",
    "venture.parser","venture.server","venture.shortcuts",
    "venture.test", "venture.cxx"]

cxx = Extension("venture.cxx.libtrace",
    define_macros = [('MAJOR_VERSION', '1'),
                     ('MINOR_VERSION', '0')],
    libraries = ['gsl', 'gslcblas', 'boost_python'],
    extra_compile_args = ["-std=c++11", "-Wall", "-g", "-O0", "-fPIC"],
    include_dirs = inc_dirs,
    sources = src_files)
ext_modules.append(cxx)

setup (
    name = 'Venture CXX',
    version = '1.0',
    author = 'MIT.PCP',
    url = 'TBA',
    long_description = 'TBA.',
    packages = packages,
    package_dir={"venture":"python/lib/", "venture.test":"python/test/", "venture.cxx":"backend/cxx/"},
    ext_modules = ext_modules
)
