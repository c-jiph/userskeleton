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


class LLDBStopHandler:
  def __init__(self, target, extra_args, dict):
    self.extra_args = extra_args
    self.target = target

  def handle_stop(self, _exe_ctx, stream):
    LLDB_STOP_HOOK()
    return True


def lldb_f_command(debugger, command, result, dict):
  args = command.split()
  debugger.HandleCommand(' '.join(['frame select'] + args))
  LLDB_STOP_HOOK()


def lldb_down_command(debugger, command, result, dict):
  frame_id = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetFrameID()
  debugger.HandleCommand(f'frame select {frame_id - 1}')
  LLDB_STOP_HOOK()


def lldb_up_command(debugger, command, result, dict):
  frame_id = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetFrameID()
  debugger.HandleCommand(f'frame select {frame_id + 1}')
  LLDB_STOP_HOOK()


class LLDBDebugger:
  def installHook(self, debugger, hook):
    self.debugger = debugger
    global LLDB_STOP_HOOK
    LLDB_STOP_HOOK = hook
    debugger.HandleCommand(f'target stop-hook add -P {__name__}.LLDBStopHandler')
    debugger.HandleCommand(f'command script add -f {__name__}.lldb_f_command f')
    debugger.HandleCommand(f'command script add -f {__name__}.lldb_down_command down')
    debugger.HandleCommand(f'command script add -f {__name__}.lldb_up_command up')

  def shutdown(self):
    pass

  def getCurrentFileAndFile(self):
    try:
      line_entry = self.debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetLineEntry()
      return (
        # Filename
        line_entry.file,
        # Line number (as string)
        str(line_entry.line)
      )
    except Exception:
      return None, None


class GDBDebugger:
  def installHook(self, hook):
    global OLD_PROMPT_HOOK

    def our_prompt_hook(current_prompt):
      global OLD_PROMPT_HOOK
      next_prompt_hook = OLD_PROMPT_HOOK
      # Disable to prevent recursion (not sure why this happens)
      gdb.prompt_hook = next_prompt_hook
      okay = hook()
      gdb.prompt_hook = our_prompt_hook
      if not okay:
        OLD_PROMPT_HOOK = None
        atexit.unregister(shutdown)
      if next_prompt_hook:
        next_prompt_hook(current_prompt)


    OLD_PROMPT_HOOK = gdb.prompt_hook
    gdb.prompt_hook = our_prompt_hook

  def shutdown(self):
    global OLD_PROMPT_HOOK
    gdb.prompt_hook = OLD_PROMPT_HOOK
    OLD_PROMPT_HOOK = None

  def getCurrentFileAndFile(self):
    def linespec_helper(linespec, fn):
      try:
        x = gdb.decode_line(linespec)[1][0]
        if x != None and x.is_valid() and x.symtab != None and x.symtab.is_valid():
          return fn(x)
      except:
        pass
      return None

    # If no process is running/attached gdb.decode_line() aborts the current
    # Python execution so there is no way to cleanly return. So try this first.
    if gdb.inferiors()[0].pid == 0:
      return None, None

    return (
      # Filename
      linespec_helper("*$pc", lambda x: x.symtab.fullname()),
      # Line number (as string)
      str(linespec_helper("*$pc", lambda x: x.line))
    )


DEBUGGER = None

SERVER_NAME = f"GDB.VI.{os.getpid()}"
X_SERVER_NUM = "1"
XVFB_TMUX_SESSION_NAME="gdb-vim-xvfb-session"
VIM_COMMAND = None
VIM_INIT = ":set number|set cursorline|hi CursorLine ctermbg=darkgrey<CR>"

def shutdown(*args):
  subprocess.run(f"""
    {VIM_COMMAND} --servername {SERVER_NAME} --remote-send '<ESC>:q!<CR>'
  """, shell=True)
  DEBUGGER.shutdown()


def vim_current_line_file():
  aFile, aLine = DEBUGGER.getCurrentFileAndFile()
  if aLine != None and aFile != None:
    subprocess.run(f"""
      {VIM_COMMAND} --servername {SERVER_NAME} --remote-send \
        "<C-\><C-N>:n {aFile}<CR>:{aLine}|set nomodifiable|norm!z.<CR>"
    """, shell=True, check=True)


def vim_hook():
  try:
    vim_current_line_file()
  except Exception:
    print("Error communicating with vim.")
    return False
  return True


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

try:
  import lldb
  DEBUGGER = LLDBDebugger()

  def __lldb_init_module(debugger, dict):
    DEBUGGER.installHook(debugger, vim_hook)
    debugger.SetDestroyCallback(shutdown)
    vim_hook()
except ImportError:
    try:
      import gdb
      OLD_PROMPT_HOOK = None
      DEBUGGER = GDBDebugger()
      DEBUGGER.installHook(vim_hook)
      atexit.register(shutdown)
    except ImportError:
        print("Couldn't import either lldb or gdb.")
