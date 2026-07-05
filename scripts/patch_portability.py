import sys
f = sys.argv[1]  # dlls/win32u/vulkan.c
src = open(f).read()
orig = src

anchor = '    TRACE( "Enabling %u host device extensions\\n", count );'
if anchor not in src:
    raise SystemExit("앵커(host device extensions TRACE) 못찾음")

inject = '''    /* MoltenVK is a portability driver; the Vulkan loader mandates that
       VK_KHR_portability_subset be enabled at vkCreateDevice. winevulkan does not
       expose it to the Windows client, so the app never requests it. Append it
       directly to the host device extension list (macOS build => MoltenVK always
       advertises it). Fixes VK_ERROR_INITIALIZATION_FAILED (-3) under ANGLE/CEF. */
    extensions[count++] = "VK_KHR_portability_subset";

'''
src = src.replace(anchor, inject + anchor, 1)

if src == orig:
    raise SystemExit("변경 없음")
open(f,'w').write(src)
print("win32u/vulkan.c convert_device_create_info 패치 완료")
