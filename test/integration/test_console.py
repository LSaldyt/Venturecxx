import subprocess as s

def testConsoleAlive():
  console = s.Popen("venture", shell=True, stdout=s.PIPE, stdin=s.PIPE)
  (stdout, _) = console.communicate("assume x (uniform_continuous 0.0 0.9)")
  assert console.returncode == 0
  assert '>>> 0.' in stdout
  print stdout
