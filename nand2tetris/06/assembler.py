#!/usr/bin/env python3

from enum import Enum
import functools
import re
import logging
import os
import argparse

CommandType = Enum('CommandType', ('A_COMMAND', 'C_COMMAND', 'L_COMMAND'))

class Parser(object):
    '''Parser of Hack assembler.

    Note that we assume that no syntax error in assembly file,
    so we dont hanle syntax error here for simplicity.
    '''
    def __init__(self, input_file_path):
        with open(input_file_path) as f:
            self._lines = f.readlines()

        # remove space, newline and comment
        self._lines = map(lambda line: re.sub(r' |\n|//.*', '', line),
                          self._lines)
        self._lines = list(filter(lambda line: line,
                                  self._lines))

        self.reset()

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
                assert args[0].command_type() in command_types
                return func(*args, **kw)
            return wrapper
        return decorator

    def reset(self):
        # at the beginning, there is no current line
        self._cur_line_idx = -1

    def has_more_commands(self):
        return self._lines and self._cur_line_idx < len(self._lines) - 1

    def advance(self):
        assert self.has_more_commands()

        self._cur_line_idx += 1

    def command_type(self):
        cur_line = self._cur_line()
        if cur_line.startswith('@'):
            return CommandType.A_COMMAND
        if cur_line.startswith('('):
            return CommandType.L_COMMAND
        return CommandType.C_COMMAND

    @_allow_command_types([CommandType.A_COMMAND, CommandType.L_COMMAND])
    def symbol(self):
        cur_line = self._cur_line()
        if self.command_type() == CommandType.A_COMMAND:
            return cur_line[1:]
        return cur_line[1:-1]

    @_allow_command_types([CommandType.C_COMMAND])
    def dest(self):
        cur_line = self._cur_line()
        if not '=' in cur_line:
            return None
        return cur_line.split('=')[0]

    @_allow_command_types([CommandType.C_COMMAND])
    def comp(self):
        comp_line = self._cur_line()

        #  if '=' in cur_line and ';' in cur_line: # dest=comp;jump
        #      dest_eq_comp = cur_line.split(';')[0]
        #      return dest_eq_comp.split('=')[1]
        #  if '=' in cur_line: # dest=comp
        #      return cur_line.split('=')[1]
        #  # comp;jump
        #  return cur_line.split(';')[0]
        #
        # three possible situations covered in the following two lines
        if ';' in comp_line:
            comp_line = comp_line.split(';')[0]
        if '=' in comp_line:
            comp_line = comp_line.split('=')[1]
        return comp_line

    @_allow_command_types([CommandType.C_COMMAND])
    def jump(self):
        cur_line = self._cur_line()
        if not ';' in cur_line:
            return None
        return cur_line.split(';')[1]

class Code(object):
    A_INSTRUCTION_HEADER = '0'
    C_INSTRUCTION_HEADER = '111'

    COMP_MNEMONIC_TO_BINARY_MAP = {
        '0': '0101010',
        '1': '0111111',
        '-1': '0111010',
        'D': '0001100',
        'A': '0110000',
        '!D': '001101',
        '!A': '0110001',
        '-D': '0001111',
        '-A': '0110011',
        'D+1': '0011111',
        'A+1': '0110111',
        'D-1': '0001110',
        'A-1': '0110010',
        'D+A': '0000010',
        'D-A': '0010011',
        'A-D': '0000111',
        'D&A': '0000000',
        'D|A': '0010101',

        'M': '1110000',
        '!M': '1110001',
        '-M': '1110011',
        'M+1': '1110111',
        'M-1': '1110010',
        'D+M': '1000010',
        'D-M': '1010011',
        'M-D': '1000111',
        'D&M': '1000000',
        'D|M': '1010101',
    }

    JUMP_MNEMONIC_TO_BINARY_MAP = {
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLT': '100',
        'JNE': '101',
        'JLE': '110',
        'JMP': '111',
    }

    @classmethod
    def dest(cls, mnemonic):
        buf = ['0'] * 3
        if mnemonic is not None:
            for idx, reg in enumerate(list('ADM')):
                if reg in mnemonic:
                    buf[idx] = '1'
        return ''.join(buf)

    @classmethod
    def comp(cls, mnemonic):
        binary_str = cls.COMP_MNEMONIC_TO_BINARY_MAP.get(mnemonic, None)
        if binary_str is None and len(mnemonic) == 3:
            # Since user may write 1+D instead of D+1, and 1+D is not defined in
            # cls.COMP_MNEMONIC_TO_BINARY_MAP, but we have D+1 defined,
            # so we can reverse mnemonic and try again.
            #
            # TODO: add symmetrical version to map directly to improve efficiency
            binary_str = cls.COMP_MNEMONIC_TO_BINARY_MAP.get(mnemonic[::-1],
                    None)

        assert binary_str is not None

        return binary_str


    @classmethod
    def jump(cls, mnemonic):
        if mnemonic is None:
            return '000'

        assert mnemonic in Code.JUMP_MNEMONIC_TO_BINARY_MAP

        return Code.JUMP_MNEMONIC_TO_BINARY_MAP[mnemonic]

class SymbolTable(object):
    def __init__(self):
        self._table = {}

    def add_entry(self, symbol, address):
        '''Add en entry to symbol table, override if already exist.'''
        self._table[symbol] = address

    def contains(self, symbol):
        return symbol in self._table

    def get_address(self, symbol):
        return self._table[symbol]

class Assembler(object):

    PREDEFINED_SYMBOLS = [
        ('SP', 0),
        ('LCL', 1),
        ('ARG', 2),
        ('THIS', 3),
        ('THAT', 4),
        ('R0', 0),
        ('R1', 1),
        ('R2', 2),
        ('R3', 3),
        ('R4', 4),
        ('R5', 5),
        ('R6', 6),
        ('R7', 7),
        ('R8', 8),
        ('R9', 9),
        ('R10', 10),
        ('R11', 11),
        ('R12', 12),
        ('R13', 13),
        ('R14', 14),
        ('R15', 15),
        ('SCREEN', 0x4000),
        ('KBD', 0x6000),
    ]

    def __init__(self, input_file_path):
        self._input_file_path = input_file_path
        self._instructions = []

        self._parser = Parser(self._input_file_path)
        self._symbol_table = SymbolTable()
        self._init_symbol_table()

        self._next_available_memory_address = 16

    def _init_symbol_table(self):
        for symbol, address in Assembler.PREDEFINED_SYMBOLS:
            self._symbol_table.add_entry(symbol, address)

    def _add_to_symbol_table_if_not_exist(self, symbol, next_pc):
        if self._symbol_table.contains(symbol):
            return
        self._symbol_table.add_entry(symbol, next_pc)

    def _scan_labels(self):
        '''Scan label definitions in assembly file, add them into symbol table,
        no binary will generate.
        '''
        pc = -1
        while self._parser.has_more_commands():
            self._parser.advance()

            if self._parser.command_type() != CommandType.L_COMMAND:
                pc += 1
                continue

            self._add_to_symbol_table_if_not_exist(self._parser.symbol(), pc+1)

    def _allocate_new_memory_address(self):
        old = self._next_available_memory_address
        self._next_available_memory_address += 1
        return old

    def _compile_A_instruction(self, symbol):
        def _is_decimal_string(s):
            return s.isdigit()
        def _decimal_to_binary_string(s):
            '''Convert decimal number or string to binary string.'''
            return '{:015b}'.format(int(s))
        def _is_new_variable(s):
            return not self._symbol_table.contains(s)
        def _to_A_instrction(constant_or_address):
            return Code.A_INSTRUCTION_HEADER + \
                   _decimal_to_binary_string(constant_or_address)

        assert symbol

        if _is_decimal_string(symbol):
            return _to_A_instrction(symbol)

        if _is_new_variable(symbol): # is a new variable
            self._symbol_table.add_entry(symbol,
                                        self._allocate_new_memory_address())

        return _to_A_instrction(self._symbol_table.get_address(symbol))

    def _compile_C_instruction(self, comp, dest, jump):
        comp = Code.comp(comp)
        dest = Code.dest(dest)
        jump = Code.jump(jump)

        assert comp and dest and jump

        return Code.C_INSTRUCTION_HEADER + comp + dest + jump

    def _handle_variables_and_generate(self):
        '''Handle variables and generate binary code.

        Handle variables for A-instruction:
            a. constant, convert decimal string to corresponding 16-bit
                binary string.
            b. variable, convert to memory address, starting from 16.
        '''
        variable_memory_address = 16
        while self._parser.has_more_commands():
            self._parser.advance()

            cur_command_type = self._parser.command_type()

            if cur_command_type == CommandType.L_COMMAND:
                continue

            if cur_command_type == CommandType.A_COMMAND:
                self._instructions.append(
                    self._compile_A_instruction(
                        self._parser.symbol()))
                continue

            self._instructions.append(
                    self._compile_C_instruction(
                        self._parser.comp(),
                        self._parser.dest(),
                        self._parser.jump()))

    def compile(self):
        if self._instructions:
            logging.warning('compile already done, no need to compile twice.')
            return

        # first pass, we just scan labels
        self._scan_labels()

        self._parser.reset() # reset parser to the initial state
        self._handle_variables_and_generate() # second pass

    def save(self, output_file_path=None):
        '''Save binary instructions to output_file_path,
        if output_file_path is None, save to current working directory.
        '''
        if not self._instructions:
            logging.warning('Trying to save, but instructions is empty.')
            return

        if output_file_path is None:
            base = os.path.basename(self._input_file_path)
            file_name_without_extension = os.path.splitext(base)[0]
            output_file_path = file_name_without_extension + '.hack'

        with open(output_file_path, 'w') as f:
            f.write('\n'.join(self._instructions))
            f.write('\n')


def main(args):
    assembler = Assembler(args.input_file_path)
    assembler.compile()
    assembler.save(args.output_file_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file_path', metavar='input-file-path')
    parser.add_argument('-output-file-path', default=None)
    args = parser.parse_args()
    main(args)
