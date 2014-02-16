# -*- coding: utf-8 -*-

import lldb
import shlex

USAGE = """
usage: inscode <filename>:<line> <code>
example: inscode MyViewController.m:32 \'NSLog(@"Hi There!");\'
"""


class InsCode(object):
    def __init__(self, session):
        self.session = session

    def insert(self, file_name, line_num, code):
        """ Insert a new code into an appropriate position """
        target = lldb.debugger.GetSelectedTarget()
        bp = target.BreakpointCreateByLocation(file_name, line_num)

        key = self._get_bp_code_map_key(bp)
        self.session[key] = code

        # set breakpoint hit callback for handling breakpoint stop event
        handler = 'inscode.execute'
        command = 'breakpoint command add -F %s %s' % (handler, bp.GetID())
        lldb.debugger.HandleCommand(command)

    def execute(self, bp):
        """ Execute an inserted code """
        key = self._get_bp_code_map_key(bp)
        code = self.session[key]

        # objc message expression needs to be cast to void
        if code.startswith('['):
            self._eval("(void)%s" % code)

        # not message expression
        else:
            self._eval("%s" % code)

    def _eval(self, expression):
        thread = lldb.debugger.GetSelectedTarget().GetProcess().GetSelectedThread()
        frame = thread.frames[0]
        return frame.EvaluateExpression(expression)

    def _get_bp_code_map_key(self, bp):
        return '_inscode_bp_%s' % bp.GetID() 


def execute(frame, location, session):
    """ breakpoint hit callback handler """
    inscode = InsCode(session)
    inscode.execute(location.GetBreakpoint())
    return False  # Don't stop at breakpoint


def inscode(debugger, command, result, internal_dict):
    args = shlex.split(command)
    if not (len(args) == 2 and len(args[0].split(':')) == 2):
        print USAGE
        return

    (file_name, line_num) = args[0].split(':')
    inscode = InsCode(internal_dict)
    inscode.insert(file_name, int(line_num), args[1])


def __lldb_init_module(debugger, dict):
    debugger.HandleCommand('command script add -f inscode.inscode inscode')
