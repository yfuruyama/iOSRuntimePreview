# -*- coding: utf-8 -*-

import lldb
import os
import time
import threading
import difflib

USAGE = """
Sync specific source file with running iOS app.

Symtax: preview <file>
Example: preview MyViewController.m
"""

NAMESPACE = '__preview'
log_path = None


class FileNotFoundException(Exception):
    pass


class Executor(object):
    def __init__(self, frame, line, mod_units):
        self.frame = frame
        self.line = line
        self.mod_units = mod_units

    def execute(self):
        jump = 0
        concatenated_code = ''
        for mod_unit in self.mod_units:
            if mod_unit.is_delete():
                jump += 1
                continue
            concatenated_code += '%s\n' % mod_unit.code
        result = self._eval(self.frame, concatenated_code)

        if jump > 0:
            self.jump_to_line(self.line + jump)
        return result

    def jump_to_line(self, line):
        log('Executor jumps to line: %s' % line)
        context = self.frame.GetSymbolContext(lldb.eSymbolContextEverything)
        if context and context.GetCompileUnit():
            compile_unit = context.GetCompileUnit()
            line_index = compile_unit.FindLineEntryIndex(
                0, line, compile_unit.GetFileSpec(), False
                )
            line_entry = compile_unit.GetLineEntryAtIndex(line_index)
            self._jump_to_line_entry(line_entry)

    def _jump_to_line_entry(self, line_entry):
        if line_entry and line_entry.GetStartAddress().IsValid():
            target = lldb.debugger.GetSelectedTarget()
            addr = line_entry.GetStartAddress().GetLoadAddress(target)
            if addr != lldb.LLDB_INVALID_ADDRESS:
                log('jump address: 0x%x' % addr)
                # set program counter
                self.frame.SetPC(addr)

    def _eval(self, frame, expression):
        log('Executor executes code: %s' % expression)
        # return frame.EvaluateExpression(expression)
        return lldb.debugger.HandleCommand('po %s' % expression)


class ModificationManager(object):
    def __init__(self, internal_dict):
        self.internal_dict = internal_dict

    def search_by_location(self, file_path, line):
        for entry in self.internal_dict[NAMESPACE]:
            if entry['file_path'] == file_path and entry['line'] == line:
                return entry
        return None

    def register(self, mod_unit):
        """ Register a ModificationUnit to LLDB debugger

        This create the only one breakpoint even if 
        there are more than one modification on the same line.
        """
        log('register')
        file_path = mod_unit.file_path
        line = mod_unit.line
        if not self.search_by_location(file_path, line):
            target = lldb.debugger.GetSelectedTarget()
            bp = target.BreakpointCreateByLocation(file_path, line)
            self.internal_dict[NAMESPACE].append({
                'bp_id': bp.GetID(),
                'file_path': file_path,
                'line': line,
                'mod_units': [],
                })
            log('ModificationManager sets breakpoint at line: %s' % line)

            # set breakpoint hit callback
            handler = 'preview.on_breakpoint_hit'
            command = ('breakpoint command add -s python -o '
                       '"%s(frame, bp_loc, internal_dict, %s)" %s'
                       ) % (handler, line, bp.GetID())
            lldb.debugger.HandleCommand(command)

        entry = self.search_by_location(file_path, line)
        entry['mod_units'].append(mod_unit)

    def unregister_all(self):
        for entry in self.internal_dict[NAMESPACE]:
            self._unregister(entry.get('bp_id'))
        self.internal_dict[NAMESPACE] = []

    def _unregister(self, bp_id):
        log('Delete breakpoint: %s' % bp_id)
        target = lldb.debugger.GetSelectedTarget()
        target.BreakpointDelete(bp_id)


class ModificationUnit(object):
    def __init__(self, file_path, diff, internal_dict):
        self.file_path = file_path
        self.line = diff['orig_line_num']
        self.code = diff.get('code', None)
        self.internal_dict = internal_dict

    def is_insert(self):
        if self.code is not None:
            return True
        else:
            return False

    def is_delete(self):
        return not self.is_insert()


class FileSystemWatcher(object):
    """ watcher for modification event
    """
    def __init__(self, callback, internal_dict):
        self.files = []
        self.callback = callback
        self.internal_dict = internal_dict

    def start(self):
        thread = threading.Thread(target=self.monitor)
        thread.setDaemon(True)
        thread.start()

    def monitor(self):
        while is_target_process_running():
            for file in self.files:
                self.monitor_file(file)
            log('monitoring...')
            time.sleep(1)

    def monitor_file(self, file):
        file_path = file['file_path']
        last_mod_time = file['last_mod_time']
        mod_time = os.path.getmtime(file_path)
        if mod_time > last_mod_time:
            log('FileSystemWatcher founds modification: %s' % file_path)
            file['last_mod_time'] = mod_time
            self.callback(
                file_path,
                file['orig_content'],
                self.internal_dict
                )

    def add(self, file_path):
        with open(file_path, 'r') as fh:
            self.files.append({
                'file_path': file_path,
                'last_mod_time': os.path.getmtime(file_path),
                'orig_content': fh.read()
            })


class Differ(object):
    @staticmethod
    def compare(doc1, doc2):
        diff = difflib.unified_diff(doc1.split('\n'), doc2.split('\n'), n=0)
        initial_skip = 2
        diffs = []
        left_start = right_start = left_n_line = right_n_line = 0
        for line in diff:
            if initial_skip > 0:
                initial_skip -= 1
                continue
            if line.startswith('@'):
                left_range, right_range = line.split()[1:3]
                left = left_range.split(',')
                right = right_range.split(',')

                left_start = abs(int(left[0]))
                right_start = int(right[0])

                left_n_line = 1 if len(left) == 1 else int(left[1])
                right_n_line = 1 if len(right) == 1 else int(right[1])
            else:
                delta_mark = line[0]
                code = line[1:]
                if delta_mark == '+':
                    orig_line_num = left_start
                    if left_n_line == 0:
                        orig_line_num = left_start + 1
                    diffs.append({
                        'action': 'insert',
                        'orig_line_num': orig_line_num,
                        'code': code,
                        })
                elif delta_mark == '-':
                    diffs.append({
                        'action': 'delete',
                        'orig_line_num': left_start,
                        'code': None,
                        })
        return diffs


""" callback functions """

def on_file_changed(file_path, orig_content, internal_dict):
    """ file change callback handler
    """
    with open(file_path, 'r') as fh:
        content = fh.read()
        diffs = Differ.compare(orig_content, content)
        log(diffs)

        mod_manager = ModificationManager(internal_dict)
        mod_manager.unregister_all()
        for diff in diffs:
            mod_unit = ModificationUnit(file_path, diff, internal_dict)
            mod_manager.register(mod_unit)


def on_breakpoint_hit(frame, location, internal_dict, line):
    """ breakpoint hit callback handler

    Don't use the value of frame.GetLineEntry().GetLine() as line number
    because LLDB may return an inaccurate line number after modification.
    
    cf.) lldb/source/Interpreter/ScriptInterpreterPython.cpp
    # ScriptInterpreterPython::GenerateBreakpointCommandCallbackData
    """
    line_entry = frame.GetLineEntry()
    file_spec = line_entry.GetFileSpec()
    file_path = get_abspath(file_spec)

    mod_manager = ModificationManager(internal_dict)
    entry = mod_manager.search_by_location(file_path, line)
    if entry:
        # execute modified codes!
        executor = Executor(frame, line, entry.get('mod_units'))
        status = executor.execute()

    # Don't stop at breakpoint
    frame.GetThread().GetProcess().Continue()


""" utility functions """

def log(message):
    """ Logging for debug

    The setlog command must be executed before calling this function
    to set log path.
    """
    global log_path
    if log_path:
        with open(log_path, 'a') as fh:
            fh.write(str(message) + '\n')


def is_target_process_running():
    process = lldb.debugger.GetSelectedTarget().GetProcess()
    if process.GetNumThreads() > 0:
        return True
    else:
        return False


def get_abspath(file_spec):
    file_name = file_spec.GetFilename()
    directory = file_spec.GetDirectory()
    if directory is None:
        directory = get_basedir(file_name)

    # when source file specified by user is not found
    if directory is None:
        raise FileNotFoundException('File not found: "%s"' % file_name)
        
    return os.path.join(directory, file_name)


def get_basedir(file_name):
    # workaround for getting base directory
    target = lldb.debugger.GetSelectedTarget()
    bp = target.BreakpointCreateByLocation(file_name, 1)
    bp_loc = bp.GetLocationAtIndex(0)
    basedir = bp_loc.GetAddress().GetLineEntry().GetFileSpec().GetDirectory()
    target.BreakpointDelete(bp.GetID())
    return basedir


""" commands """

def preview(debugger, command, result, internal_dict):
    """ 'preview' command
    """
    if command == '-h' or command == '--help' or command == '':
        print USAGE
        return

    file_name = command
    file_spec = lldb.SBFileSpec(file_name)
    try:
        file_path = get_abspath(file_spec)
    except FileNotFoundException as err:
        print err
        return
    log('file path: %s' % file_path)

    watcher_key = '_preview_watcher'
    if not internal_dict.get(watcher_key):
        watcher = FileSystemWatcher(on_file_changed, internal_dict)
        watcher.start()
        internal_dict[watcher_key] = watcher

    watcher = internal_dict[watcher_key]
    watcher.add(file_path)
    print 'Preview enabled: "%s"' % file_name


def set_log_path(debugger, command, result, internal_dict):
    global log_path
    log_path = command


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f preview.preview preview')
    debugger.HandleCommand('command script add -f preview.set_log_path setlog')
    internal_dict[NAMESPACE] = []
    preview.__doc__ = USAGE
    print 'The "preview" command has been installed, type "help preview" or "preview -h" for usage.'
