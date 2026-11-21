"""
Bytecode / call-count measurement hook for the local Python battlecode runner.

The local runner (battlecode26 1.2.2) does NOT enforce the Python bytecode limit: the bot source
is exec'd uninstrumented, so `bytecode_used` is always 0.  The tournament server converts Python
bytecode with a x3 multiplier before comparing to the Java limits (17500 baby rat / 20000 king),
so a baby rat must stay under ~5833 counted ops per turn and a king under ~6666.

This hook is activated by putting this directory on PYTHONPATH and setting BC_MEASURE_OUT=<json path>.
It uses sys.monitoring (PEP 669) to count executed instructions ONLY inside bot code objects, using the
official instrumenter's EXCLUDE list (LOAD_FAST, STORE_FAST, LOAD_GLOBAL, ... are free), and counts
crossplay round trips (rc.* calls) per turn.  Per-turn data is aggregated by (team, tag) where tag is
whatever the bot stored in TAG[0] (module global of bot.py).
"""
import os
import sys
import atexit
import json

OUT = os.environ.get("BC_MEASURE_OUT")

if OUT:
    import dis
    from types import CodeType

    EXCLUDED = set(
        dis.opmap[n]
        for n in [
            "CACHE", "JUMP_FORWARD", "POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE", "LOAD_GLOBAL", "COPY",
            "LOAD_FAST", "STORE_FAST", "GET_AWAITABLE", "KW_NAMES", "EXTENDED_ARG", "RESUME",
        ]
    )
    mon = sys.monitoring
    TOOL = mon.PROFILER_ID
    mon.use_tool_id(TOOL, "bcmeasure")

    counter = [0]
    counted_cache = {}

    def on_instr(code, offset):
        tab = counted_cache.get(code)
        if tab is None:
            raw = code.co_code
            tab = [raw[i] not in EXCLUDED for i in range(0, len(raw), 2)]
            counted_cache[code] = tab
        if tab[offset >> 1]:
            counter[0] += 1

    mon.register_callback(TOOL, mon.events.INSTRUCTION, on_instr)

    seen = {}   # id(code) -> code  (code objects compare equal by value, identity is what matters)

    def watch_code(code):
        if id(code) in seen:
            return
        seen[id(code)] = code
        mon.set_local_events(TOOL, code, mon.events.INSTRUCTION)
        for c in code.co_consts:
            if isinstance(c, CodeType):
                watch_code(c)

    def watch_namespace(ns):
        for v in list(ns.values()):
            code = getattr(v, "__code__", None)
            if isinstance(code, CodeType):
                watch_code(code)

    import battlecode26.runner as runner_mod
    import battlecode26.crossplay as cp

    # --- count rc round trips ---------------------------------------------------------------
    calls = [0]
    orig_swp = cp.send_wait_and_parse

    def counting_swp(*a, **k):
        calls[0] += 1
        return orig_swp(*a, **k)

    cp.send_wait_and_parse = counting_swp
    import battlecode26.wrappers as wr
    wr._wait = counting_swp

    # --- watch bot code ---------------------------------------------------------------------
    RR = runner_mod.RobotRunner
    orig_init = RR.init_robot
    orig_import = RR.import_call
    orig_run = RR.run

    def init_robot(self):
        orig_init(self)
        watch_namespace(self.globals)
        watch_namespace(self.locals)

    def import_call(self, name, globals=None, locals=None, fromlist=(), level=0, caller="robot"):
        mod = orig_import(self, name, globals, locals, fromlist, level, caller)
        d = getattr(mod, "__dict__", None)
        if d is not None and name not in ("random", "math", "enum", "battlecode26"):
            watch_namespace(d)
        return mod

    stats = {}

    def run(self):
        counter[0] = 0
        calls[0] = 0
        orig_run(self)
        used = counter[0]
        c = calls[0]
        tagbox = self.globals.get("TAG")
        tag = tagbox[0] if tagbox else "?"
        s = stats.setdefault(tag, {"n": 0, "sum": 0, "max": 0, "calls_sum": 0, "calls_max": 0, "hist": {}})
        s["n"] += 1
        s["sum"] += used
        s["calls_sum"] += c
        if used > s["max"]:
            s["max"] = used
        if c > s["calls_max"]:
            s["calls_max"] = c
        b = (used // 500) * 500
        s["hist"][b] = s["hist"].get(b, 0) + 1

    RR.init_robot = init_robot
    RR.import_call = import_call
    RR.run = run

    def dump():
        try:
            with open(str(OUT), "w") as f:
                json.dump(stats, f)
        except Exception:
            pass

    atexit.register(dump)
