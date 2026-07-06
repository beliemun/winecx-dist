#!/usr/bin/env python3
# Rosetta 2 workaround for Blizzard anti-cheat (D2R_loader.dll) deadlock.
# 파일 basename으로 분기:
#   sync.c   : futex_wait/wake가 os_sync_wait_on_address(macOS14.4+ 신 API) 대신 구 __ulock 사용
#   server.c : inproc(in-process futex 동기화) 비활성 → 모든 대기를 wineserver(Mach) 경로로 강제
# 목적: 유저공간 원자 compare-and-wait(Rosetta TSO 오처리 의심)를 피해 데드락 우회.
import sys, os

path = sys.argv[1]
base = os.path.basename(path)
src = open(path).read()

if base == "sync.c":
    old = "#ifdef MAC_OS_VERSION_14_4\n    if (__builtin_available( macOS 14.4, * ))"
    new = "#if 0 /* rosetta: force __ulock, skip os_sync_wait_on_address */\n    if (__builtin_available( macOS 14.4, * ))"
    n = src.count(old)
    if n != 2:
        print(f"ERROR sync.c: expected 2 os_sync blocks, found {n}", file=sys.stderr); sys.exit(1)
    src = src.replace(old, new)
    open(path, "w").write(src)
    print(f"sync.c: patched {n} os_sync blocks -> #if 0 (force __ulock)")

elif base == "server.c":
    old = ("                inproc_device_fd = wine_server_receive_fd( &handle );\n"
           "                assert( handle == reply->inproc_device );")
    new = ("                inproc_device_fd = wine_server_receive_fd( &handle );\n"
           "                assert( handle == reply->inproc_device );\n"
           "                close( inproc_device_fd ); inproc_device_fd = -1; /* rosetta: disable inproc, force server sync */")
    n = src.count(old)
    if n != 1:
        print(f"ERROR server.c: expected 1 inproc assign, found {n}", file=sys.stderr); sys.exit(1)
    src = src.replace(old, new)
    open(path, "w").write(src)
    print("server.c: inproc disabled (close fd, keep -1)")

else:
    print(f"ERROR: unexpected file {base}", file=sys.stderr); sys.exit(1)
