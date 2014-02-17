# -*- coding: utf-8 -*-

import lldb
import shlex

USAGE = """
usage: inscode <filename>:<line> <code>
example: inscode MyViewController.m:32 \'NSLog(@"Hi There!");\'
"""


class InsCode(object):
    def __init__(self, session, file_name, line):
        self.session = session
        self.file_name = file_name
        self.line = line

    def insert(self, code):
        """ Insert a new code into an appropriate position """
        key = self.get_session_key()
        if not self.session.get(key):
            target = lldb.debugger.GetSelectedTarget()
            bp = target.BreakpointCreateByLocation(self.file_name, self.line)
            # set breakpoint hit callback
            handler = 'inscode.execute'
            command = ('breakpoint command add -s python -o '
                       '"%s(frame, bp_loc, internal_dict)" %s'
                       ) % (handler, bp.GetID())
            lldb.debugger.HandleCommand(command)

        self.session.setdefault(key, []).append(code)

        print 'Inserted \'%s\' at %s:%s' % (code, self.file_name, self.line)

    def execute(self, frame, codes):
        """ Execute an inserted codes """
        return [self._eval(frame, code) for code in codes]

    def _eval(self, frame, expression):
        # return frame.EvaluateExpression(expression)
        return lldb.debugger.HandleCommand('po %s' % expression)

    def get_session_key(self):
        return '_inscode_%s_%s' % (self.file_name, self.line)


def execute(frame, location, session):
    """ breakpoint hit callback handler
    
    cf.) lldb/source/Interpreter/ScriptInterpreterPython.cpp
    # ScriptInterpreterPython::GenerateBreakpointCommandCallbackData
    """
    line_entry = frame.GetLineEntry()
    file_name = line_entry.GetFileSpec().GetFilename()
    line = line_entry.GetLine()

    inscode = InsCode(session, file_name, line)
    key = inscode.get_session_key()
    codes = inscode.session.get(key)

    # execute inserted codes!
    values = inscode.execute(frame, codes)

    # Don't stop at breakpoint
    frame.GetThread().GetProcess().Continue()


def inscode(debugger, command, result, internal_dict):
    args = shlex.split(command)
    if not (len(args) == 2 and len(args[0].split(':')) == 2):
        print USAGE
        return

    (file_name, line) = args[0].split(':')
    inscode = InsCode(internal_dict, file_name, int(line))
    inscode.insert(args[1])


def __lldb_init_module(debugger, dict):
    debugger.HandleCommand('command script add -f inscode.inscode inscode')
    print 'inscode loaded.'
