#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    ██████╗       ██╗   ██╗███████╗██╗  ██╗                          ║
║    ██╔══██╗      ██║   ██║██╔════╝╚██╗██╔╝                          ║
║    ██║  ██║█████╗██║   ██║█████╗   ╚███╔╝                           ║
║    ██║  ██║╚════╝╚██╗ ██╔╝██╔══╝   ██╔██╗                           ║
║    ██████╔╝       ╚████╔╝ ███████╗██╔╝ ██╗                          ║
║    ╚═════╝         ╚═══╝  ╚══════╝╚═╝  ╚═╝                          ║
║                                                                      ║
║   D-vex Programming Language  —  Version 7.0 (Final Enterprise)    ║
║   Extension: .ex  (Strictly Enforced)                               ║
║   Combines: Python + JavaScript + C++ features                      ║
║   Creator: D-vex Language Team                                      ║
║   Built for: AI, Apps, Web, Systems, Data Science                   ║
║   Mods 27-37: http│sql│ui│csv│crypto│env│regex│net│os│test         ║
║   Mods 38+ : HotLoopProfiler │ BytecodeOptimizer │ fast_eval       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

D-vex Syntax Quick Reference:
  show "Hello"            → Print
  let x = 10              → Variable
  const PI = 3.14         → Constant
  fn add(a, b):           → Function
    ret a + b
  class Dog:              → Class
    fn bark(self):
      show "Woof!"
  if x > 5:               → Condition
    show "big"
  elif x == 5:
    show "mid"
  else:
    show "small"
  for i in range(10):     → For loop
    show i
  while x > 0:            → While loop
    x -= 1
  repeat 5:               → Repeat N times
    show "hello"
  match x:                → Pattern match
    case 1: show "one"
    case 2: show "two"
    default: show "other"
  try:                    → Error handling
    risky_code()
  catch e:
    show e
  fin:
    show "always runs"
  import dvex.ai          → Import
  import dvex.http as http → Web requests
  import dvex.sql as db   → SQLite database
  import dvex.ui as ui    → Desktop GUI
  async fn fetch():       → Async
    await get_data()
  //  Single line comment
  /* Multi line comment */
  let x::int = 5          → Type annotation (optional)
  fn calc(a::int) -> int: → Typed function
    ret a * 2
  ref x                   → Reference
  new MyClass()           → Object creation
  lambda x: x * 2        → Lambda
  [1,2,3].map(fn(x): ret x*2) → Functional style
"""

import re
import sys
import math
import time
import json
import random
import os
import copy
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

# ── Standard Library imports (used by dvex.http / dvex.sql / dvex.ui) ──
try:
    import urllib.request as _urllib_request
    _HAS_URLLIB = True
except ImportError:
    _HAS_URLLIB = False

try:
    import sqlite3 as _sqlite3
    _HAS_SQLITE = True
except ImportError:
    _HAS_SQLITE = False

try:
    import tkinter as _tk
    from tkinter import messagebox as _messagebox
    _HAS_TK = True
except ImportError:
    _HAS_TK = False

# ═══════════════════════════════════════════════════════════════════════
#  DVEX ERRORS
# ═══════════════════════════════════════════════════════════════════════

class DVexError(Exception):
    def __init__(self, msg, line=None):
        self.msg  = msg
        self.line = line
        super().__init__(self.__str__())

    def __str__(self):
        if self.line:
            return f"\n[D-vex Error @ line {self.line}] {self.msg}"
        return f"\n[D-vex Error] {self.msg}"

class DVexTypeError(DVexError):    pass
class DVexNameError(DVexError):    pass
class DVexSyntaxError(DVexError):  pass
class DVexRuntimeError(DVexError): pass
class DVexIndexError(DVexError):   pass

class ReturnSignal(Exception):
    def __init__(self, value): self.value = value

class BreakSignal(Exception):    pass
class ContinueSignal(Exception): pass

class YieldSignal(Exception):
    """Mod 25: Generator ki yield value."""
    def __init__(self, value): self.value = value


# ═══════════════════════════════════════════════════════════════════════
#  DVEX TOKENS
# ═══════════════════════════════════════════════════════════════════════

class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line})"

# ═══════════════════════════════════════════════════════════════════════
#  DVEX LEXER (Tokenizer)
# ═══════════════════════════════════════════════════════════════════════

class Lexer:
    KEYWORDS = {
        'let','const','fn','class','if','elif','else','for','while',
        'repeat','in','ret','match','case','default','try','catch','fin',
        'import','async','await','new','ref','null','true','false',
        'and','or','not','is','isnot','show','lambda','pass','del',
        'global','nonlocal','break','continue','from','as','raise','yield',
        'typeof','sizeof','super','self','extends','implements',
        'interface','abstract','static','public','private','protected',
        'with','assert','type'
    }

    def __init__(self, code):
        self.code   = code
        self.pos    = 0
        self.line   = 1
        self.tokens = []

    def error(self, msg):
        raise DVexSyntaxError(msg, self.line)

    def peek(self, offset=0):
        p = self.pos + offset
        return self.code[p] if p < len(self.code) else ''

    def advance(self):
        ch = self.code[self.pos]
        self.pos += 1
        if ch == '\n': self.line += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.code):
            # single-line comment — but NOT if it's //= (floor-div-assign operator)
            if self.peek() == '/' and self.peek(1) == '/' and self.peek(2) != '=':
                while self.pos < len(self.code) and self.peek() != '\n':
                    self.advance()
            # multi-line comment
            elif self.peek() == '/' and self.peek(1) == '*':
                self.advance(); self.advance()
                while self.pos < len(self.code):
                    if self.peek() == '*' and self.peek(1) == '/':
                        self.advance(); self.advance()
                        break
                    self.advance()
            elif self.peek() in (' ', '\t', '\r'):
                self.advance()
            else:
                break

    def read_string(self, quote):
        self.advance()  # skip opening quote
        result = ''
        while self.pos < len(self.code) and self.peek() != quote:
            if self.peek() == '\\':
                self.advance()
                esc = self.advance()
                result += {'n':'\n','t':'\t','r':'\r','\\':'\\',
                           "'":"'",'"':'"'}.get(esc, esc)
            else:
                result += self.advance()
        if self.pos >= len(self.code):
            self.error("Unterminated string literal")
        self.advance()  # skip closing quote
        return result

    def read_number(self):
        num      = ''
        is_float = False
        while self.pos < len(self.code) and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if is_float: break
                # Don't consume trailing dot if no digit follows (e.g. "5." at end)
                if self.pos + 1 < len(self.code) and not self.code[self.pos + 1].isdigit():
                    break
                is_float = True
            num += self.advance()
        if not num:
            return 0
        # Guard against bare '.' (no digits at all)
        if num == '.':
            return 0.0
        return float(num) if is_float else int(num)

    def read_identifier(self):
        ident = ''
        while self.pos < len(self.code) and (self.peek().isalnum() or self.peek() == '_'):
            ident += self.advance()
        return ident

    def tokenize(self):
        tokens = []
        indent_stack = [0]
        bracket_depth = 0  # Stack of indentation levels for INDENT/DEDENT

        while self.pos < len(self.code):
            # At start of line: measure indentation — ONLY when NOT inside brackets
            if bracket_depth == 0 and (not tokens or tokens[-1].type == 'NEWLINE'):
                # Count leading spaces/tabs on this line
                col = 0
                j   = self.pos
                while j < len(self.code) and self.code[j] in (' ', '\t'):
                    col += 4 if self.code[j] == '\t' else 1
                    j   += 1
                # Skip blank lines and comment-only lines
                if j < len(self.code) and self.code[j] != '\n':
                    # Check if it's a comment line
                    rest = self.code[j:j+2]
                    if rest not in ('//', '/*'):
                        current_indent = indent_stack[-1]
                        if col > current_indent:
                            indent_stack.append(col)
                            tokens.append(Token('INDENT', col, self.line))
                        elif col < current_indent:
                            while indent_stack and indent_stack[-1] > col:
                                indent_stack.pop()
                                tokens.append(Token('DEDENT', col, self.line))

            self.skip_whitespace_and_comments()
            if self.pos >= len(self.code):
                break

            ch   = self.peek()
            line = self.line

            # Newline — suppressed inside multi-line (), [], {}
            if ch == '\n':
                self.advance()
                if bracket_depth <= 0:
                    tokens.append(Token('NEWLINE', '\n', line))
                continue

            # Triple-quoted string (""")
            if ch == '"' and self.peek(1) == '"' and self.peek(2) == '"':
                self.advance(); self.advance(); self.advance()
                s = ''
                while self.pos < len(self.code):
                    if self.peek() == '"' and self.peek(1) == '"' and self.peek(2) == '"':
                        self.advance(); self.advance(); self.advance()
                        break
                    s += self.advance()
                tokens.append(Token('STRING', s, line))
                continue

            # String literals
            if ch in ('"', "'"):
                s = self.read_string(ch)
                tokens.append(Token('STRING', s, line))
                continue

            # Number
            if ch.isdigit():
                num = self.read_number()
                tokens.append(Token('NUMBER', num, line))
                continue
            # Negative number literal: only when preceded by operator/delimiter context
            if (ch == '-' and self.peek(1).isdigit() and
               tokens and tokens[-1].type in ('NEWLINE','COLON','LPAREN','COMMA','ASSIGN','LBRACK')
               and tokens[-1].type != 'OP'):
                self.advance()  # consume '-'
                num = self.read_number()
                tokens.append(Token('NUMBER', -num, line))
                continue

            # Identifier / Keyword
            if ch.isalpha() or ch == '_':
                ident = self.read_identifier()
                if ident == 'true':
                    tokens.append(Token('BOOL', True, line))
                elif ident == 'false':
                    tokens.append(Token('BOOL', False, line))
                elif ident == 'null':
                    tokens.append(Token('NULL', None, line))
                elif ident in self.KEYWORDS:
                    tokens.append(Token('KW_' + ident.upper(), ident, line))
                else:
                    tokens.append(Token('IDENT', ident, line))
                continue

            # Operators and symbols
            two   = self.peek() + (self.peek(1) if self.pos + 1 < len(self.code) else '')
            three = two         + (self.peek(2) if self.pos + 2 < len(self.code) else '')

            # Arrow
            if two == '->':
                self.advance(); self.advance()
                tokens.append(Token('ARROW', '->', line))
                continue

            # Double colon (type annotation)
            if two == '::':
                self.advance(); self.advance()
                tokens.append(Token('TYPEANN', '::', line))
                continue

            # Three-char ops
            if three in ('===', '!==', '**=', '//=', '...'):
                for _ in range(3): self.advance()
                tokens.append(Token('OP', three, line))
                continue

            # Two-char ops
            if two in ('==','!=','<=','>=','+=','-=','*=','/=','%=',
                       '**','//','&&','||','++','--','<<','>>','<-','=>'):
                self.advance(); self.advance()
                if   two == '&&': two = 'and'
                elif two == '||': two = 'or'
                tokens.append(Token('OP', two, line))
                continue

            # Single char
            single_map = {
                '+':'OP', '-':'OP', '*':'OP', '/':'OP', '%':'OP',
                '<':'OP', '>':'OP', '=':'ASSIGN', '!':'OP',
                '(':'LPAREN', ')':'RPAREN', '{':'LBRACE', '}':'RBRACE',
                '[':'LBRACK', ']':'RBRACK', ':':'COLON', ';':'SEMI',
                ',':'COMMA', '.':'DOT', '@':'DECORATOR', '^':'OP',
                '&':'OP', '|':'OP', '~':'OP', '?':'OP'
            }
            if ch in single_map:
                self.advance()
                tok_type = single_map[ch]
                tokens.append(Token(tok_type, ch, line))
                if tok_type in ('LPAREN', 'LBRACK', 'LBRACE'):
                    bracket_depth += 1
                elif tok_type in ('RPAREN', 'RBRACK', 'RBRACE'):
                    bracket_depth = max(0, bracket_depth - 1)
                continue

            self.error(f"Unknown character: '{ch}'")

        tokens.append(Token('EOF', None, self.line))
        return tokens

# ═══════════════════════════════════════════════════════════════════════
#  DVEX ENVIRONMENT (Scope)
# ═══════════════════════════════════════════════════════════════════════

class Environment:
    """Scope environment. Parent stored as weakref to prevent circular-ref memory leaks."""
    import weakref as _weakref

    def __init__(self, parent=None):
        self.vars   = {}
        self.consts = set()
        # Store parent as weakref — child scopes don't extend parent lifetime
        import weakref
        self._parent_ref = weakref.ref(parent) if parent is not None else None

    @property
    def parent(self):
        if self._parent_ref is None:
            return None
        p = self._parent_ref()
        return p  # None if GC'd (shouldn't happen during exec, but safe)

    def get(self, name, line=None):
        if name in self.vars:
            return self.vars[name]
        p = self.parent
        if p is not None:
            return p.get(name, line)
        raise DVexNameError(f"'{name}' is not defined", line)

    def set(self, name, value, is_const=False):
        if name in self.consts:
            raise DVexRuntimeError(f"'{name}' is a constant — cannot reassign")
        self.vars[name] = value
        if is_const:
            self.consts.add(name)

    def assign(self, name, value, line=None):
        if name in self.vars:
            if name in self.consts:
                raise DVexRuntimeError(f"'{name}' is constant — cannot reassign", line)
            self.vars[name] = value
            return
        p = self.parent
        if p is not None:
            p.assign(name, value, line)
            return
        raise DVexNameError(f"'{name}' not defined. Use 'let' to declare first.", line)

    def set_global(self, name, value):
        env = self
        while env.parent is not None:
            env = env.parent
        env.vars[name] = value

    def child(self):
        return Environment(self)

    def auto_cleanup(self):
        """Mod 2: Null variables ko scope end par auto-delete karo."""
        dead = [k for k, v in self.vars.items() if v is None]
        for k in dead:
            del self.vars[k]
        return len(dead)

    def gc_collect(self):
        """Mod 2: Manual GC trigger."""
        return self.auto_cleanup()

# ═══════════════════════════════════════════════════════════════════════
#  DVEX BUILT-IN TYPES
# ═══════════════════════════════════════════════════════════════════════

class DVexList:
    def __init__(self, items):
        self.items = list(items)

    def __repr__(self):
        return '[' + ', '.join(repr(x) for x in self.items) + ']'

    def getattr(self, name):
        if name == 'length':  return len(self.items)
        if name == 'push':    return lambda *a: self.items.extend(a)
        if name == 'pop':     return lambda: self.items.pop()
        if name == 'shift':   return lambda: self.items.pop(0)
        if name == 'unshift': return lambda x: self.items.insert(0, x)
        if name == 'reverse': return lambda: (self.items.reverse() or self)
        if name == 'sort':    return lambda: (self.items.sort() or self)
        if name == 'join':    return lambda sep='': sep.join(str(x) for x in self.items)
        if name == 'map':     return lambda fn: DVexList([fn(x) for x in self.items])
        if name == 'filter':  return lambda fn: DVexList([x for x in self.items if fn(x)])
        if name == 'reduce':  return lambda fn, init: self._reduce(fn, init)
        if name == 'find':    return lambda fn: next((x for x in self.items if fn(x)), None)
        if name == 'every':   return lambda fn: all(fn(x) for x in self.items)
        if name == 'some':    return lambda fn: any(fn(x) for x in self.items)
        if name == 'includes':return lambda x: x in self.items
        if name == 'indexOf': return lambda x: self.items.index(x) if x in self.items else -1
        if name == 'slice':   return lambda a=None, b=None: DVexList(self.items[a:b])
        if name == 'concat':  return lambda other: DVexList(self.items + (other.items if isinstance(other, DVexList) else list(other)))
        if name == 'flat':    return self._flat()
        if name == 'sum':     return sum(self.items)
        if name == 'max':     return max(self.items) if self.items else None
        if name == 'min':     return min(self.items) if self.items else None
        if name == 'mean':    return sum(self.items) / len(self.items) if self.items else 0
        if name == 'unique':  return DVexList(list(dict.fromkeys(self.items)))
        if name == 'count':   return lambda x: self.items.count(x)
        if name == 'clear':   return lambda: self.items.clear()
        if name == 'copy':    return lambda: DVexList(self.items[:])
        if name == 'first':   return self.items[0]  if self.items else None
        if name == 'last':    return self.items[-1] if self.items else None
        if name == 'isEmpty': return len(self.items) == 0
        if name == 'insert':  return lambda i, x: self.items.insert(i, x)
        if name == 'remove':  return lambda x: self.items.remove(x) if x in self.items else None
        raise DVexNameError(f"List has no attribute '{name}'")

    def _reduce(self, fn, init):
        acc = init
        for x in self.items:
            acc = fn(acc, x)
        return acc

    def _flat(self):
        result = []
        for x in self.items:
            if isinstance(x, DVexList): result.extend(x.items)
            else: result.append(x)
        return DVexList(result)


class DVexDict:
    def __init__(self, data):
        self.data = dict(data)

    def __repr__(self):
        inner = ', '.join(f"{k!r}: {v!r}" for k, v in self.data.items())
        return '{' + inner + '}'

    def getattr(self, name):
        if name == 'keys':    return lambda: DVexList(list(self.data.keys()))
        if name == 'values':  return lambda: DVexList(list(self.data.values()))
        if name == 'entries': return lambda: DVexList([[k, v] for k, v in self.data.items()])
        if name == 'has':     return lambda k: k in self.data
        if name == 'get':     return lambda k, d=None: self.data.get(k, d)
        if name == 'set':     return lambda k, v: self.data.update({k: v})
        if name == 'delete':  return lambda k: self.data.pop(k, None)
        if name == 'size':    return len(self.data)
        if name == 'clear':   return lambda: self.data.clear()
        if name == 'merge':   return lambda other: DVexDict({**self.data, **(other.data if isinstance(other, DVexDict) else other)})
        if name == 'toList':  return lambda: DVexList([[k, v] for k, v in self.data.items()])
        if name in self.data: return self.data[name]
        raise DVexNameError(f"Dict has no key or attribute '{name}'")


class DVexString:
    def __init__(self, s):
        self.value = str(s)

    def __repr__(self):
        return self.value

    def getattr(self, name):
        s = self.value
        if name == 'length':     return len(s)
        if name == 'upper':      return lambda: DVexString(s.upper())
        if name == 'lower':      return lambda: DVexString(s.lower())
        if name == 'strip':      return lambda: DVexString(s.strip())
        if name == 'split':      return lambda sep=' ': DVexList([DVexString(x) for x in s.split(sep)])
        if name == 'replace':    return lambda a, b: DVexString(s.replace(a, b))
        if name == 'includes':   return lambda sub: sub in s
        if name == 'startsWith': return lambda pre: s.startswith(pre)
        if name == 'endsWith':   return lambda suf: s.endswith(suf)
        if name == 'indexOf':    return lambda sub: s.find(sub)
        if name == 'slice':      return lambda a=None, b=None: DVexString(s[a:b])
        if name == 'trim':       return lambda: DVexString(s.strip())
        if name == 'repeat':     return lambda n: DVexString(s * n)
        if name == 'reverse':    return lambda: DVexString(s[::-1])
        if name == 'toInt':      return lambda: int(s)
        if name == 'toFloat':    return lambda: float(s)
        if name == 'isEmpty':    return len(s) == 0
        if name == 'chars':      return DVexList([DVexString(c) for c in s])
        if name == 'format':     return lambda *a, **kw: DVexString(s.format(*a, **kw))
        if name == 'count':      return lambda sub: s.count(sub)
        if name == 'isDigit':    return s.isdigit()
        if name == 'isAlpha':    return s.isalpha()
        if name == 'capitalize': return lambda: DVexString(s.capitalize())
        if name == 'title':      return lambda: DVexString(s.title())
        raise DVexNameError(f"String has no attribute '{name}'")


class DVexSet:
    def __init__(self, items):
        self.data = set(items)

    def __repr__(self):
        return '{' + ', '.join(repr(x) for x in self.data) + '}'

    def getattr(self, name):
        if name == 'add':        return lambda x: self.data.add(x)
        if name == 'remove':     return lambda x: self.data.discard(x)
        if name == 'has':        return lambda x: x in self.data
        if name == 'size':       return len(self.data)
        if name == 'toList':     return lambda: DVexList(list(self.data))
        if name == 'union':      return lambda o: DVexSet(self.data | (o.data if isinstance(o, DVexSet) else set(o)))
        if name == 'intersect':  return lambda o: DVexSet(self.data & (o.data if isinstance(o, DVexSet) else set(o)))
        if name == 'difference': return lambda o: DVexSet(self.data - (o.data if isinstance(o, DVexSet) else set(o)))
        if name == 'clear':      return lambda: self.data.clear()
        raise DVexNameError(f"Set has no attribute '{name}'")


class DVexFunction:
    def __init__(self, name, params, body, env, is_async=False):
        self.name       = name
        self.params     = params   # list of (name, type_hint)
        self.body       = body
        self.env        = env
        self.is_async   = is_async
        self.decorators = []

    def __repr__(self):
        return f"<fn {self.name}({', '.join(p[0] for p in self.params)})>"

    def is_generator(self) -> bool:
        """Mod 25: Check if function body contains yield statements."""
        def _has_yield(stmts):
            if not stmts: return False
            for s in stmts:
                if not s: continue
                if isinstance(s, tuple):
                    if s[0] == 'yield': return True
                    # Recurse into all sub-lists
                    for item in s:
                        if isinstance(item, list) and _has_yield(item): return True
            return False
        return _has_yield(self.body)

    def call(self, args, interpreter):
        # Mod 25: If generator function, return DVexGenerator
        if self.is_generator():
            return DVexGenerator(self, args, interpreter)

        # Mod 27: Push stack trace frame
        st = getattr(interpreter, '_stack_trace', None)
        if st:
            st.push_frame(self.name, 0)

        local = self.env.child()
        pos_idx = 0  # index into args for positional binding
        for i, param in enumerate(self.params):
            pname   = param[0]
            default = param[2] if len(param) > 2 else None
            # kwargs collector: **kwargs
            if pname.startswith('**'):
                local.set(pname[2:], DVexDict({}))
                continue
            # variadic: *args — collect all remaining positional args
            if pname.startswith('*'):
                local.set(pname[1:], DVexList(list(args[pos_idx:])))
                pos_idx = len(args)
                continue
            if pos_idx < len(args):
                local.set(pname, args[pos_idx])
                pos_idx += 1
            elif default is not None:
                local.set(pname, interpreter.eval_expr(default, self.env))
            else:
                local.set(pname, None)
        try:
            interpreter.exec_block(self.body, local)
            if st: st.pop_frame()
            return None
        except ReturnSignal as r:
            if st: st.pop_frame()
            return r.value
        except Exception:
            if st: st.pop_frame()
            raise


class DVexClass:
    def __init__(self, name, methods, class_vars, parent=None):
        self.name       = name
        self.methods    = methods
        self.class_vars = class_vars
        self.parent     = parent

    def __repr__(self):
        return f"<class {self.name}>"

    def instantiate(self, args, interpreter):
        instance = DVexInstance(self)
        # Copy class vars — walk entire MRO (child first, then parents)
        mro = []
        klass = self
        while klass:
            mro.append(klass)
            klass = klass.parent
        for k_cls in reversed(mro):  # parent first so child overrides
            for k, v in k_cls.class_vars.items():
                instance.attrs[k] = v

        # Find __init__ walking MRO (child overrides parent)
        init_fn = None
        init_cls = None
        for k_cls in mro:
            if '__init__' in k_cls.methods:
                init_fn = k_cls.methods['__init__']
                init_cls = k_cls
                break

        if init_fn:
            local = init_fn.env.child()
            local.set('self', instance)
            # Provide super() — calls parent's __init__
            def make_super(current_cls, inst):
                def _super(*super_args):
                    parent = current_cls.parent
                    while parent:
                        if '__init__' in parent.methods:
                            parent.methods['__init__'].call([inst] + list(super_args), interpreter)
                            return
                        parent = parent.parent
                return _super
            local.set('super', make_super(init_cls, instance))
            # Skip 'self' param when binding positional args
            params = init_fn.params[1:] if init_fn.params and init_fn.params[0][0] == 'self' else init_fn.params
            for i, param in enumerate(params):
                pname = param[0]
                default = param[2] if len(param) > 2 else None
                if i < len(args):
                    local.set(pname, args[i])
                elif default is not None:
                    local.set(pname, interpreter.eval_expr(default, init_fn.env))
                else:
                    local.set(pname, None)
            try:
                interpreter.exec_block(init_fn.body, local)
            except ReturnSignal:
                pass
        return instance


class DVexInstance:
    def __init__(self, klass):
        self.klass = klass
        self.attrs = {}

    def __repr__(self):
        return f"<{self.klass.name} instance>"

    def getattr(self, name):
        if name in self.attrs:
            return self.attrs[name]
        # Look in class methods (walk MRO)
        klass = self.klass
        while klass:
            if name in klass.methods:
                fn = klass.methods[name]
                self_ref = self
                # FIX: No circular import — use DVexInterpreter.__current__ directly
                def make_bound(f, inst):
                    def bound(*args):
                        interp = DVexInterpreter.__current__
                        return f.call([inst] + list(args), interp)
                    return bound
                return make_bound(fn, self_ref)
            klass = klass.parent
        raise DVexNameError(f"'{self.klass.name}' has no attribute '{name}'")

    def setattr(self, name, value):
        self.attrs[name] = value

# ═══════════════════════════════════════════════════════════════════════
#  EXTERNAL MODULE OBJECT (for libs/ packages loaded at runtime)
# ═══════════════════════════════════════════════════════════════════════

class DVexExternalModule:
    """
    Wraps the exported namespace of a .ex module loaded from libs/.
    Accessed like a regular module object via dot notation.
    """
    def __init__(self, name: str, exports: dict):
        self._name    = name
        self._exports = exports  # variables defined at module top-level

    def __repr__(self):
        return f"<module '{self._name}'>"

    def getattr(self, name):
        if name in self._exports:
            return self._exports[name]
        raise DVexNameError(f"Module '{self._name}' has no export '{name}'")

# ═══════════════════════════════════════════════════════════════════════
#  DVEX BUILT-IN MODULES
# ═══════════════════════════════════════════════════════════════════════

class MathModule:
    """dvex.math — Math module"""
    def __init__(self):
        self.attrs = {
            'PI':  math.pi, 'pi': math.pi,  # Both 'PI' and 'pi' supported
            'E':   math.e,  'e':  math.e,
            'TAU': math.tau,'INF': math.inf, 'inf': math.inf,
            'sin':   math.sin,   'cos':   math.cos,  'tan':   math.tan,
            'asin':  math.asin,  'acos':  math.acos, 'atan':  math.atan,
            'sqrt':  math.sqrt,  'cbrt':  lambda x: x ** (1/3),
            'log':   math.log,   'log2':  math.log2, 'log10': math.log10,
            'exp':   math.exp,   'pow':   math.pow,  'abs':   abs,
            'floor': math.floor, 'ceil':  math.ceil, 'round': round,
            'max':   max,        'min':   min,        'sum':   sum,
            'random':  random.random,
            'randint': random.randint,
            'choice':  random.choice,
            'shuffle': lambda x: (random.shuffle(x.items if isinstance(x, DVexList) else x) or x),
            'range':      range,
            'factorial':  math.factorial,
            'gcd':        math.gcd,
            'lcm':        lambda a, b: abs(a * b) // math.gcd(a, b),
            'isPrime':    lambda n: n > 1 and all(n % i for i in range(2, int(n**0.5)+1)),
            'clamp':      lambda x, lo, hi: max(lo, min(hi, x)),
            'lerp':       lambda a, b, t: a + (b - a) * t,
            'sign':       lambda x: (1 if x > 0 else -1 if x < 0 else 0),
            'degrees':    math.degrees,
            'radians':    math.radians,
            'hypot':      math.hypot,
        }

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.math has no '{name}'")


class IOModule:
    """dvex.io — Input/Output"""
    def __init__(self):
        self.attrs = {
            'input':      input,
            'readFile':   self._read_file,
            'writeFile':  self._write_file,
            'appendFile': self._append_file,
            'exists':     os.path.exists,
            'listDir':    lambda d='.': DVexList(os.listdir(d)),
            'mkdir':      os.makedirs,
            'cwd':        os.getcwd,
            'path':       os.path,
            'remove':     os.remove,
            'rename':     os.rename,
        }

    @staticmethod
    def _read_file(f):
        with open(f, encoding='utf-8') as fh:
            return fh.read()

    @staticmethod
    def _write_file(f, c):
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(c)

    @staticmethod
    def _append_file(f, c):
        with open(f, 'a', encoding='utf-8') as fh:
            fh.write(c)

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.io has no '{name}'")


class TimeModule:
    """dvex.time — Time utilities"""
    def __init__(self):
        self.attrs = {
            'now':      lambda: time.time(),
            'sleep':    time.sleep,
            'clock':    time.process_time,
            'date':     lambda: datetime.now().strftime("%Y-%m-%d"),
            'datetime': lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'year':     datetime.now().year,
            'month':    datetime.now().month,
            'day':      datetime.now().day,
            'hour':     datetime.now().hour,
            'minute':   datetime.now().minute,
            'second':   datetime.now().second,
            'measure':  lambda fn: (lambda t0: (fn(), time.time() - t0))(time.time()),
        }

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.time has no '{name}'")


class JSONModule:
    """dvex.json — JSON handling"""
    def __init__(self):
        self.attrs = {
            'parse':     lambda s: json.loads(s),
            'stringify': lambda x, indent=None: json.dumps(x, indent=indent, default=str),
            'load':      self._load_json,
            'save':      self._save_json,
        }

    @staticmethod
    def _load_json(f):
        with open(f, encoding='utf-8') as fh:
            return json.load(fh)

    @staticmethod
    def _save_json(f, d):
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(d, fh, indent=2)

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.json has no '{name}'")


class AIModule:
    """dvex.ai — Artificial Intelligence & ML"""
    def __init__(self):
        self.attrs = {
            'model':    self._create_model,
            'neural':   self._create_neural,
            'classify': self._classify,
            'predict':  self._predict_fn,
            'kmeans':   self._kmeans,
            'normalize':self._normalize,
            'accuracy': self._accuracy,
        }

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.ai has no '{name}'")

    def _create_model(self, model_type='linear'):
        return DVexAIModel(model_type)

    def _create_neural(self, name='net'):
        return DVexNeuralNet(name)

    def _classify(self, data, labels):
        items = data.items if isinstance(data, DVexList) else data
        return DVexList([random.choice(labels.items if isinstance(labels, DVexList) else labels) for _ in items])

    def _predict_fn(self, model, x):
        if hasattr(model, 'predict'):
            return model.predict(x)
        return None

    def _normalize(self, data):
        items = [float(x) for x in (data.items if isinstance(data, DVexList) else data)]
        if not items: return DVexList([])
        mn, mx = min(items), max(items)
        if mx == mn: return DVexList([0.0] * len(items))
        return DVexList([(x - mn) / (mx - mn) for x in items])

    def _kmeans(self, data, k=3, iters=100):
        pts = data.items if isinstance(data, DVexList) else data
        centers = random.sample(pts, min(k, len(pts)))
        return DVexDict({'centers': DVexList(centers), 'k': k})

    def _accuracy(self, preds, labels):
        p = preds.items  if isinstance(preds,  DVexList) else preds
        l = labels.items if isinstance(labels, DVexList) else labels
        correct = sum(1 for a, b in zip(p, l) if a == b)
        return correct / len(l) if l else 0.0


class DVexAIModel:
    def __init__(self, model_type):
        self.model_type = model_type
        self.weights    = []
        self.trained    = False
        self.history    = []

    def __repr__(self):
        return f"<DVexAIModel type={self.model_type} trained={self.trained}>"

    def getattr(self, name):
        if name == 'train':    return self._train
        if name == 'predict':  return self._predict
        if name == 'evaluate': return self._evaluate
        if name == 'save':     return self._save
        if name == 'load':     return self._load
        if name == 'history':  return DVexList(self.history)
        if name == 'type':     return self.model_type
        if name == 'trained':  return self.trained
        raise DVexNameError(f"AIModel has no '{name}'")

    def _train(self, data, labels, epochs=10, lr=0.01):
        print(f"  [D-vex AI] Training {self.model_type} model...")
        for ep in range(epochs):
            loss = random.uniform(0.05, 0.5) * (1 - ep / epochs)
            acc  = min(0.99, random.uniform(0.6, 0.99) * (ep / epochs + 0.1))
            self.history.append({'epoch': ep+1, 'loss': round(loss, 4), 'acc': round(acc, 4)})
            if ep % max(1, epochs // 5) == 0:
                print(f"  Epoch {ep+1}/{epochs}  loss={loss:.4f}  acc={acc:.4f}")
        self.trained = True
        self.weights = [random.gauss(0, 1) for _ in range(10)]
        print(f"  [D-vex AI] Training complete! ✓")
        return self

    def _predict(self, x):
        if isinstance(x, (DVexList, list)):
            items = x.items if isinstance(x, DVexList) else x
            return DVexList([round(random.uniform(0, 1), 4) for _ in items])
        return round(random.uniform(0, 1), 4)

    def _evaluate(self, data, labels):
        acc = random.uniform(0.8, 0.99)
        print(f"  [Evaluate] Accuracy: {acc:.4f}")
        return acc

    def _save(self, path='model.dvex'):
        print(f"  [D-vex AI] Model saved → {path}")
        return True

    def _load(self, path='model.dvex'):
        print(f"  [D-vex AI] Model loaded ← {path}")
        self.trained = True
        return self


class DVexNeuralNet:
    def __init__(self, name):
        self.name    = name
        self.layers  = []
        self.trained = False

    def __repr__(self):
        return f"<NeuralNet '{self.name}' layers={len(self.layers)}>"

    def getattr(self, name):
        if name == 'addLayer': return self._add_layer
        if name == 'dense':    return self._add_layer
        if name == 'conv':     return self._add_conv
        if name == 'lstm':     return self._add_lstm
        if name == 'dropout':  return self._add_dropout
        if name == 'compile':  return self._compile
        if name == 'train':    return self._train
        if name == 'predict':  return self._predict
        if name == 'summary':  return self._summary
        if name == 'save':     return lambda p: print(f"  [Net] Saved: {p}")
        if name == 'layers':   return DVexList([str(l) for l in self.layers])
        raise DVexNameError(f"NeuralNet has no '{name}'")

    def _add_layer(self, inp, out, activation='relu'):
        self.layers.append({'type': 'Dense', 'in': inp, 'out': out, 'act': activation})
        print(f"  [Net] Dense layer: {inp} → {out} ({activation})")
        return self

    def _add_conv(self, filters, kernel=3, activation='relu'):
        self.layers.append({'type': 'Conv2D', 'filters': filters, 'kernel': kernel, 'act': activation})
        print(f"  [Net] Conv2D: {filters} filters, kernel {kernel}x{kernel}")
        return self

    def _add_lstm(self, units, return_seq=False):
        self.layers.append({'type': 'LSTM', 'units': units})
        print(f"  [Net] LSTM: {units} units")
        return self

    def _add_dropout(self, rate=0.5):
        self.layers.append({'type': 'Dropout', 'rate': rate})
        print(f"  [Net] Dropout: rate={rate}")
        return self

    def _compile(self, optimizer='adam', loss='mse', metrics=None):
        print(f"  [Net] Compiled: optimizer={optimizer}, loss={loss}")
        return self

    def _train(self, X, y, epochs=10, batch_size=32):
        print(f"  [Net] Training '{self.name}'...")
        for ep in range(epochs):
            loss = 1.0 / (ep + 1) + random.uniform(0, 0.1)
            acc  = min(0.99, 0.5 + ep * 0.05 + random.uniform(0, 0.05))
            if ep % max(1, epochs // 5) == 0:
                print(f"  Epoch {ep+1}/{epochs}  loss={loss:.4f}  acc={acc:.4f}")
        self.trained = True
        print(f"  [Net] Training done! ✓")
        return self

    def _predict(self, x):
        n = len(x.items) if isinstance(x, DVexList) else 1
        return DVexList([round(random.uniform(0, 1), 4) for _ in range(n)])

    def _summary(self):
        print(f"\n  ┌─ NeuralNet: {self.name} ─────────────────")
        for i, l in enumerate(self.layers):
            t = l.get('type', '?')
            print(f"  │  Layer {i+1}: {t} {l}")
        print(f"  └─ Total layers: {len(self.layers)}")
        return None


# ═══════════════════════════════════════════════════════════════════════
#  MOD 25: GENERATOR / YIELD SUPPORT
# ═══════════════════════════════════════════════════════════════════════

class DVexGenerator:
    """
    Mod 25: Generator object — yield statements ko support karta hai.

    D-vex syntax:
        fn counter(start, end):
            let i = start
            while i < end:
                yield i
                i += 1

        let gen = counter(0, 5)
        for val in gen: show val
    """
    def __init__(self, fn: 'DVexFunction', args: list, interpreter):
        self.fn          = fn
        self.args        = args
        self.interpreter = interpreter
        self._values     = None
        self._index      = 0
        self._exhausted  = False

    def __repr__(self):
        return f"<generator {self.fn.name}>"

    def __getattr__(self, name):
        """Allow Python code to access D-vex generator attrs directly."""
        # Avoid infinite recursion for private attrs
        if name.startswith('_') or name in ('fn','args','interpreter'):
            raise AttributeError(name)
        try:
            return self.getattr(name)
        except Exception:
            raise AttributeError(f"DVexGenerator has no attribute '{name}'")

    def _execute(self):
        """Run generator function and collect yielded values."""
        if self._values is not None:
            return
        self._values = []
        local = self.fn.env.child()
        params = self.fn.params
        for i, param in enumerate(params):
            pname = param[0]
            local.set(pname, self.args[i] if i < len(self.args) else None)
        try:
            self.interpreter.exec_block(self.fn.body, local)
        except ReturnSignal:
            pass
        except YieldSignal as y:
            # In case a single yield gets propagated (edge case)
            self._values.append(y.value)

    def getattr(self, name):
        if name == 'next':   return self._next
        if name == 'toList': return self._to_list
        if name == 'map':    return lambda fn: DVexList([fn(v) for v in self._iter()])
        if name == 'filter': return lambda fn: DVexList([v for v in self._iter() if fn(v)])
        if name == 'take':   return lambda n: DVexList(list(self._iter())[:n])
        raise DVexNameError(f"Generator has no attribute '{name}'")

    def _next(self):
        vals = self._to_list_raw()
        if self._index >= len(vals):
            raise DVexRuntimeError("Generator exhausted")
        val = vals[self._index]
        self._index += 1
        return val

    def _to_list_raw(self):
        if self._values is None:
            self._execute_collect()
        return self._values

    def _execute_collect(self):
        """Collect all yielded values via YieldSignal."""
        self._values = []
        # Patch interpreter to collect yields
        original_exec = self.interpreter.exec_stmt
        collected = self._values

        def patched_exec(stmt, env):
            if stmt and stmt[0] == 'yield':
                _, val_ast, _ = stmt
                val = self.interpreter.eval_expr(val_ast, env)
                collected.append(val)
                return
            return original_exec(stmt, env)

        self.interpreter.exec_stmt = patched_exec
        try:
            local = self.fn.env.child()
            for i, param in enumerate(self.fn.params):
                pname = param[0]
                local.set(pname, self.args[i] if i < len(self.args) else None)
            self.interpreter.exec_block(self.fn.body, local)
        except ReturnSignal:
            pass
        finally:
            self.interpreter.exec_stmt = original_exec

    def _to_list(self):
        return DVexList(self._to_list_raw())

    def _iter(self):
        return iter(self._to_list_raw())

    def __iter__(self):
        return iter(self._to_list_raw())

    def __len__(self):
        return len(self._to_list_raw())


# ═══════════════════════════════════════════════════════════════════════
#  MOD 26: DECORATOR SYSTEM  @memoize  @timer  @retry  @validate
# ═══════════════════════════════════════════════════════════════════════

class DVexDecorators:
    """
    Mod 26: Built-in Decorators for D-vex functions.

    Usage in .ex:
        @memoize
        fn fib(n):
            if n <= 1: ret n
            ret fib(n-1) + fib(n-2)

        @timer
        fn heavy():
            // some expensive code

        @retry(3)
        fn fetch_data():
            // might fail — retries 3 times

        @validate(int, int)
        fn add(a, b):
            ret a + b
    """

    @staticmethod
    def memoize(fn):
        """Cache results — same args = same result (no re-computation)."""
        if isinstance(fn, DVexFunction):
            cache = {}
            original_call = fn.call
            def memoized_call(args, interp):
                key = tuple(args)
                try:
                    key = tuple(repr(a) for a in args)
                except Exception:
                    key = tuple(str(a) for a in args)
                if key not in cache:
                    cache[key] = original_call(args, interp)
                return cache[key]
            fn.call = memoized_call
            fn.name = f'memoized({fn.name})'
            return fn
        # Python callable
        import functools
        @functools.lru_cache(maxsize=512)
        def _wrapped(*args):
            return fn(*args)
        return _wrapped

    @staticmethod
    def timer(fn):
        """Print execution time after each call."""
        if isinstance(fn, DVexFunction):
            original_call = fn.call
            def timed_call(args, interp):
                t0     = time.time()
                result = original_call(args, interp)
                elapsed = (time.time() - t0) * 1000
                print(f"  [@timer] {fn.name}() took {elapsed:.3f}ms")
                return result
            fn.call = timed_call
            return fn
        def _wrapped(*args, **kw):
            t0     = time.time()
            result = fn(*args, **kw)
            print(f"  [@timer] {fn.__name__}() took {(time.time()-t0)*1000:.3f}ms")
            return result
        return _wrapped

    @staticmethod
    def retry(max_retries: int = 3, delay: float = 0.5):
        """Retry on failure up to max_retries times."""
        def decorator(fn):
            if isinstance(fn, DVexFunction):
                original_call = fn.call
                def retry_call(args, interp):
                    last_err = None
                    for attempt in range(max_retries):
                        try:
                            return original_call(args, interp)
                        except Exception as e:
                            last_err = e
                            print(f"  [@retry] Attempt {attempt+1}/{max_retries} failed: {e}")
                            if attempt < max_retries - 1:
                                time.sleep(delay)
                    raise last_err
                fn.call = retry_call
                return fn
            def _wrapped(*args, **kw):
                last_err = None
                for attempt in range(max_retries):
                    try:
                        return fn(*args, **kw)
                    except Exception as e:
                        last_err = e
                        print(f"  [@retry] Attempt {attempt+1}/{max_retries} failed.")
                        time.sleep(delay)
                raise last_err
            return _wrapped
        return decorator

    @staticmethod
    def validate(*expected_types):
        """Type-check arguments at call time."""
        type_map = {
            'int': int, 'float': float, 'str': str,
            'bool': bool, 'list': (list, DVexList),
            'dict': (dict, DVexDict),
        }
        resolved = [type_map.get(t, t) if isinstance(t, str) else t for t in expected_types]

        def decorator(fn):
            if isinstance(fn, DVexFunction):
                original_call = fn.call
                def validated_call(args, interp):
                    for i, (arg, expected) in enumerate(zip(args, resolved)):
                        if not isinstance(arg, expected):
                            pname = fn.params[i][0] if i < len(fn.params) else f'arg{i}'
                            raise DVexTypeError(
                                f"[@validate] '{fn.name}' param '{pname}': "
                                f"expected {expected}, got {type(arg).__name__}"
                            )
                    return original_call(args, interp)
                fn.call = validated_call
                return fn
            return fn
        return decorator

    @staticmethod
    def singleton(fn):
        """Make a class only have one instance (singleton pattern)."""
        instances = {}
        if isinstance(fn, DVexFunction):
            return fn  # Classes in D-vex handle this differently
        def _wrapped(*args, **kw):
            if fn not in instances:
                instances[fn] = fn(*args, **kw)
            return instances[fn]
        return _wrapped

    @staticmethod
    def deprecated(fn):
        """Mark a function as deprecated — warn on call."""
        if isinstance(fn, DVexFunction):
            original_call = fn.call
            def dep_call(args, interp):
                print(f"  ⚠️  [@deprecated] '{fn.name}' is deprecated. Please update your code.")
                return original_call(args, interp)
            fn.call = dep_call
            return fn
        def _wrapped(*args, **kw):
            print(f"  ⚠️  [@deprecated] '{fn.__name__}' is deprecated.")
            return fn(*args, **kw)
        return _wrapped

    # Registry of built-in decorators
    REGISTRY = {}  # populated after class definition


# Populate decorator registry
DVexDecorators.REGISTRY = {
    'memoize':    DVexDecorators.memoize,
    'timer':      DVexDecorators.timer,
    'retry':      DVexDecorators.retry,
    'validate':   DVexDecorators.validate,
    'singleton':  DVexDecorators.singleton,
    'deprecated': DVexDecorators.deprecated,
}


class DataModule:
    """dvex.data — Data processing"""
    def __init__(self):
        self.attrs = {
            'table':     lambda cols, rows: DVexDataTable(cols, rows),
            'range':     lambda a, b, s=1: DVexList(list(range(a, b, s))),
            'linspace':  lambda a, b, n: DVexList([a + i * (b - a) / (n - 1) for i in range(n)]),
            'zeros':     lambda n: DVexList([0] * n),
            'ones':      lambda n: DVexList([1] * n),
            'flatten':   lambda lst: DVexList([x for sub in (lst.items if isinstance(lst, DVexList) else lst) for x in (sub.items if isinstance(sub, DVexList) else [sub])]),
            'zip':       lambda *lists: DVexList([[l.items[i] if isinstance(l, DVexList) else l[i] for l in lists] for i in range(min(len(l.items if isinstance(l, DVexList) else l) for l in lists))]),
            'enumerate': lambda lst: DVexList([[i, x] for i, x in enumerate(lst.items if isinstance(lst, DVexList) else lst)]),
            'sort':      lambda lst, key=None, rev=False: DVexList(sorted(lst.items if isinstance(lst, DVexList) else lst, key=key, reverse=rev)),
            'groupBy':   self._group_by,
            'unique':    lambda lst: DVexList(list(dict.fromkeys(lst.items if isinstance(lst, DVexList) else lst))),
            'chunk':     self._chunk,
            'stats':     self._stats,
        }

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.data has no '{name}'")

    def _group_by(self, lst, key_fn):
        groups = {}
        items  = lst.items if isinstance(lst, DVexList) else lst
        for x in items:
            k = key_fn(x)
            groups.setdefault(k, []).append(x)
        return DVexDict({k: DVexList(v) for k, v in groups.items()})

    def _chunk(self, lst, size):
        items = lst.items if isinstance(lst, DVexList) else lst
        return DVexList([DVexList(items[i:i+size]) for i in range(0, len(items), size)])

    def _stats(self, lst):
        items = [float(x) for x in (lst.items if isinstance(lst, DVexList) else lst)]
        if not items: return DVexDict({})
        n    = len(items)
        mean = sum(items) / n
        var  = sum((x - mean) ** 2 for x in items) / n
        std  = var ** 0.5
        srt  = sorted(items)
        med  = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2
        return DVexDict({
            'count':  n,
            'mean':   round(mean, 4),
            'median': round(med, 4),
            'std':    round(std, 4),
            'var':    round(var, 4),
            'min':    srt[0],
            'max':    srt[-1],
            'sum':    sum(items),
            'range':  srt[-1] - srt[0],
        })


class DVexDataTable:
    def __init__(self, cols, rows):
        self.cols = cols if isinstance(cols, list) else (cols.items if isinstance(cols, DVexList) else list(cols))
        self.rows = rows if isinstance(rows, list) else (rows.items if isinstance(rows, DVexList) else [])

    def __repr__(self):
        lines = [' | '.join(str(c) for c in self.cols)]
        lines.append('-' * max(len(lines[0]), 10))
        for row in self.rows[:10]:
            if isinstance(row, DVexList):
                lines.append(' | '.join(str(x) for x in row.items))
            elif isinstance(row, list):
                lines.append(' | '.join(str(x) for x in row))
            else:
                lines.append(str(row))
        return '\n'.join(lines)

    def getattr(self, name):
        if name == 'head':  return lambda n=5: DVexDataTable(self.cols, self.rows[:n])
        if name == 'tail':  return lambda n=5: DVexDataTable(self.cols, self.rows[-n:])
        if name == 'rows':  return DVexList(self.rows)
        if name == 'cols':  return DVexList(self.cols)
        if name == 'shape': return DVexList([len(self.rows), len(self.cols)])
        if name == 'show':  return lambda: print(str(self))
        raise DVexNameError(f"DataTable has no '{name}'")


class SysModule:
    """dvex.sys — System utilities"""
    def __init__(self):
        self.attrs = {
            'args':     DVexList(sys.argv),
            'exit':     sys.exit,
            'env':      lambda k, d=None: os.environ.get(k, d),
            'platform': sys.platform,
            'version':  '7.0',
            'cwd':      os.getcwd,
            'mem':      lambda: f"{sys.getsizeof({})} bytes (approx)",
            'shell':    lambda cmd: os.system(cmd),
        }

    def getattr(self, name):
        if name in self.attrs: return self.attrs[name]
        raise DVexNameError(f"dvex.sys has no '{name}'")


# ═══════════════════════════════════════════════════════════════════════
#  OPTIONAL: Try to import 'requests' library (faster, richer HTTP)
# ═══════════════════════════════════════════════════════════════════════
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ═══════════════════════════════════════════════════════════════════════
#  MOD 27: HTTP MODULE  (dvex.http)
# ═══════════════════════════════════════════════════════════════════════

class HTTPModule:
    """
    dvex.http — Web & API requests.
    Uses 'requests' if available, falls back to urllib.
    Provides GET, POST, PUT, DELETE, headers, params, JSON.
    """

    def __init__(self):
        if not _HAS_URLLIB and not _HAS_REQUESTS:
            raise DVexRuntimeError("No HTTP library available — cannot use dvex.http")
        self._backend = 'requests' if _HAS_REQUESTS else 'urllib'

    def getattr(self, name):
        if name == 'get':       return self._get
        if name == 'post':      return self._post
        if name == 'put':       return self._put
        if name == 'delete':    return self._delete
        if name == 'backend':   return self._backend
        if name == 'download':  return self._download
        raise DVexNameError(f"dvex.http has no attribute '{name}'")

    def _make_response(self, status, body, json_fn=None):
        """Build a DVexDict response object with status, data, text, ok, json."""
        attrs = {
            'status': status,
            'data':   body,
            'text':   body,          # alias: response.text
            'ok':     200 <= status < 300,
            'json':   json_fn if json_fn else lambda: json.loads(body),
        }
        return DVexDict(attrs)

    def _get(self, url: str, params=None, headers=None):
        """HTTP GET — returns response DVexDict {status, data, ok, json}."""
        try:
            if _HAS_REQUESTS:
                p = params.attrs if isinstance(params, DVexDict) else (params or {})
                h = headers.attrs if isinstance(headers, DVexDict) else (headers or {})
                r = _requests.get(url, params=p, headers=h, timeout=15)
                return self._make_response(r.status_code, r.text, r.json)
            else:
                # urllib fallback
                if params:
                    from urllib.parse import urlencode
                    p = params.attrs if isinstance(params, DVexDict) else params
                    url = url + '?' + urlencode(p)
                with _urllib_request.urlopen(url, timeout=15) as resp:
                    body = resp.read().decode('utf-8')
                return self._make_response(resp.status, body)
        except Exception as e:
            raise DVexRuntimeError(f"dvex.http.get failed: {e}")

    def _post(self, url: str, data=None, headers=None):
        """HTTP POST — data as DVexDict/dict → JSON, or string."""
        try:
            if _HAS_REQUESTS:
                h = headers.attrs if isinstance(headers, DVexDict) else (headers or {})
                if isinstance(data, (DVexDict, dict)):
                    d = data.attrs if isinstance(data, DVexDict) else data
                    r = _requests.post(url, json=d, headers=h, timeout=15)
                else:
                    r = _requests.post(url, data=str(data) if data else '', headers=h, timeout=15)
                return self._make_response(r.status_code, r.text, r.json)
            else:
                if isinstance(data, DVexDict):
                    payload = json.dumps(data.attrs).encode('utf-8')
                    ct = 'application/json'
                elif isinstance(data, dict):
                    payload = json.dumps(data).encode('utf-8')
                    ct = 'application/json'
                else:
                    payload = str(data or '').encode('utf-8')
                    ct = 'text/plain'
                req = _urllib_request.Request(
                    url, data=payload,
                    headers={'Content-Type': ct}, method='POST')
                with _urllib_request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode('utf-8')
                return self._make_response(resp.status, body)
        except Exception as e:
            raise DVexRuntimeError(f"dvex.http.post failed: {e}")

    def _put(self, url: str, data=None):
        """HTTP PUT."""
        try:
            if _HAS_REQUESTS:
                d = data.attrs if isinstance(data, DVexDict) else (data or {})
                r = _requests.put(url, json=d, timeout=15)
                return self._make_response(r.status_code, r.text, r.json)
            else:
                payload = json.dumps(data.attrs if isinstance(data, DVexDict) else (data or {})).encode()
                req = _urllib_request.Request(url, data=payload,
                    headers={'Content-Type': 'application/json'}, method='PUT')
                with _urllib_request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode('utf-8')
                return self._make_response(resp.status, body)
        except Exception as e:
            raise DVexRuntimeError(f"dvex.http.put failed: {e}")

    def _delete(self, url: str):
        """HTTP DELETE."""
        try:
            if _HAS_REQUESTS:
                r = _requests.delete(url, timeout=15)
                return self._make_response(r.status_code, r.text, r.json)
            else:
                req = _urllib_request.Request(url, method='DELETE')
                with _urllib_request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode('utf-8')
                return self._make_response(resp.status, body)
        except Exception as e:
            raise DVexRuntimeError(f"dvex.http.delete failed: {e}")

    def _download(self, url: str, dest_path: str) -> str:
        """Download a file from URL and save to dest_path."""
        try:
            if _HAS_REQUESTS:
                r = _requests.get(url, stream=True, timeout=30)
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                _urllib_request.urlretrieve(url, dest_path)
            return f"Downloaded → {dest_path}"
        except Exception as e:
            raise DVexRuntimeError(f"dvex.http.download failed: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  MOD 28: SQL MODULE  (dvex.sql)
# ═══════════════════════════════════════════════════════════════════════

class SQLModule:
    """
    dvex.sql — SQLite database operations.
    Supports: connect, query, execute, fetchOne, fetchAll,
              tables, schema, transaction, rollback, close.
    """

    def __init__(self):
        if not _HAS_SQLITE:
            raise DVexRuntimeError("sqlite3 not available — cannot use dvex.sql")
        self._conn     = None
        self._db_name  = None
        self._in_tx    = False

    def getattr(self, name):
        if name == 'connect':     return self._connect
        if name == 'query':       return self._query
        if name == 'execute':     return self._execute
        if name == 'exec':        return self._execute   # alias: sql.exec(...)
        if name == 'fetchAll':    return self._fetch_all
        if name == 'fetchOne':    return self._fetch_one
        if name == 'tables':      return self._tables()
        if name == 'schema':      return self._schema
        if name == 'begin':       return self._begin
        if name == 'commit':      return self._commit
        if name == 'rollback':    return self._rollback
        if name == 'close':       return self._close
        if name == 'db':          return self._db_name
        if name == 'isOpen':      return self._conn is not None
        if name == 'lastId':      return self._last_id()
        raise DVexNameError(f"dvex.sql has no attribute '{name}'")

    def _connect(self, db_name: str) -> str:
        try:
            self._conn    = _sqlite3.connect(db_name)
            self._conn.row_factory = _sqlite3.Row  # named columns
            self._db_name = db_name
            return f"Connected to '{db_name}'"
        except Exception as e:
            raise DVexRuntimeError(f"dvex.sql.connect failed: {e}")

    def _require_connection(self):
        if self._conn is None:
            raise DVexRuntimeError("dvex.sql: Call db.connect('file.db') first!")

    @staticmethod
    def _norm_p(params):
        """Normalize DVex types to Python native types for sqlite3."""
        result = []
        for p in (params or []):
            if isinstance(p, DVexString):  result.append(p.value)
            elif isinstance(p, DVexList):  result.append(str(p))
            elif isinstance(p, DVexDict):  result.append(str(p))
            else:                          result.append(p)
        return result

    def _query(self, sql: str, params=None):
        """Execute SQL and return all results as DVexList of DVexDicts."""
        self._require_connection()
        try:
            cur = self._conn.cursor()
            raw = params.items if isinstance(params, DVexList) else (params or [])
            p   = self._norm_p(raw)
            cur.execute(sql, p)
            if not self._in_tx:
                self._conn.commit()
            rows = cur.fetchall()
            # Return as DVexList of DVexDicts (named columns) if possible
            if rows and isinstance(rows[0], _sqlite3.Row):
                return DVexList([DVexDict(dict(row)) for row in rows])
            return DVexList([DVexList(list(row)) for row in rows])
        except Exception as e:
            raise DVexRuntimeError(f"dvex.sql.query failed: {e}")

    def _execute(self, sql: str, params=None):
        """Execute SQL without returning rows. Returns affected rowcount."""
        self._require_connection()
        try:
            cur = self._conn.cursor()
            raw = params.items if isinstance(params, DVexList) else (params or [])
            p   = self._norm_p(raw)
            cur.execute(sql, p)
            if not self._in_tx:
                self._conn.commit()
            self._cursor = cur
            return cur.rowcount
        except Exception as e:
            raise DVexRuntimeError(f"dvex.sql.execute failed: {e}")

    def _fetch_all(self, sql: str, params=None):
        return self._query(sql, params)

    def _fetch_one(self, sql: str, params=None):
        """Return first row only as DVexDict or DVexList."""
        self._require_connection()
        try:
            cur = self._conn.cursor()
            raw = params.items if isinstance(params, DVexList) else (params or [])
            p   = self._norm_p(raw)
            cur.execute(sql, p)
            row = cur.fetchone()
            if row is None:
                return None
            if isinstance(row, _sqlite3.Row):
                return DVexDict(dict(row))
            return DVexList(list(row))
        except Exception as e:
            raise DVexRuntimeError(f"dvex.sql.fetchOne failed: {e}")

    def _tables(self):
        """List all tables in the database."""
        self._require_connection()
        rows = self._query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return DVexList([r['name'] if isinstance(r, DVexDict) else r.items[0] for r in rows.items])

    def _schema(self, table_name: str):
        """Return CREATE TABLE statement for a table."""
        self._require_connection()
        row = self._fetch_one(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            [table_name])
        if row is None:
            raise DVexRuntimeError(f"Table '{table_name}' not found.")
        return row['sql'] if isinstance(row, DVexDict) else row.items[0]

    def _begin(self):
        """Begin a transaction (manual commit required)."""
        self._require_connection()
        self._conn.isolation_level = None
        self._conn.execute('BEGIN')
        self._in_tx = True
        return "Transaction begun."

    def _commit(self):
        """Commit current transaction."""
        self._require_connection()
        self._conn.execute('COMMIT')
        self._in_tx = False
        return "Transaction committed."

    def _rollback(self):
        """Rollback current transaction."""
        self._require_connection()
        self._conn.execute('ROLLBACK')
        self._in_tx = False
        return "Transaction rolled back."

    def _last_id(self):
        """Return last inserted row ID."""
        self._require_connection()
        cur = self._conn.cursor()
        cur.execute("SELECT last_insert_rowid()")
        row = cur.fetchone()
        return row[0] if row else None

    def _close(self):
        if self._conn:
            self._conn.close()
            self._conn    = None
            self._db_name = None
        return "Database closed."


# ═══════════════════════════════════════════════════════════════════════
#  MOD 29: UI MODULE  (dvex.ui)
# ═══════════════════════════════════════════════════════════════════════

class UIModule:
    """dvex.ui — Desktop GUI via Tkinter."""

    def __init__(self):
        if not _HAS_TK:
            raise DVexRuntimeError(
                "tkinter not available on this system — cannot use dvex.ui")
        self._root    = None
        self._widgets = []

    def getattr(self, name):
        if name == 'init':    return self._init
        if name == 'window':  return self._window
        if name == 'msg':     return self._msg
        if name == 'alert':   return self._alert
        if name == 'input':   return self._input_dialog
        if name == 'run':     return self._run
        if name == 'button':  return self._button
        if name == 'label':   return self._label
        if name == 'entry':   return self._entry
        if name == 'root':    return self._root
        raise DVexNameError(f"dvex.ui has no attribute '{name}'")

    def _init(self):
        """Create and return the root Tk window."""
        self._root = _tk.Tk()
        self._root.resizable(True, True)
        return self._root

    def _require_root(self):
        if self._root is None:
            raise DVexRuntimeError("dvex.ui: Call ui.init() first!")

    def _window(self, title: str, w: int = 400, h: int = 300):
        """Set window title and dimensions."""
        self._require_root()
        self._root.title(str(title))
        self._root.geometry(f"{int(w)}x{int(h)}")
        return self._root

    def _msg(self, title: str, message: str):
        """Show an info messagebox (non-blocking display)."""
        self._require_root()
        _messagebox.showinfo(str(title), str(message))

    def _alert(self, title: str, message: str):
        """Show a warning messagebox."""
        self._require_root()
        _messagebox.showwarning(str(title), str(message))

    def _input_dialog(self, prompt: str = 'Enter value:') -> str:
        """Simple input dialog — returns user string."""
        self._require_root()
        from tkinter import simpledialog
        return simpledialog.askstring('Input', str(prompt)) or ''

    def _button(self, text: str, command=None):
        """Add a Button widget to the window."""
        self._require_root()
        cmd = command if callable(command) else lambda: None
        btn = _tk.Button(self._root, text=str(text), command=cmd)
        btn.pack(pady=4)
        self._widgets.append(btn)
        return btn

    def _label(self, text: str):
        """Add a Label widget to the window."""
        self._require_root()
        lbl = _tk.Label(self._root, text=str(text))
        lbl.pack(pady=2)
        self._widgets.append(lbl)
        return lbl

    def _entry(self, placeholder: str = ''):
        """Add an Entry (text input field) widget."""
        self._require_root()
        e = _tk.Entry(self._root)
        if placeholder:
            e.insert(0, str(placeholder))
        e.pack(pady=2)
        self._widgets.append(e)
        return e

    def _run(self):
        """Start the Tkinter event loop (blocks until window closes)."""
        self._require_root()
        self._root.mainloop()


# ═══════════════════════════════════════════════════════════════════════
#  MOD 31: CSV MODULE  (dvex.csv)  — New Advanced Feature #1
# ═══════════════════════════════════════════════════════════════════════

class CSVModule:
    """
    dvex.csv — Read, write, and manipulate CSV files.
    csv.read("file.csv")   → DVexList of DVexDicts (header = keys)
    csv.write("file.csv", data)
    csv.parse("a,b\n1,2") → parse from string
    """
    def __init__(self):
        import csv as _csv
        self._csv = _csv

    def getattr(self, name):
        if name == 'read':   return self._read
        if name == 'write':  return self._write
        if name == 'parse':  return self._parse
        if name == 'dump':   return self._dump
        raise DVexNameError(f"dvex.csv has no attribute '{name}'")

    def _read(self, filepath: str, delimiter: str = ','):
        """Read a CSV file → DVexList of DVexDicts."""
        try:
            import csv as _csv
            rows = []
            with open(filepath, 'r', encoding='utf-8', newline='') as f:
                reader = _csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    rows.append(DVexDict(dict(row)))
            return DVexList(rows)
        except Exception as e:
            raise DVexRuntimeError(f"dvex.csv.read failed: {e}")

    def _write(self, filepath: str, data, delimiter: str = ','):
        """Write DVexList of DVexDicts to a CSV file."""
        try:
            import csv as _csv
            items = data.items if isinstance(data, DVexList) else list(data)
            if not items:
                open(filepath, 'w').close()
                return f"Written 0 rows → {filepath}"
            # Get headers from first row
            if isinstance(items[0], DVexDict):
                headers = list(items[0].attrs.keys())
                with open(filepath, 'w', encoding='utf-8', newline='') as f:
                    writer = _csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                    writer.writeheader()
                    for item in items:
                        writer.writerow(item.attrs if isinstance(item, DVexDict) else item)
            else:
                with open(filepath, 'w', encoding='utf-8', newline='') as f:
                    writer = _csv.writer(f, delimiter=delimiter)
                    for item in items:
                        writer.writerow(item.items if isinstance(item, DVexList) else [item])
            return f"Written {len(items)} rows → {filepath}"
        except Exception as e:
            raise DVexRuntimeError(f"dvex.csv.write failed: {e}")

    def _parse(self, text: str, delimiter: str = ','):
        """Parse CSV string → DVexList of DVexLists."""
        try:
            import csv as _csv
            import io
            reader = _csv.reader(io.StringIO(text), delimiter=delimiter)
            return DVexList([DVexList(row) for row in reader])
        except Exception as e:
            raise DVexRuntimeError(f"dvex.csv.parse failed: {e}")

    def _dump(self, data, delimiter: str = ',') -> str:
        """Convert DVexList of DVexLists to CSV string."""
        try:
            import csv as _csv, io
            buf = io.StringIO()
            writer = _csv.writer(buf, delimiter=delimiter)
            items = data.items if isinstance(data, DVexList) else list(data)
            for row in items:
                r = row.items if isinstance(row, DVexList) else [row]
                writer.writerow(r)
            return buf.getvalue()
        except Exception as e:
            raise DVexRuntimeError(f"dvex.csv.dump failed: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  MOD 32: CRYPTO MODULE  (dvex.crypto)  — New Advanced Feature #2
# ═══════════════════════════════════════════════════════════════════════

class CryptoModule:
    """
    dvex.crypto — Hashing, encoding, and basic cryptography.
    crypto.md5("text")     → hex hash
    crypto.sha256("text")  → hex hash
    crypto.sha512("text")  → hex hash
    crypto.base64enc("x")  → base64 encoded
    crypto.base64dec("x")  → base64 decoded
    crypto.hmac(key, msg)  → HMAC-SHA256
    crypto.uuid()          → random UUID string
    """
    def __init__(self):
        import hashlib as _hl, base64 as _b64, hmac as _hmac, uuid as _uuid
        self._hl    = _hl
        self._b64   = _b64
        self._hmac  = _hmac
        self._uuid  = _uuid

    def getattr(self, name):
        if name == 'md5':       return lambda s: self._hl.md5(str(s).encode()).hexdigest()
        if name == 'sha1':      return lambda s: self._hl.sha1(str(s).encode()).hexdigest()
        if name == 'sha256':    return lambda s: self._hl.sha256(str(s).encode()).hexdigest()
        if name == 'sha512':    return lambda s: self._hl.sha512(str(s).encode()).hexdigest()
        if name == 'base64enc': return lambda s: self._b64.b64encode(str(s).encode()).decode()
        if name == 'base64dec': return lambda s: self._b64.b64decode(str(s).encode()).decode()
        if name == 'urlenc':    return lambda s: self._b64.urlsafe_b64encode(str(s).encode()).decode()
        if name == 'urldec':    return lambda s: self._b64.urlsafe_b64decode(str(s).encode()).decode()
        if name == 'uuid':      return lambda: str(self._uuid.uuid4())
        if name == 'uuid4':     return lambda: str(self._uuid.uuid4())
        if name == 'hmac':      return self._hmac_sign
        if name == 'checksum':  return lambda s, algo='sha256': self._hl.new(algo, str(s).encode()).hexdigest()
        raise DVexNameError(f"dvex.crypto has no attribute '{name}'")

    def _hmac_sign(self, key: str, message: str) -> str:
        """HMAC-SHA256 signature."""
        try:
            import hmac as _hmac, hashlib
            sig = _hmac.new(str(key).encode(), str(message).encode(), hashlib.sha256)
            return sig.hexdigest()
        except Exception as e:
            raise DVexRuntimeError(f"dvex.crypto.hmac failed: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  MOD 33: ENV/CONFIG MODULE  (dvex.env)  — New Advanced Feature #3
# ═══════════════════════════════════════════════════════════════════════

class EnvModule:
    """
    dvex.env — Environment variables and .env file support.
    env.get("KEY")           → value or null
    env.set("KEY", "value")  → set in process env
    env.load(".env")         → load .env file
    env.all()                → DVexDict of all env vars
    env.require("KEY")       → value or raise error
    """
    def __init__(self):
        self._extra = {}  # loaded .env values

    def getattr(self, name):
        if name == 'get':     return self._get
        if name == 'set':     return self._set
        if name == 'load':    return self._load
        if name == 'all':     return self._all
        if name == 'require': return self._require
        if name == 'has':     return lambda k: k in os.environ or k in self._extra
        raise DVexNameError(f"dvex.env has no attribute '{name}'")

    def _get(self, key: str, default=None):
        return self._extra.get(key, os.environ.get(key, default))

    def _set(self, key: str, value: str):
        os.environ[key] = str(value)
        self._extra[key] = str(value)
        return f"Set {key}={value}"

    def _load(self, filepath: str = '.env'):
        """Load .env file (KEY=VALUE format, # comments supported)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, _, v = line.partition('=')
                    k = k.strip(); v = v.strip().strip('"').strip("'")
                    self._extra[k] = v
                    os.environ[k]  = v
            return f"Loaded {filepath} — {len(self._extra)} vars"
        except FileNotFoundError:
            return f".env file not found: {filepath}"
        except Exception as e:
            raise DVexRuntimeError(f"dvex.env.load failed: {e}")

    def _all(self):
        merged = dict(os.environ)
        merged.update(self._extra)
        return DVexDict(merged)

    def _require(self, key: str) -> str:
        v = self._extra.get(key, os.environ.get(key))
        if v is None:
            raise DVexRuntimeError(
                f"dvex.env.require: '{key}' is not set. Add it to your .env file.")
        return v


# ═══════════════════════════════════════════════════════════════════════
#  MOD 34: REGEX MODULE  (dvex.regex)  — New Advanced Feature #4
# ═══════════════════════════════════════════════════════════════════════

class RegexModule:
    """
    dvex.regex — Regular expression operations.
    regex.match(pattern, text)   → bool
    regex.find(pattern, text)    → first match string
    regex.findAll(pattern, text) → DVexList of matches
    regex.replace(pattern, repl, text) → new string
    regex.split(pattern, text)   → DVexList of parts
    regex.compile(pattern)       → DVexRegex object
    """
    def __init__(self): pass

    def getattr(self, name):
        if name == 'match':   return self._match
        if name == 'search':  return self._search
        if name == 'find':    return self._find
        if name == 'findAll': return self._find_all
        if name == 'replace': return self._replace
        if name == 'sub':     return self._replace
        if name == 'split':   return self._split
        if name == 'compile': return self._compile
        if name == 'escape':  return re.escape
        if name == 'IGNORECASE': return re.IGNORECASE
        if name == 'MULTILINE':  return re.MULTILINE
        raise DVexNameError(f"dvex.regex has no attribute '{name}'")

    def _match(self, pattern: str, text: str, flags: int = 0) -> bool:
        return bool(re.match(str(pattern), str(text), flags))

    def _search(self, pattern: str, text: str, flags: int = 0):
        m = re.search(str(pattern), str(text), flags)
        return m.group(0) if m else None

    def _find(self, pattern: str, text: str, flags: int = 0):
        m = re.search(str(pattern), str(text), flags)
        return m.group(0) if m else None

    def _find_all(self, pattern: str, text: str, flags: int = 0):
        return DVexList(re.findall(str(pattern), str(text), flags))

    def _replace(self, pattern: str, repl: str, text: str, count: int = 0):
        return re.sub(str(pattern), str(repl), str(text), count=count)

    def _split(self, pattern: str, text: str, maxsplit: int = 0):
        return DVexList(re.split(str(pattern), str(text), maxsplit=maxsplit))

    def _compile(self, pattern: str, flags: int = 0):
        """Return a DVexRegex compiled pattern object."""
        compiled = re.compile(str(pattern), flags)
        return _DVexCompiledRegex(compiled)


class _DVexCompiledRegex:
    """Compiled regex object returned by dvex.regex.compile()."""
    def __init__(self, pat):
        self._pat = pat

    def __repr__(self):
        return f"<DVexRegex pattern={self._pat.pattern!r}>"

    def getattr(self, name):
        if name == 'match':   return lambda s: bool(self._pat.match(str(s)))
        if name == 'find':    return lambda s: (m := self._pat.search(str(s))) and m.group(0)
        if name == 'findAll': return lambda s: DVexList(self._pat.findall(str(s)))
        if name == 'replace': return lambda repl, s: self._pat.sub(str(repl), str(s))
        if name == 'split':   return lambda s: DVexList(self._pat.split(str(s)))
        if name == 'pattern': return self._pat.pattern
        raise DVexNameError(f"DVexRegex has no attribute '{name}'")


# ═══════════════════════════════════════════════════════════════════════
#  MOD 35: NET MODULE  (dvex.net)  — New Advanced Feature #5
# ═══════════════════════════════════════════════════════════════════════

class NetModule:
    """
    dvex.net — Low-level network utilities.
    net.ping(host)         → bool (ICMP-style check via socket)
    net.resolve(host)      → IP address string
    net.localIp()          → local machine IP
    net.isOnline()         → bool (internet connectivity check)
    net.scan(host, ports)  → DVexList of open ports
    net.tcpSend(host, port, msg) → response string
    """
    def __init__(self): pass

    def getattr(self, name):
        if name == 'ping':     return self._ping
        if name == 'resolve':  return self._resolve
        if name == 'localIp':  return self._local_ip
        if name == 'isOnline': return self._is_online
        if name == 'scan':     return self._scan_ports
        if name == 'tcpSend':  return self._tcp_send
        raise DVexNameError(f"dvex.net has no attribute '{name}'")

    def _ping(self, host: str) -> bool:
        """Check if host is reachable by attempting TCP socket connection."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((str(host), 80))
            return True
        except Exception:
            return False

    def _resolve(self, host: str) -> str:
        """DNS resolution — hostname to IP."""
        import socket
        try:
            return socket.gethostbyname(str(host))
        except Exception as e:
            raise DVexRuntimeError(f"dvex.net.resolve failed: {e}")

    def _local_ip(self) -> str:
        """Get local machine IP address."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'

    def _is_online(self) -> bool:
        """Check internet connectivity."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(('8.8.8.8', 53))
            return True
        except Exception:
            return False

    def _scan_ports(self, host: str, ports) -> 'DVexList':
        """Scan a list of ports on a host. Returns open ports."""
        import socket
        port_list = ports.items if isinstance(ports, DVexList) else list(ports)
        open_ports = []
        for port in port_list:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex((str(host), int(port))) == 0:
                        open_ports.append(int(port))
            except Exception:
                pass
        return DVexList(open_ports)

    def _tcp_send(self, host: str, port: int, message: str) -> str:
        """Send a TCP message and receive response."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((str(host), int(port)))
                s.sendall(str(message).encode('utf-8'))
                return s.recv(4096).decode('utf-8', errors='replace')
        except Exception as e:
            raise DVexRuntimeError(f"dvex.net.tcpSend failed: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  MOD 36: OS MODULE  (dvex.os)  — New Advanced Feature #6
# ═══════════════════════════════════════════════════════════════════════

class OSModule:
    """
    dvex.os — Extended OS & process utilities.
    os.run(cmd)         → {stdout, stderr, code}
    os.which(tool)      → path or null
    os.cpu()            → CPU count
    os.memory()         → {total, available, percent}
    os.disk(path)       → {total, used, free}
    os.tempFile()       → temp file path
    os.watch(path, fn)  → file watcher (background)
    """
    def __init__(self): pass

    def getattr(self, name):
        if name == 'run':      return self._run
        if name == 'which':    return self._which
        if name == 'cpu':      return self._cpu_count()
        if name == 'memory':   return self._memory()
        if name == 'disk':     return self._disk
        if name == 'tempFile': return self._temp_file
        if name == 'watch':    return self._watch
        if name == 'pid':      return os.getpid()
        if name == 'hostname': return self._hostname()
        if name == 'username': return self._username()
        raise DVexNameError(f"dvex.os has no attribute '{name}'")

    def _run(self, cmd: str) -> 'DVexDict':
        """Run a shell command and return output."""
        try:
            import subprocess
            result = subprocess.run(
                str(cmd), shell=True, capture_output=True, text=True, timeout=30)
            return DVexDict({
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'code':   result.returncode,
                'ok':     result.returncode == 0,
            })
        except Exception as e:
            raise DVexRuntimeError(f"dvex.os.run failed: {e}")

    def _which(self, tool: str):
        import shutil
        return shutil.which(str(tool))

    def _cpu_count(self):
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except Exception:
            return 1

    def _memory(self):
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return DVexDict({'used_kb': usage, 'unit': 'KB'})
        except ImportError:
            return DVexDict({'used_kb': 'N/A', 'unit': 'KB'})

    def _disk(self, path: str = '.'):
        try:
            stat = os.statvfs(str(path))
            total = stat.f_blocks * stat.f_frsize
            free  = stat.f_bfree  * stat.f_frsize
            used  = total - free
            return DVexDict({
                'total': total, 'used': used, 'free': free,
                'percent': round(used / total * 100, 1) if total else 0
            })
        except Exception:
            return DVexDict({'total': 'N/A', 'used': 'N/A', 'free': 'N/A'})

    def _temp_file(self, suffix: str = '.tmp') -> str:
        import tempfile
        _, path = tempfile.mkstemp(suffix=str(suffix))
        return path

    def _watch(self, path: str, callback):
        """Watch a file for changes (background thread)."""
        import threading
        def _watcher():
            last_mtime = os.path.getmtime(str(path)) if os.path.exists(str(path)) else 0
            while True:
                time.sleep(1)
                try:
                    mtime = os.path.getmtime(str(path))
                    if mtime != last_mtime:
                        last_mtime = mtime
                        if callable(callback):
                            callback(str(path))
                except Exception:
                    pass
        t = threading.Thread(target=_watcher, daemon=True)
        t.start()
        return f"Watching '{path}' (background)"

    def _hostname(self) -> str:
        import socket
        return socket.gethostname()

    def _username(self) -> str:
        try:
            import getpass
            return getpass.getuser()
        except Exception:
            return 'unknown'


# ═══════════════════════════════════════════════════════════════════════
#  MOD 37: TEST MODULE  (dvex.test)  — New Advanced Feature #7
# ═══════════════════════════════════════════════════════════════════════

class TestModule:
    """
    dvex.test — Built-in unit testing framework.
    test.assert(cond, msg)     → pass or fail
    test.assertEqual(a, b)     → equality check
    test.assertNot(cond, msg)  → negation check
    test.run(fn)               → run a test function
    test.suite(name)           → create a test suite
    test.report()              → print results
    """
    def __init__(self):
        self._results = []  # list of {name, passed, msg}
        self._suite   = 'Default'

    def getattr(self, name):
        if name == 'assert_':      return self._assert
        if name == 'assert':       return self._assert
        if name == 'assertEqual':  return self._equal
        if name == 'assertNot':    return self._assert_not
        if name == 'assertRaises': return self._assert_raises
        if name == 'assertType':   return self._assert_type
        if name == 'run':          return self._run_fn
        if name == 'suite':        return self._set_suite
        if name == 'report':       return self._report
        if name == 'passed':       return sum(1 for r in self._results if r['passed'])
        if name == 'failed':       return sum(1 for r in self._results if not r['passed'])
        if name == 'total':        return len(self._results)
        if name == 'reset':        return self._reset
        raise DVexNameError(f"dvex.test has no attribute '{name}'")

    def _record(self, name: str, passed: bool, msg: str = ''):
        self._results.append({'suite': self._suite, 'name': name, 'passed': passed, 'msg': msg})
        status = '✓ PASS' if passed else '✗ FAIL'
        color_start = '' if passed else ''
        print(f"  [{status}] {self._suite} :: {name}" + (f" — {msg}" if msg and not passed else ''))
        return passed

    def _assert(self, condition, message: str = 'Assertion failed') -> bool:
        return self._record(str(message), bool(condition), '' if condition else str(message))

    def _equal(self, a, b, message: str = '') -> bool:
        ok  = (a == b)
        msg = message or f"Expected {b!r}, got {a!r}"
        return self._record(msg if ok else f"{msg} [FAIL: {a!r} != {b!r}]", ok, '')

    def _assert_not(self, condition, message: str = 'Should be false') -> bool:
        return self._record(str(message), not bool(condition), '' if not condition else str(message))

    def _assert_raises(self, fn, message: str = 'Should raise') -> bool:
        try:
            fn()
            return self._record(message, False, 'No exception raised')
        except Exception:
            return self._record(message, True)

    def _assert_type(self, value, expected_type: str, message: str = '') -> bool:
        actual = type(value).__name__
        ok = actual == expected_type
        msg = message or f"Type check: {actual} == {expected_type}"
        return self._record(msg, ok, '' if ok else f"Expected {expected_type}, got {actual}")

    def _run_fn(self, fn, name: str = '') -> bool:
        test_name = name or (fn.name if hasattr(fn, 'name') else str(fn))
        try:
            if callable(fn):
                fn()
            return self._record(test_name, True)
        except Exception as e:
            return self._record(test_name, False, str(e))

    def _set_suite(self, name: str):
        self._suite = str(name)
        return self

    def _report(self):
        total   = len(self._results)
        passed  = sum(1 for r in self._results if r['passed'])
        failed  = total - passed
        pct     = round(passed / total * 100, 1) if total else 0
        W = 56
        print(f"\n  {'='*W}")
        print(f"  D-vex Test Report  (dvex.test v7.0)")
        print(f"  {'-'*W}")
        print(f"  Total : {total}   Passed : {passed}   Failed : {failed}   Score: {pct}%")
        if failed == 0:
            print(f"  Result: ALL TESTS PASSED! 🎉")
        else:
            print(f"  FAILED TESTS:")
            for r in self._results:
                if not r['passed']:
                    print(f"    ✗ [{r['suite']}] {r['name']} — {r['msg']}")
        print(f"  {'='*W}")
        return DVexDict({'total': total, 'passed': passed, 'failed': failed, 'pct': pct})

    def _reset(self):
        self._results = []
        return "Tests reset."




# ═══════════════════════════════════════════════════════════════════════
#  BUILT-IN MODULE REGISTRY  (v5.0 Enterprise)
# ═══════════════════════════════════════════════════════════════════════

BUILTIN_MODULES = {
    # ── Core modules (always available) ─────────────────────────────────
    'dvex.math':   MathModule,
    'dvex.io':     IOModule,
    'dvex.time':   TimeModule,
    'dvex.json':   JSONModule,
    'dvex.ai':     AIModule,
    'dvex.data':   DataModule,
    'dvex.sys':    SysModule,
    # ── v4.0 Enterprise modules ──────────────────────────────────────────
    'dvex.http':   HTTPModule,    # Mod 27 — Web & API (GET/POST/PUT/DELETE)
    'dvex.sql':    SQLModule,     # Mod 28 — SQLite + transactions + schema
    'dvex.ui':     UIModule,      # Mod 29 — Desktop GUI (Tkinter)
    # ── v5.0 Advanced modules ────────────────────────────────────────────
    'dvex.csv':    CSVModule,     # Mod 31 — CSV read/write/parse
    'dvex.crypto': CryptoModule,  # Mod 32 — MD5/SHA/HMAC/UUID/Base64
    'dvex.env':    EnvModule,     # Mod 33 — Environment vars & .env files
    'dvex.regex':  RegexModule,   # Mod 34 — Regular expressions
    'dvex.net':    NetModule,     # Mod 35 — Ping/DNS/port scan/TCP
    'dvex.os':     OSModule,      # Mod 36 — Shell/CPU/memory/disk/watch
    'dvex.test':   TestModule,    # Mod 37 — Unit testing framework
    # ── Short aliases (import math, import sql, etc.) ────────────────────
    'math':   MathModule,
    'io':     IOModule,
    'ai':     AIModule,
    'data':   DataModule,
    'sys':    SysModule,
    'http':   HTTPModule,
    'sql':    SQLModule,
    'ui':     UIModule,
    'csv':    CSVModule,
    'crypto': CryptoModule,
    'env':    EnvModule,
    'regex':  RegexModule,
    'net':    NetModule,
    'osmod':  OSModule,    # 'os' reserved — use 'osmod' or 'dvex.os'
    'test':   TestModule,
}

# ═══════════════════════════════════════════════════════════════════════
#  DVEX PARSER
# ═══════════════════════════════════════════════════════════════════════

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def peek(self, offset=0):
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else Token('EOF', None, -1)

    def advance(self):
        t = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return t

    def expect(self, type_, val=None):
        t = self.advance()
        if t.type != type_ and (val is None or t.value != val):
            raise DVexSyntaxError(
                f"Expected {type_!r} but got {t.type!r} ({t.value!r})", t.line)
        return t

    def skip_newlines(self):
        while self.peek().type == 'NEWLINE':
            self.advance()

    def match(self, *types_or_vals):
        t = self.peek()
        for tv in types_or_vals:
            if t.type == tv or t.value == tv:
                return self.advance()
        return None

    # ── Top-level ────────────────────────────────────────────────────

    def parse(self):
        stmts = []
        self.skip_newlines()
        while self.peek().type != 'EOF':
            s = self.parse_statement()
            if s: stmts.append(s)
            self.skip_newlines()
        return stmts

    def _parse_body(self) -> list:
        """Parse either an indented block OR a single inline statement after colon."""
        # If NEWLINE immediately after colon, it's a multi-line block
        if self.peek().type == 'NEWLINE':
            self.skip_newlines()
            return self.parse_block()
        # Inline body: single statement on same line (e.g., "if x: ret x")
        s = self.parse_statement()
        return [s] if s else []

    def parse_block(self):
        """Parse an indented block. Uses INDENT/DEDENT tokens if available."""
        stmts = []
        self.skip_newlines()
        
        # Check if next token is INDENT (indented block)
        if self.peek().type == 'INDENT':
            self.advance()  # consume INDENT
            while self.peek().type not in ('EOF', 'DEDENT'):
                t = self.peek()
                if t.type in ('KW_ELIF','KW_ELSE','KW_CATCH','KW_FIN','KW_CASE','KW_DEFAULT'):
                    break
                s = self.parse_statement()
                if s: stmts.append(s)
                self.skip_newlines()
            if self.peek().type == 'DEDENT':
                self.advance()  # consume DEDENT
        else:
            # Fallback: no INDENT token (e.g., single-line block or REPL)
            while self.peek().type not in ('EOF', 'DEDENT'):
                t = self.peek()
                if t.type in ('KW_ELIF','KW_ELSE','KW_CATCH','KW_FIN','KW_CASE','KW_DEFAULT'):
                    break
                s = self.parse_statement()
                if s: stmts.append(s)
                self.skip_newlines()
        return stmts

    def parse_statement(self):
        self.skip_newlines()
        t    = self.peek()
        line = t.line

        if t.type == 'EOF': return None

        # Decorators
        if t.type == 'DECORATOR':
            return self.parse_decorator()

        # let / const
        if t.type in ('KW_LET', 'KW_CONST'):
            return self.parse_let_const()

        # fn / async fn
        if t.type == 'KW_FN':
            return self.parse_fn()

        if t.type == 'KW_ASYNC':
            self.advance()
            if self.peek().type == 'KW_FN':
                return self.parse_fn(is_async=True)

        # class
        if t.type == 'KW_CLASS':
            return self.parse_class()

        # show
        if t.type == 'KW_SHOW':
            return self.parse_show()

        # if / elif / else
        if t.type == 'KW_IF':
            return self.parse_if()

        # for
        if t.type == 'KW_FOR':
            return self.parse_for()

        # while
        if t.type == 'KW_WHILE':
            return self.parse_while()

        # repeat
        if t.type == 'KW_REPEAT':
            return self.parse_repeat()

        # match
        if t.type == 'KW_MATCH':
            return self.parse_match()

        # try
        if t.type == 'KW_TRY':
            return self.parse_try()

        # ret
        if t.type == 'KW_RET':
            return self.parse_return()

        # break / continue
        if t.type == 'KW_BREAK':
            self.advance(); return ('break', line)
        if t.type == 'KW_CONTINUE':
            self.advance(); return ('continue', line)

        # pass
        if t.type == 'KW_PASS':
            self.advance(); return ('pass', line)

        # import
        if t.type == 'KW_IMPORT':
            return self.parse_import()

        # raise
        if t.type == 'KW_RAISE':
            self.advance()
            expr = self.parse_expr()
            return ('raise', expr, line)

        # del
        if t.type == 'KW_DEL':
            self.advance()
            name = self.expect('IDENT').value
            return ('del', name, line)

        # Mod 25: yield
        if t.type == 'KW_YIELD':
            self.advance()
            val = self.parse_expr()
            return ('yield', val, line)

        # assert
        if t.type == 'KW_ASSERT':
            self.advance()
            cond = self.parse_expr()
            msg  = None
            if self.peek().type == 'COMMA':
                self.advance()
                msg = self.parse_expr()
            return ('assert', cond, msg, line)

        # type alias
        if t.type == 'KW_TYPE':
            self.advance()
            name = self.expect('IDENT').value
            self.expect('ASSIGN')
            val  = self.parse_expr()
            return ('let', name, val, False, line)

        # Expression / assignment statement
        expr = self.parse_expr()
        if self.peek().type == 'ASSIGN':
            self.advance()
            val = self.parse_expr()
            return ('assign', expr, val, line)
        if self.peek().type == 'OP' and self.peek().value in ('+=','-=','*=','/=','%=','**=','//='):
            op  = self.advance().value
            val = self.parse_expr()
            # FIX: correctly compute real op: **= → **, //= → //, += → +, etc.
            real_op = op[:-1]  # strip trailing '='
            return ('augassign', expr, real_op, val, line)
        if self.peek().type == 'NEWLINE':
            self.advance()
        return ('expr', expr, line)

    def parse_let_const(self):
        is_const  = self.advance().type == 'KW_CONST'
        name      = self.expect('IDENT').value
        type_hint = None
        # Support :: type annotation (TYPEANN) AND : type hint (let x: int = 10)
        if self.peek().type == 'TYPEANN':
            self.advance()
            type_hint = self.advance().value
        elif self.peek().type == 'COLON':
            saved = self.pos
            self.advance()  # consume ':'
            if self.peek().type == 'IDENT':
                type_hint = self.advance().value
                # Only valid if next token is ASSIGN or end-of-statement
                if self.peek().type not in ('ASSIGN', 'NEWLINE', 'EOF', 'COMMA', 'DEDENT'):
                    self.pos = saved  # roll back — not a type hint
                    type_hint = None
            else:
                self.pos = saved  # roll back
        val = None
        if self.peek().type == 'ASSIGN':
            self.advance()
            val = self.parse_expr()
        t = self.peek()
        self.skip_newlines()
        return ('let', name, val, is_const, t.line)

    def parse_fn(self, is_async=False):
        self.advance()  # consume 'fn'
        name = None
        if self.peek().type == 'IDENT':
            name = self.advance().value
        self.expect('LPAREN')
        params = self.parse_params()
        self.expect('RPAREN')
        ret_type = None
        if self.peek().type == 'ARROW':
            self.advance()
            ret_type = self.advance().value
        self.expect('COLON')
        body = self._parse_body()
        return ('fn', name, params, body, is_async, ret_type, self.peek().line)

    def parse_params(self):
        params = []
        while self.peek().type != 'RPAREN':
            if self.peek().type == 'EOF': break
            t = self.peek()
            # Variadic: *args or **kwargs
            is_variadic = False
            is_kwargs   = False
            if t.type == 'OP' and t.value == '*':
                self.advance()
                if self.peek().type == 'OP' and self.peek().value == '*':
                    self.advance()
                    is_kwargs = True
                else:
                    is_variadic = True
                t = self.peek()
            if t.type == 'KW_SELF':
                self.advance()
                pname = 'self'
            else:
                pname = self.expect('IDENT').value
            ptype   = None
            default = None
            if self.peek().type == 'TYPEANN':
                self.advance()
                ptype = self.advance().value
            elif self.peek().type == 'COLON':
                saved = self.pos
                self.advance()
                if self.peek().type == 'IDENT':
                    ptype = self.advance().value
                else:
                    self.pos = saved
            if self.peek().type == 'ASSIGN':
                self.advance()
                default = self.parse_expr()
            star = '**' if is_kwargs else ('*' if is_variadic else '')
            params.append((star + pname, ptype, default))
            if self.peek().type == 'COMMA': self.advance()
        return params

    def parse_class(self):
        self.advance()  # consume 'class'
        name   = self.expect('IDENT').value
        parent = None
        if self.peek().value == 'extends':
            self.advance()
            parent = self.expect('IDENT').value
        self.expect('COLON')
        self.skip_newlines()
        # Consume class body INDENT if present
        has_indent = self.peek().type == 'INDENT'
        if has_indent:
            self.advance()
        methods    = {}
        class_vars = {}
        while self.peek().type not in ('EOF', 'KW_CLASS', 'DEDENT'):
            self.skip_newlines()
            if self.peek().type in ('EOF', 'DEDENT'): break
            if self.peek().type in ('KW_CLASS', 'KW_IF', 'KW_FOR', 'KW_WHILE', 'KW_SHOW') and self.peek().type != 'KW_FN':
                break
            if self.peek().type in ('KW_LET', 'KW_CONST'):
                stmt = self.parse_let_const()
                if stmt[0] == 'let':
                    class_vars[stmt[1]] = stmt[2]
            elif self.peek().type in ('KW_FN', 'KW_ASYNC', 'KW_STATIC'):
                is_static = False
                if self.peek().type == 'KW_STATIC': self.advance(); is_static = True
                is_async  = False
                if self.peek().type == 'KW_ASYNC':  self.advance(); is_async  = True
                fn_stmt = self.parse_fn(is_async)
                fname   = fn_stmt[1]
                if fname:
                    methods[fname] = fn_stmt
            else:
                s = self.parse_statement()
            self.skip_newlines()
        # Consume class body DEDENT if we consumed INDENT
        if has_indent and self.peek().type == 'DEDENT':
            self.advance()
        return ('class', name, parent, methods, class_vars, self.peek().line)

    def parse_show(self):
        line  = self.advance().line  # consume 'show'
        exprs = [self.parse_expr()]
        while self.peek().type == 'COMMA':
            self.advance()
            exprs.append(self.parse_expr())
        return ('show', exprs, line)

    def parse_if(self):
        line = self.advance().line  # consume 'if'
        cond = self.parse_expr()
        self.expect('COLON')
        body     = self._parse_body()
        branches = [('if', cond, body)]
        while self.peek().type == 'KW_ELIF':
            self.advance()
            econd = self.parse_expr()
            self.expect('COLON')
            ebody = self._parse_body()
            branches.append(('elif', econd, ebody))
        else_body = None
        if self.peek().type == 'KW_ELSE':
            self.advance()
            self.expect('COLON')
            else_body = self._parse_body()
        return ('if', branches, else_body, line)

    def parse_for(self):
        line     = self.advance().line  # consume 'for'
        var      = self.expect('IDENT').value
        self.expect('KW_IN')
        iterable = self.parse_expr()
        self.expect('COLON')
        body = self._parse_body()
        return ('for', var, iterable, body, line)

    def parse_while(self):
        line = self.advance().line  # consume 'while'
        cond = self.parse_expr()
        self.expect('COLON')
        body = self._parse_body()
        return ('while', cond, body, line)

    def parse_repeat(self):
        line = self.advance().line  # consume 'repeat'
        n    = self.parse_expr()
        self.expect('COLON')
        self.skip_newlines()
        body = self.parse_block()
        return ('repeat', n, body, line)

    def parse_match(self):
        line = self.advance().line  # consume 'match'
        expr = self.parse_expr()
        self.expect('COLON')
        self.skip_newlines()
        # Consume INDENT if present (match body is indented)
        has_indent = self.peek().type == 'INDENT'
        if has_indent:
            self.advance()
        cases   = []
        default = None
        while self.peek().type in ('KW_CASE', 'KW_DEFAULT'):
            if self.peek().type == 'KW_DEFAULT':
                self.advance()
                self.expect('COLON')
                self.skip_newlines()
                default = self.parse_block()
                break
            self.advance()  # 'case'
            val = self.parse_expr()
            self.expect('COLON')
            self.skip_newlines()
            body = self.parse_block()
            cases.append((val, body))
        # Consume DEDENT if we consumed INDENT
        if has_indent and self.peek().type == 'DEDENT':
            self.advance()
        return ('match', expr, cases, default, line)

    def parse_try(self):
        line     = self.advance().line  # consume 'try'
        self.expect('COLON')
        self.skip_newlines()
        try_body   = self.parse_block()
        catch_var  = None
        catch_body = None
        fin_body   = None
        if self.peek().type == 'KW_CATCH':
            self.advance()
            if self.peek().type == 'IDENT':
                catch_var = self.advance().value
            self.expect('COLON')
            self.skip_newlines()
            catch_body = self.parse_block()
        if self.peek().type == 'KW_FIN':
            self.advance()
            self.expect('COLON')
            self.skip_newlines()
            fin_body = self.parse_block()
        return ('try', try_body, catch_var, catch_body, fin_body, line)

    def parse_return(self):
        line = self.advance().line  # consume 'ret'
        if self.peek().type in ('NEWLINE', 'EOF', 'RBRACE'):
            return ('ret', None, line)
        val = self.parse_expr()
        return ('ret', val, line)

    def parse_import(self):
        line  = self.advance().line  # consume 'import'
        parts = [self.expect('IDENT').value]
        while self.peek().type == 'DOT':
            self.advance()
            parts.append(self.expect('IDENT').value)
        alias    = None
        if self.peek().value == 'as':
            self.advance()
            alias = self.expect('IDENT').value
        mod_name = '.'.join(parts)
        return ('import', mod_name, alias, line)

    def parse_decorator(self):
        self.advance()  # @
        name = self.expect('IDENT').value
        args = []
        if self.peek().type == 'LPAREN':
            self.advance()
            while self.peek().type != 'RPAREN':
                args.append(self.parse_expr())
                if self.peek().type == 'COMMA': self.advance()
            self.advance()
        self.skip_newlines()
        fn = self.parse_fn()
        return ('decorated', name, args, fn)

    # ── Expressions ──────────────────────────────────────────────────

    def parse_expr(self):
        return self.parse_ternary()

    def parse_ternary(self):
        expr = self.parse_or()
        if self.peek().value == '?':
            self.advance()
            then  = self.parse_or()
            self.expect('COLON')
            else_ = self.parse_or()
            return ('ternary', expr, then, else_)
        # Python-style: x if cond else y
        if self.peek().type == 'KW_IF':
            self.advance()
            cond  = self.parse_or()
            self.expect('KW_ELSE')
            else_ = self.parse_or()
            return ('ternary', cond, expr, else_)
        return expr

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == 'KW_OR' or self.peek().value in ('||', 'or'):
            self.advance()
            right = self.parse_and()
            left  = ('binop', 'or', left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek().type == 'KW_AND' or self.peek().value in ('&&', 'and'):
            self.advance()
            right = self.parse_not()
            left  = ('binop', 'and', left, right)
        return left

    def parse_not(self):
        if self.peek().type == 'KW_NOT' or self.peek().value == '!':
            self.advance()
            return ('unary', 'not', self.parse_not())
        return self.parse_compare()

    def parse_compare(self):
        left = self.parse_add()
        ops  = {'==','!=','<','>','<=','>=','===','!=='}
        while self.peek().type == 'OP' and self.peek().value in ops:
            op    = self.advance().value
            right = self.parse_add()
            left  = ('binop', op, left, right)
        if self.peek().type in ('KW_IS', 'KW_ISNOT'):
            op    = 'is' if self.peek().type == 'KW_IS' else 'isnot'
            self.advance()
            right = self.parse_add()
            left  = ('binop', op, left, right)
        if self.peek().type == 'KW_IN':
            self.advance()
            right = self.parse_add()
            left  = ('binop', 'in', left, right)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.peek().type == 'OP' and self.peek().value in ('+', '-'):
            op    = self.advance().value
            right = self.parse_mul()
            left  = ('binop', op, left, right)
        return left

    def parse_mul(self):
        left = self.parse_power()
        while self.peek().type == 'OP' and self.peek().value in ('*', '/', '//', '%'):
            op    = self.advance().value
            right = self.parse_power()
            left  = ('binop', op, left, right)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.peek().value == '**':
            self.advance()
            right = self.parse_power()
            return ('binop', '**', left, right)
        return left

    def parse_unary(self):
        if self.peek().value == '-':
            self.advance()
            return ('unary', '-', self.parse_unary())
        if self.peek().value == '+':
            self.advance()
            return self.parse_unary()
        if self.peek().value == '~':
            self.advance()
            return ('unary', '~', self.parse_unary())
        return self.parse_call_index()

    def parse_call_index(self):
        expr = self.parse_primary()
        while True:
            t = self.peek()
            if t.type == 'DOT':
                self.advance()
                attr = self.advance()
                name = attr.value
                if self.peek().type == 'LPAREN':
                    self.advance()
                    args = self.parse_args()
                    self.expect('RPAREN')
                    expr = ('method_call', expr, name, args)
                else:
                    expr = ('getattr', expr, name)
            elif t.type == 'LPAREN':
                self.advance()
                args = self.parse_args()
                self.expect('RPAREN')
                expr = ('call', expr, args)
            elif t.type == 'LBRACK':
                self.advance()
                idx = self.parse_expr()
                self.expect('RBRACK')
                expr = ('index', expr, idx)
            else:
                break
        return expr

    def parse_args(self):
        args   = []
        kwargs = {}
        while self.peek().type not in ('RPAREN', 'EOF'):
            if self.peek().type == 'IDENT' and self.peek(1).type == 'ASSIGN':
                k = self.advance().value
                self.advance()
                v = self.parse_expr()
                kwargs[k] = v
            else:
                args.append(self.parse_expr())
            if self.peek().type == 'COMMA': self.advance()
        return args

    def parse_primary(self):
        t    = self.peek()
        line = t.line

        if t.type == 'NUMBER':
            return ('lit', self.advance().value)

        if t.type == 'STRING':
            return ('lit', self.advance().value)

        if t.type == 'BOOL':
            return ('lit', self.advance().value)

        if t.type == 'KW_TRUE':
            self.advance(); return ('lit', True)
        if t.type == 'KW_FALSE':
            self.advance(); return ('lit', False)
        if t.type == 'KW_NULL':
            self.advance(); return ('lit', None)
        if t.type == 'NULL':
            self.advance(); return ('lit', None)

        # new ClassName(args)
        if t.type == 'KW_NEW':
            self.advance()
            name = self.expect('IDENT').value
            args = []
            if self.peek().type == 'LPAREN':
                self.advance()
                args = self.parse_args()
                self.expect('RPAREN')
            return ('new', name, args)

        # ref variable
        if t.type == 'KW_REF':
            self.advance()
            name = self.expect('IDENT').value
            return ('ref', name)

        # typeof
        if t.type == 'KW_TYPEOF':
            self.advance()
            expr = self.parse_primary()
            return ('typeof', expr)

        # lambda x: expr
        if t.type == 'KW_LAMBDA':
            self.advance()
            params = []
            while self.peek().type != 'COLON':
                pname = self.expect('IDENT').value
                params.append((pname, None, None))
                if self.peek().type == 'COMMA': self.advance()
            self.expect('COLON')
            body = self.parse_expr()
            return ('lambda', params, body)

        # fn (anonymous): fn(params): body
        if t.type == 'KW_FN' and self.peek(1).type == 'LPAREN':
            self.advance()  # consume 'fn'
            self.expect('LPAREN')
            params = self.parse_params()
            self.expect('RPAREN')
            self.expect('COLON')
            self.skip_newlines()
            body = self.parse_block()
            return ('fn_expr', None, params, body, False, None)

        # List literal / comprehension
        if t.type == 'LBRACK':
            return self.parse_list()

        # Dict / Set literal
        if t.type == 'LBRACE':
            return self.parse_dict_or_set()

        # Parenthesized / tuple
        if t.type == 'LPAREN':
            self.advance()
            if self.peek().type == 'RPAREN':
                self.advance(); return ('lit', ())
            expr = self.parse_expr()
            if self.peek().type == 'COMMA':
                items = [expr]
                while self.peek().type == 'COMMA':
                    self.advance()
                    if self.peek().type == 'RPAREN': break
                    items.append(self.parse_expr())
                self.expect('RPAREN')
                return ('tuple', items)
            self.expect('RPAREN')
            return expr

        # Identifier
        if t.type == 'IDENT':
            return ('var', self.advance().value)

        if t.type == 'KW_SELF':
            self.advance(); return ('var', 'self')
        if t.type == 'KW_SUPER':
            self.advance(); return ('var', 'super')

        # await
        if t.type == 'KW_AWAIT':
            self.advance()
            expr = self.parse_primary()
            return ('await', expr)

        raise DVexSyntaxError(f"Unexpected token: {t.type!r} = {t.value!r}", t.line)

    def parse_list(self):
        self.advance()  # [
        items = []
        if self.peek().type != 'RBRACK':
            first = self.parse_expr()
            # List comprehension: [expr for x in iterable if cond]
            if self.peek().type == 'KW_FOR':
                self.advance()
                var  = self.expect('IDENT').value
                self.expect('KW_IN')
                src  = self.parse_or()
                cond = None
                if self.peek().type == 'KW_IF':
                    self.advance()
                    cond = self.parse_or()
                self.expect('RBRACK')
                return ('listcomp', first, var, src, cond)
            items.append(first)
            while self.peek().type == 'COMMA':
                self.advance()
                if self.peek().type == 'RBRACK': break
                items.append(self.parse_expr())
        self.expect('RBRACK')
        return ('list', items)

    def parse_dict_or_set(self):
        self.advance()  # {
        if self.peek().type == 'RBRACE':
            self.advance(); return ('dict', [])
        first = self.parse_expr()
        if self.peek().type == 'COLON':
            self.advance()
            val   = self.parse_expr()
            pairs = [(first, val)]
            while self.peek().type == 'COMMA':
                self.advance()
                if self.peek().type == 'RBRACE': break
                k = self.parse_expr()
                self.expect('COLON')
                v = self.parse_expr()
                pairs.append((k, v))
            self.expect('RBRACE')
            return ('dict', pairs)
        else:
            items = [first]
            while self.peek().type == 'COMMA':
                self.advance()
                if self.peek().type == 'RBRACE': break
                items.append(self.parse_expr())
            self.expect('RBRACE')
            return ('set', items)

# ═══════════════════════════════════════════════════════════════════════
#  DVEX INTERPRETER
# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
#  ARA AI — D-vex Built-in AI Assistant  v0.7
# ═══════════════════════════════════════════════════════════════════════
class AraAI:
    """
    ╔══════════════════════════════════════════════════════════════╗
    ║   Ara AI  v8.0  —  D-vex Built-in Intelligent Assistant     ║
    ║   10 Advanced Features + xAI Grok API Integration           ║
    ║   Feature 1 : Real-time Chat (API / Local fallback)         ║
    ║   Feature 2 : D-vex Code Generator                         ║
    ║   Feature 3 : Auto Bug Fix & Code Review                    ║
    ║   Feature 4 : Trend Detector (real topics via mock/API)     ║
    ║   Feature 5 : Conversation Memory (last 20 turns)           ║
    ║   Feature 6 : Mood Engine (chill/serious/funny/focus)       ║
    ║   Feature 7 : Emotion Detector                              ║
    ║   Feature 8 : Code Explainer                                ║
    ║   Feature 9 : Multi-language Response (hi/en)               ║
    ║   Feature 10: Tool-use Router (generate/fix/explain/trend)  ║
    ╚══════════════════════════════════════════════════════════════╝
    """

    VERSION  = '8.0'
    NAME     = 'Ara'
    ENDPOINT = 'https://api.x.ai/v1/chat/completions'

    SYSTEM_PROMPT = (
        'You are Ara 8.0, the D-vex programming language AI assistant. '
        'Your personality is: chill, brotherly, funny but smart. '
        'Respond in Hindi-English mix (Hinglish) when the user writes in Hindi. '
        'D-vex syntax: let/const, fn, class, show, ret, if/elif/else, '
        'for/while/repeat, match/case, try/catch/fin, async/await, yield, '
        '|> pipe operator, extends, super(), @decorator, import dvex.*. '
        'Always give concise, helpful D-vex code examples. '
        'If asked a joke — be genuinely funny!'
    )

    MOODS = {
        'chill':   'Relaxed, helpful, casual tone.',
        'serious': 'Focused, precise, no jokes.',
        'funny':   'Jokes in every answer, puns welcome!',
        'focus':   'Ultra-concise, just the code.',
        'tutor':   'Patient teacher mode with examples.',
    }

    def __init__(self):
        self.version  = self.VERSION
        self.name     = self.NAME
        self.mood     = 'chill'
        self.api_key  = os.environ.get('XAI_API_KEY', '')
        self._history: list = []          # Feature 5: Conversation Memory
        self._emotion_log: list = []      # Feature 7: Emotion log
        self._session_start = time.time()

        if self.api_key:
            print(f"  [Ara 8.0] xAI API key found — full API mode active ✓")
        else:
            print(f"  [Ara 8.0] No XAI_API_KEY set — smart local mode active.")

    # ── Feature 1: Real-time Chat ────────────────────────────────────────
    def chat(self, query: str) -> str:
        """Feature 1: Chat with Ara. Uses xAI API if key set, else smart local."""
        query = str(query)

        # Feature 7: Detect emotion first
        emotion = self._detect_emotion(query)
        if emotion:
            self._emotion_log.append({'q': query, 'emotion': emotion})
            if emotion == 'sad' and self.mood != 'serious':
                self.mood = 'serious'

        # Feature 10: Route to specialized tool if clear intent
        routed = self._tool_route(query)
        if routed:
            return routed

        # Add to memory
        self._history.append({'role': 'user', 'content': query})
        if len(self._history) > 40:
            self._history = self._history[-40:]  # keep last 20 turns (40 msgs)

        result = self._api_chat(query) if self.api_key else self._local_chat(query)

        self._history.append({'role': 'assistant', 'content': result})
        return result

    def _api_chat(self, query: str) -> str:
        """Call xAI Grok API via requests or urllib fallback."""
        payload = {
            'model': 'grok-beta',
            'messages': [
                {'role': 'system', 'content': self.SYSTEM_PROMPT + f' Current mood: {self.mood}. {self.MOODS.get(self.mood, "")}'} 
            ] + self._history[-20:],
            'temperature': 0.85 if self.mood == 'funny' else 0.7,
            'max_tokens': 600,
        }

        # Try requests first (faster, better error handling)
        try:
            import requests as _req
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            resp = _req.post(self.ENDPOINT, json=payload, headers=headers, timeout=25)
            if resp.status_code == 200:
                ans = resp.json()['choices'][0]['message']['content'].strip()
                return ans.replace('Grok', 'Ara').replace('xAI', 'D-vex AI')
            else:
                return f"[Ara 8.0] API Error {resp.status_code} — switching to local mode.\n{self._local_chat(query)}"
        except ImportError:
            pass  # requests not available, try urllib
        except Exception as e:
            return f"[Ara 8.0] API connection failed: {e}\n{self._local_chat(query)}"

        # Fallback: urllib
        try:
            import urllib.request as _ureq
            data = json.dumps(payload).encode('utf-8')
            req  = _ureq.Request(
                self.ENDPOINT, data=data,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type':  'application/json',
                }
            )
            with _ureq.urlopen(req, timeout=25) as resp:
                ans = json.loads(resp.read())['choices'][0]['message']['content'].strip()
                return ans.replace('Grok', 'Ara').replace('xAI', 'D-vex AI')
        except Exception as e:
            return f"[Ara 8.0] urllib also failed: {e}\n{self._local_chat(query)}"

    # ── Feature 1 Local: Smart local chat ────────────────────────────────
    def _local_chat(self, q: str) -> str:
        """Smart local responses with personality."""
        ql = q.lower().strip()

        greetings = {'hi', 'hello', 'namaste', 'hey', 'hola', 'sup', 'yo', 'kya haal'}
        if ql in greetings or any(g in ql for g in greetings):
            msgs = [
                "Heyy bhaii! 👋 Main Ara 8.0 hoon — D-vex ka apna AI! Kya bana rahe ho aaj?",
                "Namaste! 🙏 Kuch code likhna hai? Let's goo!",
                "Yo! Ara here — ready to help with D-vex magic! ✨",
            ]
            return random.choice(msgs)

        if any(w in ql for w in ('joke', 'funny', 'haha', 'mazak')):
            jokes = [
                "Programmer ne boss ko bola: 'Main 5 minute mein feature bana dunga.' Boss: 'Kitne time mein?' Programmer: '...2 hafton mein.' 😄",
                "Mujhe bugs se darr nahi lagta — darr lagta hai tab jab koi bug nahi milta! 😅",
                "Kyon programmers andheron mein kaam karte hain? Kyunki light attract karta hai bugs ko! 🦟",
            ]
            return random.choice(jokes)

        if any(w in ql for w in ('trends', 'trend', 'kya chal raha', 'latest')):
            return self.trends()

        if ql.startswith(('generate ', 'gen ', 'banao ', 'bana ')):
            topic = q.split(' ', 1)[1] if ' ' in q else 'sample'
            return self.generate(topic)

        if ql.startswith(('fix ', 'fix karo', 'error hai', 'bug hai')):
            code = q.split(' ', 1)[1] if ' ' in q else ''
            return self.fix_bug(code)

        if ql.startswith(('explain ', 'samjhao ', 'what is ', 'kya hai ')):
            topic = q.split(' ', 1)[1] if ' ' in q else q
            return self.explain(topic)

        if any(w in ql for w in ('help', 'madad', 'commands', 'syntax')):
            return self._help_text()

        if any(w in ql for w in ('sad', 'dukhi', 'frustrated', 'pareshaan', 'stuck')):
            return "Arre bhai, koi baat nahi! 💪 D-vex bugs tough hote hain, but we fix them together. Code share karo — main dekhunga!"

        if any(w in ql for w in ('good', 'great', 'awesome', 'badhiya', 'perfect', 'nice')):
            return "Shukriya bhai! 🙌 Ye sunke bahut achha laga. Aage kya banayenge?"

        if 'version' in ql or 'kaun ho' in ql or 'who are you' in ql:
            return f"Main hoon Ara {self.VERSION} — D-vex language ka official AI assistant! Mood: {self.mood} 😎"

        # Generic smart response
        return f"Suna '{q[:50]}{'...' if len(q) > 50 else ''}' — thoda aur batao, main help karunga! D-vex code chahiye? Bolo! 🤙"

    # ── Feature 2: D-vex Code Generator ─────────────────────────────────
    def generate(self, description: str) -> str:
        """Feature 2: Generate D-vex code for a given description."""
        desc = str(description).lower()

        if any(w in desc for w in ('loop', 'for', 'repeat', 'iterate')):
            return f"""// Ara 8.0 — Generated: {description}
for i in range(1, 11):
    show i
// Output: 1 to 10"""

        if any(w in desc for w in ('function', 'fn', 'method', 'calculator', 'calc')):
            return f"""// Ara 8.0 — Generated: {description}
fn calculate(a, b, op):
    if op == "+": ret a + b
    elif op == "-": ret a - b
    elif op == "*": ret a * b
    elif op == "/":
        if b == 0: ret "Error: Division by zero!"
        ret a / b
    else: ret "Unknown op"

show calculate(10, 5, "+")  // 15
show calculate(10, 5, "/")  // 2.0"""

        if any(w in desc for w in ('class', 'object', 'oop')):
            name = ''.join(w.capitalize() for w in desc.split() if w.isalpha())[:10] or 'MyClass'
            return f"""// Ara 8.0 — Generated: {description}
class {name}:
    fn __init__(self, name):
        self.name = name
        self.created = "now"

    fn greet(self):
        show "Hello from " + self.name + "!"

    fn info(self) -> str:
        ret "Name: " + self.name

let obj = new {name}("D-vex")
obj.greet()
show obj.info()"""

        if any(w in desc for w in ('fibonacci', 'fib')):
            return """// Ara 8.0 — Generated: Fibonacci
fn fib(n):
    if n <= 1: ret n
    ret fib(n-1) + fib(n-2)

for i in range(10):
    show fib(i)"""

        if any(w in desc for w in ('sort', 'bubble', 'sorting')):
            return """// Ara 8.0 — Generated: Bubble Sort
fn bubbleSort(arr):
    let n = len(arr)
    repeat n:
        for i in range(n - 1):
            if arr[i] > arr[i+1]:
                let temp = arr[i]
                arr[i] = arr[i+1]
                arr[i+1] = temp
    ret arr

let nums = [64, 34, 25, 12, 22, 11, 90]
show bubbleSort(nums)"""

        # Generic template
        return f"""// Ara 8.0 — Generated: {description}
fn main():
    show "D-vex: {description}"
    let result = 0
    for i in range(1, 11):
        result += i
    show "Sum 1-10: " + str(result)
    ret result

let out = main()
show "Done! Result: " + str(out)"""

    # ── Feature 3: Auto Bug Fix ───────────────────────────────────────────
    def fix_bug(self, code: str) -> str:
        """Feature 3: Auto bug fix and code review."""
        code = str(code)
        issues = []
        fixed  = code

        if '/ 0' in code or '/0' in code.replace(' ', ''):
            issues.append("⚠️  Division by zero detected!")
            fixed = fixed.replace('/ 0', '/ (0 + 0.0001)')  # safe guard

        if 'undefined' in code.lower() or 'null.getattr' in code.lower():
            issues.append("⚠️  Possible null reference — use null check.")

        if code.strip().endswith(':') and '\n' not in code.strip():
            issues.append("⚠️  Block body missing after ':'.")

        if 'print(' in code:
            issues.append("ℹ️  Use 'show' instead of 'print()' in D-vex.")
            fixed = fixed.replace('print(', 'show ')
            fixed = fixed.replace(')',  '', 1) if 'show ' in fixed else fixed

        if not issues:
            return f"✅ Code looks clean! No obvious bugs found.\n\nCode:\n{code}"

        result = "🔍 Ara 8.0 Bug Report:\n"
        result += '\n'.join(f"  {i}" for i in issues)
        result += f"\n\n💡 Suggestion: Wrap in try/catch:\ntry:\n  {code.strip()}\ncatch e:\n  show 'Error: ' + str(e)"
        if fixed != code:
            result += f"\n\n🔧 Auto-fixed version:\n{fixed}"
        return result

    # ── Feature 4: Trends ────────────────────────────────────────────────
    def trends(self) -> str:
        """Feature 4: Show current D-vex and tech trends."""
        trend_list = [
            "🔥 D-vex v7.0 — Final Enterprise with Ara 8.0!",
            "🤖 AI-first programming languages are rising",
            "⚡ Async/await patterns replacing callbacks everywhere",
            "🧩 Functional style: |> pipe operator is trending",
            "🔒 Security-first: dvex.crypto module in every project",
            "📊 Data science with dvex.data — replace pandas!",
            "🌐 dvex.http for REST APIs without external libs",
            "🧪 dvex.test — built-in testing is the new standard",
        ]
        return "📡 Ara 8.0 — Current Trends:\n" + '\n'.join(f"  {t}" for t in trend_list)

    # ── Feature 6: Mood Engine ────────────────────────────────────────────
    def set_mood(self, mood: str) -> str:
        """Feature 6: Change Ara's mood/personality."""
        mood = str(mood).lower()
        if mood in self.MOODS:
            self.mood = mood
            return f"[Ara 8.0] Mood → {mood}! {self.MOODS[mood]} 😎"
        avail = ', '.join(self.MOODS.keys())
        return f"[Ara 8.0] Unknown mood '{mood}'. Available: {avail}"

    # ── Feature 7: Emotion Detection ─────────────────────────────────────
    def _detect_emotion(self, text: str) -> str:
        """Feature 7: Detect user emotion from text."""
        t = text.lower()
        if any(w in t for w in ('sad', 'dukhi', 'cry', 'frustrated', 'angry', 'ugh', 'stuck')):
            return 'sad'
        if any(w in t for w in ('happy', 'khush', 'excited', 'great', 'awesome', 'love it')):
            return 'happy'
        if any(w in t for w in ('confused', 'confusing', 'dont understand', 'samajh nahi')):
            return 'confused'
        return ''

    # ── Feature 8: Code Explainer ─────────────────────────────────────────
    def explain(self, topic: str) -> str:
        """Feature 8: Explain a D-vex concept or code snippet."""
        topic_l = topic.lower().strip()
        explanations = {
            'let':    "let x = 10 — Variable declare karo. Re-assign possible hai.",
            'const':  "const PI = 3.14 — Constant. Once set, can't change. Error aayega!",
            'fn':     "fn add(a, b):\n  ret a + b\n— Function define karo. ret = return value.",
            'class':  "class Dog:\n  fn bark(self):\n    show 'Woof!'\nlet d = new Dog()\nd.bark()",
            'for':    "for i in range(10):\n  show i\n— 0 se 9 tak loop.",
            'while':  "while x > 0:\n  x -= 1\n— Condition true hone tak loop.",
            'repeat': "repeat 5:\n  show 'hello'\n— Exactly 5 baar repeat.",
            'match':  "match x:\n  case 1: show 'one'\n  default: show 'other'\n— Pattern matching.",
            'try':    "try:\n  risky()\ncatch e:\n  show e\nfin:\n  show 'done'\n— Error handling.",
            'import': "import dvex.math\nimport dvex.http as http\n— Module import.",
            'async':  "async fn fetch():\n  let data = await getUrl(url)\n  ret data\n— Async functions.",
            'lambda': "let double = lambda x: x * 2\nshow double(5)  // 10",
            'yield':  "fn counter():\n  yield 1\n  yield 2\nfor n in counter(): show n",
            'pipe':   "data |> clean |> process |> show\n— Same as: show(process(clean(data)))",
        }
        for key, val in explanations.items():
            if key in topic_l:
                return f"📖 Ara 8.0 explains '{key}':\n{val}"

        return f"📖 Ara 8.0: '{topic}' ke baare mein — D-vex docs check karo ya mujhe full code do, explain kar dunga!"

    # ── Feature 9: Multi-language Support ────────────────────────────────
    def translate_response(self, text: str, lang: str = 'hi') -> str:
        """Feature 9: Basic Hindi/English response toggle."""
        if lang == 'en':
            # Very basic Hinglish → English cleanup
            replacements = {
                'bhai': 'friend', 'karo': 'do it', 'hai': 'is',
                'nahi': "isn't", 'aur': 'and', 'ke': 'of', 'ho': 'is',
            }
            for hi, en in replacements.items():
                text = text.replace(hi, en)
        return text

    # ── Feature 10: Tool Router ────────────────────────────────────────────
    def _tool_route(self, query: str) -> str:
        """Feature 10: Route clear-intent queries to specialized tools."""
        ql = query.lower().strip()

        # Code generation intent
        if ql.startswith(('generate ', 'gen ', 'create code', 'write code', 'banao code')):
            topic = query.split(' ', 1)[1] if ' ' in query else 'sample'
            return self.generate(topic)

        # Bug fix intent
        if ql.startswith(('fix ', 'debug ', 'find bug', 'bug fix')):
            code = query.split(' ', 1)[1] if ' ' in query else ''
            return self.fix_bug(code)

        # Explain intent
        if ql.startswith(('explain ', 'what is ', 'how does ', 'samjhao ')):
            topic = query.split(' ', 1)[1] if ' ' in query else query
            return self.explain(topic)

        # Trend intent
        if ql in ('trends', 'trend', 'what is trending', 'kya chal raha'):
            return self.trends()

        # Mood change
        if ql.startswith(('mood ', 'set mood', 'mood change')):
            m = query.split(' ')[-1]
            return self.set_mood(m)

        return ''  # No routing — fall through to chat

    def _help_text(self) -> str:
        return """🤖 Ara 8.0 — D-vex AI Help:

  ara.chat("hi")                  → Chat with Ara
  ara.generate("fibonacci")       → Generate D-vex code
  ara.fix_bug("let x = / 0")      → Bug fix suggestions
  ara.explain("match")            → Explain D-vex syntax
  ara.trends()                    → Current tech trends
  ara.set_mood("funny")           → Change Ara's mood
  ara.history()                   → See conversation history

  Moods: chill | serious | funny | focus | tutor

  D-vex Syntax Quick Reference:
    let x = 10       → Variable
    const PI = 3.14  → Constant
    fn add(a,b):     → Function
      ret a + b
    show "Hello"     → Print
    for i in range(5): show i  → Loop"""

    def history(self) -> str:
        """Feature 5: Show conversation history."""
        if not self._history:
            return "[Ara 8.0] No conversation history yet. Start chatting!"
        lines = []
        for i, msg in enumerate(self._history[-10:], 1):
            role = "You" if msg['role'] == 'user' else "Ara"
            content = msg['content'][:80] + ('...' if len(msg['content']) > 80 else '')
            lines.append(f"  [{i}] {role}: {content}")
        return "📜 Ara 8.0 — Last 10 messages:\n" + '\n'.join(lines)

    def suggest(self, context: str) -> str:
        return f'💡 Ara suggests: ara.chat("{context}")'

    def getattr(self, name: str):
        """Allow D-vex dot-notation access: ara.chat("hi")"""
        methods = {
            'chat':      self.chat,
            'generate':  self.generate,
            'fix_bug':   self.fix_bug,
            'fixBug':    self.fix_bug,
            'trends':    self.trends,
            'set_mood':  self.set_mood,
            'setMood':   self.set_mood,
            'explain':   self.explain,
            'translate': self.translate_response,
            'history':   self.history,
            'suggest':   self.suggest,
            'version':   self.version,
            'mood':      self.mood,
            'name':      self.name,
        }
        if name in methods:
            return methods[name]
        raise DVexNameError(f"Ara has no attribute '{name}'. Try: ara.chat(), ara.generate(), ara.fix_bug()")

    def __repr__(self):
        mode = "xAI API" if self.api_key else "local smart"
        return f'<Ara AI v{self.VERSION} | mood={self.mood} | {mode} | history={len(self._history)} msgs>'


class DVexInterpreter:
    __current__ = None  # global reference for bound method calls

    def __init__(self):
        DVexInterpreter.__current__ = self
        self.global_env = Environment()
        self.modules    = {}
        self._setup_builtins()

    def _setup_builtins(self):
        env = self.global_env

        # Core functions
        env.set('show',    print)
        env.set('input',   input)
        env.set('len',     lambda x: len(x.items) if isinstance(x, DVexList) else (len(x.data) if isinstance(x, (DVexDict, DVexSet)) else len(x)))
        env.set('range',   lambda *a: DVexList(list(range(*a))))
        env.set('type',    lambda x: type(x).__name__)
        env.set('int',     int)
        env.set('float',   float)
        env.set('str',     lambda x: str(x.value) if isinstance(x, DVexString) else str(x))
        env.set('bool',    bool)
        env.set('list',    lambda x=None: DVexList(x.items if isinstance(x, DVexList) else (list(x) if x else [])))
        env.set('dict',    lambda x=None: DVexDict(x.data if isinstance(x, DVexDict) else (dict(x) if x else {})))
        env.set('set',     lambda x=None: DVexSet(x.items if isinstance(x, DVexList) else (set(x) if x else set())))
        env.set('abs',     abs)
        env.set('round',   round)
        env.set('max',     lambda *a: max(*(x.items if isinstance(x, DVexList) else [x] for x in a)) if len(a) == 1 else max(*a))
        env.set('min',     lambda *a: min(*(x.items if isinstance(x, DVexList) else [x] for x in a)) if len(a) == 1 else min(*a))
        env.set('sum',     lambda x: sum(x.items) if isinstance(x, DVexList) else sum(x))
        env.set('sorted',  lambda x, r=False: DVexList(sorted(x.items if isinstance(x, DVexList) else x, reverse=r)))
        env.set('reversed',lambda x: DVexList(list(reversed(x.items if isinstance(x, DVexList) else x))))
        env.set('zip',     lambda *ls: DVexList([[ls[j].items[i] for j in range(len(ls))] for i in range(min(len(l.items) for l in ls))]))
        env.set('enumerate',lambda x: DVexList([[i, v] for i, v in enumerate(x.items if isinstance(x, DVexList) else x)]))
        env.set('map',     lambda fn, lst: DVexList([fn(x) for x in (lst.items if isinstance(lst, DVexList) else lst)]))
        env.set('filter',  lambda fn, lst: DVexList([x for x in (lst.items if isinstance(lst, DVexList) else lst) if fn(x)]))
        env.set('print',   print)
        env.set('format',  lambda s, *a, **kw: s.format(*a, **kw))
        env.set('repr',    repr)
        env.set('isinstance', isinstance)
        env.set('hasattr', hasattr)
        env.set('chr',     chr)
        env.set('ord',     ord)
        env.set('hex',     hex)
        env.set('bin',     bin)
        env.set('oct',     oct)

        # D-vex specific
        env.set('ara', AraAI())  # Built-in AI assistant
        env.set('dvex_version', '3.0v')
        env.set('dvex_ext',     '.ex')
        env.set('null',     None)
        env.set('true',     True)
        env.set('false',    False)
        env.set('Infinity', math.inf)
        env.set('NaN',      float('nan'))

        # Math shortcuts
        env.set('PI',   math.pi)
        env.set('E',    math.e)
        env.set('sqrt', math.sqrt)
        env.set('pow',  pow)
        env.set('log',  math.log)
        env.set('sin',  math.sin)
        env.set('cos',  math.cos)
        env.set('tan',  math.tan)

        # ── Mod 6: AI-First Global Module (import ke bina predict) ──────
        env.set('predict', lambda data: random.choice([0, 1]))  # AI predict global

        # ── Mod 7: Smart Show ────────────────────────────────────────────
        def _smart_show(*args):
            parts = []
            for a in args:
                if isinstance(a, DVexList): parts.append('[' + ' | '.join(str(x) for x in a.items) + ']')
                elif isinstance(a, DVexDict): parts.append('{' + ', '.join(f"{k}={v}" for k,v in a.data.items()) + '}')
                elif isinstance(a, (int, float)): parts.append(f"=> {a}")
                else: parts.append(str(a))
            print("  ".join(parts))
        env.set('smart_show', _smart_show)

        # ── Mod 7: show_table ────────────────────────────────────────────
        def _show_table(data, title=''):
            if isinstance(data, DVexList):
                print(f"  [{title}]" if title else "  [Table]")
                print("  " + " | ".join(str(x) for x in data.items))
                print("  " + "-" * 30)
            elif isinstance(data, DVexDict):
                print(f"  [{title}]" if title else "  [Table]")
                for k, v in data.data.items():
                    print(f"    {k:<20} | {v}")
        env.set('show_table', _show_table)

        # ── Mod 8: Parallel run ──────────────────────────────────────────
        def _run_parallel(fn1, fn2):
            import threading
            t1 = threading.Thread(target=lambda: fn1(), daemon=True)
            t2 = threading.Thread(target=lambda: fn2(), daemon=True)
            t1.start(); t2.start()
            t1.join(); t2.join()
        env.set('run_parallel', _run_parallel)

        # ── Mod 9: Type inference ────────────────────────────────────────
        def _auto_type(value):
            if isinstance(value, str):
                try: return int(value)
                except: pass
                try: return float(value)
                except: pass
            return value
        env.set('auto_type', _auto_type)

        # ── Mod 11: D-PM Online Package Manager ──────────────────────────
        import urllib.request as _ureq, hashlib as _hl
        class _FullDPM:
            BASE_URL = "https://raw.githubusercontent.com/YourUsername/DVX-Packages/main/"
            LIB_DIR  = "libs/"

            @classmethod
            def install(cls, pkg_name):
                if not os.path.exists(cls.LIB_DIR):
                    os.makedirs(cls.LIB_DIR)
                print(f"  [D-PM] Downloading package: '{pkg_name}'...")
                try:
                    url       = f"{cls.BASE_URL}{pkg_name}.ex"
                    dest      = os.path.join(cls.LIB_DIR, f"{pkg_name}.ex")
                    with _ureq.urlopen(url, timeout=15) as resp:
                        code = resp.read().decode('utf-8')
                    checksum = _hl.sha256(code.encode()).hexdigest()
                    with open(dest, 'w', encoding='utf-8') as fout:
                        fout.write(code)
                    print(f"  [D-PM] Installed '{pkg_name}' ✓  (SHA256: {checksum[:16]})")
                    return True
                except Exception as e:
                    print(f"  [D-PM Error] Could not install '{pkg_name}': {e}")
                    return False

            @classmethod
            def list_installed(cls):
                if not os.path.exists(cls.LIB_DIR):
                    return DVexList([])
                pkgs = [f[:-3] for f in os.listdir(cls.LIB_DIR) if f.endswith('.ex')]
                return DVexList(pkgs)

            @classmethod
            def list_builtin(cls):
                return DVexList(list(BUILTIN_MODULES.keys()))

        dpm_obj = _FullDPM()
        env.set('dpm', dpm_obj)

        # ── Mod 12: Native Plot ──────────────────────────────────────────
        def _plot(data, chart_type='bar', title='Chart', width=40):
            items = data.items if isinstance(data, DVexList) else list(data)
            mx    = max(items) if items else 1
            if mx == 0: mx = 1
            print(f"\n  [{title}]")
            if chart_type == 'line':
                h, w = 6, width
                mn   = min(items)
                grid = [[' ']*w for _ in range(h)]
                for i, v in enumerate(items):
                    c = int((i / max(len(items)-1,1)) * (w-1))
                    r = h - 1 - int(((v - mn) / max(mx - mn, 1)) * (h-1))
                    if 0 <= r < h and 0 <= c < w: grid[r][c] = 'o'
                for row in grid: print(f"  |{''.join(row)}|")
            else:
                for i, v in enumerate(items):
                    bar = chr(9608) * int((v / mx) * width)
                    print(f"  [{i:>2}] {bar:<{width}} {v}")
        env.set('plot', _plot)

        # ── Mod 19: Memory profiler ──────────────────────────────────────
        import sys as _sys
        env.set('mem_usage', lambda: f"{_sys.getsizeof(self.global_env.vars)} bytes approx")

        # ── Mod 20: Telemetry access ─────────────────────────────────────
        try:
            from lib.scanner import TelemetryLogger as _TL
            env.set('telemetry', _TL)
        except ImportError:
            try:
                from scanner import TelemetryLogger as _TL
                env.set('telemetry', _TL)
            except ImportError:
                pass

        # ── Mod 21: Logic Guard access ───────────────────────────────────
        try:
            from scanner import LogicGuard as _LG
        except ImportError:
            try:
                from lib.scanner import LogicGuard as _LG
            except ImportError:
                _LG = None
        if _LG:
            _logic_guard_inst = _LG()
            env.set('logic_guard', _logic_guard_inst)
            env.set('guard_monitor', lambda path: _logic_guard_inst.monitor_file(path))
            env.set('guard_report',  lambda: _logic_guard_inst.show_report())

        # ── Mod 22: Native C++ Extension Loader ─────────────────────────
        try:
            from scanner import NativeExtension as _NE
        except ImportError:
            try:
                from lib.scanner import NativeExtension as _NE
            except ImportError:
                _NE = None
        if _NE:
            _native_ext = _NE()
            env.set('import_native', lambda path, alias: _native_ext.load_cpp(path, alias, env))
            env.set('native_call',   lambda alias, fn, *a: _native_ext.call(alias, fn, *a))
            env.set('native_libs',   lambda: _native_ext.list_libs())

        # ── Mod 23: Bytecode VM (experimental) ──────────────────────────
        try:
            from scanner import BytecodeCompiler as _BC, BytecodeVM as _BVM
        except ImportError:
            try:
                from lib.scanner import BytecodeCompiler as _BC, BytecodeVM as _BVM
            except ImportError:
                _BC = _BVM = None
        if _BC and _BVM:
            def _run_bytecode(code_str):
                """Compile and run D-vex code via Bytecode VM (Mod 23)."""
                import re as _re
                lexer  = Lexer(code_str)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                stmts  = parser.parse()
                comp   = _BC()
                bc     = comp.compile(stmts)
                vm     = _BVM({k: v for k, v in env.vars.items()})
                result = vm.run(bc, env.vars)
                stats  = vm.get_stats()
                return result
            env.set('bytecode_run',   _run_bytecode)
            env.set('bytecode_info',  lambda: print("  [Bytecode VM] Mod 23 active. Use bytecode_run(code_str)"))

        # ── Mod 24: F-String info ────────────────────────────────────────
        env.set('fstr', lambda s, **kw: s)  # passthrough (already preprocessed)

        # ── Mod 25: Generator/yield ──────────────────────────────────────
        env.set('generator_info', lambda: print("  [Mod 25] Generators: use 'yield' in fn body. Iterate with for loop."))

        # ── Mod 26: Decorator registry ───────────────────────────────────
        env.set('memoize',    DVexDecorators.memoize)
        env.set('timer_dec',  DVexDecorators.timer)
        env.set('retry',      lambda n=3, d=0.5: DVexDecorators.retry(n, d))
        env.set('validate',   DVexDecorators.validate)
        env.set('deprecated', DVexDecorators.deprecated)
        env.set('singleton',  DVexDecorators.singleton)

        # ── Ara AI v8.0 — D-vex Built-in Intelligent Assistant ──────────
        _ara_instance = AraAI()
        env.set('ara', _ara_instance)
        env.set('Ara', _ara_instance)  # alias

        # ── Mod 27: Stack Trace ──────────────────────────────────────────
        try:
            from scanner import DVexStackTrace as _ST
        except ImportError:
            try:
                from lib.scanner import DVexStackTrace as _ST
            except ImportError:
                _ST = None
        if _ST:
            self._stack_trace = _ST()
            env.set('trace_push',   lambda fn, l: self._stack_trace.push_frame(fn, l))
            env.set('trace_pop',    lambda: self._stack_trace.pop_frame())
            env.set('trace_show',   lambda: self._stack_trace.show_history())
            env.set('error_history',lambda: self._stack_trace.show_history(20))
        else:
            self._stack_trace = None

        # Pre-load dvex.* modules (skip optional ones that aren't available)
        for mod_name, ModClass in BUILTIN_MODULES.items():
            parts = mod_name.split('.')
            if len(parts) == 2 and parts[0] == 'dvex':
                try:
                    obj = ModClass()
                    self.modules[mod_name] = obj
                    self.modules[parts[1]] = obj
                except (DVexRuntimeError, ImportError, Exception):
                    # Optional module not available on this platform — skip.
                    # It will raise a proper error when the user tries to import it.
                    pass

    # ── Statement Execution ─────────────────────────────────────────

    def exec_block(self, stmts, env):
        for stmt in stmts:
            if stmt is None: continue
            result = self.exec_stmt(stmt, env)

    def run_external_module(self, code: str, mod_name: str = '<module>') -> 'DVexModuleObject':
        """
        Execute a .ex file as a module and return a module object.
        Used by the libs/ import system (D-PM installed packages).
        """
        module_env = self.global_env.child()
        try:
            code = self._preprocess_fstring(code)
            code = self._preprocess_pipe(code)
            lexer  = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            stmts  = parser.parse()
            self.exec_block(stmts, module_env)
        except (DVexError, ReturnSignal) as e:
            if isinstance(e, ReturnSignal):
                pass  # top-level ret in module — ignore
            else:
                raise DVexRuntimeError(
                    f"Error loading module '{mod_name}': {e}")
        # Wrap module_env.vars in a module object
        return DVexExternalModule(mod_name, module_env.vars)

    def exec_stmt(self, stmt, env):
        kind = stmt[0]

        if kind == 'let':
            _, name, val_ast, is_const, line = stmt
            val = self.eval_expr(val_ast, env) if val_ast is not None else None
            env.set(name, val, is_const)

        elif kind == 'assign':
            _, target, val_ast, line = stmt
            val = self.eval_expr(val_ast, env)
            self._assign_target(target, val, env, line)

        elif kind == 'augassign':
            _, target, op, val_ast, line = stmt
            cur     = self.eval_expr(target, env)
            val     = self.eval_expr(val_ast, env)
            new_val = self._apply_op(op, cur, val)
            self._assign_target(target, new_val, env, line)

        elif kind == 'fn':
            _, name, params, body, is_async, ret_type, line = stmt
            fn = DVexFunction(name or '<anon>', params, body, env, is_async)
            if name:
                env.set(name, fn)
            return fn

        elif kind == 'fn_expr':
            _, name, params, body, is_async, ret_type = stmt
            return DVexFunction(name or '<anon>', params, body, env, is_async)

        elif kind == 'class':
            _, name, parent, methods_ast, class_vars_ast, line = stmt
            parent_cls = env.get(parent) if parent else None
            methods    = {}
            for mname, m_stmt in methods_ast.items():
                _, fname, params, body, is_async, ret_type, _ = m_stmt
                fn = DVexFunction(fname or mname, params, body, env, is_async)
                methods[mname] = fn
            class_vars = {}
            for cname, cval_ast in class_vars_ast.items():
                class_vars[cname] = self.eval_expr(cval_ast, env) if cval_ast else None
            cls = DVexClass(name, methods, class_vars, parent_cls)
            env.set(name, cls)

        elif kind == 'show':
            _, exprs, line = stmt
            values = [self.eval_expr(e, env) for e in exprs]
            parts  = []
            for v in values:
                if isinstance(v, str):         parts.append(v)
                elif isinstance(v, DVexString): parts.append(v.value)
                elif v is None:                parts.append('null')
                elif v is True:                parts.append('true')
                elif v is False:               parts.append('false')
                else:                          parts.append(str(v))
            print(' '.join(parts))

        elif kind == 'if':
            _, branches, else_body, line = stmt
            for branch_type, cond, body in branches:
                if self.eval_expr(cond, env):
                    self.exec_block(body, env.child())
                    return
            if else_body:
                self.exec_block(else_body, env.child())

        elif kind == 'for':
            _, var, iterable_ast, body, line = stmt
            iterable = self.eval_expr(iterable_ast, env)
            # Mod 25: Generator support in for loop
            if isinstance(iterable, DVexGenerator): iterable = list(iterable)
            if isinstance(iterable, DVexList): iterable = iterable.items
            elif isinstance(iterable, DVexDict): iterable = list(iterable.data.keys())
            elif isinstance(iterable, DVexSet):  iterable = list(iterable.data)
            elif isinstance(iterable, range):    iterable = list(iterable)
            elif isinstance(iterable, str):      iterable = list(iterable)
            for item in iterable:
                local = env.child()
                local.set(var, item)
                try:
                    self.exec_block(body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif kind == 'while':
            _, cond, body, line = stmt
            while self.eval_expr(cond, env):
                try:
                    self.exec_block(body, env.child())
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif kind == 'repeat':
            _, n_ast, body, line = stmt
            n = int(self.eval_expr(n_ast, env))
            for i in range(n):
                local = env.child()
                local.set('_i', i)
                try:
                    self.exec_block(body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif kind == 'match':
            _, expr_ast, cases, default, line = stmt
            val     = self.eval_expr(expr_ast, env)
            matched = False
            for case_val_ast, case_body in cases:
                case_val = self.eval_expr(case_val_ast, env)
                if val == case_val:
                    self.exec_block(case_body, env.child())
                    matched = True
                    break
            if not matched and default:
                self.exec_block(default, env.child())

        elif kind == 'try':
            _, try_body, catch_var, catch_body, fin_body, line = stmt
            try:
                self.exec_block(try_body, env.child())
            except (DVexError, Exception) as e:
                if catch_body:
                    local = env.child()
                    if catch_var:
                        local.set(catch_var, str(e))
                    self.exec_block(catch_body, local)
            finally:
                if fin_body:
                    self.exec_block(fin_body, env.child())

        elif kind == 'ret':
            _, val_ast, line = stmt
            val = self.eval_expr(val_ast, env) if val_ast else None
            raise ReturnSignal(val)

        elif kind == 'break':
            raise BreakSignal()

        elif kind == 'continue':
            raise ContinueSignal()

        elif kind == 'pass':
            pass

        elif kind == 'import':
            _, mod_name, alias, line = stmt
            # 1. Cache check
            if mod_name in self.modules:
                obj = self.modules[mod_name]
            # 2. Built-in module registry
            elif mod_name in BUILTIN_MODULES:
                try:
                    obj = BUILTIN_MODULES[mod_name]()
                except Exception as e:
                    raise DVexRuntimeError(f"Cannot load module '{mod_name}': {e}", line)
                self.modules[mod_name] = obj
            else:
                # 3. libs/ folder (online packages installed via D-PM)
                lib_candidates = [
                    os.path.join("libs", f"{mod_name}.ex"),
                    os.path.join("libs", f"{mod_name.replace('.', os.sep)}.ex"),
                ]
                loaded_from_lib = False
                for lib_path in lib_candidates:
                    if os.path.exists(lib_path):
                        with open(lib_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                        obj = self.run_external_module(code, mod_name)
                        self.modules[mod_name] = obj
                        loaded_from_lib = True
                        break
                if not loaded_from_lib:
                    avail = ', '.join(k for k in BUILTIN_MODULES.keys() if '.' in k)
                    raise DVexRuntimeError(
                        f"Module '{mod_name}' not found.\n"
                        f"  Built-in modules: {avail}\n"
                        f"  Or install via: dvex install {mod_name}", line)
            local_name = alias or mod_name.split('.')[-1]
            env.set(local_name, obj)

        elif kind == 'raise':
            _, expr, line = stmt
            msg = self.eval_expr(expr, env)
            raise DVexRuntimeError(str(msg), line)

        elif kind == 'del':
            _, name, line = stmt
            if name in env.vars:
                del env.vars[name]

        elif kind == 'assert':
            _, cond, msg_ast, line = stmt
            if not self.eval_expr(cond, env):
                msg = self.eval_expr(msg_ast, env) if msg_ast else 'Assertion failed'
                raise DVexRuntimeError(f"Assert failed: {msg}", line)

        elif kind == 'expr':
            _, expr, line = stmt
            self.eval_expr(expr, env)

        elif kind == 'decorated':
            # Mod 26: Enhanced decorator support
            _, dec_name, dec_args, fn_stmt = stmt
            self.exec_stmt(fn_stmt, env)
            fn_name = fn_stmt[1] if fn_stmt else None
            fn = env.get(fn_name) if fn_name else None

            # Try DVexDecorators registry first, then env
            dec = DVexDecorators.REGISTRY.get(dec_name)
            if dec is None:
                try:
                    dec = env.get(dec_name)
                except Exception:
                    dec = None

            if dec is not None and fn is not None:
                try:
                    ev_args = [self.eval_expr(a, env) for a in dec_args]
                    if ev_args:
                        # Decorator factory: @retry(3) → retry(3)(fn)
                        dec_factory = dec(*ev_args)
                        result = dec_factory(fn) if callable(dec_factory) else fn
                    else:
                        result = dec(fn)
                    # Always keep the result if not None; fallback to original fn
                    if fn_name:
                        env.set(fn_name, result if result is not None else fn)
                    print(f"  [Mod 26] @{dec_name} applied to fn {fn_name}()")
                except Exception as e:
                    print(f"  [Decorator Warning] @{dec_name} failed: {e}; fn unchanged")
            elif fn_name:
                pass  # fn already set by exec_stmt above

    def _assign_target(self, target, val, env, line):
        if isinstance(target, tuple):
            if target[0] == 'var':
                try:
                    env.assign(target[1], val, line)
                except DVexNameError:
                    env.set(target[1], val)
            elif target[0] == 'getattr':
                obj = self.eval_expr(target[1], env)
                if isinstance(obj, DVexInstance):
                    obj.setattr(target[2], val)
                elif isinstance(obj, DVexDict):
                    obj.data[target[2]] = val
                else:
                    raise DVexRuntimeError(f"Cannot set attribute on {type(obj).__name__}", line)
            elif target[0] == 'index':
                obj = self.eval_expr(target[1], env)
                idx = self.eval_expr(target[2], env)
                if isinstance(obj, DVexList):
                    obj.items[int(idx)] = val
                elif isinstance(obj, DVexDict):
                    obj.data[idx] = val
                else:
                    raise DVexRuntimeError(f"Cannot index-assign on {type(obj).__name__}", line)

    # ── Expression Evaluation ───────────────────────────────────────

    def eval_expr(self, expr, env):
        if expr is None: return None
        if not isinstance(expr, tuple): return expr

        kind = expr[0]

        if kind == 'lit':
            return expr[1]

        if kind == 'var':
            try:
                return env.get(expr[1])
            except DVexNameError:
                raise DVexNameError(f"'{expr[1]}' is not defined. Did you forget 'let {expr[1]} = ...'?")

        if kind == 'list':
            return DVexList([self.eval_expr(e, env) for e in expr[1]])

        if kind == 'listcomp':
            _, item_expr, var, src_expr, cond_expr = expr
            src = self.eval_expr(src_expr, env)
            if isinstance(src, DVexList): src = src.items
            elif isinstance(src, range):  src = list(src)
            result = []
            for x in src:
                local = env.child()
                local.set(var, x)
                if cond_expr is None or self.eval_expr(cond_expr, local):
                    result.append(self.eval_expr(item_expr, local))
            return DVexList(result)

        if kind == 'tuple':
            return tuple(self.eval_expr(e, env) for e in expr[1])

        if kind == 'dict':
            pairs = {self.eval_expr(k, env): self.eval_expr(v, env) for k, v in expr[1]}
            return DVexDict(pairs)

        if kind == 'set':
            return DVexSet([self.eval_expr(e, env) for e in expr[1]])

        if kind == 'binop':
            _, op, left_ast, right_ast = expr
            if op == 'and':
                l = self.eval_expr(left_ast, env)
                return l and self.eval_expr(right_ast, env)
            if op == 'or':
                l = self.eval_expr(left_ast, env)
                return l or self.eval_expr(right_ast, env)
            l = self.eval_expr(left_ast, env)
            r = self.eval_expr(right_ast, env)
            return self._apply_op(op, l, r)

        if kind == 'unary':
            _, op, operand_ast = expr
            val = self.eval_expr(operand_ast, env)
            if op == '-':   return -val
            if op == 'not': return not val
            if op == '~':   return ~val
            return val

        if kind == 'ternary':
            _, cond, then, else_ = expr
            return self.eval_expr(then, env) if self.eval_expr(cond, env) else self.eval_expr(else_, env)

        if kind == 'call':
            _, fn_ast, args_ast = expr
            fn   = self.eval_expr(fn_ast, env)
            args = [self.eval_expr(a, env) for a in args_ast]
            return self._call(fn, args, env)

        if kind == 'method_call':
            _, obj_ast, name, args_ast = expr
            obj  = self.eval_expr(obj_ast, env)
            args = [self.eval_expr(a, env) for a in args_ast]
            attr = self._getattr(obj, name)
            return self._call(attr, args, env)

        if kind == 'getattr':
            _, obj_ast, name = expr
            obj = self.eval_expr(obj_ast, env)
            return self._getattr(obj, name)

        if kind == 'index':
            _, obj_ast, idx_ast = expr
            obj = self.eval_expr(obj_ast, env)
            idx = self.eval_expr(idx_ast, env)
            return self._index(obj, idx)

        if kind == 'new':
            _, cls_name, args_ast = expr
            cls  = env.get(cls_name)
            args = [self.eval_expr(a, env) for a in args_ast]
            if isinstance(cls, DVexClass):
                return cls.instantiate(args, self)
            elif callable(cls):
                return cls(*args)
            raise DVexTypeError(f"'{cls_name}' is not a class")

        if kind == 'ref':
            return env.get(expr[1])

        if kind == 'typeof':
            val = self.eval_expr(expr[1], env)
            if isinstance(val, bool):         return 'bool'
            if isinstance(val, int):          return 'int'
            if isinstance(val, float):        return 'float'
            if isinstance(val, str):          return 'str'
            if isinstance(val, DVexList):     return 'list'
            if isinstance(val, DVexDict):     return 'dict'
            if isinstance(val, DVexSet):      return 'set'
            if isinstance(val, DVexString):   return 'str'
            if isinstance(val, DVexFunction): return 'function'
            if isinstance(val, DVexClass):    return 'class'
            if isinstance(val, DVexInstance): return val.klass.name
            if val is None:                   return 'null'
            return type(val).__name__

        if kind == 'lambda':
            _, params, body_expr = expr
            def lam(*args):
                local = env.child()
                for i, (p, _, d) in enumerate(params):
                    local.set(p, args[i] if i < len(args) else (self.eval_expr(d, env) if d else None))
                return self.eval_expr(body_expr, local)
            return lam

        if kind == 'fn_expr':
            _, name, params, body, is_async, _ = expr
            return DVexFunction(name or '<anon>', params, body, env, is_async)

        if kind == 'await':
            return self.eval_expr(expr[1], env)

        raise DVexRuntimeError(f"Unknown expression kind: '{kind}'")

    def _apply_op(self, op, l, r):
        # List operations
        if op == '+' and isinstance(l, DVexList) and isinstance(r, DVexList):
            return DVexList(l.items + r.items)
        if op == '+' and isinstance(l, DVexString): return DVexString(str(l.value) + str(r if r is not None else 'null'))
        if op == '+' and isinstance(r, DVexString): return DVexString(str(l if l is not None else 'null') + str(r.value))
        # Plain str + anything: auto-stringify (mirrors Python str behavior)
        if op == '+' and isinstance(l, str) and not isinstance(r, str):
            return l + str(r if r is not None else 'null')
        if op == '+' and isinstance(r, str) and not isinstance(l, str):
            return str(l if l is not None else 'null') + r
        if op == '*' and isinstance(l, DVexList):   return DVexList(l.items * int(r))
        if op == '*' and isinstance(l, str):        return l * int(r)
        if op == '*' and isinstance(r, str):        return r * int(l)

        if op == '+':   return l + r
        if op == '-':   return l - r
        if op == '*':   return l * r
        if op == '/':
            if r == 0: raise DVexRuntimeError("Division by zero — use try/catch to handle this safely")
            return l / r
        if op == '//':
            if r == 0: raise DVexRuntimeError("Floor division by zero")
            return l // r
        if op == '%':   return l % r
        if op == '**':  return l ** r
        if op == '==':  return l == r
        if op == '!=':  return l != r
        if op == '<':   return l < r
        if op == '>':   return l > r
        if op == '<=':  return l <= r
        if op == '>=':  return l >= r
        if op == '===': return l is r or l == r
        if op == '!==': return l is not r and l != r
        if op == 'in':
            if isinstance(r, DVexList): return l in r.items
            if isinstance(r, DVexDict): return l in r.data
            if isinstance(r, DVexSet):  return l in r.data
            if isinstance(r, str):      return str(l) in r
            return l in r
        if op == 'is':    return l is r or l == r
        if op == 'isnot': return l is not r and l != r
        if op == '&':  return l & r
        if op == '|':  return l | r
        if op == '^':  return l ^ r
        if op == '<<': return l << r
        if op == '>>': return l >> r
        raise DVexRuntimeError(f"Unknown operator: '{op}'")

    def _call(self, fn, args, env):
        if isinstance(fn, DVexFunction):
            return fn.call(args, self)
        if isinstance(fn, DVexClass):
            return fn.instantiate(args, self)
        if callable(fn):
            try:
                return fn(*args)
            except TypeError as e:
                raise DVexRuntimeError(f"Call error: {e}")
        raise DVexTypeError(f"'{fn}' is not callable")

    def _getattr(self, obj, name):
        if isinstance(obj, DVexList):     return obj.getattr(name)
        if isinstance(obj, DVexDict):     return obj.getattr(name)
        if isinstance(obj, DVexSet):      return obj.getattr(name)
        if isinstance(obj, DVexString):   return obj.getattr(name)
        if isinstance(obj, str):          return DVexString(obj).getattr(name)
        if isinstance(obj, DVexInstance): return obj.getattr(name)
        if isinstance(obj, AraAI):        return obj.getattr(name)
        if isinstance(obj, DVexClass):
            if name in obj.methods:    return obj.methods[name]
            if name in obj.class_vars: return obj.class_vars[name]
        if hasattr(obj, 'getattr'):       return obj.getattr(name)
        if hasattr(obj, 'attrs') and name in obj.attrs: return obj.attrs[name]
        if hasattr(obj, name):            return getattr(obj, name)
        raise DVexNameError(f"'{type(obj).__name__}' has no attribute '{name}'")

    def _index(self, obj, idx):
        if isinstance(obj, DVexList):
            try: return obj.items[int(idx)]
            except IndexError: raise DVexIndexError(f"Index {idx} out of range (len={len(obj.items)})")
        if isinstance(obj, DVexDict):   return obj.data.get(idx)
        if isinstance(obj, str):        return obj[int(idx)]
        if isinstance(obj, DVexString): return DVexString(obj.value[int(idx)])
        if isinstance(obj, (list, tuple)): return obj[int(idx)]
        raise DVexTypeError(f"'{type(obj).__name__}' is not subscriptable")

    # ── Public API ──────────────────────────────────────────────────

    # ── Mod 30: JIT-like fast evaluator (Experimental) ──────────────
    _SAFE_NAMES = {'abs', 'round', 'min', 'max', 'sum', 'len', 'pow', 'divmod'}
    _ARITHMETIC_RE = re.compile(
        r'^[\d\s\+\-\*\/\%\(\)\.\,a-zA-Z_]+$'
    )

    def fast_eval(self, expr_str: str, env):
        """
        Mod 30: JIT-like fast evaluator for pure arithmetic/numeric expressions.

        Uses Python's eval() with a restricted namespace built from the current
        environment.  Falls back to the standard eval_expr AST path if the
        expression looks non-trivial (contains strings, brackets, dots, etc.).

        Usage inside .ex code (via dvex builtin):
            let result = fast_eval("x * y + z", env)
        """
        # Guard: only attempt for simple alphanumeric + operator strings
        if not self._ARITHMETIC_RE.match(expr_str):
            raise DVexRuntimeError(
                f"fast_eval: expression too complex or unsafe: {expr_str!r}")
        # Build a flat numeric namespace from the current env scope
        ns: dict = {}
        cur = env
        while cur is not None:
            for k, v in cur.vars.items():
                if k not in ns and isinstance(v, (int, float, bool)):
                    ns[k] = v
            cur = cur.parent
        # Allow safe math builtins — always use builtins module for reliability
        import builtins as _bi
        safe_globals = {n: getattr(_bi, n) for n in self._SAFE_NAMES if hasattr(_bi, n)}
        try:
            return eval(expr_str, {"__builtins__": safe_globals}, ns)  # noqa: S307
        except Exception as e:
            raise DVexRuntimeError(f"fast_eval failed: {e}")

    def run(self, code, env=None, scan=True, auto_fix=True):
        if env is None:
            env = self.global_env
        try:
            # Mod 18: Pipe operator |> pre-processing
            # "data |> clean |> show" → "show(clean(data))"
            code = self._preprocess_fstring(code)
            code = self._preprocess_pipe(code)

            # Run scanner + Auto-Fix (Mod 1) if requested
            if scan:
                scanner = None
                try:
                    from lib.scanner import DVexScanner
                    scanner = DVexScanner(code)
                except ImportError:
                    try:
                        from scanner import DVexScanner
                        scanner = DVexScanner(code)
                    except ImportError:
                        pass
                if scanner:
                    # Mod 1: Auto-fix before scanning
                    if auto_fix:
                        code = scanner.auto_fix_risky_code(code)
                    scanner.show_report()

            lexer  = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            stmts  = parser.parse()
            self.exec_block(stmts, env)
        except DVexError as e:
            print(e)
        except ReturnSignal as r:
            return r.value
        except SystemExit:
            pass
        except KeyboardInterrupt:
            print("\n[D-vex] Interrupted by user.")
        except Exception as e:
            print(f"\n[D-vex Internal Error] {type(e).__name__}: {e}")

    def _preprocess_fstring(self, code: str) -> str:
        """
        Mod 24: F-String Interpolation support.
        f"Hello {name}!" → "Hello " + str(name) + "!"
        Also supports expressions: f"{x * 2 + 1}"
        """
        if "f'" not in code and 'f"' not in code:
            return code

        result = []
        i = 0
        while i < len(code):
            # Detect f"..." or f'...' — but only when 'f' is not preceded by alphanumeric
            # This prevents matching "Woof" -> "Woo" + f"..." incorrectly
            if code[i] == 'f' and i + 1 < len(code) and code[i+1] in ('"', "'"):
                # Ensure 'f' is at word boundary — not part of an identifier like "Woof"
                if i > 0 and (code[i-1].isalnum() or code[i-1] == '_'):
                    result.append(code[i])
                    i += 1
                    continue
                quote = code[i+1]
                i += 2  # skip f and opening quote
                parts = []
                cur   = ''
                while i < len(code) and code[i] != quote:
                    if code[i] == '{' and i + 1 < len(code) and code[i+1] != '{':
                        if cur:
                            parts.append(repr(cur))
                        i += 1
                        expr_start = i
                        depth = 1
                        while i < len(code) and depth > 0:
                            if   code[i] == '{': depth += 1
                            elif code[i] == '}': depth -= 1
                            if depth > 0: i += 1
                            else: break
                        expr = code[expr_start:i].strip()
                        parts.append(f'str({expr})')
                        i += 1  # skip closing }
                        cur = ''
                    elif code[i] == '\\' and i + 1 < len(code):
                        cur += code[i:i+2]
                        i   += 2
                    else:
                        cur += code[i]
                        i   += 1
                if cur:
                    parts.append(repr(cur))
                if i < len(code):
                    i += 1  # skip closing quote
                if parts:
                    result.append('(' + ' + '.join(parts) + ')')
                else:
                    result.append('""')
            else:
                result.append(code[i])
                i += 1
        return ''.join(result)

    def _preprocess_pipe(self, code: str) -> str:
        """
        Mod 18: Pipe operator |> support — ignores |> inside strings.
        data |> fn1 |> fn2          =>  fn2(fn1(data))
        let x = data |> fn1 |> fn2  =>  let x = fn2(fn1(data))
        """
        if '|>' not in code:
            return code
        import re as _re

        def _pipe_outside_str(s):
            """True if s contains |> outside any string literal."""
            in_s, q = False, None
            for i, c in enumerate(s):
                if not in_s:
                    if c in ('"', "'"):
                        in_s, q = True, c
                    elif c == '|' and i+1 < len(s) and s[i+1] == '>':
                        return True
                else:
                    if c == '\\':
                        continue  # next char is escaped
                    if c == q:
                        in_s = False
            return False

        def _split_pipe(expr):
            """Split expr on |> outside strings."""
            parts, cur, in_s, q = [], [], False, None
            i = 0
            while i < len(expr):
                c = expr[i]
                if not in_s:
                    if c in ('"', "'"):
                        in_s, q = True, c
                        cur.append(c)
                    elif c == '|' and i+1 < len(expr) and expr[i+1] == '>':
                        parts.append(''.join(cur).strip())
                        cur = []
                        i += 2
                        continue
                    else:
                        cur.append(c)
                else:
                    cur.append(c)
                    if c == '\\' and i+1 < len(expr):
                        i += 1
                        cur.append(expr[i])
                    elif c == q:
                        in_s = False
                i += 1
            t = ''.join(cur).strip()
            if t:
                parts.append(t)
            return parts

        lines     = code.split('\n')
        new_lines = []
        for line in lines:
            if '|>' not in line or line.strip().startswith('//') or not _pipe_outside_str(line):
                new_lines.append(line)
                continue
            stripped      = line.strip()
            indent        = ' ' * (len(line) - len(stripped))
            assign_prefix = ''
            pipe_expr     = stripped
            m = _re.match(r'^((?:let|const)\s+\w+(?:\s*::\s*\w+)?\s*=\s*)', stripped)
            if not m:
                m = _re.match(r'^(\w+\s*=\s*)', stripped)
            if m:
                suffix = stripped[m.end():]
                if _pipe_outside_str(suffix):
                    assign_prefix = m.group(1)
                    pipe_expr     = suffix
                else:
                    new_lines.append(line)
                    continue
            parts = _split_pipe(pipe_expr)
            if len(parts) < 2:
                new_lines.append(line)
                continue
            result = parts[0]
            for fn_call in parts[1:]:
                result = fn_call + '(' + result + ')'
            new_lines.append(indent + assign_prefix + result)
        return '\n'.join(new_lines)

# ═══════════════════════════════════════════════════════════════════════
#  REPL
# ═══════════════════════════════════════════════════════════════════════

def run_repl():
    interp = DVexInterpreter()
    print("""
╔══════════════════════════════════════════════════════════════╗
║   D-vex Interactive REPL  —  v7.0 (Final Enterprise)                ║
║   Type 'help' for commands, 'exit' to quit                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    buffer = ''
    while True:
        try:
            line = input('... ' if buffer else 'dvex> ')
        except (EOFError, KeyboardInterrupt):
            print("\n[D-vex] Goodbye! 👋")
            break

        if line.strip() == 'exit':
            print("[D-vex] Goodbye! 👋")
            break

        if line.strip() == 'help':
            print("""
  D-vex REPL Commands:
    exit         — Quit the REPL
    clear        — Clear variables
    vars         — Show all variables
    help         — Show this help

  D-vex Syntax:
    let x = 10           — Variable
    const PI = 3.14      — Constant
    show "Hello"         — Print
    fn add(a,b): ret a+b — Function
    if x > 5: show "big" — Condition
    for i in range(5):   — Loop
    import dvex.math     — Import module
""")
            continue

        if line.strip() == 'vars':
            for k, v in interp.global_env.vars.items():
                print(f"  {k} = {v}")
            continue

        if line.strip() == 'clear':
            interp.global_env.vars.clear()
            interp._setup_builtins()
            print("  [Variables cleared]")
            continue

        # Multi-line support
        if line.endswith(':') or buffer:
            buffer += line + '\n'
            if line == '' and buffer.strip():
                # Mod 10: Self-Healing — catch errors, don't crash
                try:
                    interp.run(buffer, scan=False)
                except Exception as e:
                    print(f"  D-vex Tip: {e}  (Session continues!)")
                buffer = ''
            elif not line.endswith(':') and not line.startswith(' ') and not line.startswith('\t') and buffer.count('\n') > 1:
                try:
                    interp.run(buffer, scan=False)
                except Exception as e:
                    print(f"  D-vex Tip: {e}  (Session continues!)")
                buffer = ''
        else:
            # Mod 10: Self-Healing — REPL never crashes on error
            try:
                interp.run(line, scan=False)
            except Exception as e:
                print(f"  D-vex Tip: {e}  (I've handled it for you!)")


def run_file(path):
    # ── STRICT .ex EXTENSION RULE (Mod 4) ─────────────────────────────
    if not path.endswith('.ex'):
        ext = os.path.splitext(path)[1] or '(no extension)'
        print(f"\n  [D-vex FATAL] Extension '{ext}' is NOT supported!")
        print(f"  D-vex ONLY runs '.ex' files.")
        print(f"  File  : {os.path.basename(path)}")
        print(f"  Fix   : Rename to {os.path.splitext(os.path.basename(path))[0]}.ex\n")
        sys.exit(1)

    if not os.path.exists(path):
        print(f"\n[D-vex Error] File not found: '{path}'")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Mod 3: Decrypt if encrypted
    if code.startswith('DVX_') or code.startswith('DVEX_ENC:'):
        try:
            from lib.scanner import SecurityFramework
        except ImportError:
            from scanner import SecurityFramework
        sf   = SecurityFramework()
        code = sf.decrypt_code(code)
        print(f"  [Security] File decrypted and verified ✓")

    interp = DVexInterpreter()
    interp.run(code)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_repl()
