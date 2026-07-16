# ROM info

## `Pokemon Prism (v0.95 build 254 Hotfix 5).gbc`

- **SHA1**: `752076692ae3387cf426ce5f51a98c6b60e8df6a` (mirrored in `../rom.sha1`)
- **File size**: 2,097,152 bytes (2 MB)
- **Header title**: `PM_PRISM`
- **CGB flag**: `0xC0` (CGB-only, matches Crystal)
- **Cartridge type**: `0x10` (MBC3+TIMER+RAM+BATTERY — same as retail Crystal,
  consistent with Prism keeping the RTC for day/night)
- **ROM size code**: `0x06` (2 MB)
- **RAM size code**: `0x03` (32 KB)
- **Destination code**: `0x01` (non-Japanese)
- **Version byte**: `0x00`
- **Release**: v0.95 build 254, Hotfix 5 — the source zip's internal filename
  and modification date (2023-08-25) both agree with this being that release.
- **Provenance**: user already had this ROM (and a second, older v0.94 build,
  2022-10-17) as zip files sitting in the workspace root; extracted into
  `rom/` on 2026-07-12 (session 2) once this subproject was otherwise blocked
  waiting for a ROM to arrive. v0.94 was not extracted/used — kept as a
  fallback only if a v0.95-specific offset ever needs cross-checking against
  an older build.
- **Full header field extraction command** (for re-verifying against a
  different copy): see `docs/TOOLCHAIN.md`'s "ROM acquired" note for the
  Python one-liner used to dump these fields.
