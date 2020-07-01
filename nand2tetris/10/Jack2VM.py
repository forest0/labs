#!/usr/bin/env python3

'''Parser of Jack language.

Done:
    1. Tokenizer.
    2. Show ast by xml.

TODO:
    1. how to refactor Tokenizer's DFA?
        - DFA can be described as a table.
    2. lots of Token instances are creaetd, but they are used to judge equality
        most of the time, maybe we should define them as constant or enum at first?
'''

import logging
import argparse
import enum
import functools

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

class CompileEngine(object):

    def __init__(self, tokenizer, output_file_path, print_ast_as_xml=False):
        self._tokenizer = tokenizer
        self._output_file_path = output_file_path

        self._print_ast_as_xml = print_ast_as_xml

        self._cur_token = None
        self._next_token = self._get_next_token_if_any()

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
                while args[0]._next_token in tokens:
                    func(*args, **kw)
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

    @_print_ast_as_xml_if_necessary('class')
    def _compile_class(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'class'))
        self._expect_tokens(Token(TokenType.IDENTIFIER))
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

    def _compile_class_var_dec(self):
        self._expect_tokens([Token(TokenType.KEYWORD, 'static'),
                             Token(TokenType.KEYWORD, 'field')])

        self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)

        self._expect_tokens(Token(TokenType.IDENTIFIER))

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            self._expect_tokens(Token(TokenType.IDENTIFIER))

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

    @_if_next_token_in([Token(TokenType.KEYWORD, 'constructor'),
                        Token(TokenType.KEYWORD, 'function'),
                        Token(TokenType.KEYWORD, 'method')])
    @_print_ast_as_xml_if_necessary('subroutineDec')
    def _compile_subroutine_dec_if_any(self):
        return self._compile_subroutine_dec()

    def _compile_subroutine_dec(self):
        self._expect_tokens([Token(TokenType.KEYWORD, 'constructor'),
                             Token(TokenType.KEYWORD, 'function'),
                             Token(TokenType.KEYWORD, 'method')])

        self._expect_tokens([Token(TokenType.KEYWORD, 'void')] + \
                             JackSpecification.TOKENS_THAT_CAN_BE_TYPE)

        self._expect_tokens(Token(TokenType.IDENTIFIER))

        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_parameter_list_if_any()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        self._compile_subroutine_dec_body()

    @_print_ast_as_xml_if_necessary('subroutineBody')
    def _compile_subroutine_dec_body(self):
        self._expect_tokens(Token(TokenType.SYMBOL, '{'))
        self._compile_var_dec_if_any()
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
        self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
        self._expect_tokens(Token(TokenType.IDENTIFIER))

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)
            self._expect_tokens(Token(TokenType.IDENTIFIER))

    @_if_next_token_in([Token(TokenType.KEYWORD, 'var')])
    @_print_ast_as_xml_if_necessary('varDec')
    def _compile_var_dec_if_any(self):
        return self._compile_var_dec()

    def _compile_var_dec(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'var'))

        self._expect_tokens(JackSpecification.TOKENS_THAT_CAN_BE_TYPE)

        self._expect_tokens(Token(TokenType.IDENTIFIER))

        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            self._expect_tokens(Token(TokenType.IDENTIFIER))

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

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

    @_print_ast_as_xml_if_necessary('doStatement')
    def _compile_do(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'do'))
        self._expect_tokens(Token(TokenType.IDENTIFIER))
        if self._next_token == Token(TokenType.SYMBOL, '.'):
            self._expect_tokens(Token(TokenType.SYMBOL, '.'))
            self._expect_tokens(Token(TokenType.IDENTIFIER))
        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_expression_list()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

    @_print_ast_as_xml_if_necessary('letStatement')
    def _compile_let(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'let'))
        self._expect_tokens(Token(TokenType.IDENTIFIER))

        if self._next_token == Token(TokenType.SYMBOL, '['):
            self._expect_tokens(Token(TokenType.SYMBOL, '['))
            self._compile_expression()
            self._expect_tokens(Token(TokenType.SYMBOL, ']'))

        self._expect_tokens(Token(TokenType.SYMBOL, '='))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

    @_print_ast_as_xml_if_necessary('whileStatement')
    def _compile_while(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'while'))
        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))
        self._expect_tokens(Token(TokenType.SYMBOL, '{'))
        self._compile_statements()
        self._expect_tokens(Token(TokenType.SYMBOL, '}'))

    @_print_ast_as_xml_if_necessary('returnStatement')
    def _compile_return(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'return'))
        if self._next_token != Token(TokenType.SYMBOL, ';'):
            self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ';'))

    @_print_ast_as_xml_if_necessary('ifStatement')
    def _compile_if(self):
        self._expect_tokens(Token(TokenType.KEYWORD, 'if'))
        self._expect_tokens(Token(TokenType.SYMBOL, '('))
        self._compile_expression()
        self._expect_tokens(Token(TokenType.SYMBOL, ')'))

        self._expect_tokens(Token(TokenType.SYMBOL, '{'))
        self._compile_statements()
        self._expect_tokens(Token(TokenType.SYMBOL, '}'))

        if self._next_token == Token(TokenType.KEYWORD, 'else'):
            self._expect_tokens(Token(TokenType.KEYWORD, 'else'))
            self._expect_tokens(Token(TokenType.SYMBOL, '{'))
            self._compile_statements()
            self._expect_tokens(Token(TokenType.SYMBOL, '}'))

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
            self._expect_tokens(OP_TOKENS)
            self._compile_term()

    @_print_ast_as_xml_if_necessary('term')
    def _compile_term(self):
        if self._next_token in [Token(TokenType.CONST_INTEGER),
                                Token(TokenType.CONST_STRING),
                                Token(TokenType.KEYWORD, 'true'),
                                Token(TokenType.KEYWORD, 'false'),
                                Token(TokenType.KEYWORD, 'null'),
                                Token(TokenType.KEYWORD, 'this'),]:
            self._expect_tokens(self._next_token)
        elif self._next_token == Token(TokenType.SYMBOL, '('):
            self._expect_tokens(Token(TokenType.SYMBOL, '('))
            self._compile_expression()
            self._expect_tokens(Token(TokenType.SYMBOL, ')'))
        elif self._next_token in [Token(TokenType.SYMBOL, '-'),
                                  Token(TokenType.SYMBOL, '~')]:
            self._expect_tokens(self._next_token)
            self._compile_term()
        elif self._next_token == Token(TokenType.IDENTIFIER):
            self._expect_tokens(Token(TokenType.IDENTIFIER))
            if self._next_token == Token(TokenType.SYMBOL, '['):
                self._expect_tokens(Token(TokenType.SYMBOL, '['))
                self._compile_expression()
                self._expect_tokens(Token(TokenType.SYMBOL, ']'))
            elif self._next_token == Token(TokenType.SYMBOL, '('):
                self._expect_tokens(Token(TokenType.SYMBOL, '('))
                self._compile_expression_list()
                self._expect_tokens(Token(TokenType.SYMBOL, ')'))
            elif self._next_token == Token(TokenType.SYMBOL, '.'):
                self._expect_tokens(Token(TokenType.SYMBOL, '.'))
                self._expect_tokens(Token(TokenType.IDENTIFIER))
                self._expect_tokens(Token(TokenType.SYMBOL, '('))
                self._compile_expression_list()
                self._expect_tokens(Token(TokenType.SYMBOL, ')'))

    @_print_ast_as_xml_if_necessary('expressionList')
    def _compile_expression_list(self):
        if self._next_token == Token(TokenType.SYMBOL, ')'):
            return
        self._compile_expression()
        while self._next_token == Token(TokenType.SYMBOL, ','):
            self._expect_tokens(Token(TokenType.SYMBOL, ','))
            self._compile_expression()

class Analyzer(object):
    def __init__(self, input_file_path, print_ast_as_xml=False):
        self._input_file_path = input_file_path
        self._tokenizer = Tokenizer(self._input_file_path)
        self._compile_engine = CompileEngine(self._tokenizer, None,
                print_ast_as_xml)

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

def main(args):
    analyzer = Analyzer(args.input_path, args.print_ast_as_xml)

    if args.print_token_as_xml:
        analyzer.print_tokens()
        return

    analyzer._compile_engine._compile_class()

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
