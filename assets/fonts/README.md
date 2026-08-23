# Bundled font record

CultureShift bundles one font for deterministic English and Simplified Chinese fixture
composition.

| Field | Value |
| --- | --- |
| File | `NotoSansCJKsc-Regular.otf` |
| Family / style | Noto Sans CJK SC Regular |
| Upstream | `https://github.com/notofonts/noto-cjk` |
| Pinned commit | `f8d157532fbfaeda587e826d4cd5b21a49186f7c` |
| Upstream path | `Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf` |
| Retrieval date | 2026-08-23 |
| Size | 16,437,364 bytes |
| SHA-256 | `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b` |
| Licence | SIL Open Font License 1.1 |
| Licence file | `OFL-1.1.txt` |
| Licence SHA-256 | `6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2` |
| Permitted project use | Bundle, embed, and redistribute with the licence retained |

The font is used unchanged. The compositor fails closed if the file is missing, has a
different hash, or cannot be loaded by Pillow. It never falls back to a machine font.
