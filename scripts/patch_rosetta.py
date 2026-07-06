#!/usr/bin/env python3
# Rosetta 2 workaround for Blizzard anti-cheat (D2R_loader.dll) startup deadlock.
#
# 진단(lldb+sample): D2R_loader.dll의 DllMain에서 안티치트가 워커 스레드들을
# SuspendThread로 정지시킨 뒤, 메인 스레드가 NtWaitForAlertByThreadId로 그 워커의
# 알림을 무한 대기 → 정지된 워커는 알림 못 보냄 → Rosetta에서 데드락(0.7초).
# 안티치트는 ntdll export를 우회해 syscall을 직접 호출하므로, 반드시 거치는
# wineserver 서버측 suspend를 무력화한다.
#
# 패치: server/thread.c의 suspend_thread()에서 stop_thread() 호출 제거.
# → SuspendThread가 suspend 카운트만 올리고 스레드를 실제로 멈추지 않음.
#   워커가 계속 실행되어 알림을 보냄 → 데드락 소멸. GetThreadContext는
#   thread->context가 NULL이면 unix 레벨(mach)로 실행중 스레드에서 잡음.
import sys, os

path = sys.argv[1]
src = open(path).read()

# 내용 기반 감지: server/thread.c 만 처리 (dlls/ntdll/unix/thread.c 와 파일명 동일)
if "int suspend_thread( struct thread *thread )" in src and "stop_thread( thread )" in src:
    old = """    int old_count = thread->suspend;
    if (thread->suspend < MAXIMUM_SUSPEND_COUNT)
    {
        if (!is_thread_suspended( thread )) stop_thread( thread );
        thread->suspend++;
    }"""
    new = """    int old_count = thread->suspend;
    if (thread->suspend < MAXIMUM_SUSPEND_COUNT)
    {
        /* rosetta workaround: do NOT actually stop the thread. Blizzard anti-cheat
         * (D2R_loader) suspends its worker threads then waits (NtWaitForAlertByThreadId)
         * for them to signal; under Rosetta 2 the suspended worker can never signal so
         * it deadlocks. Keeping the thread running lets it signal, breaking the deadlock. */
        thread->suspend++;
    }"""
    n = src.count(old)
    if n != 1:
        print(f"ERROR server/thread.c: expected 1 suspend_thread body, found {n}", file=sys.stderr)
        sys.exit(1)
    src = src.replace(old, new)
    open(path, "w").write(src)
    print("server/thread.c: suspend_thread no longer stops the thread")
else:
    print(f"SKIP: {path} is not server/thread.c (no suspend_thread), leaving unchanged")
