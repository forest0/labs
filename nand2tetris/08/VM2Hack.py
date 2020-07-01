#!/usr/bin/env python3

'''VM2Hack.

Translate VM language to Hack assembly language.

VM program structure:
    In VM language, a program consists of one or multiple vm file(s),
    every vm file is a module and a module only corresponding to on vm file.
    Each vm file can have one or multiple function definition(s).

Compiling procedure:
    1. Compile every `xxx.vm` file, generate corresponding Hack assembly file
        `xxx.asm.part`
    2. Write bootstrap code, merge all `xxx.asm.part` to final `XXX.asm`

Testing:
    ProgramFlow/BasicLoop:
        We can not add bootstrap code in this test, so just test
        `BasicLoop.asm.part`, comparison passed
    ProgramFlow/FibonacciSeries
        We can not add bootstrap code in this test, so just test
        `FibonacciSeries.asm.part`, comparison passed

    FunctionCalls/SimpleFunction:
        We can not add bootstrap code in this test, so just test
        `SimpleFunction.asm.part`, comparison passed
    FunctionCalls/NestedCall:
        According to the doc, whether add bootstrap code or not is not
        important, and I add indeed. The output fails on RAM[5], which is used to
        check the return value of Sys.add12. When returning from Sys.add12 to
        Sys.main, we can manually verify that `pop temp 0` gives the expected
        result 135, but after returning to Sys.init, the content in `temp 0` is
        changed, so when finally check on RAM[5], it fails. The reason why it
        change is that I use `temp 0` to save LCL when returning, and according
        to VM's specification, the content in temp segment is undefined when
        the called function returns.
    FunctionCalls/FibonacciElement, FunctionCalls/StaticsTest:
        Bootstrap code added, comparison passed.
'''

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
    But syntax check is very import, e.g., if we dont check the legality of
    identifier, we may jump to the wrong target.
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

    COMMAND_TYPES_THAT_HAS_ZERO_ARG = [
        CommandType.ARITHMETIC,
        CommandType.RETURN,
    ]
    COMMAND_TYPES_THAT_HAS_ONE_ARG = [
        CommandType.ARITHMETIC,
        CommandType.PUSH,
        CommandType.POP,
        CommandType.LABEL,
        CommandType.GOTO,
        CommandType.IF,
        CommandType.FUNCTION,
        CommandType.CALL
    ]
    COMMAND_TYPES_THAT_HAS_TWO_ARG = [
        CommandType.PUSH,
        CommandType.POP,
        CommandType.FUNCTION,
        CommandType.CALL
    ]

    def __init__(self, input_file_path):
        with open(input_file_path) as f:
            self._lines = f.readlines()

        self._lines = self._regularize_lines(self._lines)

        self._cur_line_idx = -1
        self._cur_command_type = None
        self._arg1 = None
        self._arg2 = None

        # Note that some test scripts does not provide a function definition,
        # because at the beginning stages we does not handle function command
        # yet, so we provide a default function name here to let these test
        # scripts happy.
        # TODO: vm command can only be writen in function?
        self._cur_function_name = '$miss_function_name$'

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

    def _check_syntax_argument_amount(self):
        # TODO
        cur_argument_amount = len(self._cur_line().split(' ')) - 1

    def _check_syntax_argument(self):
        # TODO
        pass

    def _parse_cur_line(self):
        self._cur_command_type = self._parse_command_type()

        self._check_syntax_argument_amount()

        self._parse_arg1_if_necessary()
        self._parse_arg2_if_necessary()

        self._check_syntax_argument()

    def _parse_command_type(self):
        command = self.command()
        for detector, type in Parser.COMMAND_TYPE_DETECTORS:
            if detector(command):
                return type
        raise Exception(f'syntax error: unknown command type: {command}')

    def _parse_arg1_if_necessary(self):
        if self._cur_command_type == CommandType.ARITHMETIC:
            self._arg1 = self.command()
        elif self._cur_command_type in Parser.COMMAND_TYPES_THAT_HAS_ONE_ARG + \
                                       Parser.COMMAND_TYPES_THAT_HAS_TWO_ARG:
            self._arg1 = self._parse_arg1()
        else:
            self._arg1 = None

    def _parse_arg1(self):
        return self._cur_line().split(' ')[1]

    def _parse_arg2_if_necessary(self):
        if self._cur_command_type in Parser.COMMAND_TYPES_THAT_HAS_TWO_ARG:
            self._arg2 = self._parse_arg2()
        else:
            self._arg2 = None

    def _parse_arg2(self):
        arg = self._cur_line().split(' ')[2]
        return int(arg)

    def has_more_commands(self):
        return self._lines and self._cur_line_idx < len(self._lines) - 1

    def advance(self):
        # TODO: maybe we can check syntax here

        assert self.has_more_commands()

        self._cur_line_idx += 1

        self._parse_cur_line()

    def command(self):
        return self._cur_line().split(' ')[0]

    def command_type(self):
        return self._cur_command_type

    @_allow_command_types(COMMAND_TYPES_THAT_HAS_ONE_ARG)
    def arg1(self):
        return self._arg1

    @_allow_command_types(COMMAND_TYPES_THAT_HAS_TWO_ARG +
                          COMMAND_TYPES_THAT_HAS_TWO_ARG)
    def arg2(self):
        return self._arg2


class CodeWriter(object):
    '''Translate VM language to Hack assembly language, write translation result
    to output file.
    '''
    SEMGENT_MAP = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
        'pointer': '3',
        'temp': '5',
    }

    # used to create unique internal label name
    _internal_label_idx = -1

    # record the module name, in which Sys.init is defined
    module_name_contains_sys_init = None

    def __init__(self, module_name, output_file_path):
        self._module_name = module_name
        self._output_file_path = output_file_path

        # we just use the default buffering,
        # which is set to io.DEFAULT_BUFFER_SIZE,
        # the typical value is 4096 or 8192 bytes.
        self._output_file = open(self._output_file_path, 'w')

        #  self._internal_label_idx = -1
        self._cur_function_name = None

    def __del__(self):
        self._output_file.close()

    def _write(func):
        '''Decorator that write translation result to output file.
        A newline will be append at last if missing.
        '''
        @functools.wraps(func)
        def write_to_file(*args, **kw):
            hack_assembly = func(*args, **kw)
            if not hack_assembly:
                return

            if hack_assembly[-1] != '\n':
                hack_assembly += '\n'

            # args[0] is self
            args[0]._output_file.write(hack_assembly)

        return write_to_file

    @_write
    def _translate_arithmetic_add(self):
        '''Translate VM's add command to hack assembly.

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
        return '''@SP
AM=M-1
D=M
A=A-1
M=M+D
'''

    @_write
    def _translate_arithmetic_sub(self):
        # similar to add
        return '''@SP
AM=M-1
D=M
A=A-1
M=M-D
'''

    @_write
    def _translate_arithmetic_neg(self):
        return '''@SP
A=M-1
M=-M
'''

    def _regularize_internal_label_name(self, internal_label_name):
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
        return f'${self._module_name}:int:{internal_label_name}:{self._internal_label_idx}$'

    def _regularize_static_variable_name(self, variable_idx):
        '''Regularize static variable name.

        Same consideration need to be taken into acount as label name.

        Note that I did NOT follow the VM specification, which required the name
        to be `module_name.variable_idx`, but instead I use
        `module_name:static:variable_idx` for better readability.
        '''
        return f'${self._module_name}:static:{variable_idx}$'


    def _regularize_user_label_name(self, function_name, label_name):
        '''Regularize user defined label name, unique in every function.'''
        return f'{self._module_name}:func:{function_name}:{label_name}'

    @classmethod
    def _regularize_user_function_name(cls, module_name, function_name):
        '''Regularize user defined function name, unique in global.

        According to VM's specification, the function name is unique among all
        vm files, and function_A in A.vm can call function_B in B.vm directly,
        without to specify the vm file name, so when we see a function call,
        e.g. `call xxx`, the only information user provided is the function
        name xxx, we have no idea which vm file contains the definition of xxx,
        i.e., we dont know the module name, so we can not decorate function name
        with module name.

        Actually, we can find which vm file contains the definition of function
        xxx, but this requires we maintain a global symbol table, which is very
        similar to the symbol table in assembler we have just written, what's more,
        to find all the symbols, maybe we need to scan all vm codes twice.
        So for simplicity, we just keep the function name as is. And if user
        follow a good naming practice(e.g., a function xxx in Xxx.vm can be
        named as Xxx.xxx), it is actually fine.
        '''
        #  return f'{module_name}:func:{function_name}'
        return function_name

    @_write
    def _translate_arithmetic_eq(self):
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
        end_label_name = self._regularize_internal_label_name('END')
        return f'''@SP
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

    @_write
    def _translate_arithmetic_gt(self):
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
        end_label_name = self._regularize_internal_label_name('END')
        return f'''@SP
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

    @_write
    def _translate_arithmetic_lt(self):
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
        end_label_name = self._regularize_internal_label_name('END')
        return f'''@SP
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

    @_write
    def _translate_arithmetic_and(self):
        # similar to add
        return '''@SP
AM=M-1
D=M
A=A-1
M=M&D
'''

    @_write
    def _translate_arithmetic_or(self):
        # similar to add
        return '''@SP
AM=M-1
D=M
A=A-1
M=M|D
'''

    @_write
    def _translate_arithmetic_not(self):
        # similar to not
        return '''@SP
A=M-1
M=!M
'''

    def write_arithmetic(self, command):
        # REFACTOR: _write_arithmetic_xxx
        ARITHMETIC_TRANSLATERS = [
            ('add', self._translate_arithmetic_add),
            ('sub', self._translate_arithmetic_sub),
            ('neg', self._translate_arithmetic_neg),
            ('eq', self._translate_arithmetic_eq),
            ('gt', self._translate_arithmetic_gt),
            ('lt', self._translate_arithmetic_lt),
            ('and', self._translate_arithmetic_and),
            ('or', self._translate_arithmetic_or),
            ('not', self._translate_arithmetic_not),
        ]
        for cmd, translater in ARITHMETIC_TRANSLATERS:
            if cmd == command:
                translater()
                return
        raise Exception(f'Not supported arithmetic operation: {command}')


    def write_stack_operation(self, command, segment, index):
        # TODO: enum these hardcode command
        if command == 'pop':
            if segment == 'static':
                self._translate_pop_static(index)
            else:
                self._translate_pop_not_constant_static(segment, index)
        elif command == 'push':
            if segment == 'constant':
                self._write_push_constant(index)
            elif segment == 'static':
                self._translate_push_static(index)
            else:
                self._translate_push_not_constant_static(segment, index)
        else:
            raise Exception(f'Not supported stack operation: {command}')

    @classmethod
    def _translate_push_constant(cls, constant_value):
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

            @SP
            M=M+1 // sp = sp + 1
        """
        return f'''@{constant_value}
D=A
@SP
A=M
M=D
@SP
M=M+1
'''

    @classmethod
    def _tranlate_push_register(cls, register_name):
        return f'''@{register_name}
D=M
@SP
A=M
M=D
@SP
M=M+1
'''

    @_write
    def _write_push_constant(self, constant_value):
        return self._translate_push_constant(constant_value)

    @_write
    def _translate_push_static(self, index):
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
        return f'''@{variable_name}
D=M
@SP
A=M
M=D
@SP
M=M+1
'''

    @_write
    def _translate_push_not_constant_static(self, segment, index):
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
        return f'''@{segment}
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

    @_write
    def _translate_pop_static(self, index):
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
        return f'''@SP
M=M-1
A=M
D=M
@{variable_name}
M=D
'''

    @_write
    def _translate_pop_not_constant_static(self, segment, index):
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
        return f'''@{segment}
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


    def _translate_init(self):
        pass

    def write_program_flow(self, command, label):
        if command == 'label':
            self._translate_label(label)
        elif command == 'goto':
            self._translate_goto(label)
        elif command == 'if-goto':
            self._translate_if(label)
        else:
            raise Exception(f'Not supported program flow command: {command}')

    @_write
    def _translate_label(self, label):
        label = self._regularize_user_label_name(self._cur_function_name, label)
        return f'''({label})
'''

    @_write
    def _translate_goto(self, label):
        label = self._regularize_user_label_name(self._cur_function_name, label)
        return f'''@{label}
0;JMP
'''

    @_write
    def _translate_if(self, label):
        '''Translate VM's if-goto command to Hack assembly.

        VM:
            if-goto label

        Pseudo code:
            sp -= 1
            if memory[sp] != 0
                jump to label

        Hack assembly:
            @SP
            M=M-1 // sp = sp-1

            A=M // A points to memory[sp]
            D=M // D holds memory[sp]

            @label
            D;JNE
        '''
        label = self._regularize_user_label_name(self._cur_function_name, label)
        return f'''@SP
M=M-1
A=M
D=M
@{label}
D;JNE
'''

    @_write
    def write_call(self, function_name, argument_amount):
        return self._translate_call(function_name, argument_amount)

    def _translate_call(self, function_name, argument_amount):
        '''Translate VM's call command to Hack aseembly.

        VM:
            call function_name argument_amount

        Pseudo code:
            push return_address // label defined at last

            // save segment registers
            push LCL
            push ARG
            push THIS
            push THAT

            // reset ARG and LCL
            ARG = SP - argument_amount - 5
            LCL = SP

            goto function_name

            (return_address)
        '''
        return_address = self._regularize_internal_label_name(f'RET_{self._cur_function_name}')

        reset_ARG = f'''@SP
D=M
@{argument_amount+5}
D=D-A
@ARG
M=D
'''
        reset_LCL = '''@SP
D=M
@LCL
M=D
'''

        function_name = self._regularize_user_function_name(
                self._module_name, function_name)
        goto_func = f'''@{function_name}
0;JMP
'''

        return_label = f'({return_address})\n'

        # Newline already contained in each piece, so no need to add newline again.
        return ''.join([
            self._translate_push_constant(return_address),

            self._tranlate_push_register('LCL'),
            self._tranlate_push_register('ARG'),
            self._tranlate_push_register('THIS'),
            self._tranlate_push_register('THAT'),

            reset_ARG,
            reset_LCL,

            goto_func,

            return_label,
        ])

    @_write
    def write_return(self):
        return self._translate_return()

    def _translate_return(self):
        '''Translate VM's return command.

        VM:
            return

        Pseudo code:
            frame = LCL // frame is a temp variable
            // according to specification, after returned to callee,
            // the content in temp segment in undefined, we can use them safely.

            // Save return address to temp variable.
            // Note that we MUST store return address to temp variable before we
            // move return value to *ARG, since ARG may point to return address.
            // because
            ret = *(frame - 5)

            *ARG = pop() // mv return value to the top of the callee

            SP = ARG + 1 // reset callee's frame

            // reset callee's segment registers
            THAT = *(frame - 1)
            THIS = *(frame - 2)
            ARG = *(frame - 3)
            LCL = *(frame - 4)

            goto ret // return to callee

        Hack assembly:
            @LCL
            D=M
            @R5
            M=D // save LCL to R5, a register in temp segment

            @5
            A=D-A // A = frame - 5
            D=M // D = *(frame - 5)
            @R6
            M=D // save return address to R6, a register in temp segment

            @SP
            A=M-1
            D=M // now D holds return value
            @ARG
            A=M
            M=D // *ARG = return value

            D=A+1 // D = ARG + 1
            @SP
            M=D // SP = ARG + 1

            @R5
            A=M-1 // A = frame - 1
            D=M // D = *(frame - 1)
            @THAT
            M=D // THAT = *(frame - 1)

            @R5
            D=M
            @2
            A=D-A // A = frame - 2
            D=M // D = *(frame - 2)
            @THIS
            M=D

            @R5
            D=M
            @3
            A=D-A // A = frame - 3
            D=M // D = *(frame - 3)
            @ARG
            M=D

            @R5
            D=M
            @4
            A=D-A // A = frame - 4
            D=M // D = *(frame - 4)
            @LCL
            M=D

            @R6
            A=M
            0;JMP
        '''
        return '''@LCL
D=M
@R5
M=D
@5
A=D-A
D=M
@R6
M=D
@SP
A=M-1
D=M
@ARG
A=M
M=D
D=A+1
@SP
M=D
@R5
A=M-1
D=M
@THAT
M=D
@R5
D=M
@2
A=D-A
D=M
@THIS
M=D
@R5
D=M
@3
A=D-A
D=M
@ARG
M=D
@R5
D=M
@4
A=D-A
D=M
@LCL
M=D
@R6
A=M
0;JMP
'''

    @_write
    def write_function(self, function_name, local_variable_amount):
        return self._translate_function(function_name, local_variable_amount)

    def _translate_function(self, function_name, local_variable_amount):
        '''Translate VM's function command to Hack assembly.

        VM:
            function function_name local_variable_amount

        Pseudo code:
            (function_name) // declare a label at the entry of the function

            // initialize every local variable to 0
            repeat local_variable_amount times:
                push constant 0
        '''
        self._cur_function_name = function_name
        if function_name == 'Sys.init':
            CodeWriter.module_name_contains_sys_init = self._module_name

        function_name = self._regularize_user_function_name(
                self._module_name, function_name)
        push_constant_0 = self._translate_push_constant(0)
        push_commands = ''.join([push_constant_0] * local_variable_amount)
        if not push_commands:
            return f'''({function_name})
'''
        return f'''({function_name})
{push_commands}'''

    @classmethod
    def get_bootstrap_hack_assembly(cls):
        '''Hack assembly that bootstrapping VM.

        Pseudo code:
            sp = 256
            call Sys.init

        REFACTOR:
            saddly, we can not use the _translate_call defined above because of
            bad design, we have to manually repeat the call logic here.
        '''
        reset_SP = '''@256
D=A
@SP
M=D
'''
        return_address = '$$bootstrap$:int:RET:0$'

        reset_ARG = f'''@SP
D=M
@5
D=D-A
@ARG
M=D
'''
        reset_LCL = '''@SP
D=M
@LCL
M=D
'''

        function_name = cls._regularize_user_function_name(
                module_name=cls.module_name_contains_sys_init,
                function_name='Sys.init')
        goto_func = f'''@{function_name}
0;JMP
'''

        return_label = f'({return_address})\n'

        # Newline already contained in each piece, so no need to add newline again.
        return ''.join([
            reset_SP,

            cls._translate_push_constant(return_address),

            cls._tranlate_push_register('LCL'),
            cls._tranlate_push_register('ARG'),
            cls._tranlate_push_register('THIS'),
            cls._tranlate_push_register('THAT'),

            reset_ARG,
            reset_LCL,

            goto_func,

            return_label,
        ])


class VM2Hack(object):

    _final_output_file_path = ''
    _output_file_paths = []

    def __init__(self, input_file_path, output_file_path=None):
        '''Constructor of VM2Hack.

        Args:
            input_file_path: current compiling input file path.
            output_file_path: the file path to save current compiling result,
                default to basename of input_file_path with file extension as
                `.asm.part`.
        '''
        self._input_file_path = input_file_path
        self._output_file_path = self._set_output_file_path(output_file_path)
        self._output_file_paths.append(self._output_file_path)

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
            output_file_path = filename_without_extension + '.asm.part'
        return output_file_path

    def compile_single_file(self):
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
            elif command_type in [CommandType.LABEL, CommandType.GOTO,
                                  CommandType.IF]:
                self._code_writer.write_program_flow(
                        command=self._parser.command(),
                        label=self._parser.arg1()
                )
            elif command_type == CommandType.FUNCTION:
                self._code_writer.write_function(
                    function_name=self._parser.arg1(),
                    local_variable_amount=self._parser.arg2(),
                )
            elif command_type == CommandType.CALL:
                self._code_writer.write_call(
                    function_name=self._parser.arg1(),
                    argument_amount=self._parser.arg2(),
                )
            elif command_type == CommandType.RETURN:
                self._code_writer.write_return()
            else:
                raise Exception(f'Not supported command type: {command_type}')

        return self._output_file_path

    @classmethod
    def set_final_output_file_path(cls, path):
        cls._final_output_file_path = path

    @classmethod
    def write_bookstrap_and_merge_all(cls):
        '''Write VM's bootstrap Hack assembly code, then merge all seperated
        compiling result to get the final Hack assembly file.
        '''
        def cat(input_file_paths, output_file):
            for input_file_path in input_file_paths:
                with open(input_file_path) as fin:
                    output_file.write(fin.read())

        with open(cls._final_output_file_path, 'w') as f:
            f.write(CodeWriter.get_bootstrap_hack_assembly())
            cat(cls._output_file_paths, f)

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
    output_file_path = compiler.compile_single_file()
    return output_file_path

def main(args):
    input_path = os.path.abspath(args.input_path)

    if os.path.isdir(input_path):
        vm_file_paths = glob.glob(os.path.join(input_path, '*.vm'))
    else:
        vm_file_paths = [input_path]

    final_output_file_path = os.path.basename(input_path) + '.asm'

    for vm_file_path in vm_file_paths:
        compile_single_file(vm_file_path)

    VM2Hack.set_final_output_file_path(final_output_file_path)
    VM2Hack.write_bookstrap_and_merge_all()

if __name__ == "__main__":
    configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', metavar='input-path')

    args = parser.parse_args()

    main(args)
