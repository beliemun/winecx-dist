import sys, re
f = sys.argv[1]
src = open(f).read()
orig = src

# 1) string.h 추가
if '#include <string.h>' not in src:
    src = src.replace('#include <stdlib.h>', '#include <stdlib.h>\n#include <string.h>', 1)

APPEND = '''    /* portability_subset patch: MoltenVK requires VK_KHR_portability_subset
     * enabled at device creation, but winevulkan does not expose it to the app. */
    {
        uint32_t _ps_i, _ps_n = out->enabledExtensionCount;
        int _ps_have = 0;
        for (_ps_i = 0; _ps_i < _ps_n; _ps_i++)
            if (out->ppEnabledExtensionNames[_ps_i] && !strcmp(out->ppEnabledExtensionNames[_ps_i], "VK_KHR_portability_subset")) { _ps_have = 1; break; }
        if (!_ps_have)
        {
            const char **_ps_names = conversion_context_alloc(ctx, (_ps_n + 1) * sizeof(*_ps_names));
            for (_ps_i = 0; _ps_i < _ps_n; _ps_i++) _ps_names[_ps_i] = out->ppEnabledExtensionNames[_ps_i];
            _ps_names[_ps_n] = "VK_KHR_portability_subset";
            out->ppEnabledExtensionNames = _ps_names;
            out->enabledExtensionCount = _ps_n + 1;
        }
    }
'''

def patch_func(src, func_sig, ext_line):
    idx = src.find(func_sig)
    if idx < 0:
        raise SystemExit(f"함수 못찾음: {func_sig}")
    line_idx = src.find(ext_line, idx)
    if line_idx < 0:
        raise SystemExit(f"확장 라인 못찾음 in {func_sig}")
    insert_at = src.find('\n', line_idx) + 1
    return src[:insert_at] + APPEND + src[insert_at:]

# win64: out->ppEnabledExtensionNames = in->ppEnabledExtensionNames;
src = patch_func(src, 'convert_VkDeviceCreateInfo_win64_to_host',
                 'out->ppEnabledExtensionNames = in->ppEnabledExtensionNames;')
# win32: out->ppEnabledExtensionNames = convert_char_pointer_array_win32_to_host(...
src = patch_func(src, 'convert_VkDeviceCreateInfo_win32_to_host',
                 'out->ppEnabledExtensionNames = convert_char_pointer_array_win32_to_host(ctx, (const PTR32 *)UlongToPtr(in->ppEnabledExtensionNames), in->enabledExtensionCount);')

if src == orig:
    raise SystemExit("변경 없음!")
open(f,'w').write(src)
print("패치 적용 완료:", src.count('VK_KHR_portability_subset patch') if False else "2개 함수 + string.h")
