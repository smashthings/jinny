#!/usr/bin/env python3

Active = False

def Cmd(cmd, workingDir:str=".", shell:bool=True, quitOnFailure:bool=True, returnStatusCode:bool=False, returnStdOut:bool=True, returnStdErr:bool=True, outputJoin:str="\n", raw:bool=False):
  if not Active:
    raise Exception(f'jinny_unsafe.Cmd(): "cmd" is an unsafe function and thus requires the -u / --unsafe CLI argument to utilise. This is done to protect you from potentially malicious execution')
  import subprocess
  execCmd = subprocess.run(cmd, shell=shell, cwd=workingDir, capture_output=True)
  status = execCmd.returncode
  if raw:
    stdout = execCmd.stdout.decode('utf-8')
    stderr = execCmd.stderr.decode('utf-8')
  else:
    stdout = execCmd.stdout.decode('utf-8').strip()
    stderr = execCmd.stderr.decode('utf-8').strip()

  if status != 0 and quitOnFailure:
    raise Exception(f'jinny_unsafe.Cmd(): Provided command failed with exit status {status}. Command:\n{cmd}\nStdOut:\n{stdout}\nStdErr:\n{stderr}\n')

  out = []
  if returnStatusCode:
    out.append(str(status))
  if returnStdOut:
    out.append(stdout)
  if returnStdErr and (stderr or raw):
    out.append(stderr)
  return outputJoin.join(out)

UnsafeGlobalMap = {
  "cmd": Cmd
}

UnsafeFiltersMap = {
}

def Activate():
  global Active
  Active = True
