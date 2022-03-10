# Opens vim in a tmux split which updates every time the gdb prompt is shown.
# The effect is doing things like "next", or "up" will immediately show the
# current line of code in the vim instance.
#
# This script uses/assumes:
# * We're already in a tmux session and tmux command is available.
# * Will try and use vim or 'gvim -v' depending on which is available and has
#   the +clientserver feature.
# * If an X session is not available, will try make one available with xvfb-run.
# * Existence of xlsclients.
#
# Very hacky but quite useful in practice.
#
# Based on https://stackoverflow.com/a/30151257/1476546

import atexit
import os
import subprocess
import time

SERVER_NAME = f"GDB.VI.{os.getpid()}"
X_SERVER_NUM = "1"
XVFB_TMUX_SESSION_NAME="gdb-vim-xvfb-session"
VIM_COMMAND = None
VIM_INIT = ":set number|set cursorline|hi CursorLine ctermbg=darkgrey<CR>"
OLD_PROMPT_HOOK = None


def linespec_helper(linespec, fn):
  try:
    x = gdb.decode_line(linespec)[1][0]
    if x != None and x.is_valid() and x.symtab != None and x.symtab.is_valid():
      return fn(x)
  except:
    pass
  return None


def current_file():
  return linespec_helper("*$pc", lambda x: x.symtab.fullname())


def current_line():
  return str(linespec_helper("*$pc", lambda x: x.line))


def shutdown():
  global OLD_PROMPT_HOOK
  subprocess.run(f"""
    {VIM_COMMAND} --servername {SERVER_NAME} --remote-send '<ESC>:q!<CR>'
  """, shell=True)
  gdb.prompt_hook = OLD_PROMPT_HOOK
  OLD_PROMPT_HOOK = None


def vim_current_line_file():
  aLine = current_line()
  aFile = current_file()
  if aLine != None and aFile != None:
    subprocess.run(f"""
      {VIM_COMMAND} --servername {SERVER_NAME} --remote-send \
        "<C-\><C-N>:n {aFile}<CR>:{aLine}|set nomodifiable|norm!z.<CR>"
    """, shell=True, check=True)


def vim_prompt(current_prompt):
  global OLD_PROMPT_HOOK
  next_prompt_hook = OLD_PROMPT_HOOK
  try:
    # Disable to prevent recursion (not sure why this happens)
    gdb.prompt_hook = next_prompt_hook
    vim_current_line_file()
    gdb.prompt_hook = vim_prompt
  except Exception:
    print("Error communicating with vim, will not retry.")
    OLD_PROMPT_HOOK = None
    atexit.unregister(shutdown)
  if next_prompt_hook:
    next_prompt_hook(current_prompt)


# Detect a usable version of vim
if VIM_COMMAND is None:
  if subprocess.run(
      "(vim --version | grep +clientserver) >/dev/null 2>&1",
      shell=True).returncode == 0:
    VIM_COMMAND = "vim"
  elif subprocess.run(
      "(gvim --version | grep +clientserver) >/dev/null 2>&1",
      shell=True).returncode == 0:
    VIM_COMMAND = "gvim -v"
  else:
    raise Exception("Couldn't find vim with +clientserver (try installing gvim)")


# Vim uses X11 to communicate with other Vim processes so start an Xvfb session
# if an X server isn't available.
if os.getenv("DISPLAY") is None:
  subprocess.run(f"""
    tmux has-session -t {XVFB_TMUX_SESSION_NAME} ||
    (
      tmux new-session -d -s {XVFB_TMUX_SESSION_NAME} \
        'xvfb-run -s :{X_SERVER_NUM} cat' &&
      while ! DISPLAY=:{X_SERVER_NUM} xlsclients 2>/dev/null >/dev/null ; do
        sleep 0.1s
      done
    )
  """, shell=True)
  VIM_COMMAND = f"DISPLAY=:{X_SERVER_NUM} {VIM_COMMAND}"


# Start a controllable Vim instance in a Tmux split
subprocess.run(f"""
  tmux split-window -bd '{VIM_COMMAND} --servername {SERVER_NAME}' &&
  while ! {VIM_COMMAND} --serverlist | grep {SERVER_NAME} >/dev/null ; do
    sleep 0.1s
  done
""", shell=True)


subprocess.run(f"""
  {VIM_COMMAND} --servername {SERVER_NAME} --remote-send '{VIM_INIT}'
""", shell=True)

OLD_PROMPT_HOOK = gdb.prompt_hook
gdb.prompt_hook = vim_prompt
atexit.register(shutdown)
