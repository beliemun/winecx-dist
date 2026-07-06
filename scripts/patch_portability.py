import sys
f = sys.argv[1]  # dlls/winevulkan/loader.c
src = open(f).read()
orig = src

anchor = '''        if (!is_device_extension_supported(physical_device, extension, &extensions))
            return VK_ERROR_EXTENSION_NOT_PRESENT;'''
repl = '''        if (strcmp(extension, "VK_KHR_portability_subset") &&
            !is_device_extension_supported(physical_device, extension, &extensions))
            return VK_ERROR_EXTENSION_NOT_PRESENT;'''

if anchor not in src:
    raise SystemExit("앵커(vkCreateDevice device ext reject) 못찾음")
n = src.count(anchor)
if n != 1:
    raise SystemExit(f"앵커가 {n}번 나타남 (1개여야 함)")
src = src.replace(anchor, repl, 1)
if src == orig:
    raise SystemExit("변경 없음")
open(f,'w').write(src)
print("loader.c vkCreateDevice portability_subset 통과 패치 완료")
