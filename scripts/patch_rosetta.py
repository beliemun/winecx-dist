#!/usr/bin/env python3
# Rosetta 2 workaround for Blizzard anti-cheat (D2R_loader.dll) startup deadlock.
#
# 진단(스택 샘플): 안티치트가 워커 스레드 4개를 SuspendThread로 정지시킨 뒤,
# 컨트롤러 스레드가 그 정지된 워커들이 시그널하기를 무한 대기 → Rosetta 타이밍
# 차이로 데드락(0.7초, 0% CPU, 창 없음). Wine 동기화 프리미티브(futex/inproc/msync)
# 교체로는 해결 안 됨(2회 검증) → 서스펜션 자체를 무력화한다.
#
# 패치: NtSuspendThread를 실제 정지 없이 즉시 STATUS_SUCCESS 반환.
# 안티치트가 "정지"시킨 워커가 실제론 계속 실행 → 시그널 도달 → 데드락 소멸.
import sys, os

path = sys.argv[1]
base = os.path.basename(path)
src = open(path).read()

if base == "thread.c":
    old = """NTSTATUS WINAPI NtSuspendThread( HANDLE handle, ULONG *count )
{
    unsigned int ret;

    SERVER_START_REQ( suspend_thread )
    {
        req->handle = wine_server_obj_handle( handle );
        if (!(ret = wine_server_call( req )))
        {
            if (count) *count = reply->count;
        }
    }
    SERVER_END_REQ;
    return ret;
}"""
    new = """NTSTATUS WINAPI NtSuspendThread( HANDLE handle, ULONG *count )
{
    /* rosetta workaround: no-op suspend. Blizzard anti-cheat (D2R_loader) suspends
     * its own worker threads then waits for them to signal; under Rosetta 2 the
     * timing deadlocks. Not actually suspending keeps the workers running so they
     * still signal, breaking the deadlock. */
    if (count) *count = 0;
    return STATUS_SUCCESS;
}"""
    n = src.count(old)
    if n != 1:
        print(f"ERROR thread.c: expected 1 NtSuspendThread body, found {n}", file=sys.stderr)
        sys.exit(1)
    src = src.replace(old, new)
    open(path, "w").write(src)
    print("thread.c: NtSuspendThread -> no-op (return SUCCESS)")

else:
    print(f"ERROR: unexpected file {base}", file=sys.stderr)
    sys.exit(1)
