import battlecode.schema.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

/** Dump a .bc26 replay as a compact per-interval table.  usage: ReplayDump file [interval] [verbose] */
public class ReplayDump {
    static class TT extends com.google.flatbuffers.Table {
        int pos() { return bb_pos; }
        ByteBuffer buf() { return bb; }
    }

    static byte[] readAll(String path) throws IOException {
        byte[] b = Files.readAllBytes(Paths.get(path));
        if (b.length > 2 && (b[0] & 0xff) == 0x1f && (b[1] & 0xff) == 0x8b) {
            try (GZIPInputStream in = new GZIPInputStream(new ByteArrayInputStream(b))) {
                return in.readAllBytes();
            }
        }
        return b;
    }

    public static void main(String[] a) throws Exception {
        byte[] data = readAll(a[0]);
        int interval = a.length > 1 ? Integer.parseInt(a[1]) : 25;
        boolean verbose = a.length > 2 && a[2].equals("v");
        int posFrom = -1, posTo = -1, posEvery = 1;
        if (a.length > 4 && a[2].equals("pos")) { posFrom = Integer.parseInt(a[3]); posTo = Integer.parseInt(a[4]); if (a.length > 5) posEvery = Integer.parseInt(a[5]); }
        GameWrapper gw = GameWrapper.getRootAsGameWrapper(ByteBuffer.wrap(data));
        Map<Integer, int[]> info = new HashMap<>(); // id -> {team, type}
        int[] teamIds = new int[2];
        int[] atk = new int[2], died = new int[2], spawned = new int[2], traps = new int[2], squeaks = new int[2], digs = new int[2], places = new int[2];
        int[] catAtk = new int[2];
        int[][] hist = new int[3][32];
        java.util.TreeMap<Integer,Integer>[] dmgHist = new java.util.TreeMap[3];
        for (int i = 0; i < 3; i++) dmgHist[i] = new java.util.TreeMap<>();
        int[][] hit = new int[3][4]; // attacker team (0,1,cat) x target kind (T0 baby, T0 king, T1 baby, T1 king)
        String[] names = new String[2];
        int W = 0, H = 0;
        for (int i = 0; i < gw.eventsLength(); i++) {
            EventWrapper ev = gw.events(i);
            byte t = ev.eType();
            if (t == Event.GameHeader) {
                GameHeader gh = (GameHeader) ev.e(new GameHeader());
                for (int k = 0; k < gh.teamsLength() && k < 2; k++) names[k] = gh.teams(k).name();
            } else if (t == Event.MatchHeader) {
                MatchHeader mh = (MatchHeader) ev.e(new MatchHeader());
                GameMap gm = mh.map();
                InitialBodyTable ib = gm.initialBodies();
                for (int k = 0; k < ib.spawnActionsLength(); k++) {
                    SpawnAction sa = ib.spawnActions(k);
                    info.put(sa.id(), new int[]{sa.team(), sa.robotType()});
                }
                System.out.println("MAP " + mh.map().name() + " teams " + names[0] + " vs " + names[1]);
            } else if (t == Event.Round) {
                Round r = (Round) ev.e(new Round());
                if (r.teamIdsLength() >= 2) { teamIds[0] = r.teamIds(0); teamIds[1] = r.teamIds(1); }
                int rn = r.roundId();
                int[] kx = {-1, -1}, ky = {-1, -1}, kh = {0, 0}, nk = {0, 0};
                int[] nb = {0, 0}, hpsum = {0, 0};
                int[] catx = {-1}, caty = {-1};
                StringBuilder[] pl = {new StringBuilder(), new StringBuilder(), new StringBuilder()};
                for (int k = 0; k < r.turnsLength(); k++) {
                    Turn tu = r.turns(k);
                    int[] inf = info.get(tu.robotId());
                    if (inf == null) continue;
                    int ti = inf[0] == teamIds[0] ? 0 : (inf[0] == teamIds[1] ? 1 : -1);
                    if (inf[1] == RobotType.CAT) { pl[2].append(" CAT(" + tu.x() + "," + tu.y() + ")hp" + tu.health()); continue; }
                    if (inf[1] == RobotType.RAT_KING && ti >= 0) {
                        if (kh[ti] == 0 || tu.health() > kh[ti]) { kx[ti] = tu.x(); ky[ti] = tu.y(); }
                        kh[ti] += tu.health(); nk[ti]++;
                    } else if (inf[1] == RobotType.RAT && ti >= 0) {
                        nb[ti]++; hpsum[ti] += tu.health();
                        pl[ti].append(" (" + tu.x() + "," + tu.y() + ")" + tu.health() + "/d" + tu.dir() + (tu.cheese() > 0 ? "c" + tu.cheese() : ""));
                    }
                    for (int q = 0; q < tu.actionsLength(); q++) {
                        byte at = tu.actionsType(q);
                        hist[ti >= 0 ? ti : 2][at]++;
                        if (at == Action.SpawnAction) {
                            SpawnAction sa = new SpawnAction();
                            sa.__assign(com.google.flatbuffers.Acc.unionPos(tu, 26, q), com.google.flatbuffers.Acc.bb(tu));
                            info.put(sa.id(), new int[]{sa.team(), sa.robotType()});
                            int tj = sa.team() == teamIds[0] ? 0 : 1;
                            if (sa.robotType() == RobotType.RAT) spawned[tj]++;
                        } else if (at == Action.RatAttack && ti >= 0) { atk[ti]++; }
                        else if (at == Action.PlaceTrap && ti >= 0) { traps[ti]++; }
                        if (at == Action.DamageAction) {
                            int off2 = com.google.flatbuffers.Acc.unionPos(tu, 26, q);
                            java.nio.ByteBuffer b2 = com.google.flatbuffers.Acc.bb(tu);
                            int vid = b2.getShort(off2) & 0xffff;
                            int dm = b2.getShort(off2 + 2) & 0xffff;
                            int[] vi = info.get(vid);
                            int vt = 2;
                            if (vi != null) vt = vi[0] == teamIds[0] ? 0 : (vi[0] == teamIds[1] ? 1 : 2);
                            dmgHist[vt].merge(dm, 1, Integer::sum);
                        }
                        if (at == Action.RatAttack && ti >= 0) {
                            int off = com.google.flatbuffers.Acc.unionPos(tu, 26, q);
                            int tid = com.google.flatbuffers.Acc.bb(tu).getShort(off) & 0xffff;
                            int[] ti2 = info.get(tid);
                            if (ti2 == null) { hit[ti][3]++; }
                            else {
                                int tj = ti2[0] == teamIds[0] ? 0 : (ti2[0] == teamIds[1] ? 1 : -1);
                                if (tj < 0) hit[ti][2]++; else hit[ti][tj]++;
                            }
                        }
                        else if (at == Action.PlaceDirt && ti >= 0) { places[ti]++; }
                        else if (at == Action.BreakDirt && ti >= 0) { digs[ti]++; }
                        else if (at == Action.CatScratch) { catAtk[0]++; }
                        else if (at == Action.UpgradeToRatKing && ti >= 0) {
                            System.out.println("  r" + rn + " team" + ti + " UPGRADE to king at " + tu.x() + "," + tu.y());
                            info.put(tu.robotId(), new int[]{inf[0], RobotType.RAT_KING});
                        }
                    }
                }
                for (int k = 0; k < r.diedIdsLength(); k++) {
                    int[] inf = info.get(r.diedIds(k));
                    if (inf != null) {
                        int ti = inf[0] == teamIds[0] ? 0 : (inf[0] == teamIds[1] ? 1 : -1);
                        if (ti >= 0) died[ti]++;
                    }
                }
                if (posFrom >= 0 && rn >= posFrom && rn <= posTo && (rn - posFrom) % posEvery == 0) {
                    System.out.println("== r" + rn + " T0 king " + kx[0] + "," + ky[0] + " hp" + kh[0] + " | T1 king " + kx[1] + "," + ky[1] + " hp" + kh[1]);
                    System.out.println("  T0:" + pl[0]);
                    System.out.println("  T1:" + pl[1]);
                    System.out.println("  cats:" + pl[2]);
                }
                if (posFrom >= 0) { atk = new int[2]; continue; }
                if (rn % interval == 0 || rn == 1 || (verbose && rn % 5 == 0)) {
                    StringBuilder sb = new StringBuilder();
                    sb.append(String.format("r%4d ", rn));
                    for (int ti = 0; ti < 2; ti++) {
                        sb.append(String.format("| T%d babies %2d(hp%4d) kings %d hp%4d @%2d,%2d  xfer %4d catdmg %4d traps %2d | bites %3d died %3d dig %2d dirt %2d ",
                                ti, nb[ti], hpsum[ti], nk[ti], kh[ti], kx[ti], ky[ti],
                                r.teamCheeseTransferredLength() > ti ? r.teamCheeseTransferred(ti) : -1,
                                r.teamCatDamageLength() > ti ? r.teamCatDamage(ti) : -1,
                                r.teamRatTrapCountLength() > ti ? r.teamRatTrapCount(ti) : -1,
                                atk[ti], died[ti], digs[ti], places[ti]));
                    }
                    System.out.println(sb);
                    if (verbose) {
                        StringBuilder hb = new StringBuilder("      acts:");
                        for (int ti = 0; ti < 3; ti++) {
                            hb.append(" [" + (ti < 2 ? "T" + ti : "cat") + "]");
                            for (int at = 1; at < 25; at++) {
                                if (at == 22 || at == 23 || at == 24) continue;
                                if (hist[ti][at] > 0) hb.append(" " + Action.names[at] + "=" + hist[ti][at]);
                            }
                        }
                        System.out.println(hb);
                    }
                    if (verbose) {
                        System.out.println("      hits: T0->T0 " + hit[0][0] + " T0->T1 " + hit[0][1] + " T0->cat " + hit[0][2] + " | T1->T0 " + hit[1][0] + " T1->T1 " + hit[1][1] + " T1->cat " + hit[1][2] + " unk " + hit[0][3] + "/" + hit[1][3]);
                    }
                    if (verbose) { System.out.println("      damage taken T0: " + dmgHist[0] + "  T1: " + dmgHist[1] + "  other: " + dmgHist[2]); }
                    for (int qq = 0; qq < 3; qq++) dmgHist[qq] = new java.util.TreeMap<>();
                    hit = new int[3][4];
                    hist = new int[3][32];
                    atk = new int[2]; died = new int[2]; digs = new int[2]; places = new int[2];
                }
            }
        }
    }
}
