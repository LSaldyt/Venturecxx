"""A StarCluster plugin for Venture.

Installs Venture (including development sources) on all nodes."""
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
import os.path
import tempfile
import subprocess

class VentureInstaller(ClusterSetup): # Exceptions by default are acceptable pylint: disable=abstract-method
  def __init__(self, tarfile=None, checkout=None, unpacked_dir=None, release=None,
               github_branch="master", skip_cxx=False): # pylint: disable=super-init-not-called
    # The example in docs didn't call super.
    self.checkout = checkout
    self.github_branch = github_branch
    self.tarfile = tarfile
    self.release = release
    self.skip_cxx = skip_cxx

    self.checkout_parent = None
    self.unpacked_venture_dir = unpacked_dir
    self._check_config()

  def _check_config(self):
    if self.tarfile is not None and not os.path.isfile(self.tarfile):
      log.warn("%s does not appear to be a file; ignoring." % self.tarfile)
      self.tarfile = None
    if self.checkout is not None and not os.path.isdir(self.checkout):
      log.warn("%s does not appear to be a directory; ignoring." % self.checkout)
      self.checkout = None
    valid_releases = ["0.1.1"]
    if self.release is not None and self.release not in valid_releases:
      log.warn("%s is not a valid released version of Venture; ignoring.  Valid releases are %s" % (self.release, valid_releases))
      self.release = None

    if self.tarfile is None and self.checkout is None and self.release is None and self.github_branch is None:
      # TODO What exception to raise?
      raise Exception("No source for Venture specified.  Please indicate a checkout, a Github branch (if you have permission to read the repository), a tarball, or a public release.")

    method_attrs = ["checkout", "github_branch", "tarfile", "release"]
    for i in range(len(method_attrs)):
      if getattr(self, method_attrs[i]) is not None:
        for j in range(i+1,len(method_attrs)):
          if getattr(self, method_attrs[j]) is not None:
            log.warn("%s %s and %s %s given as source for Venture.  Preferring the %s." %
                     (method_attrs[i].capitalize(), getattr(self, method_attrs[i]),
                      method_attrs[j], getattr(self, method_attrs[j]), method_attrs[i]))
            setattr(self, method_attrs[j], None)

    if self.checkout is not None and self.unpacked_venture_dir is None:
      # The purpose of this complexity is to allow a user to install
      # Venture from a checkout that names the repository something
      # other than Venturecxx.
      (d, f) = os.path.split(self.checkout)
      if f == "":
        (d, f) = os.path.split(os.path.dirname(self.checkout))
      if f != "":
        self.checkout_parent = d
        self.unpacked_venture_dir = f
    if self.unpacked_venture_dir is None:
      self.unpacked_venture_dir = "Venturecxx"

  def run(self, nodes, master, user, user_shell, volumes):
    for node in nodes:
      log.info("Installing Venture on %s" % node.alias)
      self.install_venture(node)

  def install_venture(self, node):
    self.ensure_basics(node)
    if not self.skip_cxx:
      self.prepare_for_c11(node)
      self.ensure_c11(node)
    self.ensure_python_deps(node)
    self.ensure_venture_source(node)
    self.ensure_venture(node)

  def ensure_basics(self, node):
    log.info("Ensuring basic dependencies present on %s" % node.alias)
#    node.apt_command('update')
    node.apt_install('git python-pip python-virtualenv')
    node.ssh.execute('pip install -U distribute')

  def prepare_for_c11(self, node):
    log.info("Preparing %s for C++11" % node.alias)
    node.apt_install('libboost1.48-all-dev libgsl0-dev cmake make ccache')

  def ensure_c11(self, node):
    log.info("Installing C++11 on %s" % node.alias)
    node.apt_install('python-software-properties')
    node.ssh.execute('add-apt-repository -y ppa:ubuntu-toolchain-r/test')
    node.apt_command('update')
    node.apt_install('gcc-4.8 g++-4.8')
    node.ssh.execute('update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 50')
    node.ssh.execute('update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 50')

  def ensure_python_deps(self, node):
    log.info("Installing Python dependencies on %s" % node.alias)
    node.apt_install('python-pyparsing python-flask python-requests python-numpy python-matplotlib')

  def ensure_venture_source(self, node):
    if self.checkout is not None:
      tempd = tempfile.mkdtemp()
      try:
        tarfile = os.path.join(tempd, "venture.tgz")
        try:
          subprocess.call(["tar", "-czf", tarfile, self.unpacked_venture_dir], cwd=self.checkout_parent)
          self.push_venture_from_tarball(node, tarfile)
        finally:
          if os.path.isfile(tarfile):
            os.remove(tarfile)
      finally:
        os.rmdir(tempd)
    if self.github_branch is not None:
      # Trust github.com
      node.ssh.execute("ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no github.com exit || true")
      # TODO blows away all the caches :( but at least ensures unpacking
      # of fresh source.
      node.ssh.execute('rm -rf Venturecxx')
      node.shell(forward_agent=True, command="git clone git@github.com:mit-probabilistic-computing-project/Venturecxx.git")
      node.ssh.execute('cd Venturecxx; git checkout %s' % self.github_branch)
    elif self.tarfile is not None:
      self.push_venture_from_tarball(node, self.tarfile)
    elif self.release is not None:
      node.ssh.execute("wget http://probcomp.csail.mit.edu/venture/venture-%s.tgz" % self.release)
      # TODO blows away all the caches :( but at least ensures unpacking
      # of fresh source.
      node.ssh.execute('rm -rf Venturecxx')
      node.ssh.execute('tar --extract --gunzip --file venture-%s.tgz' % self.release)
    else:
      raise Exception("This should not happen: no Venture source found in valid config.")

  def push_venture_from_tarball(self, node, tarfile):
    node.ssh.put(tarfile, 'venture.tgz')
    # TODO blows away all the caches :( but at least ensures unpacking
    # of fresh source.
    node.ssh.execute('rm -rf %s' % self.unpacked_venture_dir)
    node.ssh.execute('tar --extract --gunzip --file venture.tgz')

  def ensure_venture(self, node):
    log.info("Building Venture on %s" % node.alias)
    node.ssh.execute('cd %s; pip install -r requirements.txt' % self.unpacked_venture_dir)
    if not self.skip_cxx:
      node.ssh.execute('cd %s; python setup.py install' % self.unpacked_venture_dir)
    else:
      node.ssh.execute('cd %s; SKIP_CXX_BACKEND=true python setup.py install' % self.unpacked_venture_dir)
