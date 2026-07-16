# rom/

This directory is gitignored — never commit ROM files here.

Two files are expected before Phase 1 (reverse engineering) can start:

- **A Pokemon Prism ROM** (`.gbc`). This is the actual target of the port.
- **A vanilla Pokemon Crystal ROM** (`.gbc`), any legitimate dump. Used to build
  a byte-identical(ish) reference ROM from `pret/pokecrystal` source and bindiff
  it against the real Prism ROM — since Prism is a direct Crystal derivative,
  this localizes Prism's shifted-but-related routines (catch handler, gift/trade,
  PC deposit) far faster than blind search. See `../docs/TOOLCHAIN.md`.

Once both files are in place:
1. Compute and record their SHA1 in `../rom.sha1` — every later finding
   (offsets, routine addresses, free-space regions) is pinned to that checksum.
   Re-verify before trusting any note against a different copy/revision.
2. Phase 1 can begin.
