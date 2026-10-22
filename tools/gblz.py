#!/usr/bin/env python3
"""pokecrystal-format LZ (de)compression, used by Prism's pic loader (GetTrainerPic 0B:707C ->
$09F3). decompress(rom, offset) -> (bytes, compressed length)."""


def decompress(data, off=0):
    out = bytearray()
    i = off
    while True:
        b = data[i]; i += 1
        if b == 0xFF:
            return bytes(out), i - off
        if b >> 5 == 7:                       # long command
            cmd = (b >> 2) & 7
            n = (((b & 3) << 8) | data[i]) + 1; i += 1
        else:
            cmd = b >> 5
            n = (b & 0x1F) + 1
        if cmd == 0:
            out += data[i:i + n]; i += n
        elif cmd == 1:
            out += bytes([data[i]]) * n; i += 1
        elif cmd == 2:
            a, c = data[i], data[i + 1]; i += 2
            out += bytes((a, c)[k & 1] for k in range(n))
        elif cmd == 3:
            out += bytes(n)
        else:
            p = data[i]; i += 1
            if p & 0x80:
                src = len(out) - (p & 0x7F) - 1
            else:
                src = (p << 8) | data[i]; i += 1
            if cmd == 4:
                for k in range(n):
                    out.append(out[src + k])
            elif cmd == 5:
                for k in range(n):
                    x = out[src + k]
                    out.append(int('{:08b}'.format(x)[::-1], 2))
            elif cmd == 6:
                for k in range(n):
                    out.append(out[src - k])


def compress(data):
    """Simple valid encoder: literals, zero runs, byte runs, and back-references (cmd 4)."""
    out = bytearray()
    i, n = 0, len(data)
    lit = bytearray()

    def emit(cmd, length, payload=b""):
        length -= 1
        if length < 32 and cmd != 7:
            out.append(cmd << 5 | length)
        else:
            out.append(0xE0 | cmd << 2 | length >> 8); out.append(length & 0xFF)
        out.extend(payload)

    def flush():
        nonlocal lit
        while lit:
            chunk = lit[:1024]; lit = lit[1024:]
            emit(0, len(chunk), chunk)

    while i < n:
        # zero / byte run
        run = 1
        while i + run < n and data[i + run] == data[i] and run < 1024:
            run += 1
        # back reference
        best_len, best_src = 0, 0
        lo = max(0, i - 0x7FFF)
        for s in range(lo, i):
            L = 0
            while i + L < n and data[s + L] == data[i + L] and L < 1024:
                L += 1
            if L > best_len:
                best_len, best_src = L, s
        if run >= 3 and run >= best_len:
            flush()
            if data[i] == 0:
                emit(3, run)
            else:
                emit(1, run, bytes([data[i]]))
            i += run
        elif best_len >= 4:
            flush()
            d = i - best_src - 1
            if d < 0x80:
                emit(4, best_len, bytes([0x80 | d]))
            else:
                emit(4, best_len, bytes([best_src >> 8, best_src & 0xFF]))
            i += best_len
        else:
            lit.append(data[i]); i += 1
    flush()
    out.append(0xFF)
    return bytes(out)
