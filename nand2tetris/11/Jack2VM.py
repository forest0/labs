#!/usr/bin/env python3

'''Compiler of Jack language.

The syntax analysis code are copied from the previous project.

I know this is a big file, but I just want to keep the compiler a single file,
and I have split many functionalities into classes, so cut them will be easy.

Testing:
    all passed.

The version of VMEmulator which is packed with source code is 2.6,
at the very beginning I translate a function call with the wrong name,
the VMEmulator just throws an exception, something like java.substring out of
range, so my VM program refused to load. Then I found the source code of
VMEmulator on Github, but the source code version has updated to 2.6.2,
so I failed to found where the exception was threw. Then I stopped and use the
new version(2.6.2) of VMEmulator, and it gives better error hint, so I finally
find the cause of my bug.
One more thing that I noticed is that the VMEmulator's step over function not
work properly sometimes, namely, jump to some random place, which is really a
terrible debug experience.
'''

import logging
import argparse
import enum
import functools
import os
import glob

logger = logging.getLogger(name=__name__)

@enum.unique
class TokenType(enum.Enum):
    KEYWORD = enum.auto()
    SYMBOL = enum.auto()
    IDENTIFIER = enum.auto()
    CONST_INTEGER = enum.auto()
    CONST_STRING = enum.auto()

    @staticmethod
    def to_string(type):
        return {
            TokenType.KEYWORD: 'keyword',
            TokenType.SYMBOL: 'symbol',
            TokenType.IDENTIFIER: 'identifier',
            TokenType.CONST_INTEGER: 'integerConstant',
            TokenType.CONST_STRING: 'stringConstant',
        }[type]

class Token(object):
    def __init__(self, type, string=''):
        assert isinstance(type, TokenType)

        self.type = type
        self.string = string

    def __eq__(self, other):
        if not isinstance(other, Token) or self.type != other.type:
            return False

        if self.type in [TokenType.IDENTIFIER,
                         TokenType.CONST_INTEGER,
                         TokenType.CONST_STRING]:
            return True

        return self.string == other.string

    def __str__(self):
        return f'{self.type.name}:{self.string}'

    def to_xml_string(self):
        tag = Utils.escape_xml(TokenType.to_string(self.type))
        value = Utils.escape_xml(self.string)
        return f'<{tag}> {value} </{tag}>'

@enum.unique
class SymbolKind(enum.Enum):
    STATIC = enum.auto()
    FIELD = enum.auto()
    ARGUMENT = enum.auto()
    VARIABLE = enum.auto()

    @classmethod
    def from_string(cls, s):
        return {
            'static': cls.STATIC,
            'field': cls.FIELD,
            'var': cls.VARIABLE,
        }[s]

class Symbol(object):
    def __init__(self, name, type, kind, index):
        assert isinstance(kind, SymbolKind)

        self.name = name
        self.type = type
        self.kind = kind
        self.index = index

    def __str__(self):
        return f'Symbol({self.name}, {self.type}, {self.kind}, {self.index})'

class VMSpecification(object):
    @enum.unique
    class SegmentType(enum.Enum):
        CONSTANT = 'constant'
        ARGUMENT = 'argument'
        LOCAL = 'local'
        STATIC = 'static'
        THIS = 'this'
        THAT = 'that'
        POINTER = 'pointer'
        TEMP = 'temp'

    @enum.unique
    class CommandType(enum.Enum):
        ADD = 'add'
        SUB = 'sub'
        NEG = 'neg'
        EQ = 'eq'
        GT = 'gt'
        LT = 'lt'
        AND = 'and'
        OR = 'or'
        NOT = 'not'

class JackSpecification(object):
    KEYWORDS = [
        'class',
        'constructor',
        'function',
        'method',
        'field',
        'static',
        'var',
        'int',
        'char',
        'boolean',
        'void',
        'true',
        'false',
        'null',
        'this',
        'let',
        'do',
        'if',
        'else',
        'while',
        'return',
    ]

    SYMBOLS = [
        '{',
        '}',
        '(',
        ')',
        '[',
        ']',
        '.',
        ',',
        ';',
        '+',
        '-',
        '*',
        '/',
        '&',
        '|',
        '<',
        '>',
        '=',
        '~',
    ]

    WHITESPACE = [
        ' ',
        # seems that tab is not specified in Jack specification,
        # but it show up in ArrayTest/Main.jack
        '\t',
        '\n',
    ]

    TOKENS_THAT_CAN_BE_TYPE = [
        Token(TokenType.KEYWORD, 'int'),
        Token(TokenType.KEYWORD, 'char'),
        Token(TokenType.KEYWORD, 'boolean'),
        Token(TokenType.IDENTIFIER),
    ]

    VARIABLE_KIND_TO_SEGMENT_MAP = {
        SymbolKind.STATIC: VMSpecification.SegmentType.STATIC,
        SymbolKind.FIELD: VMSpecification.SegmentType.THIS,
        SymbolKind.ARGUMENT: VMSpecification.SegmentType.ARGUMENT,
        SymbolKind.VARIABLE: VMSpecification.SegmentType.LOCAL,
    }

    @classmethod
    def is_whitespace(cls, s):
        return s in cls.WHITESPACE

    @classmethod
    def is_keyword(cls, s):
        return s in cls.KEYWORDS

    @classmethod
    def is_symbol(cls, s):
        return s in cls.SYMBOLS

class SyntaxError(Exception):
    def __init__(self, file_path, line_number, message):
        super().__init__(file_path, line_number, message)

        self.file_path = file_path
        self.line_number = line_number
        self.message = message

    def __str__(self):
        return f'{self.file_path}:{self.line_number} {self.message}'

class SemanticError(Exception):
    def __init__(self, file_path, line_number, message):
        super().__init__(file_path, line_number, message)

        self.file_path = file_path
        self.line_number = line_number
        self.message = message

    def __str__(self):
        return self.message

class Utils(object):
    @staticmethod
    def escape_xml(value):
        repalce_rules = [
            ('&', '&amp;'), # this one must comes first
            ('<', '&lt;'),
            ('>', '&gt;'),
        ]
        for old, new in repalce_rules:
            value = value.replace(old, new)
        return value

class Tokenizer(object):

    @enum.unique
    class _Status(enum.Enum):
        '''Token scanner DFA status.'''
        START = enum.auto()
        DONE = enum.auto()

        IN_LINE_COMMENT = enum.auto()
        IN_BLOCK_COMMENT = enum.auto()
        IN_NUMBER = enum.auto()
        IN_ID = enum.auto()
        In_STRING = enum.auto()

    def __init__(self, input_file_path):
        self._input_file_path = input_file_path

        with open(self._input_file_path) as f:
            self._all_chars_in_input_file = f.read()

        self._input_file_length = len(self._all_chars_in_input_file)
        self._last_valid_char_idx_in_input_file = self._get_last_valid_char_index_in_input_file()

        self._cur_char_idx_in_input_file = -1
        self._cur_char_idx_in_line = -1
        self._cur_line_number = 0

        self._cur_token_type = None
        self._cur_token_string = ''

    def _get_last_valid_char_index_in_input_file(self):
        cur_idx = self._input_file_length - 1
        while cur_idx >= 0 and self._all_chars_in_input_file[cur_idx] in ' \n':
            cur_idx -= 1

        return cur_idx

    def _has_more_chars(self):
        return self._input_file_length > 0 and \
            self._cur_char_idx_in_input_file < self._input_file_length - 1

    def _get_next_char(self):
        if self._cur_char_idx_in_input_file > -1 and \
            self._all_chars_in_input_file[self._cur_char_idx_in_input_file] == '\n':
            self._cur_char_idx_in_line = 0
            self._cur_line_number += 1
        else:
            self._cur_char_idx_in_line += 1

        self._cur_char_idx_in_input_file += 1

        return self._all_chars_in_input_file[self._cur_char_idx_in_input_file]

    def _unget_next_char(self):
        if self._cur_char_idx_in_input_file < 0:
            return

        self._cur_char_idx_in_input_file -= 1
        idx = self._cur_char_idx_in_input_file
        if self._all_chars_in_input_file[idx] == '\n':
            self._cur_line_number -= 1
            idx -= 1
            while idx >= 0 and self._all_chars_in_input_file[idx] != '\n':
                idx -= 1
            self._cur_char_idx_in_line = self._cur_char_idx_in_input_file - idx - 1
        else:
            self._cur_char_idx_in_line -= 1

    def _get_next_char_if_any(self):
        if self._has_more_chars():
            return self._get_next_char()
        return None

    def _get_char(self, offset):
        '''Get char at cur_char_idx_in_input_file + offset. If out of boundary,
        None is returned.

        Sometimes we need to look ahead to eliminate ambiguity.
        '''
        idx = self._cur_char_idx_in_input_file + offset
        if idx >= self._input_file_length:
            return None

        return self._all_chars_in_input_file[idx]

    def _is_alpha_or_underline(self, c):
        if c is None:
            return False
        # we can NOT use str.isalpha here, since str.isalpha is a superset of
        # what we want.
        return c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'

    def _get_next_token(self):
        '''Get next token by running a DFA.'''
        status = Tokenizer._Status.START
        cur_token_buffer = []

        # REFACTOR:
        # what a mess
        while status != Tokenizer._Status.DONE:
            c = self._get_next_char_if_any()
            need_save = True
            if status == Tokenizer._Status.START:
                if c is None: # TODO: EOF
                    logger.fatal(f'EOF in DFA, status: {status}')
                elif JackSpecification.is_whitespace(c):
                    need_save = False
                elif c.isdigit():
                    status = Tokenizer._Status.IN_NUMBER
                elif self._is_alpha_or_underline(c):
                    status = Tokenizer._Status.IN_ID
                elif c == '"':
                    need_save = False
                    status = Tokenizer._Status.In_STRING
                elif c == '/':
                    # we have to look ahead to check whethe it is a divide
                    # symbol or a comment symbol
                    look_ahead_one_char = self._get_char(1)
                    if look_ahead_one_char == '/':
                        self._get_next_char_if_any() # we can consume next char safely
                        status = Tokenizer._Status.IN_LINE_COMMENT
                        need_save = False
                    elif look_ahead_one_char == '*':
                        self._get_next_char_if_any() # we can consume next char safely
                        status = Tokenizer._Status.IN_BLOCK_COMMENT
                        need_save = False
                    else: # look_ahead_one_char is some other char or None
                        status = Tokenizer._Status.DONE
                        self._cur_token_type = TokenType.SYMBOL
                elif JackSpecification.is_symbol(c):
                    # note that the symbol / is alread handled above,
                    # but / is still in JackSpecification.SYMBOLS
                    status = Tokenizer._Status.DONE
                    self._cur_token_type = TokenType.SYMBOL
            elif status == Tokenizer._Status.IN_LINE_COMMENT:
                need_save = False
                if c is None:
                    # line comment without newline at last,
                    # this can rarely happen, namely, the last line of input
                    # file is line comment, but the last char is not newline.
                    status = Tokenizer._Status.DONE
                elif c == '\n':
                    # comment is ignored by parser, so we continue to find next token
                    status = Tokenizer._Status.START
            elif status == Tokenizer._Status.IN_BLOCK_COMMENT:
                need_save = False
                if c is None:
                    # the coment is not closed by */, which is a syntax error
                    raise self.syntax_error(
                        'Block comment are expected to be closed by "*/"')
                elif c == '*':
                    look_ahead_one_char = self._get_char(1)
                    if look_ahead_one_char is None:
                        raise self.syntax_error(
                            'Block comment are expected to be closed by "*/"')
                    elif look_ahead_one_char == '/':
                        self._get_next_char_if_any() # we can consume next char safely
                        status = Tokenizer._Status.START
            elif status == Tokenizer._Status.IN_ID:
                if c is None:
                    need_save = False
                    status = Tokenizer._Status.DONE
                elif not self._is_alpha_or_underline(c):
                    need_save = False
                    self._unget_next_char() # we need send this char back
                    status = Tokenizer._Status.DONE

                if status == Tokenizer._Status.DONE:
                    self._cur_token_type = TokenType.IDENTIFIER
            elif status == Tokenizer._Status.IN_NUMBER:
                if c is None:
                    need_save = False
                    status = Tokenizer._Status.DONE
                elif not c.isdigit():
                    need_save = False
                    self._unget_next_char() # we need send this char back
                    status = Tokenizer._Status.DONE

                if status == Tokenizer._Status.DONE:
                    self._cur_token_type = TokenType.CONST_INTEGER

            elif status == Tokenizer._Status.In_STRING:
                if c is None:
                    raise self.syntax_error(
                        'String literal should be enclosed by \'"\'')
                if c == '"':
                    need_save = False
                    status = Tokenizer._Status.DONE
                    self._cur_token_type = TokenType.CONST_STRING

            if need_save:
                cur_token_buffer.append(c)

        self._cur_token_string = ''.join(cur_token_buffer)

    def syntax_error(self, message):
        return SyntaxError(self._input_file_path,
                           self._cur_line_number,
                           message)

    def semantic_error(self, message):
        return SemanticError(self._input_file_path,
                           self._cur_line_number,
                           message)

    def has_more_tokens(self):
        # FIXME: false positive when there is comment at the end of input file.
        return self._cur_char_idx_in_input_file < self._last_valid_char_idx_in_input_file

    def advance(self):
        assert self.has_more_tokens()

        self._get_next_token()

        if self._cur_token_type == TokenType.IDENTIFIER and \
                JackSpecification.is_keyword(self._cur_token_string):
            self._cur_token_type = TokenType.KEYWORD

    def token(self):
        return Token(self._cur_token_type, self._cur_token_string)

class SymbolTable(object):

    _static_symbol_idx = -1

    def __init__(self):
        self._class_scope_symbols = {}
        self._subroutine_scope_symbols = {}

        self._field_symbol_idx = -1
        self._argument_symbol_idx = -1
        self._variable_symbol_idx = -1

    def new_subroutine(self, is_method):
        self._subroutine_scope_symbols = {}
        self._argument_symbol_idx = -1
        self._variable_symbol_idx = -1

        if is_method:
            # this will be passed as the the first argument,
            # so all other auguments' idx must add 1
            self._argument_symbol_idx += 1

    def add(self, name, type, kind):
        if isinstance(kind, str):
            kind = SymbolKind.from_string(kind)
        assert isinstance(kind, SymbolKind)

        if kind == SymbolKind.STATIC:
            SymbolTable._static_symbol_idx += 1
            idx = SymbolTable._static_symbol_idx
            symbols = self._class_scope_symbols
        elif kind == SymbolKind.FIELD:
            self._field_symbol_idx += 1
            idx = self._field_symbol_idx
            symbols = self._class_scope_symbols
        elif kind == SymbolKind.ARGUMENT:
            self._argument_symbol_idx += 1
            idx = self._argument_symbol_idx
            symbols = self._subroutine_scope_symbols
        else:
            self._variable_symbol_idx += 1
            idx = self._variable_symbol_idx
            symbols = self._subroutine_scope_symbols

        symbol = Symbol(name, type, kind, idx)
        symbols[name] = symbol
        return symbol

    def symbol_amount(self, kind):
        '''Return the symbol amount of the kind.'''
        assert isinstance(kind, SymbolKind)

        if kind in [SymbolKind.STATIC, SymbolKind.FIELD]:
            symbols = self._class_scope_symbols.values()
        else:
            symbols = self._subroutine_scope_symbols.values()

        cnt = 0
        for symbol in symbols:
            if symbol.kind == kind:
                cnt += 1

        return cnt

    def get(self, name):
        '''Get the symbol with the name, None is returned if not exist.'''
        if name in self._subroutine_scope_symbols:
            return self._subroutine_scope_symbols[name]
        return self._class_scope_symbols.get(name, None)

    def contains_variable(self, name):
        if not (name in self._subroutine_scope_symbols):
            return False

        # FIXME
        return self._subroutine_scope_symbols[name].kind == SymbolKind.VARIABLE

class VMWriter(object):

    def __init__(self, output_file_path):
        self._output_file_path = output_file_path

        self._output_file = open(self._output_file_path, 'w')

    def __del__(self):
        self._output_file.close()

    # FIXME: suppress lint warning: no-self-argument
    def _write(func): # pylint: disable=no-self-argument
        '''Decorator that write translation result to output file.
        A newline will be append at last if missing.
        '''
        @functools.wraps(func)
        def write_to_file(*args, **kw):
            vm_codes = func(*args, **kw)
            if not vm_codes:
                return

            if vm_codes[-1] != '\n':
                vm_codes += '\n'

            #  print(vm_codes, end='')

            # args[0] is self
            args[0]._output_file.write(vm_codes)

        return write_to_file

    @_write
    def push(self, segment, index):
        assert isinstance(segment, VMSpecification.SegmentType)

        return f'''push {segment.value} {index}
'''

    @_write
    def pop(self, segment, index):
        assert isinstance(segment, VMSpecification.SegmentType)

        return f'''pop {segment.value} {index}
'''

    @_write
    def arithmetic(self, command):
        assert isinstance(command, VMSpecification.CommandType)

        return f'''{command.value}
'''

    @_write
    def label(self, name):
        return f'''label {name}
'''

    @_write
    def goto(self, label):
        return f'''goto {label}
'''

    @_write
    def if_goto(self, label):
        return f'''if-goto {label}
'''

    @_write
    def call(self, name, argument_amount):
        return f'''call {name} {argument_amount}
'''

    @_write
    def function(self, name, argument_amount):
        return f'''function {name} {argument_amount}
'''

    @_write
    def ret(self):
        return 'return\n'

class CompileEngine(object):

    next_available_label_idx = 0

    def __init__(self, tokenizer, output_file_path, print_ast_as_xml=False):
        self._tokenizer = tokenizer
        self._output_file_path = output_file_path

        self._print_ast_as_xml = print_ast_as_xml

        self._cur_token = None
        self._next_token = self._get_next_token_if_any()

        self._cur_classname = None

        self._symbol_table = SymbolTable()
        self._code_writer = VMWriter(output_file_path)

        # According to Jack Specification, every .jack file contains exactly one
        # class definition, and class is the top structure in .jack file.
        assert self._next_token == Token(TokenType.KEYWORD, 'class')
        #  self._compile_class()

    def _get_next_token_if_any(self):
        if not self._tokenizer.has_more_tokens():
            return None

        self._tokenizer.advance()
        return self._tokenizer.token()

    def _advance_token(self):
        self._cur_token = self._next_token
        self._next_token = self._get_next_token_if_any()

    def _expect_tokens(self, tokens):
        if not isinstance(tokens, list):
            tokens = [tokens]

        self._advance_token()

        cur_token = self._cur_token
        if cur_token is None:
            # TODO: better syntax error message
            raise self._tokenizer.syntax_error(
                f'Unexpected EOF, expecte token {tokens}')
        elif cur_token not in tokens:
            # TODO: better syntax error message
            raise self._tokenizer.syntax_error(
                f'Unexpected token {cur_token.type} {cur_token.string}, ' +
                f'expecte token {tokens}'
            )

        if self._print_ast_as_xml:
            print(cur_token.to_xml_string())
        return cur_token

    # FIXME: suppress lint warning: no-self-argument
    def _if_next_token_in(tokens): # pylint: disable=no-self-argument
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                # args[0] is self
                next_token = args[0]._next_token

                # we have to keep compiling, since the grammer of some
                # non-terminals can show up repeatly.
                # e.g.
                #       class: 'class' className '{'
                #           classVarDec*
                #           subroutineDec*
                #       '}'
                # classVarDec can show up zero or many times,
                # if zero, we do noting,
                # else we continue compiling possible multiple classVarDec
                cnt = 0
                while args[0]._next_token in tokens:
                    ret = func(*args, **kw)
                    if isinstance(ret, int):
                        cnt += ret
                return cnt
            return wrapper
        return decorator

    # FIXME: suppress lint warning: no-self-argument
    def _print_ast_as_xml_if_necessary(tag): # pylint: disable=no-self-argument
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                # args[0] is self
                if not args[0]._print_ast_as_xml:
                    return func(*args, **kw)

                # TODO: why tag = Utils.escape_xml(tag) will cause
                # UnboundLocalError: local variable 'tag' referenced before assignment
                _tag = Utils.escape_xml(tag)
                print(f'<{_tag}>')
                ret = func(*args, **kw)
                print(f'</{_tag}>')
                return ret
            return wrapper
        return decorator

    def _read_variable(self, symbol):
        assert symbol is not None

        self._code_writer.push(
            JackSpecification.VARIABLE_KIND_TO_SEGMENT_MAP[symbol.kind],
            symbol.index)

    def _write_variable(self, symbol):
        assert symbol is not None

        self._code_writer.pop(
            JackSpecification.VARIABLE_KIND_TO_SEGMENT_MAP[symbol.kind],
            symbol.index)

    @_print_ast_as_xml_if_necessary('class')
    def _compile_class(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'class'))

        classname_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
        self._cur_classname = classname_token.string

        self._expect_tokens(Token(TokenType.SYMBOL, '{'))

        self._compile_class_var_dec_if_any()
        self._compile_subroutine_dec_if_any()

        self._expect_tokens(Token(TokenType.SYMBOL, '}'))

    # NOTE: the order of these two decorator matters,
    # we only produce <classVarDec> xxx </classVarDec>, if we are sure the next
    # token is part of classVarDec, i.e., no empty <classVarDec> </classVarDec>
    # is allowd, so _print_ast_as_xml_if_necessary must come after _if_next_token_in.
    @_if_next_token_in([Token(TokenType.KEYWORD, 'static'),
                        Token(TokenType.KEYWORD, 'field')])
    @_print_ast_as_xml_if_necessary('classVarDec')
    def _compile_class_var_dec_if_any(self):
        return self._compile_class_var_dec()

    def _translate_class_var(self, identifier_name, type, kind):
        symbol = self._symbol_table.add(identifier_name, type, kind)

    def _compile_class_var_dec(self):
        kind_token = self._expect_tokens([Token(TokenType.KEYWORD, 'static'),
                                          Token(TokenType.KEYWORD, 'field')])
        type_token = self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
        identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
        self._translate_class_var(identifier_token.string,
                                  type_token.string,
                                  kind_token.string)
        cnt = 1

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
            self._translate_class_var(identifier_token.string,
                                    type_token.string,
                                    kind_token.string)
            cnt += 1

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

        return cnt

    @_if_next_token_in([Token(TokenType.KEYWORD, 'constructor'),
                        Token(TokenType.KEYWORD, 'function'),
                        Token(TokenType.KEYWORD, 'method')])
    @_print_ast_as_xml_if_necessary('subroutineDec')
    def _compile_subroutine_dec_if_any(self):
        return self._compile_subroutine_dec()

    def _get_class_field_amount(self):
        amount = self._symbol_table.symbol_amount(SymbolKind.FIELD)
        return amount

    def _translate_subroutine_head(self, subroutine_name, local_argument_amount,
            kind):
        name = f'{self._cur_classname}.{subroutine_name}'
        self._code_writer.function(name, local_argument_amount)

        if kind == 'constructor':
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT,
                                   self._get_class_field_amount())
            self._code_writer.call('Memory.alloc', 1)
            self._code_writer.pop(VMSpecification.SegmentType.POINTER, 0)
        elif kind == 'method':
            # assign argument 0 to this
            self._code_writer.push(VMSpecification.SegmentType.ARGUMENT, 0)
            self._code_writer.pop(VMSpecification.SegmentType.POINTER, 0)

    def _compile_subroutine_dec(self):

        kind_token = self._expect_tokens(
            [Token(TokenType.KEYWORD, 'constructor'),
            Token(TokenType.KEYWORD, 'function'),
            Token(TokenType.KEYWORD, 'method')])

        self._symbol_table.new_subroutine(is_method=kind_token.string == 'method')

        return_type_token = self._expect_tokens(
                [Token(TokenType.KEYWORD, 'void')] + \
                JackSpecification.TOKENS_THAT_CAN_BE_TYPE)

        name_token = self._expect_tokens(Token(TokenType.IDENTIFIER))

        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_parameter_list_if_any()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        self._compile_subroutine_dec_body(name_token.string, kind_token.string)

        return 1

    @_print_ast_as_xml_if_necessary('subroutineBody')
    def _compile_subroutine_dec_body(self, subroutine_name, kind):
        self._expect_tokens(Token(TokenType.SYMBOL, '{'))
        local_argument_amount = self._compile_var_dec_if_any()
        self._translate_subroutine_head(subroutine_name,
                                        local_argument_amount,
                                        kind=kind)
        self._compile_statements()
        self._expect_tokens(Token(TokenType.SYMBOL, '}'))

    # NOTE: the order of these two decorator matters,
    # even though there is no parameter list,
    # we still have to produce empty tag, namely <parameterList> </parameterList>,
    # so _print_ast_as_xml_if_necessary must come first.
    @_print_ast_as_xml_if_necessary('parameterList')
    @_if_next_token_in(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
    def _compile_parameter_list_if_any(self):
        return self._compile_parameter_list()

    def _compile_parameter_list(self):
        type_token = self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
        identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
        self._symbol_table.add(identifier_token.string,
                               type_token.string,
                               SymbolKind.ARGUMENT)
        cnt = 1

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            type_token = self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
            identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
            self._symbol_table.add(identifier_token.string,
                                type_token.string,
                                SymbolKind.ARGUMENT)
            cnt += 1

        return cnt

    @_if_next_token_in([Token(TokenType.KEYWORD, 'var')])
    @_print_ast_as_xml_if_necessary('varDec')
    def _compile_var_dec_if_any(self):
        return self._compile_var_dec()

    #  def _translate_var_dec(self, symbol):
    #      assert symbol.kind == SymbolKind.VARIABLE
    #
    #      self._code_writer.push(VMSpecification.SegmentType.LOCAL, symbol.index)

    def _compile_var_dec(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'var'))

        type_token = self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)

        identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
        symbol = self._symbol_table.add(identifier_token.string,
                                        type_token.string,
                                        SymbolKind.VARIABLE)
        #  self._translate_var_dec(symbol)
        cnt = 1

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
            symbol = self._symbol_table.add(identifier_token.string,
                                            type_token.string,
                                            SymbolKind.VARIABLE)
            #  self._translate_var_dec(symbol)
            cnt += 1

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

        return cnt

    @_print_ast_as_xml_if_necessary('statements')
    def _compile_statements(self):
        while self._next_token in [Token(TokenType.KEYWORD, 'let'),
                                   Token(TokenType.KEYWORD, 'if'),
                                   Token(TokenType.KEYWORD, 'while'),
                                   Token(TokenType.KEYWORD, 'do'),
                                   Token(TokenType.KEYWORD, 'return')]:

            if self._next_token == Token(TokenType.KEYWORD, 'let'):
                self._compile_let()
            elif self._next_token == Token(TokenType.KEYWORD, 'if'):
                self._compile_if()
            elif self._next_token == Token(TokenType.KEYWORD, 'while'):
                self._compile_while()
            elif self._next_token == Token(TokenType.KEYWORD, 'do'):
                self._compile_do()
            elif self._next_token == Token(TokenType.KEYWORD, 'return'):
                self._compile_return()

    def _translate_subroutine_call(self, class_or_variable_name,
            subroutine_name, argument_amount, drop_return_value=False):
        '''Translate subroutine call class_or_variable_name.subroutine_name(),
        class_or_variable_name can be None.
        '''
        if class_or_variable_name is None:
            clasname = self._cur_classname
        else:
            symbol = self._symbol_table.get(class_or_variable_name)
            if symbol is None:
                clasname = class_or_variable_name
            else:
                clasname = symbol.type

        function_name = f'{clasname}.{subroutine_name}'

        self._code_writer.call(function_name, argument_amount)

        if drop_return_value:
            self._code_writer.pop(VMSpecification.SegmentType.TEMP, 0)

    def _pass_this_if_necessary(self, class_or_variable_name, subroutine_name):
        '''Pass this to the called subroutine if necessary, return True if
        passed acctually, otherwise return False.

        Three possible cases:
            1. X.xxx()
                X is a classname, this will call a function named xxx in class X,
                no need to pass this.
            2. x.xxx()
                x is a variable(can be static, field, argument or local variable
                in subroutine) name, this will call a method named xxx of object x,
                we need to pass this.
            3. xxx()
                xxx is a method in the same class, we need to pass this.
                Note that xxx can not be a function name, since function must be
                called by X.xxx()
        '''
        need = True
        variable = None

        # Only on case 1, we dont pass this, check it.
        if class_or_variable_name is not None:
            # classname is not stored in symbol table
            variable = self._symbol_table.get(class_or_variable_name)
            if variable is None:
                need = False

        if need:
            if variable is None: # case 3
                # call method in same class, just duplicate current this
                self._code_writer.push(VMSpecification.SegmentType.POINTER, 0)
            else: # case 2
                self._read_variable(variable)
                #  self._code_writer.push(
                #      JackSpecification.VARIABLE_KIND_TO_SEGMENT_MAP[variable.kind],
                #      variable.index)

        return need

    def _compile_subroutine_call(self, method_or_class_or_var_name_token,
            is_from_do_statement):
        class_or_variable_name = None
        subroutine_name = method_or_class_or_var_name_token.string

        if self._next_token == Token(TokenType.SYMBOL, '.'):
            self._expect_tokens(Token(TokenType.SYMBOL, '.'))
            subroutine_name_token = self._expect_tokens(Token(TokenType.IDENTIFIER))

            class_or_variable_name = method_or_class_or_var_name_token.string
            subroutine_name = subroutine_name_token.string

        passed_this = self._pass_this_if_necessary(class_or_variable_name,
                subroutine_name)

        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        expression_amount = self._compile_expression_list()
        assert expression_amount >= 0
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))


        argument_amount = expression_amount
        if passed_this:
            argument_amount += 1
        self._translate_subroutine_call(class_or_variable_name,
                                        subroutine_name,
                                        argument_amount,
                                        drop_return_value=is_from_do_statement)

    @_print_ast_as_xml_if_necessary('doStatement')
    def _compile_do(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'do'))

        # this can not be a function name, since all the function must be called
        # as Xxx.xxx(), and all the method must be called directly as xxx() if
        # they are at the same class.
        method_or_class_or_var_name_token = \
                self._expect_tokens(Token(TokenType.IDENTIFIER))

        self._compile_subroutine_call(method_or_class_or_var_name_token,
                                      is_from_do_statement=True)

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

    def _translate_let(self, symbol, is_array_write):
        if is_array_write:
            # now the top of the stack is rhs, the next of the top is the
            # address
            self._code_writer.pop(VMSpecification.SegmentType.TEMP, 0)
            self._code_writer.pop(VMSpecification.SegmentType.POINTER, 1)
            self._code_writer.push(VMSpecification.SegmentType.TEMP, 0)
            self._code_writer.pop(VMSpecification.SegmentType.THAT, 0)
        else:
            self._write_variable(symbol)

    @_print_ast_as_xml_if_necessary('letStatement')
    def _compile_let(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'let'))
        identifier_token = self._expect_tokens(Token(TokenType.IDENTIFIER))
        symbol = self._symbol_table.get(identifier_token.string)

        is_array_write = False
        if self._next_token == Token(TokenType.SYMBOL, '['):
            is_array_write = True
            self._expect_tokens(Token(TokenType.SYMBOL, '['))
            self._compile_expression()
            self._expect_tokens(Token(TokenType.SYMBOL, ']'))

            self._read_variable(symbol)
            self._code_writer.arithmetic(VMSpecification.CommandType.ADD)

        self._expect_tokens(Token(TokenType.SYMBOL, '='))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

        self._translate_let(symbol, is_array_write)

    def _new_label(self, name):
        # We use a unique index to avoid conflict.
        label = f'{name}_{CompileEngine.next_available_label_idx}'
        CompileEngine.next_available_label_idx += 1
        return label

    def _new_label_pair(self, name, start='start', end='end'):
        '''Get a pair of related labels.
        '''
        label = self._new_label(name)
        return f'{label}_{start}', f'{label}_{end}'

    @_print_ast_as_xml_if_necessary('whileStatement')
    def _compile_while(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'while'))
        while_start_label, while_end_label = self._new_label_pair('while')

        self._code_writer.label(while_start_label)

        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        self._code_writer.arithmetic(VMSpecification.CommandType.NOT)
        self._code_writer.if_goto(while_end_label)

        self._expect_tokens(Token(TokenType.SYMBOL, '{'))
        self._compile_statements()
        self._expect_tokens(Token(TokenType.SYMBOL, '}'))

        self._code_writer.goto(while_start_label)

        self._code_writer.label(while_end_label)

    def _translate_return(self, is_void):
        if is_void:
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT, 0)

        self._code_writer.ret()

    @_print_ast_as_xml_if_necessary('returnStatement')
    def _compile_return(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'return'))
        is_void = True
        if self._next_token != Token(TokenType.SYMBOL, ';'):
            self._compile_expression()
            is_void = False
        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

        self._translate_return(is_void)

    @_print_ast_as_xml_if_necessary('ifStatement')
    def _compile_if(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'if'))
        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        false_label, end_label = self._new_label_pair('if',
                                                       start='false')
        self._code_writer.arithmetic(VMSpecification.CommandType.NOT)

        self._code_writer.if_goto(false_label)

        self._expect_tokens(Token(TokenType.SYMBOL, '{'))

        self._compile_statements()

        self._expect_tokens(Token(TokenType.SYMBOL, '}'))
        self._code_writer.goto(end_label)

        self._code_writer.label(false_label)

        if self._next_token == Token(TokenType.KEYWORD, 'else'):
            self._expect_tokens(Token(TokenType.KEYWORD, 'else'))
            self._expect_tokens(Token(TokenType.SYMBOL, '{'))
            self._compile_statements()
            self._expect_tokens(Token(TokenType.SYMBOL, '}'))

        self._code_writer.label(end_label)

    def _translate_binary_operation(self, op):
        '''Translate operation that has two operands.'''
        assert op in '+-*/&|<>='

        OP_MAP_EXCEPT_MUL_DIV = {
            '+': VMSpecification.CommandType.ADD,
            '-': VMSpecification.CommandType.SUB,
            '&': VMSpecification.CommandType.AND,
            '|': VMSpecification.CommandType.OR,
            '<': VMSpecification.CommandType.LT,
            '>': VMSpecification.CommandType.GT,
            '=': VMSpecification.CommandType.EQ,
        }
        if op in OP_MAP_EXCEPT_MUL_DIV:
            self._code_writer.arithmetic(OP_MAP_EXCEPT_MUL_DIV[op])
            return

        # multiply and divide are not supported by VM natively, we have to call
        # the functionality thet OS provides.
        MUL_DIV_MAP = {
            '*': 'Math.multiply',
            '/': 'Math.divide'
        }
        self._code_writer.call(MUL_DIV_MAP[op], 2)

    @_print_ast_as_xml_if_necessary('expression')
    def _compile_expression(self):
        OP_TOKENS = [Token(TokenType.SYMBOL, '+'),
                     Token(TokenType.SYMBOL, '-'),
                     Token(TokenType.SYMBOL, '*'),
                     Token(TokenType.SYMBOL, '/'),
                     Token(TokenType.SYMBOL, '&'),
                     Token(TokenType.SYMBOL, '|'),
                     Token(TokenType.SYMBOL, '<'),
                     Token(TokenType.SYMBOL, '>'),
                     Token(TokenType.SYMBOL, '=')]
        self._compile_term()
        while self._next_token in OP_TOKENS:
            op_token = self._expect_tokens(OP_TOKENS)
            # Right Polish Notation, first evaluate two operands, then the
            # operator itself.
            self._compile_term()
            self._translate_binary_operation(op_token.string)

    def _translate_constant_string(self, string):
        # allocate memory for this string literal.
        self._code_writer.push(VMSpecification.SegmentType.CONSTANT, len(string))
        self._code_writer.call('String.new', 1)

        # now string's this already on stack, so there is no need to push this
        # when the first time to call String.appendChar.
        #
        # what's more, String.appendChar will return this, so no need to push
        # this on the remaining calls.
        for c in string:
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT, ord(c))
            self._code_writer.call('String.appendChar', 2)

    def _translate_constant(self, token):
        assert token in [Token(TokenType.CONST_INTEGER),
                         Token(TokenType.CONST_STRING),
                         Token(TokenType.KEYWORD, 'true'),
                         Token(TokenType.KEYWORD, 'false'),
                         Token(TokenType.KEYWORD, 'null'),
                         Token(TokenType.KEYWORD, 'this'),]

        if token == Token(TokenType.CONST_INTEGER):
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT, token.string)
            return
        if token == Token(TokenType.CONST_STRING):
            self._translate_constant_string(token.string)
            return

        keyword = token.string

        if keyword == 'this':
            self._code_writer.push(VMSpecification.SegmentType.POINTER, 0)
            return

        if keyword in ['null', 'false']:
            # null and false are mapped to 0
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT, 0)
            return

        if keyword == 'true':
            # true are mapped to -1
            self._code_writer.push(VMSpecification.SegmentType.CONSTANT, 1)
            self._code_writer.arithmetic(VMSpecification.CommandType.NEG)

    def _translate_unary_operation(self, op):
        assert op in '-~'

        OP_MAP = {
            '-': VMSpecification.CommandType.NEG,
            '~': VMSpecification.CommandType.NOT,
        }
        self._code_writer.arithmetic(OP_MAP[op])

    def _translate_array_read(self, identifier_name):
        '''Read identifier_name[offset] into stack, note that offset is alread
        on the top of the stack.
        '''
        symbol = self._symbol_table.get(identifier_name)
        self._read_variable(symbol)
        self._code_writer.arithmetic(VMSpecification.CommandType.ADD)
        self._code_writer.pop(VMSpecification.SegmentType.POINTER, 1)
        self._code_writer.push(VMSpecification.SegmentType.THAT, 0)

    @_print_ast_as_xml_if_necessary('term')
    def _compile_term(self):
        if self._next_token in [Token(TokenType.CONST_INTEGER),
                                Token(TokenType.CONST_STRING),
                                Token(TokenType.KEYWORD, 'true'),
                                Token(TokenType.KEYWORD, 'false'),
                                Token(TokenType.KEYWORD, 'null'),
                                Token(TokenType.KEYWORD, 'this'),]:
            # integerConstant, stringConstant, keywordConstant
            constant_token = self._expect_tokens(self._next_token)
            self._translate_constant(constant_token)
        elif self._next_token == Token(TokenType.SYMBOL, '('):
            # '(' expression ')'
            self._expect_tokens(Token(TokenType.SYMBOL, '('))
            self._compile_expression()
            self._expect_tokens(Token(TokenType.SYMBOL, ')'))
        elif self._next_token in [Token(TokenType.SYMBOL, '-'),
                                  Token(TokenType.SYMBOL, '~')]:
            # unaryOp term
            op_token = self._expect_tokens(self._next_token)
            self._compile_term()
            self._translate_unary_operation(op_token.string)
        elif self._next_token == Token(TokenType.IDENTIFIER):
            method_or_class_or_var_name_token = self._expect_tokens(
                    Token(TokenType.IDENTIFIER))
            if self._next_token == Token(TokenType.SYMBOL, '['):
                # varName '[' expression ']'
                self._expect_tokens(Token(TokenType.SYMBOL, '['))
                self._compile_expression()
                self._expect_tokens(Token(TokenType.SYMBOL, ']'))
                self._translate_array_read(method_or_class_or_var_name_token.string)
            elif self._next_token in [Token(TokenType.SYMBOL, '('),
                                      Token(TokenType.SYMBOL, '.')]:
                # subroutineCall
                self._compile_subroutine_call(method_or_class_or_var_name_token,
                                              is_from_do_statement=False)
            else:
                # varName
                symbol = self._symbol_table.get(method_or_class_or_var_name_token.string)
                self._read_variable(symbol)

    @_print_ast_as_xml_if_necessary('expressionList')
    def _compile_expression_list(self):
        '''Compile expression list, the number of expression is reuturned.'''
        if self._next_token == Token(TokenType.SYMBOL, ')'):
            return 0
        self._compile_expression()
        cnt = 1

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            self._compile_expression()
            cnt += 1

        return cnt

class Compiler(object):
    def __init__(self, input_file_path, output_file_path=None,
            print_ast_as_xml=False):
        self._input_file_path = input_file_path
        self._output_file_path = self._set_output_file_path(output_file_path)
        self._tokenizer = Tokenizer(self._input_file_path)
        self._compile_engine = CompileEngine(self._tokenizer,
                                             self._output_file_path,
                                             print_ast_as_xml)

    def _set_output_file_path(self, output_file_path):
        '''Saving output file to current working directory if output_file_path
        is not specified.
        '''
        if output_file_path is None:
            # output_file_path not provided, save to current working directory
            base = os.path.basename(self._input_file_path)
            filename_without_extension = os.path.splitext(base)[0]
            output_file_path = filename_without_extension + '.vm'
        return output_file_path

    def print_tokens(self):
        '''Print tokens to standart output with xml format.'''
        buf = ['<tokens>']
        tokenizer = Tokenizer(self._input_file_path)
        while tokenizer.has_more_tokens():
            tokenizer.advance()
            #  print(f'{tokenizer.token_type():20} ---> {tokenizer._cur_token_string}')
            buf.append(tokenizer.token().to_xml_string())
        buf.append('</tokens>')
        print('\n'.join(buf))

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

def compile_single_file(input_file_path, print_token_as_xml=False,
        print_ast_as_xml=False):
    compiler = Compiler(input_file_path, print_ast_as_xml=print_ast_as_xml)

    if args.print_token_as_xml:
        compiler.print_tokens()
        return

    base = os.path.basename(input_file_path)
    #  print(f"\n//////////////////// {base} start ////////////////////\n")
    compiler._compile_engine._compile_class()
    #  print(f"\n//////////////////// {base} end ////////////////////\n")

def main(args):
    input_path = os.path.abspath(args.input_path)
    if os.path.isdir(input_path):
        input_file_paths = glob.glob(os.path.join(input_path, '*.jack'))
    else:
        input_file_paths = [input_path]

    for input_file_path in input_file_paths:
        compile_single_file(input_file_path)

if __name__ == "__main__":
    configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('input_path', metavar='input-path')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--print-token-as-xml', action='store_true',
            default=False)
    group.add_argument('--print-ast-as-xml', action='store_true',
            default=False)

    args = parser.parse_args()

    main(args)
