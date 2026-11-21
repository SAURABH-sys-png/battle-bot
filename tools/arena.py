#!/usr/bin/env python3
"""
Run our python bot against Version41 (java) on one or more maps and summarise.

  tools/arena.py --maps DefaultSmall,cheesefarm            # we are team A
  tools/arena.py --maps DefaultSmall --swap                # we are team B (Version41 is A)
  tools/arena.py --maps DefaultSmall --bc                  # also report python bytecode per role
  tools/arena.py --bot saurabh_py --opp Version41 --maps all
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "tools", "sitehook")

DEFAULT_MAPS = "DefaultSmall,DefaultMedium,DefaultLarge,cheesefarm,dirtfulcat"
ALL_MAPS = (
    "DefaultSmall DefaultMedium DefaultLarge cheesefarm dirtfulcat canyoudig tiny rift Meow "
    "EscapeTheNight TheHeist ZeroDay arrows cheesebottles cheeseguardians closeup "
    "corridorofdoomanddespair dirtpassageway evileye hatefullattice jail keepout knifefight "
    "mercifullattice minimaze peaceinourtime pipes popthecork safelycontained sittingducks "
    "starvation streetsofnewyork thunderdome toomuchcheese trapped uneruesansfin wallsofparadis"
).split()


def lang_of(name):
    return "java" if name.startswith("Version") else "python"


def run_one(bot, opp, map_name, swap, bc, timeout):
    a, b = (opp, bot) if swap else (bot, opp)
    replay_dir = os.path.join(ROOT, "matches", "arena")
    os.makedirs(replay_dir, exist_ok=True)
    replay = f"matches/arena/{a}-vs-{b}-on-{map_name}.bc26"
    cmd = [
        "./gradlew", "runLocal", "--offline", "-q",
        f"-PteamA={a}", f"-PlanguageA={lang_of(a)}", f"-PpackageNameA={a}",
        f"-PteamB={b}", f"-PlanguageB={lang_of(b)}", f"-PpackageNameB={b}",
        f"-Pmaps={map_name}", f"-Preplay={replay}",
    ]
    env = dict(os.environ)
    bc_out = None
    if bc:
        bc_out = f"/tmp/claude-1000/bc_{bot}_{map_name}.json"
        try:
            os.remove(bc_out)
        except OSError:
            pass
        env["PYTHONPATH"] = HOOK + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        env["BC_MEASURE_OUT"] = bc_out
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
        out = p.stdout + "\n" + p.stderr
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        out += "\nTIMEOUT"
    dt = time.time() - t0
    res = {"map": map_name, "secs": round(dt, 1), "winner": "?", "round": "?", "reason": "", "errors": []}
    me_team = "B" if swap else "A"
    for line in out.splitlines():
        m = re.search(r"\[server\]\s+(\S+) \((A|B)\) wins(?: \(round (\d+)\))?", line)
        if m:
            res["winner"] = m.group(2)
            res["round"] = m.group(3) or "?"
            res["won"] = (m.group(2) == me_team)
        m = re.search(r"Reason: (.*)", line)
        if m:
            res["reason"] = m.group(1).strip()
        if "ERROR" in line and f"[{me_team}:" in line:
            res["errors"].append(line.strip())
        if "Traceback" in line or "Exception" in line:
            if len(res["errors"]) < 6:
                res["errors"].append(line.strip())
    if "TIMEOUT" in out:
        res["reason"] = "TIMEOUT"
    res["out"] = out
    res["bc"] = None
    if bc_out and os.path.exists(bc_out):
        with open(bc_out) as f:
            res["bc"] = json.load(f)
    return res


def print_bc(bcstats):
    print("    tag                          turns   avg_ops   max_ops  avg_calls max_calls   max*3")
    for tag, s in sorted(bcstats.items()):
        n = s["n"]
        print(
            f"    {tag:<28} {n:6d} {s['sum']/n:9.0f} {s['max']:9d} {s['calls_sum']/n:9.1f} {s['calls_max']:9d} {s['max']*3:7d}"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default="saurabh_py")
    ap.add_argument("--opp", default="Version41")
    ap.add_argument("--maps", default=DEFAULT_MAPS)
    ap.add_argument("--swap", action="store_true", help="we play as team B")
    ap.add_argument("--both", action="store_true", help="play each map as A and as B")
    ap.add_argument("--bc", action="store_true", help="collect python bytecode stats")
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--log", action="store_true", help="print bot log lines (PROBE/DBG)")
    args = ap.parse_args()

    maps = ALL_MAPS if args.maps == "all" else args.maps.split(",")
    sides = [False, True] if args.both else [args.swap]
    wins = 0
    total = 0
    for mp in maps:
        for sw in sides:
            r = run_one(args.bot, args.opp, mp, sw, args.bc, args.timeout)
            total += 1
            won = r.get("won", False)
            wins += 1 if won else 0
            side = "B" if sw else "A"
            print(
                f"{mp:<22} as {side}: {'WIN ' if won else 'LOSS'}  winner={r['winner']} round={r['round']:>5} "
                f"({r['secs']}s)  {r['reason'][:70]}"
            )
            for e in r["errors"][:4]:
                print("    !!", e[:160])
            if args.log:
                for line in r["out"].splitlines():
                    if "DBG" in line or "PROBE" in line or "ERR" in line:
                        print("    |", line[:200])
            if r["bc"]:
                print_bc(r["bc"])
            sys.stdout.flush()
    print(f"\nTOTAL: {wins}/{total} wins")


if __name__ == "__main__":
    main()
