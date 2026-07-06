#!/usr/bin/env python3
# Rosetta 2 workaround: Blizzard의 새 안티치트가 x86 코드를 Rosetta 2로 돌릴 때
# os_sync_wait_on_address(macOS 14.4+ 신 API)에서 데드락한다.
# futex_wait/futex_wake_one이 os_sync 경로를 건너뛰고 항상 구 __ulock_wait/__ulock_wake를
# 쓰도록 강제한다. (CrossOver 3월 프리뷰의 우회책으로 추정)
import sys

path = sys.argv[1]
src = open(path).read()

# futex_wait / futex_wake_one 안의 os_sync 블록을 #if 0 으로 비활성 → __ulock 폴백 강제
old = "#ifdef MAC_OS_VERSION_14_4\n    if (__builtin_available( macOS 14.4, * ))"
new = "#if 0 /* rosetta: force __ulock, skip os_sync_wait_on_address */\n    if (__builtin_available( macOS 14.4, * ))"

count = src.count(old)
if count != 2:
    print(f"ERROR: expected 2 os_sync blocks, found {count} — aborting", file=sys.stderr)
    sys.exit(1)

src = src.replace(old, new)
open(path, "w").write(src)
print(f"patched {count} os_sync blocks -> #if 0 (force __ulock)")
