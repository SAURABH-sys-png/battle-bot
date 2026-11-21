package com.google.flatbuffers;
public class Acc {
    public static int unionPos(Table t, int voff, int j) {
        int o = t.__offset(voff);
        if (o == 0) return -1;
        int e = t.__vector(o) + j * 4;
        return e + t.bb.getInt(e);
    }
    public static java.nio.ByteBuffer bb(Table t) { return t.bb; }
}
