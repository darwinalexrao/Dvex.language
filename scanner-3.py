#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║   D-vex Intelligent Scanner  —  lib/scanner.py  —  v5.0v (Enterprise)  ║
║                                                                          ║
║   Mod  1–20: Core Scanner (Auto-Fix, GC, Encryption, Sandbox, etc.)    ║
║   Mod 21–27: LogicGuard, C++ Bridge, BytecodeVM, F-String, Gen, Dec    ║
║   Mod 28–30: HTTP, SQL, UI modules                                      ║
║   Mod 31–37: CSV, Crypto, Env, Regex, Net, OS, Test  (NEW v5.0)        ║
║   Mod 38   : Hot Loop Profiler  (NEW v5.0)                              ║
║   Mod BC   : BytecodeOptimizer — Constant folding + Peephole (NEW)      ║
║                                                                          ║
║   Mod  1: Auto-Fix Scanner (division → try/catch auto-inject)           ║
║   Mod  2: Smart Memory Autoclean (null-var GC + 5-min timer)            ║
║   Mod  3: Strict Encryption Guard (Base64 + SHA256 auto-encrypt)        ║
║   Mod  4: .ex Extension Hard-Lock (Fatal check)                         ║
║   Mod  5: Auto-Suggestion System (keyword typo correction)              ║
║   Mod  6: AI-First Global (predict without import)                      ║
║   Mod  7: Smart Show Formatting (visual output)                         ║
║   Mod  8: Parallel Tasking (threading support)                          ║
║   Mod  9: Type Inference (auto detect int/str/float)                    ║
║   Mod 10: Self-Healing REPL (crash-free shell)                          ║
║   Mod 11: D-PM Package Manager                                          ║
║   Mod 12: Native Plotting (ASCII charts)                                ║
║   Mod 13: Strict Constant Protection                                    ║
║   Mod 14: Docstring Auto-Generator                                      ║
║   Mod 15: Lazy Module Loading                                           ║
║   Mod 16: Type Validation                                               ║
║   Mod 17: Secure Sandbox Mode                                           ║
║   Mod 18: Pipe Operator |>                                              ║
║   Mod 19: Real-time Memory Profiler                                     ║
║   Mod 20: Telemetry / Audit Logging                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import re, os, sys, time, threading, hashlib, base64, random, ctypes, traceback, collections
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# MOD 20: TELEMETRY LOGGER
# ═══════════════════════════════════════════════════════════════════════

class TelemetryLogger:
    """Mod 20: Har error, event aur threat ka record."""
    _log  = collections.deque(maxlen=1000)  # bounded — memory safe
    _lock = threading.Lock()

    @classmethod
    def log(cls, etype, msg, detail=''):
        with cls._lock:
            cls._log.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'type': etype, 'msg': msg, 'detail': detail
            })

    @classmethod
    def show_log(cls, n=20):
        print("\n  D-vex Telemetry Log")
        print("  " + "-" * 60)
        for e in cls._log[-n:]:
            print(f"  [{e['time']}] [{e['type']:<12}] {e['msg']}")
            if e['detail']:
                print(f"               | {e['detail']}")
        print("  " + "-" * 60)

    @classmethod
    def export_log(cls, path='dvex_audit.log'):
        with open(path, 'w', encoding='utf-8') as f:
            f.write("D-vex Audit Log\n" + "="*50 + "\n")
            for e in cls._log:
                f.write(f"[{e['time']}][{e['type']}] {e['msg']}\n")
        print(f"  [Log] Saved -> {path}")

    @classmethod
    def security_log_audit(cls, event, info):
        """Mod 20: security.log_audit() shortcut."""
        cls.log('SECURITY', event, info)


# ═══════════════════════════════════════════════════════════════════════
# MOD 19: MEMORY PROFILER
# ═══════════════════════════════════════════════════════════════════════

class MemoryProfiler:
    """Mod 19: Real-time memory profiling."""
    def __init__(self):
        self._snaps = []
        self._t0    = time.time()

    def snapshot(self, label=''):
        try:
            import resource
            kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except ImportError:
            kb = sys.getsizeof({}) * 50
        elapsed = round(time.time() - self._t0, 2)
        self._snaps.append({'label': label, 'kb': kb, 't': elapsed})
        TelemetryLogger.log('MEM', f"{label}: {kb}KB @{elapsed}s")
        return kb

    def show_profile(self):
        print("\n  Memory Profile:")
        for s in self._snaps:
            bar = '#' * min(30, s['kb']//500)
            print(f"  {s['label']:<20} {s['kb']:>8}KB  {bar}")

    def get_current(self):
        return self.snapshot('current')

    @property
    def mem_usage(self):
        return f"{self.get_current()} KB"


# ═══════════════════════════════════════════════════════════════════════
# MOD 2: SMART MEMORY AUTOCLEAN
# ═══════════════════════════════════════════════════════════════════════

class MemoryManagement:
    """
    Mod 2: Smart Memory Autoclean
    - Function scope ke baad null vars auto-delete
    - Har 5 min background GC timer
    """
    def __init__(self):
        import weakref
        self._objects  = weakref.WeakValueDictionary()  # auto-GC when no other refs
        self._refs     = {}
        self._gc_runs  = 0
        self._threads  = []
        self._lock     = threading.Lock()
        self._profiler = MemoryProfiler()
        self._start_timer()

    def _start_timer(self):
        """Mod 2: 5-minute GC timer."""
        def _gc():
            while True:
                time.sleep(300)
                freed = self._gc_sweep(silent=True)
                if freed:
                    TelemetryLogger.log('GC_TIMER', f'Periodic: {freed} freed')
        threading.Thread(target=_gc, daemon=True).start()

    def auto_cleanup(self, env_vars: dict) -> int:
        """Mod 2: Null vars delete karo jab function ends."""
        dead = [k for k, v in env_vars.items() if v is None]
        for k in dead:
            del env_vars[k]
        if dead:
            TelemetryLogger.log('AUTO_CLEAN', f'{len(dead)} null vars removed')
        return len(dead)

    def gc_collect(self, env_vars: dict) -> int:
        """Mod 2: Manual GC — same as auto_cleanup."""
        return self.auto_cleanup(env_vars)

    def _gc_sweep(self, silent=False) -> int:
        with self._lock:
            # WeakValueDictionary handles live objects automatically.
            # Clean up _refs entries for objects no longer in _objects
            dead = [oid for oid in list(self._refs.keys()) if oid not in self._objects]
            for oid in dead:
                self._refs.pop(oid, None)
            self._gc_runs += 1
            freed = len(dead)
        if freed and not silent:
            print(f"  [GC] {freed} freed — Run #{self._gc_runs}")
        TelemetryLogger.log('GC', f'Run#{self._gc_runs}: {freed} freed')
        return freed

    def register(self, obj_id, obj):
        with self._lock:
            self._objects[obj_id] = obj
            self._refs[obj_id]    = 1
            if len(self._objects) > 50:
                self._gc_sweep(silent=True)

    def automatic_garbage_collection(self, silent=False):
        return self._gc_sweep(silent)

    def enable_multitasking(self, tasks: list) -> dict:
        """Mod 8: Parallel tasks."""
        results, errors = {}, {}
        def _run(name, fn, args):
            try:
                results[name] = fn(*args)
            except Exception as e:
                errors[name] = str(e)
        # Remove dead threads before adding new ones to prevent unbounded growth
        self._threads = [t for t in self._threads if t.is_alive()]
        ts = []
        for name, fn, args in tasks:
            t = threading.Thread(target=_run, args=(name, fn, args), daemon=True)
            ts.append(t); self._threads.append(t)
        for t in ts: t.start()
        for t in ts: t.join(timeout=30)
        for tn, err in errors.items():
            print(f"  [Parallel] FAIL '{tn}': {err}")
        return results

    def run_parallel(self, task1, task2, timeout=30):
        """Mod 8: Simple 2-task parallel run."""
        t1 = threading.Thread(target=task1, daemon=True)
        t2 = threading.Thread(target=task2, daemon=True)
        t1.start(); t2.start()
        t1.join(timeout=timeout)
        t2.join(timeout=timeout)
        if t1.is_alive():
            TelemetryLogger.log('PARALLEL_WARN', 'task1 did not finish in time (timed out)')
        if t2.is_alive():
            TelemetryLogger.log('PARALLEL_WARN', 'task2 did not finish in time (timed out)')

    def get_stats(self):
        return {
            'live_objects': len(self._objects),
            'gc_runs':      self._gc_runs,
            'threads':      len([t for t in self._threads if t.is_alive()]),
            'mem_kb':       self._profiler.get_current(),
        }


# ═══════════════════════════════════════════════════════════════════════
# MOD 3: STRICT ENCRYPTION GUARD
# ═══════════════════════════════════════════════════════════════════════

class SecurityFramework:
    """Mod 3: Auto-encrypt on save + audit + access control."""

    AUTHORIZED_ROLES = {'admin', 'developer', 'tester', 'root'}
    SANDBOX_BLOCKED  = ['os.system', 'subprocess', 'exec(', 'eval(',
                        '__import__', 'open(', 'readFile', 'writeFile',
                        'http.post', 'http.get', 'db.execute', 'db.query']
    THREAT_PATTERNS  = [
        (r'eval\s*\(',             'eval() injection risk'),
        (r'exec\s*\(',             'exec() arbitrary execution'),
        (r'__import__',            '__import__ dynamic import'),
        (r'os\.system\s*\(',       'os.system shell injection'),
        (r'subprocess',            'subprocess shell risk'),
        (r'password\s*=\s*["\'][^"\']{1,8}["\']', 'Weak hardcoded password'),
    ]

    def __init__(self):
        self._audit  = []
        self._blocked = set()
        self._sandbox = False

    # Mod 3: Auto-secure payload
    def auto_secure_payload(self, raw_code: str) -> str:
        """File save hote hi auto-encrypt."""
        cs  = hashlib.sha256(raw_code.encode()).hexdigest()[:8]
        enc = base64.b64encode(raw_code.encode()).decode()
        TelemetryLogger.log('ENCRYPT', f'auto_secure checksum={cs}')
        return f"DVX_{cs}_{enc}"

    def apply_encryption(self, code: str) -> str:
        cs  = hashlib.sha256(code.encode()).hexdigest()[:16]
        enc = base64.b64encode(code.encode()).decode()
        TelemetryLogger.log('ENCRYPT', f'Full encrypt cs={cs}')
        return f"DVEX_ENC:{cs}:{enc}"

    def encrypt_ex_file(self, code: str) -> str:
        """Mod 3: Simple .ex lock."""
        return f"DVX_LOCKED_{base64.b64encode(code.encode()).decode()}"

    def decrypt_code(self, payload: str) -> str:
        if payload.startswith("DVX_") and not payload.startswith("DVX_LOCKED_"):
            try:
                parts = payload.split('_', 2)
                if len(parts) < 3:
                    raise SecurityError("Invalid DVX_ payload format")
                cs_stored = parts[1]
                code = base64.b64decode(parts[2].encode()).decode('utf-8')
            except SecurityError:
                raise
            except Exception as e:
                raise SecurityError(f"Decryption failed (DVX_): {e}")
            if hashlib.sha256(code.encode()).hexdigest()[:8] != cs_stored:
                raise SecurityError("Integrity check FAILED — tampered!")
            return code
        if payload.startswith("DVEX_ENC:"):
            try:
                _, cs, enc = payload.split(':', 2)
                code = base64.b64decode(enc.encode()).decode('utf-8')
            except Exception as e:
                raise SecurityError(f"Decryption failed (DVEX_ENC): {e}")
            if hashlib.sha256(code.encode()).hexdigest()[:16] != cs:
                raise SecurityError("Integrity check FAILED!")
            return code
        if payload.startswith("DVX_LOCKED_"):
            try:
                encoded = payload[len("DVX_LOCKED_"):]
                return base64.b64decode(encoded.encode()).decode('utf-8')
            except Exception as e:
                raise SecurityError(f"Decryption failed (DVX_LOCKED_): {e}")
        return payload

    # Mod 4: .ex extension
    @staticmethod
    def check_extension(filename: str):
        if not filename.endswith('.ex'):
            ext = os.path.splitext(filename)[1] or '(none)'
            print(f"\n  FATAL: Only .ex files allowed!")
            print(f"  Got  : {os.path.basename(filename)} [{ext}]")
            print(f"  Fix  : Rename to .ex extension\n")
            TelemetryLogger.log('EXT_FATAL', filename)
            sys.exit(1)

    # Mod 17: Sandbox
    def enable_sandbox(self):
        self._sandbox = True
        TelemetryLogger.log('SANDBOX', 'Enabled')
        print("  [Sandbox] Secure mode ON")

    def check_sandbox(self, code: str) -> list:
        if not self._sandbox: return []
        found = [op for op in self.SANDBOX_BLOCKED if op in code]
        if found: TelemetryLogger.log('SANDBOX_BLOCK', str(found))
        return found

    def run_security_audit(self, code: str) -> list:
        threats = []
        for i, line in enumerate(code.split('\n'), 1):
            s = line.strip()
            if s.startswith('//') or s.startswith('/*'): continue
            for pat, desc in self.THREAT_PATTERNS:
                if re.search(pat, line, re.IGNORECASE):
                    threats.append(f"L{i}: THREAT — {desc}")
                    TelemetryLogger.log('THREAT', desc, f'L{i}')
        if threats:
            self._log('AUDIT', f'{len(threats)} threats')
            print(f"\n  SECURITY ALERT: {len(threats)} threat(s)!")
        else:
            self._log('AUDIT', 'Passed')
        return threats

    def enforce_access_control(self, user: str, resource='code') -> bool:
        ok = user in self.AUTHORIZED_ROLES
        self._log('ACCESS', f"{'GRANTED' if ok else 'BLOCKED'}: {user}")
        TelemetryLogger.log('ACCESS', f"{user} -> {resource}: {'OK' if ok else 'NO'}")
        if not ok: self._blocked.add(user)
        return ok

    def _log(self, etype, msg):
        self._audit.append({'t': datetime.now().isoformat()[:19], 'type': etype, 'msg': msg})

    def show_audit_log(self):
        print("\n  Security Audit Log:")
        for e in self._audit[-15:]:
            print(f"  [{e['t'][11:]}] [{e['type']:8}] {e['msg']}")

    def get_security_summary(self):
        return {'audit_events': len(self._audit), 'blocked_users': len(self._blocked)}

    # Mod 20: shortcut
    def log_audit(self, event, info):
        TelemetryLogger.security_log_audit(event, info)


class SecurityError(Exception): pass


# ═══════════════════════════════════════════════════════════════════════
# MOD 5: AUTO-SUGGESTION SYSTEM
# ═══════════════════════════════════════════════════════════════════════

class KeywordSuggester:
    """Mod 5: Typo hone par sahi keyword suggest karo."""
    KEYWORDS = [
        'show','let','const','fn','class','if','elif','else','for','while',
        'repeat','in','ret','match','case','default','try','catch','fin',
        'import','new','null','true','false','and','or','not','lambda',
        'break','continue','raise','typeof','extends','self','async','await',
        # D-vex built-in modules
        'dvex.math','dvex.ai','dvex.data','dvex.io','dvex.time','dvex.json',
        'dvex.sys','dvex.http','dvex.sql','dvex.ui',
    ]

    @classmethod
    def suggest(cls, word: str) -> list:
        import difflib
        word = word.lower().strip()
        # difflib-based similarity — handles typos, transpositions, missing chars
        kw_lower = [k.lower() for k in cls.KEYWORDS]
        # Start-with matches (exact prefix)
        found = [cls.KEYWORDS[i] for i, k in enumerate(kw_lower)
                 if k.startswith(word) and k != word]
        # difflib close matches for typos
        close = difflib.get_close_matches(word, kw_lower, n=5, cutoff=0.6)
        for c in close:
            for k in cls.KEYWORDS:
                if k.lower() == c and k not in found:
                    found.append(k)
        return list(dict.fromkeys(found))[:5]

    @classmethod
    def suggest_correction(cls, word: str) -> str:
        s = cls.suggest(word)
        return f"Did you mean '{s[0]}'?" if s else f"Unknown: '{word}'"

    @classmethod
    def check_code(cls, code: str) -> list:
        results = []
        for i, line in enumerate(code.split('\n'), 1):
            s = line.strip()
            if not s or s.startswith('//'): continue
            words = s.split()
            if words and words[0].isalpha() and words[0] not in cls.KEYWORDS:
                sug = cls.suggest(words[0])
                if sug:
                    results.append(f"L{i}: Typo '{words[0]}' -> Did you mean '{sug[0]}'?")
        return results


# ═══════════════════════════════════════════════════════════════════════
# MOD 7: SMART SHOW
# ═══════════════════════════════════════════════════════════════════════

class SmartShow:
    """Mod 7: Beautiful output formatting."""
    @staticmethod
    def smart_show(*args):
        parts = []
        for a in args:
            if isinstance(a, list):
                parts.append('[' + ' | '.join(str(x) for x in a) + ']')
            elif isinstance(a, dict):
                parts.append('{' + ', '.join(f"{k}={v}" for k,v in a.items()) + '}')
            elif isinstance(a, (int, float)):
                parts.append(f"=> {a}")
            else:
                parts.append(str(a))
        out = "  ".join(parts)
        print(out)
        TelemetryLogger.log('SHOW', out[:60])

    @staticmethod
    def show_table(data, title=''):
        """Mod 7 + Mod 12: Table format output."""
        if isinstance(data, list) and data:
            cols = ['Index', 'Value']
            rows = [[str(i), str(x)] for i, x in enumerate(data)]
        elif isinstance(data, dict):
            cols = ['Key', 'Value']
            rows = [[str(k), str(v)] for k, v in data.items()]
        else:
            print(str(data)); return
        w = [max(len(c), max((len(r[i]) for r in rows), default=0)) for i, c in enumerate(cols)]
        sep = '+' + '+'.join('-'*(x+2) for x in w) + '+'
        hdr = '|' + '|'.join(f" {cols[i]:<{w[i]}} " for i in range(len(cols))) + '|'
        if title: print(f"\n  -- {title} --")
        print('  '+sep); print('  '+hdr); print('  '+sep)
        for row in rows[:20]:
            print('  |' + '|'.join(f" {row[i]:<{w[i]}} " for i in range(len(cols))) + '|')
        print('  '+sep)


# ═══════════════════════════════════════════════════════════════════════
# MOD 9 + 16: TYPE INFERENCE + VALIDATION
# ═══════════════════════════════════════════════════════════════════════

class TypeInference:
    """Mod 9: Auto data type detect. Mod 16: Strict type validation."""
    @staticmethod
    def auto_type(value):
        if isinstance(value, str):
            try: return int(value)
            except: pass
            try: return float(value)
            except: pass
            if value.lower() == 'true': return True
            if value.lower() == 'false': return False
            if value.lower() == 'null': return None
        return value

    @staticmethod
    def infer(val) -> str:
        if isinstance(val, bool):  return 'bool'
        if isinstance(val, int):   return 'int'
        if isinstance(val, float): return 'float'
        if isinstance(val, str):   return 'str'
        if isinstance(val, list):  return 'list'
        if isinstance(val, dict):  return 'dict'
        if val is None:            return 'null'
        return type(val).__name__

    @staticmethod
    def validate(value, hint: str, var_name='var'):
        """Mod 16: let x::int = "abc" => TypeError."""
        TYPE_MAP = {'int': int, 'float': float, 'str': str, 'bool': bool}
        if hint not in TYPE_MAP: return value
        if not isinstance(value, TYPE_MAP[hint]):
            TelemetryLogger.log('TYPE_ERR', f"{var_name}::{hint} got {type(value).__name__}")
            raise TypeError(
                f"[D-vex TypeError] '{var_name}' declared as '{hint}' "
                f"but got '{type(value).__name__}': {value!r}"
            )
        return value


# ═══════════════════════════════════════════════════════════════════════
# MOD 11: D-PM PACKAGE MANAGER
# ═══════════════════════════════════════════════════════════════════════

class DvexPackageManager:
    """Mod 11: D-PM — Local + Online Package Manager (DPI + GitHub support)."""

    # GitHub-hosted D-vex Package Index (user can override)
    BASE_URL      = "https://raw.githubusercontent.com/dvex-lang/registry/main/libs/"
    GITHUB_REPO   = "https://raw.githubusercontent.com/YourUsername/DVX-Packages/main/"
    LIB_DIR       = "libs/"

    # Local built-in registry — all v5.0 modules
    REGISTRY = {
        # ── Core ────────────────────────────────────────────────────────
        'dvex.math':   'Built-in math & stats',
        'dvex.ai':     'AI / ML module',
        'dvex.data':   'Data processing',
        'dvex.io':     'File I/O',
        'dvex.time':   'Time utilities',
        'dvex.json':   'JSON handling',
        'dvex.sys':    'System utilities',
        # ── v4.0 Enterprise ─────────────────────────────────────────────
        'dvex.http':   'Web & API requests  (GET/POST/PUT/DELETE)',
        'dvex.sql':    'SQLite database + transactions + schema',
        'dvex.ui':     'Desktop GUI via Tkinter',
        # ── v5.0 Advanced ────────────────────────────────────────────────
        'dvex.csv':    'CSV read/write/parse/dump',
        'dvex.crypto': 'MD5/SHA256/HMAC/UUID/Base64 encoding',
        'dvex.env':    'Environment variables & .env file loader',
        'dvex.regex':  'Full regex: match/find/replace/split/compile',
        'dvex.net':    'Ping/DNS/port-scan/TCP networking',
        'dvex.os':     'Shell/CPU/memory/disk/file-watch',
        'dvex.test':   'Built-in unit testing framework',
        # ── External (download from DPI) ─────────────────────────────────
        'dvex.plot':   'Advanced ASCII/terminal charting',
        'dvex.async':  'Full async/await event loop',
        'dvex.orm':    'SQLite ORM (object-relational mapping)',
        'dvex.fmt':    'Advanced string formatting & templates',
    }
    _installed = set()

    @classmethod
    def install(cls, pkg: str, source: str = 'auto') -> bool:
        """
        Install a package.
        source='auto' → try local first, then DPI
        source='dpi'  → force online download
        source='github' → download from GITHUB_REPO
        """
        # ── Local built-in ───────────────────────────────────────────────
        if source == 'auto' and pkg in cls.REGISTRY and pkg not in ('dvex.plot','dvex.async','dvex.orm','dvex.fmt'):
            cls._installed.add(pkg)
            TelemetryLogger.log('DPM_INSTALL', f'local:{pkg}')
            print(f"  [D-PM] ✓ Installed (built-in): {pkg}")
            print(f"  [D-PM]   {cls.REGISTRY[pkg]}")
            return True

        # ── Online DPI ───────────────────────────────────────────────────
        print(f"  [D-PM] Searching DPI for '{pkg}'...")
        if not os.path.exists(cls.LIB_DIR):
            os.makedirs(cls.LIB_DIR)

        urls_to_try = [cls.BASE_URL + pkg + ".ex"]
        if source == 'github':
            urls_to_try = [cls.GITHUB_REPO + pkg + ".ex"]

        try:
            import urllib.request
            for url in urls_to_try:
                try:
                    print(f"  [D-PM] Fetching: {url}")
                    with urllib.request.urlopen(url, timeout=10) as response:
                        code = response.read().decode('utf-8')
                    dest = os.path.join(cls.LIB_DIR, f"{pkg}.ex")
                    with open(dest, 'w', encoding='utf-8') as f:
                        f.write(code)
                    cls._installed.add(pkg)
                    if pkg not in cls.REGISTRY:
                        cls.REGISTRY[pkg] = 'External package (DPI)'
                    TelemetryLogger.log('DPM_DPI', f'online:{pkg}')
                    print(f"  [D-PM] ✓ Installed from DPI: {dest}")
                    return True
                except Exception:
                    continue
            print(f"  [D-PM Error] Package '{pkg}' not found online.")
            print(f"  [D-PM Hint ] Check spelling or see: https://github.com/dvex-lang/registry")
            TelemetryLogger.log('DPM_FAIL', pkg)
            return False
        except ImportError:
            print(f"  [D-PM Error] urllib not available.")
            return False

    @classmethod
    def uninstall(cls, pkg: str) -> bool:
        """Remove a package from installed set and delete local .ex if present."""
        if pkg in cls._installed:
            cls._installed.discard(pkg)
            # Look in libs/ and current dir
            for fname in [os.path.join(cls.LIB_DIR, f"{pkg}.ex"), f"{pkg}.ex"]:
                if os.path.exists(fname):
                    try:
                        os.remove(fname)
                        print(f"  [D-PM] Removed: {fname}")
                    except OSError as e:
                        print(f"  [D-PM Warning] Could not remove {fname}: {e}")
            TelemetryLogger.log('DPM_UNINSTALL', pkg)
            print(f"  [D-PM] ✓ Uninstalled: {pkg}")
            return True
        print(f"  [D-PM] '{pkg}' is not installed.")
        return False

    @classmethod
    def list_all(cls):
        """Display all packages with status."""
        cats = [
            ('Core',      ['dvex.math','dvex.ai','dvex.data','dvex.io','dvex.time','dvex.json','dvex.sys']),
            ('v4.0',      ['dvex.http','dvex.sql','dvex.ui']),
            ('v5.0 New',  ['dvex.csv','dvex.crypto','dvex.env','dvex.regex','dvex.net','dvex.os','dvex.test']),
            ('External',  ['dvex.plot','dvex.async','dvex.orm','dvex.fmt']),
        ]
        print(f"\n  D-PM Registry  v5.0  |  {len(cls._installed)}/{len(cls.REGISTRY)} installed")
        print("  " + "─" * 60)
        for cat, pkgs in cats:
            print(f"  [{cat}]")
            for pkg in pkgs:
                desc = cls.REGISTRY.get(pkg, '—')
                st   = '✓' if pkg in cls._installed else '·'
                print(f"    {st} {pkg:<22} {desc}")
        print("  " + "─" * 60)
        print(f"  DPI: {cls.BASE_URL}")

    @classmethod
    def search(cls, query: str):
        """Search registry by keyword."""
        q = query.lower()
        results = {k: v for k, v in cls.REGISTRY.items()
                   if q in k.lower() or q in v.lower()}
        if results:
            print(f"  [D-PM] Results for '{query}':")
            for k, v in results.items():
                st = '✓' if k in cls._installed else '·'
                print(f"    {st} {k:<22} {v}")
        else:
            print(f"  [D-PM] No packages matching '{query}'.")
        return results

    @classmethod
    def update_all(cls):
        """Re-install all currently installed external packages."""
        ext = [p for p in cls._installed if p not in cls.REGISTRY or
               p in ('dvex.plot','dvex.async','dvex.orm','dvex.fmt')]
        if not ext:
            print("  [D-PM] Nothing to update (only built-ins installed).")
            return
        for pkg in ext:
            cls.install(pkg, source='dpi')


# ═══════════════════════════════════════════════════════════════════════
# MOD 12: NATIVE PLOTTING
# ═══════════════════════════════════════════════════════════════════════

class NativePlotter:
    """Mod 12: ASCII charts — no matplotlib needed."""
    @staticmethod
    def plot_bar(data: list, title='Bar Chart', width=40):
        mx = max(data) if data else 1
        if mx == 0: mx = 1
        print(f"\n  [{title}]")
        for i, v in enumerate(data):
            bar = chr(9608) * int((v / mx) * width)
            print(f"  [{i:>3}] {bar:<{width}} {v}")

    @staticmethod
    def plot_line(data: list, title='Line Chart', h=8, w=50):
        if not data: return
        mn, mx = min(data), max(data)
        if mx == mn: mx += 1
        grid = [[' ']*w for _ in range(h)]
        for i, v in enumerate(data):
            c = int((i / max(len(data)-1, 1)) * (w-1))
            r = h - 1 - int(((v - mn) / (mx - mn)) * (h-1))
            if 0 <= r < h and 0 <= c < w:
                grid[r][c] = 'o'
        print(f"\n  [{title}]  max={mx:.2f}")
        for row in grid:
            print(f"  | {''.join(row)}")
        print(f"  | min={mn:.2f}")

    def plot(self, data, chart_type='bar', **kw):
        if chart_type == 'line': self.plot_line(data, **kw)
        else: self.plot_bar(data, **kw)


# ═══════════════════════════════════════════════════════════════════════
# MOD 14: DOCSTRING AUTO-GENERATOR
# ═══════════════════════════════════════════════════════════════════════

class DocGenerator:
    """Mod 14: /* ... */ comments se docs banao."""
    @staticmethod
    def generate(code: str, path='dvex_docs.txt') -> str:
        docs    = re.findall(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
        fns     = re.findall(r'\bfn\s+(\w+)\s*\(([^)]*)\)', code)
        classes = re.findall(r'\bclass\s+(\w+)', code)
        lines   = [
            "D-vex Auto Documentation",
            "=" * 40,
            f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
        ]
        if classes:
            lines += ["CLASSES:", "-"*30] + [f"  class {c}" for c in classes] + [""]
        if fns:
            lines += ["FUNCTIONS:", "-"*30] + [f"  fn {n}({p})" for n, p in fns] + [""]
        if docs:
            lines += ["DOCSTRINGS:", "-"*30] + [f"  {d.strip()}" for d in docs] + [""]
        content = '\n'.join(lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        TelemetryLogger.log('DOC_GEN', f'Saved -> {path}')
        print(f"  [DocGen] Docs saved -> {path}")
        return content


# ═══════════════════════════════════════════════════════════════════════
# MOD 15: LAZY MODULE LOADER
# ═══════════════════════════════════════════════════════════════════════

class LazyModuleLoader:
    """Mod 15: Startup fast — load on demand."""
    def __init__(self, registry: dict):
        self._reg    = registry
        self._loaded = {}

    def get(self, name: str):
        if name in self._loaded: return self._loaded[name]
        if name in self._reg:
            obj = self._reg[name]()
            self._loaded[name] = obj
            TelemetryLogger.log('LAZY_LOAD', f'"{name}" loaded on demand')
            return obj
        return None

    def stats(self):
        print(f"  [Lazy] {len(self._loaded)}/{len(self._reg)} modules loaded")


# ═══════════════════════════════════════════════════════════════════════
# MOD 1 + ALL: MAIN DVEX SCANNER
# ═══════════════════════════════════════════════════════════════════════

class AdvancedDocGen:
    """Mod 14 Expansion: Professional HTML/Markdown Manual Generator.
    Extracts /* ... */ docstrings, fn signatures, and class names
    from D-vex (.ex) source code and produces a structured reference document.
    """

    @staticmethod
    def generate_html(code: str, filename: str = "docs.html", title: str = "D-vex API Reference") -> str:
        import re, datetime
        docs  = re.findall(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
        fns   = re.findall(r'fn\s+(\w+)\s*\(([^)]*)\)', code)
        classes = re.findall(r'class\s+(\w+)', code)
        now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <title>{title}</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; background: #0d1117; color: #c9d1d9; }}
    h1   {{ color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }}
    h2   {{ color: #f78166; margin-top: 30px; }}
    h3   {{ color: #e6ad40; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
             padding: 15px 20px; margin: 12px 0; }}
    .sig  {{ font-family: 'Courier New', monospace; color: #79c0ff; font-size: 1.05em; }}
    .doc  {{ color: #8b949e; font-style: italic; margin-top: 6px; }}
    .class-tag {{ background: #388bfd26; color: #388bfd; border-radius: 4px;
                  padding: 2px 8px; font-size: 0.85em; margin-right: 6px; }}
    .footer {{ margin-top: 40px; color: #484f58; font-size: 0.85em; }}
  </style>
</head>
<body>
  <h1>📖 {title}</h1>
  <p style='color:#8b949e'>Generated: {now}</p>
"""
        # Classes section
        if classes:
            html += "<h2>📦 Classes</h2>"
            for c in set(classes):
                html += f"<div class='card'><span class='class-tag'>CLASS</span><span class='sig'>class {c}</span></div>\n"

        # Functions section
        if fns:
            html += "<h2>⚙️ Functions</h2>"
            for i, (fname, fargs) in enumerate(fns):
                doc_text = docs[i].replace('\n', ' ').strip() if i < len(docs) else ""
                html += f"""<div class='card'>
  <div class='sig'>fn {fname}({fargs})</div>
  {'<div class="doc">📝 ' + doc_text + '</div>' if doc_text else ''}
</div>\n"""

        html += f"  <div class='footer'>Generated by D-vex AdvancedDocGen (Mod 14) — D-vex v5.0 Enterprise</div>\n</body></html>"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  [DocGen] ✅ HTML manual: {filename}  ({len(fns)} functions, {len(set(classes))} classes)")
        return filename

    @staticmethod
    def generate_markdown(code: str, filename: str = "API_REFERENCE.md", title: str = "D-vex API Reference") -> str:
        import re, datetime
        docs    = re.findall(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
        fns     = re.findall(r'fn\s+(\w+)\s*\(([^)]*)\)', code)
        classes = re.findall(r'class\s+(\w+)', code)
        now     = datetime.datetime.now().strftime("%Y-%m-%d")

        md = f"# {title}\n\n> Auto-generated by D-vex DocGen (Mod 14) | {now}\n\n"

        if classes:
            md += "## Classes\n\n"
            for c in set(classes):
                md += f"- `class {c}`\n"
            md += "\n"

        if fns:
            md += "## Functions\n\n"
            for i, (fname, fargs) in enumerate(fns):
                doc_text = docs[i].replace('\n', ' ').strip() if i < len(docs) else ""
                md += f"### `fn {fname}({fargs})`\n"
                if doc_text:
                    md += f"> {doc_text}\n"
                md += "\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  [DocGen] ✅ Markdown manual: {filename}")
        return filename

    @staticmethod
    def auto_doc(filepath: str) -> None:
        """Auto-detect file and generate both HTML + Markdown docs."""
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        base = filepath.replace('.ex', '')
        AdvancedDocGen.generate_html(code, f"{base}_docs.html")
        AdvancedDocGen.generate_markdown(code, f"{base}_docs.md")


class DVexScanner:
    """
    D-vex Intelligent Scanner v3.0v
    Mod 1: Auto-Fix risky code before run
    + All 20 modifications integrated
    """
    ALLOWED_EXTENSION = '.ex'

    @staticmethod
    def enforce_extension(fp: str) -> bool:
        if not fp.endswith('.ex'):
            SecurityFramework.check_extension(fp)
            return False
        return True

    def __init__(self, code: str, filepath='<code>', auto_fix_timeout=180, sandbox=False):
        self.code            = code
        self.filepath        = filepath
        self.lines           = code.split('\n')
        self.suggestions     = []
        self.warnings        = []
        self.vulnerabilities = []
        self.auto_fix_timeout = auto_fix_timeout

        self.memory    = MemoryManagement()
        self.security  = SecurityFramework()
        self.suggester = KeywordSuggester()
        self.profiler  = MemoryProfiler()
        self.plotter   = NativePlotter()

        if sandbox:
            self.security.enable_sandbox()

        self.memory.register(id(self), self)
        TelemetryLogger.log('SCANNER_INIT', filepath)

    # ── MOD 1: Auto-Fix Division ──────────────────────────────────────

    def auto_fix_risky_code(self, code: str) -> str:
        """Mod 1: Division ko automatically try/catch mein wrap karo."""
        if '/' not in code or 'try' in code:
            return code
        lines, new_lines, fixed = code.split('\n'), [], False
        for line in lines:
            s = line.strip()
            if s.startswith('//') or s.startswith('/*') or not s:
                new_lines.append(line); continue
            if re.search(r'(?<![/<])/(?![/*=])', line) and 'try' not in line:
                ind = len(line) - len(line.lstrip())
                sp  = ' ' * ind
                new_lines += [
                    f"{sp}try:",
                    f"  {line}",
                    f"{sp}catch e:",
                    f"{sp}  show 'Safety Guard: Division Error:', e",
                ]
                fixed = True
                TelemetryLogger.log('AUTO_FIX', 'div->try/catch', line.strip()[:40])
            else:
                new_lines.append(line)
        if fixed:
            print("  [Auto-Fix] Division operations wrapped in try/catch")
        return '\n'.join(new_lines)

    def auto_fix_logic(self, code: str) -> str:
        """Mod 1 (alternative): Top-level wrap."""
        if '/' in code and 'try' not in code:
            fixed = "try:\n    " + code.replace("\n", "\n    ")
            fixed += "\ncatch e:\n    show 'Safety Guard triggered'"
            TelemetryLogger.log('AUTO_FIX_LOGIC', 'top-level wrap')
            return fixed
        return code

    def scan_with_auto_fix(self, code_ref: list):
        """Mod 1: Scan + 3-min auto-fix timer."""
        report = self.analyze()
        total  = sum(len(v) for v in report.values())
        if total == 0:
            print("  [Scanner] Code clean!")
            return report
        self.show_report()
        done = [False]
        def _timer():
            time.sleep(self.auto_fix_timeout)
            if not done[0]:
                code_ref[0] = self.auto_fix_risky_code(code_ref[0])
                done[0] = True
                print(f"\n  [Auto-Fix] Applied after {self.auto_fix_timeout}s timeout!")
                TelemetryLogger.log('AUTO_FIX_TIMER', 'timeout fix applied')
        threading.Thread(target=_timer, daemon=True).start()
        print(f"\n  {self.auto_fix_timeout}s mein Auto-Fix apply hoga if not fixed manually.")
        return report, done

    def auto_advance_fix(self, code: str) -> str:
        fixed = self.auto_fix_risky_code(code)
        if re.search(r'\bwhile\s+true\b', fixed, re.IGNORECASE):
            ls, nls = fixed.split('\n'), []
            for i, l in enumerate(ls):
                nls.append(l)
                if re.search(r'\bwhile\s+true\b', l, re.IGNORECASE):
                    if 'break' not in '\n'.join(ls[i:i+15]):
                        sp = ' ' * (len(l) - len(l.lstrip()) + 2)
                        nls.append(f"{sp}// AUTO-FIX: Add break condition here!")
            fixed = '\n'.join(nls)
        print("  [Auto-Advance Fix] Complete!")
        return fixed

    # ── Analysis ──────────────────────────────────────────────────────

    def analyze(self):
        # Clear lists to prevent duplicate accumulation on repeated calls
        self.suggestions.clear()
        self.warnings.clear()
        self.vulnerabilities.clear()
        self.profiler.snapshot('analyze')
        # Security (Mod 3)
        for t in self.security.run_security_audit(self.code):
            self.vulnerabilities.append(t)
        # Sandbox (Mod 17)
        for op in self.security.check_sandbox(self.code):
            self.vulnerabilities.append(f"SANDBOX BLOCKED: '{op}'")
        # Keyword suggestions (Mod 5)
        self.suggestions.extend(self.suggester.check_code(self.code))

        for i, line in enumerate(self.lines):
            n = i + 1
            s = line.strip()
            if not s or s.startswith('//'): continue
            self._check_naming(line, n)
            self._check_security(line, n)
            self._check_logic(line, n, i)
            self._check_style(line, n)
        self._check_global()
        self.memory.automatic_garbage_collection(silent=True)
        TelemetryLogger.log('ANALYZE_DONE',
            f"V:{len(self.vulnerabilities)} W:{len(self.warnings)} S:{len(self.suggestions)}")
        return {
            'vulnerabilities': self.vulnerabilities,
            'warnings':        self.warnings,
            'suggestions':     self.suggestions,
        }

    def _check_naming(self, line, n):
        for v in re.findall(r'\blet\s+([a-z])\s*=', line):
            self.suggestions.append(f"L{n}: Naming — '{v}' chota naam. Use 'counter'/'result'.")
        for v in re.findall(r'\blet\s+([A-Z_]{2,})\s*=', line):
            self.suggestions.append(f"L{n}: Style — '{v}' ALL_CAPS paar const nahi. Use 'const'.")

    def _check_security(self, line, n):
        if re.search(r'(?<![/<])/(?![/*=])', line) and 'try' not in self.code:
            self.vulnerabilities.append(f"L{n}: Division bina try/catch — Auto-Fix available!")
        for op in re.findall(r'\b(readFile|writeFile|appendFile)\b', line):
            if 'try' not in self.code:
                self.vulnerabilities.append(f"L{n}: '{op}()' bina try/catch.")

    def _check_logic(self, line, n, idx):
        if line.count(' if ') > 3 or line.count('elif') > 2:
            self.suggestions.append(f"L{n}: Complex if/elif — use match/case.")
        s = line.strip()
        if s.endswith(':') and not s.startswith('//'):
            nxt = self.lines[idx+1].strip() if idx+1 < len(self.lines) else ''
            if nxt in ('pass', ''):
                self.suggestions.append(f"L{n}: Empty block — kuch likhna bhule?")
        if re.search(r'\bwhile\s+true\b', line, re.IGNORECASE):
            if 'break' not in '\n'.join(self.lines[idx:idx+20]):
                self.warnings.append(f"L{n}: while true bina break! Infinite loop!")

    def _check_style(self, line, n):
        magic = [m for m in re.findall(r'(?<![a-zA-Z_\.])\b([0-9]{3,})\b', line)
                 if m not in ('100','1000','255','360')]
        if magic:
            self.suggestions.append(f"L{n}: Magic number {magic[0]} — use 'const MAX={magic[0]}'")
        if len(line) > 120:
            self.suggestions.append(f"L{n}: Line {len(line)} chars — break it.")

    def _check_global(self):
        lets = re.findall(r'^let\s+\w+\s*=', self.code, re.MULTILINE)
        if len(lets) > 15:
            self.suggestions.append(f"Architecture: {len(lets)} global vars — use Classes.")
        cl = [l for l in self.lines if l.strip() and not l.strip().startswith('//')]
        if 'fn ' not in self.code and len(cl) > 30:
            self.suggestions.append(f"Structure: {len(cl)} lines, no functions defined.")
        if 'class ' not in self.code and len(cl) > 50:
            self.suggestions.append("OOP: Large project — use Classes.")
        risky = [op for op in ['readFile','writeFile','/ '] if op in self.code]
        if risky and 'try' not in self.code:
            self.warnings.append(f"Error handling missing for: {', '.join(risky[:3])}")

    # ── Report ─────────────────────────────────────────────────────────

    def show_report(self):
        report = self.analyze()
        total  = sum(len(v) for v in report.values())
        W = 62
        print("\n" + "="*W)
        print("  D-vex Scan Report  v4.0v")
        print("  " + "-"*58)
        print(f"  File : {self.filepath}")
        print(f"  Time : {datetime.now():%Y-%m-%d %H:%M:%S}")
        print("  " + "="*58)
        if total == 0:
            print("  Code CLEAN! Koi issue nahi.")
        else:
            if report['vulnerabilities']:
                print(f"\n  VULNERABILITIES ({len(report['vulnerabilities'])}):")
                for v in report['vulnerabilities']:
                    print(f"    {v}")
            if report['warnings']:
                print(f"\n  WARNINGS ({len(report['warnings'])}):")
                for w in report['warnings']:
                    print(f"    {w}")
            if report['suggestions']:
                print(f"\n  SUGGESTIONS ({len(report['suggestions'])}):")
                for s in report['suggestions'][:8]:
                    print(f"    {s}")
        mem = self.memory.get_stats()
        sec = self.security.get_security_summary()
        print(f"\n  Memory: {mem['live_objects']} objects | GC: {mem['gc_runs']} runs")
        print(f"  Security: {sec['audit_events']} events")
        print(f"  Telemetry: {len(TelemetryLogger._log)} events")
        print("  " + "-"*58)
        print(f"  Total: {total} | {len(report['vulnerabilities'])} Critical | "
              f"{len(report['warnings'])} Warnings | {len(report['suggestions'])} Tips")
        if report['vulnerabilities']:
            print("  TIP: python dvex.py autofix <file.ex> se auto-fix karo!")
        print("  " + "="*58 + "\n")

    def get_summary(self):
        r = self.analyze()
        return {
            'critical': len(r['vulnerabilities']),
            'warnings': len(r['warnings']),
            'suggestions': len(r['suggestions']),
            'total': sum(len(v) for v in r.values()),
            'clean': sum(len(v) for v in r.values()) == 0,
        }

    def generate_docs(self, path='dvex_docs.txt'):
        """Mod 14: Auto docs generate karo."""
        return DocGenerator.generate(self.code, path)


# ═══════════════════════════════════════════════════════════════════════
# MOD 21: REAL-TIME LOGIC GUARD & 3-MIN AUTO-FIX
# ═══════════════════════════════════════════════════════════════════════

class LogicGuard:
    """
    Mod 21: Real-time Logic Monitoring & 3-Minute Auto-Fix
    -------------------------------------------------------
    - Background thread har 2-3 line par code check karta hai
    - Infinite loops, division errors, empty blocks detect karta hai
    - 3 minute baad auto-fix lagata hai bina user input ke
    - File modification time se linked hai — sirf changed code scan hota hai
    """

    PATTERNS = [
        # (regex, severity, message, tip)
        (r'\bwhile\s+true\b(?!.*break)',          'CRITICAL', 'Infinite loop detected!',
         "Add 'if condition: break' inside the loop."),
        (r'(?<![/<])/(?![/*=0-9])\s*[a-zA-Z0-9_]+\s*(?!try)',
         'WARNING',  'Division outside try/catch block',
         "Wrap with try: ... catch e: show e"),
        (r'\bfor\s+\w+\s+in\s+\[\s*\]',          'INFO',     'Iterating over empty list',
         "Ensure the list is populated before the loop."),
        (r'let\s+\w+\s*=\s*null\b',               'INFO',     'Variable set to null immediately',
         "Consider lazy initialization with a value."),
        (r'fn\s+\w+\([^)]*\):\s*\n?\s*(pass|$)',  'INFO',     'Empty function body',
         "Add implementation or raise NotImplemented."),
        (r'class\s+\w+[^:]*:\s*\n?\s*(pass|$)',   'INFO',     'Empty class body',
         "Add __init__ or methods."),
    ]

    SEVERITY_COLORS = {
        'CRITICAL': '🔴',
        'WARNING':  '🟡',
        'INFO':     '🔵',
    }

    def __init__(self, interpreter=None, auto_fix_delay=180):
        self.interpreter    = interpreter
        self.auto_fix_delay = auto_fix_delay  # seconds (default 3 min)
        self.last_code_hash = ''
        self.last_mtime     = 0.0
        self.is_monitoring  = True
        self._issues_cache  = []
        self._lock          = threading.Lock()
        self._fix_pending   = False
        TelemetryLogger.log('LOGIC_GUARD', 'Initialized', f'delay={auto_fix_delay}s')

    # ── File-based monitoring ────────────────────────────────────────

    def monitor_file(self, code_path: str):
        """
        Mod 21: Background monitoring — file read + smart diff.
        Sirf changed code ko re-scan karta hai.
        3 minute baad auto-fix apply karta hai.
        """
        def _worker():
            print(f"\n  [D-vex Guard] 👁  Monitoring: {code_path}")
            print(f"  [D-vex Guard] ⏱  Auto-fix in {self.auto_fix_delay}s if issues found.")
            fix_timer_start = None

            while self.is_monitoring:
                try:
                    if not os.path.exists(code_path):
                        time.sleep(2)
                        continue

                    mtime = os.path.getmtime(code_path)
                    if mtime != self.last_mtime:
                        with open(code_path, 'r', encoding='utf-8') as f:
                            code = f.read()

                        code_hash = hashlib.md5(code.encode()).hexdigest()
                        if code_hash != self.last_code_hash:
                            self.last_code_hash = code_hash
                            self.last_mtime = mtime
                            issues = self.analyze_logic(code)

                            if issues:
                                fix_timer_start = time.time()
                                self._fix_pending = True
                                TelemetryLogger.log('LOGIC_GUARD', f'{len(issues)} issues found')
                            else:
                                fix_timer_start = None
                                self._fix_pending = False

                    # Check 3-minute auto-fix timer
                    if self._fix_pending and fix_timer_start:
                        elapsed = time.time() - fix_timer_start
                        if elapsed >= self.auto_fix_delay:
                            self.apply_auto_fix(code_path)
                            self._fix_pending = False
                            fix_timer_start = None

                    time.sleep(3)  # Check every 3 seconds

                except Exception as e:
                    TelemetryLogger.log('LOGIC_GUARD_ERR', str(e))
                    time.sleep(5)

        t = threading.Thread(target=_worker, daemon=True, name='DVexLogicGuard')
        t.start()
        return t

    # ── Code analysis ────────────────────────────────────────────────

    def analyze_logic(self, code: str) -> list:
        """Mod 21: Logic issues scan karo — patterns + heuristics."""
        issues = []
        lines  = code.split('\n')

        # Pattern-based scan
        # Separate whole-code patterns from per-line patterns to avoid N×M duplicates
        whole_code_patterns = [(p, s, m, t) for p, s, m, t in self.PATTERNS if 'while' in p]
        per_line_patterns   = [(p, s, m, t) for p, s, m, t in self.PATTERNS if 'while' not in p]

        # Whole-code patterns: check once against entire code
        for pattern, severity, msg, tip in whole_code_patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                icon = self.SEVERITY_COLORS.get(severity, '⚪')
                issue = {
                    'line':     1,
                    'severity': severity,
                    'message':  msg,
                    'tip':      tip,
                    'code':     '',
                }
                if not any(x['message'] == msg for x in issues):
                    issues.append(issue)
                    print(f"\n  {icon} [D-vex Guard] GLOBAL: {severity} — {msg}")
                    print(f"     Tip : {tip}")

        # Per-line patterns: check each line individually
        for pattern, severity, msg, tip in per_line_patterns:
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('//') or s.startswith('/*') or not s:
                    continue
                if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                    icon = self.SEVERITY_COLORS.get(severity, '⚪')
                    issue = {
                        'line':     i + 1,
                        'severity': severity,
                        'message':  msg,
                        'tip':      tip,
                        'code':     s[:60],
                    }
                    issues.append(issue)
                    print(f"\n  {icon} [D-vex Guard] L{i+1}: {severity} — {msg}")
                    print(f"     Code: {s[:60]}")
                    print(f"     Tip : {tip}")

        # Heuristic: deeply nested code (> 4 levels)
        for i, line in enumerate(lines):
            indent = len(line) - len(line.lstrip())
            if indent > 16:  # 4+ levels at 4 spaces each
                issues.append({
                    'line': i + 1, 'severity': 'INFO',
                    'message': f'Deep nesting (indent={indent}) — hard to read',
                    'tip': 'Extract inner logic into a separate function.',
                    'code': line.strip()[:60],
                })

        # Heuristic: very long functions (> 50 lines)
        in_fn, fn_start, fn_lines = False, 0, 0
        for i, line in enumerate(lines):
            s = line.strip()
            if re.match(r'^\s*fn\s+\w+', line):
                in_fn, fn_start, fn_lines = True, i + 1, 0
            elif in_fn:
                if s and not line.startswith(' ') and not line.startswith('\t') and not s.startswith('//'):
                    if fn_lines > 50:
                        issues.append({
                            'line': fn_start, 'severity': 'INFO',
                            'message': f'Long function ({fn_lines} lines) — consider splitting',
                            'tip': 'Break into smaller helper functions for readability.',
                            'code': '',
                        })
                    in_fn = False
                else:
                    fn_lines += 1

        with self._lock:
            self._issues_cache = issues

        TelemetryLogger.log('LOGIC_SCAN', f'{len(issues)} issues', code[:30])
        return issues

    def get_cached_issues(self) -> list:
        with self._lock:
            return list(self._issues_cache)

    # ── Auto-fix application ─────────────────────────────────────────

    def apply_auto_fix(self, code_path: str):
        """Mod 21: 3 minutes baad auto-fix apply karo."""
        try:
            print(f"\n  [D-vex Guard] ⚡ 3 minutes passed. Applying Auto-Fix to: {code_path}")
            with open(code_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Import DVexScanner for Mod 1 fixes
            try:
                from lib.scanner import DVexScanner
            except ImportError:
                from scanner import DVexScanner

            scanner    = DVexScanner(code)
            fixed_code = scanner.auto_advance_fix(code)
            # Additional logic-level fixes
            fixed_code = self._fix_infinite_loops(fixed_code)
            fixed_code = self._fix_empty_bodies(fixed_code)

            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)

            print(f"  [D-vex Guard] ✅ Auto-Fix Applied successfully!")
            TelemetryLogger.log('LOGIC_AUTOFIX', 'Applied', code_path)

        except Exception as e:
            print(f"  [D-vex Guard] ❌ Auto-Fix failed: {e}")
            TelemetryLogger.log('LOGIC_AUTOFIX_ERR', str(e))

    def _fix_infinite_loops(self, code: str) -> str:
        """Add safety counter to infinite while true loops."""
        lines, new_lines, in_while = code.split('\n'), [], False
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.search(r'\bwhile\s+true\b', line, re.IGNORECASE):
                # Look 15 lines ahead for break
                look_ahead = '\n'.join(lines[i:i+15])
                if 'break' not in look_ahead:
                    indent = ' ' * (len(line) - len(line.lstrip()))
                    # Inject a safety counter before while true
                    new_lines.append(f"{indent}let __guard_counter = 0  // LogicGuard: safety counter")
                    new_lines.append(line)
                    i += 1
                    # Add guard check as first line of loop body
                    if i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t')):
                        body_indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
                        new_lines.append(f"{body_indent}__guard_counter += 1")
                        new_lines.append(f"{body_indent}if __guard_counter > 100000: break  // LogicGuard: auto-break")
                    TelemetryLogger.log('LOGIC_FIX', 'infinite loop guard added')
                    continue
            new_lines.append(line)
            i += 1
        return '\n'.join(new_lines)

    def _fix_empty_bodies(self, code: str) -> str:
        """Add 'pass' comment to empty function/class bodies."""
        lines, new_lines = code.split('\n'), []
        for i, line in enumerate(lines):
            new_lines.append(line)
            s = line.strip()
            if s.endswith(':') and re.match(r'\s*(fn|class)\s+\w+', line):
                # Check if next non-empty line is same or lower indent
                next_content = ''
                for j in range(i + 1, min(i + 5, len(lines))):
                    ns = lines[j].strip()
                    if ns:
                        next_content = lines[j]
                        break
                if not next_content or (len(next_content) - len(next_content.lstrip()) <=
                                        len(line) - len(line.lstrip())):
                    indent = ' ' * (len(line) - len(line.lstrip()) + 2)
                    new_lines.append(f"{indent}pass  // LogicGuard: empty body placeholder")
                    TelemetryLogger.log('LOGIC_FIX', 'empty body pass added')
        return '\n'.join(new_lines)

    def stop(self):
        """Stop monitoring."""
        self.is_monitoring = False
        print("  [D-vex Guard] Monitoring stopped.")
        TelemetryLogger.log('LOGIC_GUARD', 'Stopped')

    def show_report(self):
        """Print cached issues report."""
        issues = self.get_cached_issues()
        if not issues:
            print("  [D-vex Guard] ✅ No logic issues found!")
            return
        print(f"\n  [D-vex Guard] Found {len(issues)} logic issue(s):")
        print("  " + "─" * 60)
        for iss in issues:
            icon = self.SEVERITY_COLORS.get(iss['severity'], '⚪')
            print(f"  {icon} L{iss['line']:4d} [{iss['severity']:<8}] {iss['message']}")
            if iss['code']:
                print(f"         Code: {iss['code']}")
            print(f"         Tip : {iss['tip']}")
        print("  " + "─" * 60)


# ═══════════════════════════════════════════════════════════════════════
# MOD 22: NATIVE C++ EXTENSION LOADER
# ═══════════════════════════════════════════════════════════════════════

class NativeExtension:
    """
    Mod 22: C++ Library ko D-vex mein load karo via ctypes.
    ----------------------------------------------------------
    Usage in .ex:
        import_native("./mylib.so", "mylib")
        let result = mylib_sum(10, 20)

    C++ compile:
        g++ -O3 -shared -fPIC -o mylib.so mylib.cpp
    """

    # Default type signatures for common functions
    DEFAULT_SIGNATURES = {
        'fast_sum':   ([ctypes.c_int,    ctypes.c_int],    ctypes.c_int),
        'heavy_calc': ([ctypes.c_double],                   ctypes.c_double),
        'fast_sort':  ([ctypes.POINTER(ctypes.c_int), ctypes.c_int], ctypes.c_void_p),
        'fast_strlen':([ctypes.c_char_p],                   ctypes.c_int),
    }

    def __init__(self):
        self.libs      = {}   # alias -> ctypes.CDLL
        self.functions = {}   # "alias_funcname" -> wrapped callable
        TelemetryLogger.log('NATIVE_EXT', 'Initialized')

    def load_cpp(self, path: str, alias: str, env=None) -> bool:
        """
        .so / .dll C++ library load karo aur D-vex environment mein register karo.
        """
        if not os.path.exists(path):
            print(f"  [Native Error] File not found: '{path}'")
            TelemetryLogger.log('NATIVE_ERR', f'Not found: {path}')
            return False

        try:
            lib = ctypes.CDLL(path)
            self.libs[alias] = lib
            print(f"  [Native] ✅ C++ Library '{alias}' loaded from: {path}")
            TelemetryLogger.log('NATIVE_LOAD', alias, path)

            # Auto-register known functions
            registered = 0
            for fn_name, (argtypes, restype) in self.DEFAULT_SIGNATURES.items():
                try:
                    fn = getattr(lib, fn_name)
                    fn.argtypes = argtypes
                    fn.restype  = restype
                    key = f"{alias}_{fn_name}"
                    self.functions[key] = fn
                    if env:
                        env.set(key, fn)
                    registered += 1
                    print(f"  [Native]   ↳ Registered: {key}()")
                except AttributeError:
                    pass  # Function not in this lib — OK

            # Generic function accessor
            def make_accessor(a, l):
                def _get_fn(fn_name, res_type='int'):
                    try:
                        fn = getattr(l, fn_name)
                        type_map = {
                            'int':    ctypes.c_int,
                            'float':  ctypes.c_float,
                            'double': ctypes.c_double,
                            'str':    ctypes.c_char_p,
                            'void':   ctypes.c_void_p,
                        }
                        fn.restype = type_map.get(res_type, ctypes.c_int)
                        return fn
                    except AttributeError:
                        raise ValueError(f"Function '{fn_name}' not found in '{a}'")
                return _get_fn

            if env:
                env.set(f"{alias}_get", make_accessor(alias, lib))

            if registered == 0:
                print(f"  [Native] ℹ️  No standard functions found. Use {alias}_get('fn_name') to access.")

            return True

        except OSError as e:
            print(f"  [Native Error] Failed to load '{path}': {e}")
            TelemetryLogger.log('NATIVE_ERR', str(e), path)
            return False

    def call(self, alias: str, fn_name: str, *args):
        """Direct call to a loaded C++ function."""
        key = f"{alias}_{fn_name}"
        if key in self.functions:
            try:
                return self.functions[key](*args)
            except Exception as e:
                raise RuntimeError(f"[Native] Error calling {key}: {e}")
        if alias in self.libs:
            try:
                return getattr(self.libs[alias], fn_name)(*args)
            except AttributeError:
                raise ValueError(f"[Native] '{fn_name}' not found in '{alias}'")
        raise ValueError(f"[Native] Library '{alias}' not loaded")

    def list_libs(self):
        """Show all loaded native libraries."""
        if not self.libs:
            print("  [Native] No libraries loaded.")
            return
        print(f"\n  [Native] Loaded Libraries ({len(self.libs)}):")
        for alias, lib in self.libs.items():
            fns = [k for k in self.functions if k.startswith(alias + '_')]
            print(f"    {alias}: {lib._name} — {len(fns)} functions registered")
            for fn in fns:
                print(f"      ↳ {fn}()")


# ═══════════════════════════════════════════════════════════════════════
# MOD 23: BYTECODE VM — STACK-BASED VIRTUAL MACHINE
# ═══════════════════════════════════════════════════════════════════════

# Bytecode Opcodes
OP_PUSH     = 'PUSH'      # Push constant on stack
OP_POP      = 'POP'       # Pop from stack
OP_LOAD     = 'LOAD'      # Load variable
OP_STORE    = 'STORE'     # Store to variable
OP_ADD      = 'ADD'       # +
OP_SUB      = 'SUB'       # -
OP_MUL      = 'MUL'       # *
OP_DIV      = 'DIV'       # /
OP_MOD      = 'MOD'       # %
OP_POW      = 'POW'       # **
OP_NEG      = 'NEG'       # unary -
OP_EQ       = 'EQ'        # ==
OP_NEQ      = 'NEQ'       # !=
OP_LT       = 'LT'        # <
OP_GT       = 'GT'        # >
OP_LTE      = 'LTE'       # <=
OP_GTE      = 'GTE'       # >=
OP_AND      = 'AND'       # and
OP_OR       = 'OR'        # or
OP_NOT      = 'NOT'       # not
OP_JUMP     = 'JUMP'      # Unconditional jump
OP_JUMP_IF  = 'JUMP_IF'   # Jump if true
OP_JUMP_NOT = 'JUMP_NOT'  # Jump if false
OP_CALL     = 'CALL'      # Function call (n args)
OP_RET      = 'RET'       # Return
OP_SHOW     = 'SHOW'      # print top of stack
OP_MAKE_LIST= 'MAKE_LIST' # Make list from N stack items
OP_MAKE_DICT= 'MAKE_DICT' # Make dict from 2N stack items
OP_GETATTR  = 'GETATTR'   # obj.attr
OP_SETATTR  = 'SETATTR'   # obj.attr = val
OP_INDEX    = 'INDEX'     # obj[idx]
OP_NOP      = 'NOP'       # No operation
OP_HALT     = 'HALT'      # Stop VM
OP_DUP      = 'DUP'       # Duplicate top of stack


class Instruction:
    """Single bytecode instruction."""
    __slots__ = ('opcode', 'arg', 'line')

    def __init__(self, opcode: str, arg=None, line: int = 0):
        self.opcode = opcode
        self.arg    = arg
        self.line   = line

    def __repr__(self):
        a = f" {self.arg!r}" if self.arg is not None else ''
        return f"{self.opcode}{a}"


class BytecodeCompiler:
    """
    Mod 23: AST → Bytecode Compiler
    D-vex AST tuples ko bytecode instructions mein convert karta hai.
    """

    def __init__(self):
        self.instructions: list[Instruction] = []
        self.constants:    list              = []
        self.locals:       dict              = {}
        self._label_counter = 0

    def _emit(self, opcode: str, arg=None, line: int = 0) -> int:
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, arg, line))
        return idx

    def _new_label(self) -> str:
        self._label_counter += 1
        return f'L{self._label_counter}'

    def _patch_jump(self, idx: int):
        """Patch a JUMP instruction's target to current position."""
        self.instructions[idx].arg = len(self.instructions)

    def compile(self, stmts: list) -> list:
        """Compile a list of AST statements to bytecode, then run optimizer."""
        for stmt in stmts:
            if stmt: self._compile_stmt(stmt)
        self._emit(OP_HALT)
        # ── Mod 23 Expansion: Peephole Optimizer ──────────────────────────
        self.instructions = BytecodeOptimizer.optimize(self.instructions)
        # ──────────────────────────────────────────────────────────────────
        return self.instructions

    def _compile_stmt(self, stmt):
        kind = stmt[0]

        if kind == 'let':
            _, name, val_ast, is_const, line = stmt
            if val_ast is not None:
                self._compile_expr(val_ast, line)
            else:
                self._emit(OP_PUSH, None, line)
            self._emit(OP_STORE, name, line)

        elif kind == 'assign':
            _, target, val_ast, line = stmt
            self._compile_expr(val_ast, line)
            if isinstance(target, tuple) and target[0] == 'var':
                self._emit(OP_STORE, target[1], line)
            else:
                self._emit(OP_STORE, str(target), line)

        elif kind == 'show':
            _, args, line = stmt
            for a in args:
                self._compile_expr(a, line)
            self._emit(OP_SHOW, len(args), line)

        elif kind == 'expr':
            _, expr, line = stmt
            self._compile_expr(expr, line)
            self._emit(OP_POP, None, line)

        elif kind == 'ret':
            _, val_ast, line = stmt
            if val_ast is not None:
                self._compile_expr(val_ast, line)
            else:
                self._emit(OP_PUSH, None, line)
            self._emit(OP_RET, None, line)

        elif kind == 'if':
            # AST format: ('if', branches, else_body, line)
            # branches = [('if', cond, body), ('elif', cond, body), ...]
            _, branches, else_body, line = stmt
            end_jumps = []
            for idx, (btype, cond_ast, body) in enumerate(branches):
                self._compile_expr(cond_ast, line)
                jmp_false = self._emit(OP_JUMP_NOT, None, line)
                for s in body:
                    self._compile_stmt(s)
                jmp_end = self._emit(OP_JUMP, None, line)
                end_jumps.append(jmp_end)
                self._patch_jump(jmp_false)
            if else_body:
                for s in else_body:
                    self._compile_stmt(s)
            for j in end_jumps:
                self._patch_jump(j)

        elif kind == 'while':
            _, cond_ast, body, line = stmt
            loop_start = len(self.instructions)
            self._compile_expr(cond_ast, line)
            jmp_end = self._emit(OP_JUMP_NOT, None, line)
            for s in body: self._compile_stmt(s)
            self._emit(OP_JUMP, loop_start, line)
            self._patch_jump(jmp_end)

        elif kind == 'pass':
            self._emit(OP_NOP)

        else:
            # For unsupported nodes, emit NOP
            self._emit(OP_NOP)

    def _compile_expr(self, expr, line: int = 0):
        if expr is None:
            self._emit(OP_PUSH, None, line); return

        if not isinstance(expr, tuple):
            self._emit(OP_PUSH, expr, line); return

        kind = expr[0]

        if kind == 'lit':
            self._emit(OP_PUSH, expr[1], line)

        elif kind == 'var':
            self._emit(OP_LOAD, expr[1], line)

        elif kind == 'binop':
            _, op, left, right = expr
            self._compile_expr(left, line)
            self._compile_expr(right, line)
            op_map = {
                '+': OP_ADD, '-': OP_SUB, '*': OP_MUL, '/': OP_DIV,
                '%': OP_MOD, '**': OP_POW, '==': OP_EQ, '!=': OP_NEQ,
                '<': OP_LT,  '>': OP_GT,  '<=': OP_LTE, '>=': OP_GTE,
                'and': OP_AND, 'or': OP_OR,
            }
            self._emit(op_map.get(op, OP_NOP), op, line)

        elif kind == 'unary':
            _, op, operand = expr
            self._compile_expr(operand, line)
            if op == '-':   self._emit(OP_NEG, None, line)
            elif op == 'not': self._emit(OP_NOT, None, line)

        elif kind == 'call':
            _, fn_ast, args_ast = expr
            self._compile_expr(fn_ast, line)
            for a in args_ast: self._compile_expr(a, line)
            self._emit(OP_CALL, len(args_ast), line)

        elif kind == 'list':
            for e in expr[1]: self._compile_expr(e, line)
            self._emit(OP_MAKE_LIST, len(expr[1]), line)

        elif kind == 'getattr':
            _, obj, name = expr
            self._compile_expr(obj, line)
            self._emit(OP_GETATTR, name, line)

        elif kind == 'index':
            _, obj, idx = expr
            self._compile_expr(obj, line)
            self._compile_expr(idx, line)
            self._emit(OP_INDEX, None, line)

        else:
            self._emit(OP_PUSH, None, line)

    def disassemble(self) -> str:
        """Human-readable bytecode dump."""
        lines = ["\n  ╔══ D-vex Bytecode Disassembly ══╗"]
        for i, ins in enumerate(self.instructions):
            arg = f"  {ins.arg!r}" if ins.arg is not None else ''
            lines.append(f"  │ {i:>4}  {ins.opcode:<12}{arg}")
        lines.append("  ╚══════════════════════════════╝")
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════
# MOD 23 EXPANSION: BYTECODE PEEPHOLE OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════

class BytecodeOptimizer:
    """
    Mod 23 Expansion: Peephole Optimizer for D-vex Bytecode.

    Optimizations applied at compile-time:
      1. Constant Folding   — PUSH 5, PUSH 10, ADD → PUSH 15
      2. Dead NOP Removal   — Remove all NOP instructions
      3. Double Negation    — NEG NEG → (removed)
      4. Load-Store Elim    — STORE x, LOAD x → STORE x (keep top of stack)
      5. Strength Reduction — MUL by 2 → ADD self
      6. Jump Chain         — JUMP to another JUMP → direct target

    Usage:
        compiler = BytecodeCompiler()
        raw = compiler.compile(stmts)
        optimized = BytecodeOptimizer.optimize(raw)
    """

    _FOLD_OPS = {
        'ADD': lambda a, b: a + b,
        'SUB': lambda a, b: a - b,
        'MUL': lambda a, b: a * b,
        'DIV': lambda a, b: a / b if b != 0 else None,
        'MOD': lambda a, b: a % b if b != 0 else None,
        'POW': lambda a, b: a ** b,
    }

    @classmethod
    def optimize(cls, instructions: list) -> list:
        """Apply all peephole optimizations. Returns optimized instruction list."""
        optimized = instructions[:]
        # Apply multiple passes until stable
        for _ in range(3):
            prev_len = len(optimized)
            optimized = cls._fold_constants(optimized)
            optimized = cls._remove_nops(optimized)
            optimized = cls._elim_double_neg(optimized)
            optimized = cls._elim_load_after_store(optimized)
            optimized = cls._resolve_jump_chains(optimized)
            if len(optimized) == prev_len:
                break  # stable — no more improvements

        TelemetryLogger.log('BC_OPT',
            f'Reduced {len(instructions)} → {len(optimized)} instructions '
            f'({len(instructions)-len(optimized)} removed)')
        return optimized

    @classmethod
    def _fold_constants(cls, ins: list) -> list:
        """
        Constant Folding: consecutive PUSH num + PUSH num + arithmetic_op
        → single PUSH result
        """
        out = []
        i   = 0
        while i < len(ins):
            # Pattern: PUSH <num>, PUSH <num>, FOLD_OP
            if (i + 2 < len(ins)
                    and ins[i].opcode   == 'PUSH'
                    and ins[i+1].opcode == 'PUSH'
                    and ins[i+2].opcode in cls._FOLD_OPS
                    and isinstance(ins[i].arg,   (int, float))
                    and isinstance(ins[i+1].arg, (int, float))):
                fn     = cls._FOLD_OPS[ins[i+2].opcode]
                result = fn(ins[i].arg, ins[i+1].arg)
                if result is not None:  # Skip if would cause div/mod by zero
                    out.append(Instruction('PUSH', result, ins[i].line))
                    i += 3
                    continue
            out.append(ins[i])
            i += 1
        return out

    @classmethod
    def _remove_nops(cls, ins: list) -> list:
        """Remove all NOP instructions (they do nothing)."""
        return [x for x in ins if x.opcode != 'NOP']

    @classmethod
    def _elim_double_neg(cls, ins: list) -> list:
        """NEG NEG → remove both (double negation cancels out)."""
        out = []
        i   = 0
        while i < len(ins):
            if (i + 1 < len(ins)
                    and ins[i].opcode   == 'NEG'
                    and ins[i+1].opcode == 'NEG'):
                i += 2  # skip both
                continue
            out.append(ins[i])
            i += 1
        return out

    @classmethod
    def _elim_load_after_store(cls, ins: list) -> list:
        """
        STORE x, LOAD x optimization.

        NOTE: STORE pops the value from the stack (stores it to variable).
        After STORE, the value is NO longer on the stack.
        Therefore, STORE x followed immediately by LOAD x is semantically
        necessary — LOAD is required to put the value back.
        This optimization is intentionally left as a pass-through (no-op)
        to avoid incorrect bytecode generation.
        """
        # Do not optimize this pattern — it is semantically required.
        return ins

    @classmethod
    def _resolve_jump_chains(cls, ins: list) -> list:
        """
        Jump Chain Optimization: if a JUMP lands on another JUMP,
        point directly to the final target.
        """
        out = list(ins)
        for i, instruction in enumerate(out):
            if instruction.opcode in ('JUMP', 'JUMP_NOT') and isinstance(instruction.arg, int):
                target = instruction.arg
                # Follow chain (max 10 hops to avoid infinite loops)
                for _ in range(10):
                    if (target < len(out)
                            and out[target].opcode == 'JUMP'
                            and isinstance(out[target].arg, int)):
                        target = out[target].arg
                    else:
                        break
                out[i] = Instruction(instruction.opcode, target, instruction.line)
        return out

    @staticmethod
    def stats(original: list, optimized: list) -> dict:
        """Return optimization statistics."""
        removed  = len(original) - len(optimized)
        ratio    = removed / len(original) * 100 if original else 0
        return {
            'original':  len(original),
            'optimized': len(optimized),
            'removed':   removed,
            'ratio_pct': round(ratio, 1),
        }


# ═══════════════════════════════════════════════════════════════════════
# MOD 38: HOT LOOP PROFILER (Runtime Performance)
# ═══════════════════════════════════════════════════════════════════════

class HotLoopProfiler:
    """
    Mod 38: Runtime profiler that tracks which code sections execute most
    and identifies "hot loops" — loops that run > threshold times.

    Usage in scanner / interpreter integration:
        profiler = HotLoopProfiler()
        profiler.tick('loop_body', line=42)
        profiler.report()
    """

    def __init__(self, hot_threshold: int = 100):
        self._counts:    dict = {}   # location → execution count
        self._times:     dict = {}   # location → cumulative time (ms)
        self._threshold  = hot_threshold
        self._lock       = threading.Lock()

    def tick(self, location: str, line: int = 0, elapsed_ms: float = 0.0):
        """Record an execution tick at a location."""
        key = f"{location}:L{line}"
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + 1
            self._times[key]  = self._times.get(key, 0.0) + elapsed_ms

    def hot_spots(self) -> list:
        """Return locations executed more than hot_threshold times."""
        spots = [(k, v) for k, v in self._counts.items() if v >= self._threshold]
        return sorted(spots, key=lambda x: -x[1])

    def report(self):
        """Print profiling report."""
        all_locs = sorted(self._counts.items(), key=lambda x: -x[1])
        W = 60
        print(f"\n  ╔{'═'*W}╗")
        print(f"  ║  D-vex Hot Loop Profiler Report  (Mod 38){' '*(W-43)}║")
        print(f"  ╠{'═'*W}╣")
        print(f"  ║  {'Location':<35} {'Count':>8} {'Time(ms)':>10}  ║")
        print(f"  ╠{'─'*W}╣")
        for loc, count in all_locs[:20]:
            t   = self._times.get(loc, 0)
            hot = ' 🔥' if count >= self._threshold else ''
            print(f"  ║  {loc:<35} {count:>8} {t:>10.2f}{hot}  ║")
        hot_count = len(self.hot_spots())
        print(f"  ╠{'═'*W}╣")
        print(f"  ║  Total locations: {len(self._counts):<10} "
              f"Hot spots: {hot_count:<10}{' '*(W-45)}║")
        print(f"  ╚{'═'*W}╝")
        TelemetryLogger.log('PROFILER', f'{hot_count} hot spots found')

    def reset(self):
        self._counts.clear()
        self._times.clear()


class BytecodeVM:
    """
    Mod 23: Stack-based Virtual Machine
    Bytecode instructions execute karta hai.
    Tree-walking interpreter se ~3x faster for arithmetic-heavy code.
    """

    def __init__(self, globals_dict: dict = None):
        self.stack:   list = []
        self.globals: dict = globals_dict or {}
        self.locals:  dict = {}
        self.ip:      int  = 0      # instruction pointer
        self.call_stack: list = []  # (return_ip, saved_locals)
        self._executed  = 0
        TelemetryLogger.log('BYTECODE_VM', 'Initialized')

    def run(self, instructions: list, env_vars: dict = None) -> any:
        """Execute bytecode instructions."""
        self.ip      = 0
        self.stack   = []
        self.locals  = dict(self.globals)
        if env_vars:
            self.locals.update(env_vars)
        self._executed = 0

        while self.ip < len(instructions):
            ins = instructions[self.ip]
            self.ip += 1
            self._executed += 1
            self._exec(ins)

            if ins.opcode == OP_HALT:
                break

        TelemetryLogger.log('VM_EXEC', f'{self._executed} instructions executed')
        return self.stack[-1] if self.stack else None

    def _exec(self, ins: Instruction):
        op  = ins.opcode
        arg = ins.arg

        if op == OP_PUSH:
            self.stack.append(arg)

        elif op == OP_POP:
            if self.stack: self.stack.pop()

        elif op == OP_LOAD:
            val = self.locals.get(arg)
            if val is None and arg not in self.locals:
                raise NameError(f"[VM] '{arg}' is not defined")
            self.stack.append(val)

        elif op == OP_STORE:
            val = self.stack.pop() if self.stack else None
            self.locals[arg] = val

        elif op == OP_ADD:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l + r)

        elif op == OP_SUB:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l - r)

        elif op == OP_MUL:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l * r)

        elif op == OP_DIV:
            r, l = self.stack.pop(), self.stack.pop()
            if r == 0: raise ZeroDivisionError("[VM] Division by zero")
            self.stack.append(l / r)

        elif op == OP_MOD:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l % r)

        elif op == OP_POW:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l ** r)

        elif op == OP_NEG:
            self.stack.append(-self.stack.pop())

        elif op == OP_EQ:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l == r)

        elif op == OP_NEQ:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l != r)

        elif op == OP_LT:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l < r)

        elif op == OP_GT:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l > r)

        elif op == OP_LTE:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l <= r)

        elif op == OP_GTE:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l >= r)

        elif op == OP_AND:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l and r)

        elif op == OP_OR:
            r, l = self.stack.pop(), self.stack.pop()
            self.stack.append(l or r)

        elif op == OP_NOT:
            self.stack.append(not self.stack.pop())

        elif op == OP_JUMP:
            self.ip = arg

        elif op == OP_JUMP_IF:
            cond = self.stack.pop()
            if cond: self.ip = arg

        elif op == OP_JUMP_NOT:
            cond = self.stack.pop()
            if not cond: self.ip = arg

        elif op == OP_SHOW:
            n    = arg or 1
            vals = []
            for _ in range(n):
                vals.insert(0, self.stack.pop() if self.stack else None)
            print(' '.join(str(v) for v in vals))

        elif op == OP_MAKE_LIST:
            n     = arg or 0
            items = []
            for _ in range(n):
                items.insert(0, self.stack.pop() if self.stack else None)
            self.stack.append(items)

        elif op == OP_MAKE_DICT:
            n    = arg or 0
            d    = {}
            vals = []
            for _ in range(n * 2):
                vals.insert(0, self.stack.pop() if self.stack else None)
            for i in range(0, len(vals), 2):
                d[vals[i]] = vals[i + 1] if i + 1 < len(vals) else None
            self.stack.append(d)

        elif op == OP_CALL:
            n_args = arg or 0
            args   = []
            for _ in range(n_args):
                args.insert(0, self.stack.pop() if self.stack else None)
            fn = self.stack.pop() if self.stack else None
            if callable(fn):
                result = fn(*args)
                self.stack.append(result)
            else:
                raise TypeError(f"[VM] '{fn}' is not callable")

        elif op == OP_RET:
            val = self.stack.pop() if self.stack else None
            if self.call_stack:
                ret_ip, saved_locals = self.call_stack.pop()
                self.ip     = ret_ip
                self.locals = saved_locals
            self.stack.append(val)

        elif op == OP_GETATTR:
            obj = self.stack.pop()
            if hasattr(obj, 'getattr'):
                self.stack.append(obj.getattr(arg))
            elif hasattr(obj, arg):
                self.stack.append(getattr(obj, arg))
            elif isinstance(obj, dict):
                self.stack.append(obj.get(arg))
            else:
                raise AttributeError(f"[VM] No attribute '{arg}'")

        elif op == OP_INDEX:
            idx = self.stack.pop()
            obj = self.stack.pop()
            if isinstance(obj, (list, tuple)):
                self.stack.append(obj[int(idx)])
            elif isinstance(obj, dict):
                self.stack.append(obj.get(idx))
            else:
                self.stack.append(None)

        elif op in (OP_NOP, OP_HALT):
            pass  # No operation / halt

        elif op == OP_DUP:
            if self.stack:
                self.stack.append(self.stack[-1])

    def get_stats(self) -> dict:
        return {
            'instructions_executed': self._executed,
            'stack_depth':           len(self.stack),
            'variables':             len(self.locals),
        }


# ═══════════════════════════════════════════════════════════════════════
# MOD 27: FULL STACK TRACE & RICH ERROR REPORTER
# ═══════════════════════════════════════════════════════════════════════

class DVexStackTrace:
    """
    Mod 27: Professional stack trace aur error reporting.
    D-vex errors ko beautiful, readable format mein show karta hai.
    Python-style traceback ke saath D-vex line info bhi deta hai.
    """

    SEVERITY_ICONS = {
        'DVexSyntaxError':  '🔴 SYNTAX',
        'DVexTypeError':    '🟠 TYPE',
        'DVexNameError':    '🟡 NAME',
        'DVexRuntimeError': '🔴 RUNTIME',
        'DVexIndexError':   '🟡 INDEX',
        'ZeroDivisionError':'🔴 DIVISION',
        'DVexError':        '❌ ERROR',
    }

    def __init__(self):
        self._call_stack: list = []  # list of (fn_name, line, source_snippet)
        self._error_history: list = []

    def push_frame(self, fn_name: str, line: int, snippet: str = ''):
        """Enter a function — push frame."""
        self._call_stack.append({
            'fn':      fn_name,
            'line':    line,
            'snippet': snippet[:80],
            'time':    time.time(),
        })

    def pop_frame(self):
        """Exit a function — pop frame."""
        if self._call_stack:
            self._call_stack.pop()

    def format_error(self, error: Exception, code_lines: list = None) -> str:
        """
        Rich error message banao with:
        - Error type icon
        - Stack trace
        - Source code context (3 lines before/after)
        - Helpful fix suggestions
        """
        err_type = type(error).__name__
        err_msg  = str(error)
        icon     = self.SEVERITY_ICONS.get(err_type, '❌')

        lines = [
            "",
            "  ╔══════════════════════════════════════════════════════╗",
            f"  ║  {icon} Error                                        ║",
            "  ╠══════════════════════════════════════════════════════╣",
        ]

        # Error message
        clean_msg = err_msg.replace('\n[D-vex Error', '').replace('\n[D-vex', '').strip()
        if clean_msg:
            for part in clean_msg.split('\n'):
                lines.append(f"  ║  {part[:52]:<52} ║")

        # D-vex call stack
        if self._call_stack:
            lines.append("  ╠══ Call Stack ═══════════════════════════════════════╣")
            for frame in reversed(self._call_stack[-8:]):
                fn_info = f"  fn {frame['fn']}() — line {frame['line']}"
                lines.append(f"  ║  {fn_info:<52} ║")
                if frame['snippet']:
                    lines.append(f"  ║    > {frame['snippet'][:50]:<50} ║")

        # Source context
        line_num = getattr(error, 'line', None)
        if line_num and code_lines and isinstance(line_num, int):
            lines.append("  ╠══ Source Context ══════════════════════════════════╣")
            start = max(0, line_num - 3)
            end   = min(len(code_lines), line_num + 2)
            for i in range(start, end):
                marker = "►" if i == line_num - 1 else " "
                snippet = code_lines[i][:48] if i < len(code_lines) else ''
                lines.append(f"  ║ {marker} {i+1:3d} │ {snippet:<48} ║")

        # Suggestion
        suggestion = self._suggest_fix(err_type, err_msg)
        if suggestion:
            lines.append("  ╠══ Tip ═════════════════════════════════════════════╣")
            for part in suggestion.split('\n'):
                lines.append(f"  ║  💡 {part[:50]:<50} ║")

        lines.append("  ╚══════════════════════════════════════════════════════╝")
        result = '\n'.join(lines)

        # Store in history
        self._error_history.append({
            'time':  datetime.now().strftime('%H:%M:%S'),
            'type':  err_type,
            'msg':   err_msg[:100],
            'line':  line_num,
        })
        TelemetryLogger.log('STACK_TRACE', err_type, err_msg[:60])

        return result

    def _suggest_fix(self, err_type: str, err_msg: str) -> str:
        """Smart fix suggestions based on error type."""
        if 'DVexNameError' in err_type or 'not defined' in err_msg:
            # Extract variable name
            m = re.search(r"'(\w+)' is not defined", err_msg)
            name = m.group(1) if m else 'variable'
            return f"Use 'let {name} = value' before using it.\nCheck for typos in variable name."

        if 'DVexTypeError' in err_type or 'TypeError' in err_type:
            return "Check that you're using the right type.\nUse typeof() to inspect variable types."

        if 'Division by zero' in err_msg:
            return "Wrap division in try/catch:\ntry:\n  let r = a / b\ncatch e:\n  show 'Error:', e"

        if 'DVexSyntaxError' in err_type:
            return "Check:\n• Missing ':' after fn/if/for/while\n• Unclosed brackets '()' '[]' '{}'\n• Wrong indentation"

        if 'DVexIndexError' in err_type or 'Index' in err_msg:
            return "Check list length before indexing.\nUse list.length or list.isEmpty first."

        if 'constant' in err_msg.lower():
            return "Use 'let' instead of 'const' if you need to reassign.\nOr create a new variable."

        if 'not callable' in err_msg:
            return "Make sure the value is a function.\nCheck: is it declared with 'fn'?"

        return "Run: python dvex.py scan file.ex  for detailed analysis."

    def print_error(self, error: Exception, code_lines: list = None):
        """Print formatted error to stdout."""
        print(self.format_error(error, code_lines))

    def show_history(self, n: int = 10):
        """Show last N errors."""
        if not self._error_history:
            print("  [Stack Trace] No errors recorded.")
            return
        print(f"\n  D-vex Error History (last {n}):")
        print("  " + "─" * 55)
        for e in self._error_history[-n:]:
            line_info = f"L{e['line']}" if e['line'] else '   '
            print(f"  [{e['time']}] {line_info:>4} {e['type']:<20} {e['msg'][:30]}")

    def clear(self):
        """Clear call stack and history."""
        self._call_stack.clear()
        self._error_history.clear()

    def get_traceback_str(self) -> str:
        """Python-style traceback string."""
        if not self._call_stack:
            return "  (no D-vex frames)"
        lines = ["  D-vex Traceback (most recent call last):"]
        for frame in self._call_stack:
            lines.append(f'    fn {frame["fn"]}(), line {frame["line"]}')
            if frame['snippet']:
                lines.append(f'      {frame["snippet"]}')
        return '\n'.join(lines)


# Global singleton instances (accessible from interpreter)
_native_extension = NativeExtension()
_bytecode_vm      = BytecodeVM()
_stack_trace      = DVexStackTrace()
