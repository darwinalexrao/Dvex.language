#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║   D-VEX PROGRAMMING LANGUAGE (DVX) — CLI LAUNCHER v5.0 (Enterprise)    ║
║   Ecosystem: HTTP │ SQL │ AI │ BYTECODE VM │ ONLINE D-PM │ TEST        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

def _import_interpreter():
    try:
        from dvex_interpreter import run_file, run_repl, Lexer, Parser
        return run_file, run_repl, Lexer, Parser
    except ImportError as e:
        print(f"  [D-vex Fatal] Cannot load interpreter: {e}"); sys.exit(1)

def _import_scanner():
    try:
        from scanner import DVexScanner, BytecodeCompiler
        return DVexScanner, BytecodeCompiler
    except ImportError as e:
        print(f"  [D-vex Fatal] Cannot load scanner: {e}"); sys.exit(1)

BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║   D-VEX PROGRAMMING LANGUAGE (DVX) — v5.0 Enterprise                   ║
║   Ecosystem: HTTP │ SQL │ UI │ CSV │ Crypto │ Env │ Regex               ║
║              Net  │ OS  │ AI │ Test │ Bytecode VM │ D-PM Online        ║
╚══════════════════════════════════════════════════════════════════════════╝"""

HELP_TEXT = """
COMMANDS:
  run <file.ex>          Execute a .ex file.
  scan <file.ex>         Run security & logic vulnerability scanner.
  install <package>      Download & install a package from D-PM repo.
  bytecode <file.ex>     Show optimized bytecode disassembly.
  docgen <file.ex>       Auto-generate HTML + Markdown API reference docs.
  repl                   Start interactive D-vex shell.
  version                Show version and active module list.
  help                   Show this help.

STANDARD MODULES:
  dvex.math  dvex.io    dvex.time  dvex.json  dvex.ai    dvex.data
  dvex.sys   dvex.http  dvex.sql   dvex.ui    dvex.csv   dvex.crypto
  dvex.env   dvex.regex dvex.net   dvex.os    dvex.test
"""

def _require_file(path):
    if not path:
        print("  [D-vex Error] File path missing."); sys.exit(1)
    if not path.endswith('.ex'):
        ext = os.path.splitext(path)[1] or '(no extension)'
        print(f"  [D-vex Error] Extension '{ext}' not supported. Only .ex files allowed.")
        sys.exit(1)
    if not os.path.exists(path):
        print(f"  [D-vex Error] File not found: '{path}'"); sys.exit(1)
    return path

def cmd_run(args):
    path = _require_file(args[0] if args else '')
    run_file, run_repl, Lexer, Parser = _import_interpreter()
    run_file(path)

def cmd_scan(args):
    path = _require_file(args[0] if args else '')
    DVexScanner, BytecodeCompiler = _import_scanner()
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    try:
        scanner = DVexScanner(code, filepath=path)
        scanner.show_report()
    except Exception as e:
        print(f"  [Scanner Error] {e}")

def cmd_install(args):
    if not args:
        print("  [D-vex Error] Package name missing."); sys.exit(1)
    pkg = args[0]
    import urllib.request, hashlib
    LIB_DIR  = "libs"
    BASE_URL = "https://raw.githubusercontent.com/YourUsername/DVX-Packages/main/"
    os.makedirs(LIB_DIR, exist_ok=True)
    print(f"  [D-PM] Downloading '{pkg}'...")
    try:
        url  = f"{BASE_URL}{pkg}.ex"
        dest = os.path.join(LIB_DIR, f"{pkg}.ex")
        with urllib.request.urlopen(url, timeout=15) as resp:
            code = resp.read().decode('utf-8')
        checksum = hashlib.sha256(code.encode()).hexdigest()
        with open(dest, 'w', encoding='utf-8') as fout:
            fout.write(code)
        print(f"  [D-PM] Installed '{pkg}' -> {dest}  (SHA256: {checksum[:16]})")
        print(f"  [D-PM] Use it:  import {pkg}")
    except Exception as e:
        print(f"  [D-PM Error] Failed: {e}")

def cmd_bytecode(args):
    path = _require_file(args[0] if args else '')
    run_file, run_repl, Lexer, Parser = _import_interpreter()
    DVexScanner, BytecodeCompiler = _import_scanner()
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    try:
        tokens = Lexer(code).tokenize()
        stmts  = Parser(tokens).parse()
        comp   = BytecodeCompiler()
        bc     = comp.compile(stmts)   # optimizer called inside compile()
        print(f"\n  File: {path}  |  Optimized instructions: {len(bc)}")
        print(comp.disassemble())
    except Exception as e:
        print(f"  [Bytecode Error] {e}")

def cmd_repl(_args):
    run_file, run_repl, Lexer, Parser = _import_interpreter()
    run_repl()

def cmd_docgen(args):
    path = _require_file(args[0] if args else '')
    DVexScanner, BytecodeCompiler = _import_scanner()
    try:
        from scanner import AdvancedDocGen
        AdvancedDocGen.auto_doc(path)
        base = path.replace('.ex', '')
        print(f"  [DocGen] HTML: {base}_docs.html | Markdown: {base}_docs.md")
    except Exception as e:
        print(f"  [DocGen Error] {e}")

def cmd_version(_args):
    print(BANNER)
    rows = [
        ("Version",    "D-vex v5.0 (Enterprise Edition)"),
        ("Extension",  ".ex (strictly enforced)"),
        ("Engine",     "Tree-walk Interpreter + Bytecode VM (Mod 23)"),
        ("Optimizer",  "Peephole + Constant Folding + Jump Chain (Mod BC)"),
        ("Modules",    "dvex.math  dvex.io  dvex.time  dvex.json  dvex.ai"),
        ("",           "dvex.data  dvex.sys  dvex.http  dvex.sql  dvex.ui"),
        ("",           "dvex.csv  dvex.crypto  dvex.env  dvex.regex"),
        ("",           "dvex.net  dvex.os  dvex.test"),
        ("Decorators", "@memoize  @timer  @retry  @validate  @deprecated"),
        ("Features",   "Generators | F-Strings | Pipe |> | Pattern Match"),
        ("Security",   "Logic Guard (Mod 21) | Stack Trace (Mod 27)"),
        ("D-PM",       "Online package manager  (libs/ folder)"),
    ]
    for label, val in rows:
        lbl = f"{label:<14}" if label else ' ' * 14
        print(f"  {lbl}: {val}")
    print()

def cmd_help(_args):
    print(BANNER)
    print(HELP_TEXT)

COMMANDS = {
    'run':      cmd_run,
    'scan':     cmd_scan,
    'install':  cmd_install,
    'bytecode': cmd_bytecode,
    'bc':       cmd_bytecode,
    'docgen':   cmd_docgen,
    'doc':      cmd_docgen,
    'repl':     cmd_repl,
    'version':  cmd_version,
    'ver':      cmd_version,
    'help':     cmd_help,
    '--help':   cmd_help,
    '-h':       cmd_help,
}

def main():
    if len(sys.argv) < 2:
        print(BANNER); print(HELP_TEXT); return
    cmd  = sys.argv[1].lower()
    rest = sys.argv[2:]
    if cmd in COMMANDS:
        COMMANDS[cmd](rest)
    else:
        print(f"  [D-vex] Unknown command: '{cmd}'")
        print(HELP_TEXT)

if __name__ == "__main__":
    main()
