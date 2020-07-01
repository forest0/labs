#!/usr/bin/env python3

import logging
import argparse
import enum
import re
import functools
import os
import glob

logger = logging.getLogger(name=__name__)

@enum.unique
class CommandType(enum.Enum):
    ARITHMETIC = enum.auto()
    PUSH       = enum.auto()
    POP        = enum.auto()
    LABEL      = enum.auto()
    GOTO       = enum.auto()
    IF         = enum.auto()
    FUNCTION   = enum.auto()
    RETURN     = enum.auto()
    CALL       = enum.auto()

    @staticmethod
    def is_arithmetic(command):
        return command in ['add',
                           'sub',
                           'neg',
                           'eq',
                           'gt',
                           'lt',
                           'and',
                           'or',
                           'not',]

    @staticmethod
    def is_push(command):
        return command == 'push'

    @staticmethod
    def is_pop(command):
        return command == 'pop'

    @staticmethod
    def is_label(command):
        return command == 'label'

    @staticmethod
    def is_goto(command):
        return command == 'goto'

    @staticmethod
    def is_if(command):
        return command == 'if-goto'

    @staticmethod
    def is_function(command):
        return command == 'function'

    @staticmethod
    def is_return(command):
        return command == 'return'

    @staticmethod
    def is_call(command):
        return command == 'call'

class Parser(object):
    '''Parser of VM.

    Note that we assume that no syntax error in VM file,
    so we dont hanle syntax error here for simplicity.
    '''

    COMMAND_TYPE_DETECTORS = [
        (CommandType.is_arithmetic, CommandType.ARITHMETIC),
        (CommandType.is_push, CommandType.PUSH),
        (CommandType.is_pop, CommandType.POP),
        (CommandType.is_label, CommandType.LABEL),
        (CommandType.is_goto, CommandType.GOTO),
        (CommandType.is_if, CommandType.IF),
        (CommandType.is_function, CommandType.FUNCTION),
        (CommandType.is_return, CommandType.RETURN),
        (CommandType.is_call, CommandType.CALL),
    ]

    def __init__(self, input_file_path):
        with open(input_file_path) as f:
            self._lines = f.readlines()

        self._lines = self._regularize_lines(self._lines)

        self._cur_line_idx = -1

    def _regularize_lines(self, lines):
        '''Remove unnecessary space, newline and comment.
        '''
        def regularize_line(line):
            line = line.strip()
            line = re.sub(r'//.*', '', line) # remove comment
            # remove unnecessary space
            # e.g., convert `push   local 3` to `push local 3`
            line = ' '.join(line.split())
            return line

        lines = map(regularize_line, lines)
        lines = filter(lambda line: line, lines)

        return list(lines)

    def _cur_line(self):
        return self._lines[self._cur_line_idx]

    # FIXME: suppress lint warning: no-self-argument
    def _allow_command_types(command_types): # pylint: disable=no-self-argument
        '''Decorator that set limit to call APIs according to current command type.
        i.e., only when current command_type in command_types, the decorated API
        can be called.
        '''
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                # args[0] is self
                cur_command_type = args[0].command_type()
                if not cur_command_type in command_types:
                    raise Exception(f'semantic error: {cur_command_type} is \
                            forbidden to call {func.__name__}')
                return func(*args, **kw)
            return wrapper
        return decorator

    def has_more_commands(self):
        return self._lines and self._cur_line_idx < len(self._lines) - 1

    def advance(self):
        assert self.has_more_commands()

        self._cur_line_idx += 1

    def command(self):
        return self._cur_line().split(' ')[0]

    def command_type(self):
        command = self.command()
        for detector, type in Parser.COMMAND_TYPE_DETECTORS:
            if detector(command):
                return type
        raise Exception(f'syntax error: unknown command type: {command}')

    @_allow_command_types([CommandType.ARITHMETIC,
                           CommandType.PUSH,
                           CommandType.POP,
                           CommandType.LABEL,
                           CommandType.GOTO,
                           CommandType.IF,
                           CommandType.FUNCTION,
                           CommandType.CALL])
    def arg1(self):
        command = self._cur_line()
        if self.command_type() == CommandType.ARITHMETIC:
            return command
        return command.split(' ')[1]

    @_allow_command_types([CommandType.PUSH,
                           CommandType.POP,
                           CommandType.FUNCTION,
                           CommandType.CALL])
    def arg2(self):
        command = self._cur_line()
        arg = command.split(' ')[2]
        return int(arg)

class CodeWriter(object):
    SEMGENT_MAP = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
        'pointer': '3',
        'temp': '5',
    }

    def __init__(self, module_name, output_file_path):
        self._module_name = module_name
        self._output_file_path = output_file_path

        # we just use the default buffering,
        # which is set to io.DEFAULT_BUFFER_SIZE,
        # the typical value is 4096 or 8192 bytes.
        self._output_file = open(self._output_file_path, 'w')

        # used to create unique internal label name
        self._internal_label_idx = -1

    def __del__(self):
        self._output_file.close()

    def _write(self, content):
        self._output_file.write(content)

    def _write_line(self, content):
        '''Write content to output file, a newline is append automatically.
        '''
        self._write(content + '\n')

    def _write_arithmetic_add(self):
        '''
        VM:
            x + y

        Pseudo code:
            sp -= 2
            D = x
            A = y
            D = A + D
            memory[sp] = D

        Hack aseembly:
            @SP
            AM=M-1 // sp=sp-1, A points to y

            D=M // D = y

            A=A-1 // now A points to x
            M=M+D // x + y, save result to sp-1
        '''
        hack_assembly = '''@SP
AM=M-1
D=M
A=A-1
M=M+D
'''
        self._write(hack_assembly)

    def _write_arithmetic_sub(self):
        # similar to add
        hack_assembly = '''@SP
AM=M-1
D=M
A=A-1
M=M-D
'''
        self._write(hack_assembly)

    def _write_arithmetic_neg(self):
        hack_assembly = '''@SP
A=M-1
M=-M
'''
        self._write(hack_assembly)

    def _regularize_label_name(self, internal_label_name):
        '''Regularize internal label name used by VM2Hack compiler,
        to avoid conflict with user defined label name in VM language.

        We have to design internal label name used by VM2Hack compiler carefully,
        since it must satisfy:
            A. is valid name in Hack assembly language.
            B. no conflict with user defined label name in VM language.
            C. no conflict with internal_label_name used by VM2Hack compiler.
            D. no conflict among different modules(a single vm file is viewed as
                a module).

        Luckily, check the specifications of Hack assembly language and VM
        language, we find that $ is valid in Hack aseembly language, but it is
        invalid in VM language, so we can use $ in VM translation safely,
        which satisfies A and B.
        For C, we use a unique index here.
        For D, we use module name as prefix.
        '''
        # FIXME: module with same name.
        self._internal_label_idx += 1
        return f'${self._module_name}:{internal_label_name}:{self._internal_label_idx}$'

    def _regularize_static_variable_name(self, variable_idx):
        '''Same consideration need to be taken into acount as label name.'''
        return f'${self._module_name}:static:{variable_idx}$'

    def _write_arithmetic_eq(self):
        '''Translate VM's eq command.

        Idea: x - y, then jump according to result.

        VM:
            x = y, if true, store 0xFFFF to stack,
                   else store 0x0000 to stack
        Pseudo code:
            D = x - y
            result = false
            if D == 0:
                result = true

        Hack assembly(internal label not regularized):
            @SP
            AM=M-1
            D=M
            A=A-1
            D=M-D // similar to sub, here D holds x-y

            M=0 // save false by default

            @END
            D;JNE // not equal, we are done, jump to last

            @SP   // equal, we need change false to true
            A=M-1
            M=!M
            (END)
        '''
        end_label_name = self._regularize_label_name('END')
        hack_assembly = f'''@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@{end_label_name}
D;JNE
@SP
A=M-1
M=!M
({end_label_name})
'''
        self._write(hack_assembly)

    def _write_arithmetic_gt(self):
        '''Translate VM's gt command.

        Similar to eq.

        Hack assembly(not regularized):
            @SP
            AM=M-1
            D=M
            A=A-1
            D=M-D // similar to sub, here D holds x-y

            M=0 // save false by default

            @END
            D;JLE // x <= y, we are done, jump to last

            @SP   // x > y, we need change false to true
            A=M-1
            M=!M
            (END)
        '''
        end_label_name = self._regularize_label_name('END')
        hack_assembly = f'''@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@{end_label_name}
D;JLE
@SP
A=M-1
M=!M
({end_label_name})
'''
        self._write(hack_assembly)

    def _write_arithmetic_lt(self):
        '''Translate VM's lt command.

        Similar to eq.

        Hack assembly(not regularized):
            @SP
            AM=M-1
            D=M
            A=A-1
            D=M-D // similar to sub, here D holds x-y

            M=0 // save false by default

            @END
            D;JGE // x >= y, we are done, jump to last

            @SP   // x < y, we need change false to true
            A=M-1
            M=!M
            (END)
        '''
        end_label_name = self._regularize_label_name('END')
        hack_assembly = f'''@SP
AM=M-1
D=M
A=A-1
D=M-D
M=0
@{end_label_name}
D;JGE
@SP
A=M-1
M=!M
({end_label_name})
'''
        self._write(hack_assembly)

    def _write_arithmetic_and(self):
        # similar to add
        hack_assembly = '''@SP
AM=M-1
D=M
A=A-1
M=M&D
'''
        self._write(hack_assembly)

    def _write_arithmetic_or(self):
        # similar to add
        hack_assembly = '''@SP
AM=M-1
D=M
A=A-1
M=M|D
'''
        self._write(hack_assembly)

    def _write_arithmetic_not(self):
        # similar to not
        hack_assembly = '''@SP
A=M-1
M=!M
'''
        self._write(hack_assembly)

    def write_arithmetic(self, command):
        # REFACTOR: _write_arithmetic_xxx
        ARITHMETIC_WRITERS = [
            ('add', self._write_arithmetic_add),
            ('sub', self._write_arithmetic_sub),
            ('neg', self._write_arithmetic_neg),
            ('eq', self._write_arithmetic_eq),
            ('gt', self._write_arithmetic_gt),
            ('lt', self._write_arithmetic_lt),
            ('and', self._write_arithmetic_and),
            ('or', self._write_arithmetic_or),
            ('not', self._write_arithmetic_not),
        ]
        for cmd, writer in ARITHMETIC_WRITERS:
            if cmd == command:
                writer()
                return
        raise Exception(f'Not supported arithmetic operation: {command}')


    def write_stack_operation(self, command, segment, index):
        # TODO: enum these hardcode command
        if command == 'pop':
            if segment == 'static':
                self._write_pop_static(index)
            else:
                self._write_pop_not_constant_static(segment, index)
        elif command == 'push':
            if segment == 'constant':
                self._write_push_constant(index)
            elif segment == 'static':
                self._write_push_static(index)
            else:
                self._write_push_not_constant_static(segment, index)
        else:
            raise Exception(f'Not supported stack operation: {command}')

    def _write_push_constant(self, constant_value):
        """Translate VM's push command(constant version) to hack assembly language.

        VM:
            push constant value

        Pseudo code:
            memory[sp] = value
            sp += 1

            Note: here sp means the content in register SP

        Hack assembly:
            @value
            D=A // D = value

            @SP
            A=M // indirect addressing, now A holds memory[sp]'s address
            M=D // memory[sp] = *(segment + index)

            D=A+1 // sp + 1
            @SP
            M=D // sp = sp + 1
        """
        hack_assembly = f'''@{constant_value}
D=A
@SP
A=M
M=D
D=A+1
@SP
M=D
'''
        self._write(hack_assembly)

    def _write_push_static(self, index):
        """Translate VM's push command with static segment.

        VM:
            push static index

        Pseudo code:
            memory[sp] = module_name.index
            sp += 1

        Hack assembly:
            @module_name.index
            D=M

            @SP
            A=M
            M=D

            @SP
            M=M+1 // sp = sp + 1
        """
        variable_name = self._regularize_static_variable_name(index)
        hack_assembly = f'''@{variable_name}
D=M
@SP
A=M
M=D
@SP
M=M+1
'''
        self._write(hack_assembly)

    def _write_push_not_constant_static(self, segment, index):
        """Translate VM's push command to hack assembly language.
        Note that constant segment or static segment is handled by other
        function.

        VM:
            push segment index

        Pseudo code:
            memory[sp] = segment[index]
            sp += 1

            Note: here sp means the content in register SP

        Hack assembly:
            @segment
            D=A if is temp else D=M
            @index
            A=D+A // now A holds segment+index

            D=M // *(segment + index)

            @SP
            A=M // indirect addressing, now A holds memory[sp]'s address
            M=D // memory[sp] = *(segment + index)

            D=A+1 // sp + 1
            @SP
            M=D // sp = sp + 1
        """
        assert segment in CodeWriter.SEMGENT_MAP

        # segment temp and pointer are used directly, not base address
        segment_addressing = 'D=A' if segment in ['temp', 'pointer'] else 'D=M'

        segment = CodeWriter.SEMGENT_MAP[segment]
        hack_assembly = f'''@{segment}
{segment_addressing}
@{index}
A=D+A
D=M
@SP
A=M
M=D
D=A+1
@SP
M=D
'''
        self._write(hack_assembly)

    def _write_pop_static(self, index):
        """Translate VM's pop command with static segment.

        VM:
            pop static index

        Pseudo code:
            sp -= 1
            module.index = memory[sp]

        Hack assembly:
            @SP
            M=M-1

            A=M
            D=M // D holds memory[sp]

            @module_name.index
            M=D
        """
        variable_name = self._regularize_static_variable_name(index)
        hack_assembly = f'''@SP
M=M-1
A=M
D=M
@{variable_name}
M=D
'''
        self._write(hack_assembly)

    def _write_pop_not_constant_static(self, segment, index):
        """Translate VM's pop command(not constant version) to hack assembly language.

        VM:
            pop segment index

        Pseudo code:
            sp -= 1
            segment[index] = memory[sp]

            Note: here sp means the content in register SP

        Hack assembly:
            @segment
            D=A if is temp else D=M
            @index
            D=D+A // D holds segment+index

            @SP
            A=M
            M=D // save segment+index to current sp

            D=A-1 // sp-1
            @SP
            M=D // sp=sp-1

            A=D
            D=M // memory[sp]

            A=A+1
            A=M
            M=D
        """
        assert segment in CodeWriter.SEMGENT_MAP

        # segment temp and pointer are used directly, not base address
        segment_addressing = 'D=A' if segment in ['temp', 'pointer'] else 'D=M'

        segment = CodeWriter.SEMGENT_MAP[segment]
        hack_assembly = f'''@{segment}
{segment_addressing}
@{index}
D=D+A
@SP
A=M
M=D
D=A-1
@SP
M=D
A=D
D=M
A=A+1
A=M
M=D
'''
        self._write(hack_assembly)

class VM2Hack(object):
    def __init__(self, input_file_path, output_file_path=None):
        self._input_file_path = input_file_path
        self._output_file_path = self._set_output_file_path(output_file_path)

        self._parser = Parser(self._input_file_path)

        self._code_writer = CodeWriter(self._get_module_name(input_file_path),
                                       self._output_file_path)

    def _get_module_name(self, input_file_path):
        '''A single Xxx.vm is viewed as a module, the module name is Xxx.'''
        base = os.path.basename(input_file_path)
        filename_without_extension = os.path.splitext(base)[0]
        return filename_without_extension

    def _set_output_file_path(self, output_file_path):
        '''Saving output file to current working directory if output_file_path
        is not specified.
        '''
        if output_file_path is None:
            # output_file_path not provided, save to current working directory
            base = os.path.basename(self._input_file_path)
            filename_without_extension = os.path.splitext(base)[0]
            output_file_path = filename_without_extension + '.asm'
        return output_file_path

    def compile(self):
        while self._parser.has_more_commands():
            self._parser.advance()

            command_type = self._parser.command_type()
            if command_type in [CommandType.PUSH, CommandType.POP]:
                self._code_writer.write_stack_operation(
                    command=self._parser.command(),
                    segment=self._parser.arg1(),
                    index=self._parser.arg2(),
                )
            elif command_type == CommandType.ARITHMETIC:
                self._code_writer.write_arithmetic(self._parser.command())

def configure():
    def configure_logger():
        logger.setLevel(logging.DEBUG)
        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    configure_logger()

def compile_single_file(file_path):
    compiler = VM2Hack(file_path)
    compiler.compile()

def main(args):
    input_path = args.input_path

    if os.path.isdir(input_path):
        vm_file_paths = glob.glob(os.path.join(input_path, '*.vm'))
    else:
        vm_file_paths = [input_path]

    for vm_file_path in vm_file_paths:
        compile_single_file(vm_file_path)

if __name__ == "__main__":
    configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', metavar='input-path')

    args = parser.parse_args()

    main(args)
