import sys
f = sys.argv[1]
src = open(f).read()
D24 = "VK_FORMAT_D24_UNORM_S8_UINT"
D32 = "VK_FORMAT_D32_SFLOAT_S8_UINT"

def patch_plain(src, callline, pd_expr, fp_expr):
    ins = ('\n    if (params->format == %s && !(%s)->optimalTilingFeatures)\n'
           '        vulkan_physical_device_from_handle(%s)->instance->p_vkGetPhysicalDeviceFormatProperties(vulkan_physical_device_from_handle(%s)->host.physical_device, %s, %s);'
           % (D24, fp_expr, pd_expr, pd_expr, D32, fp_expr))
    i = src.find(callline)
    if i < 0:
        raise SystemExit("plain anchor not found: " + callline[:50])
    end = src.find(';', i) + 1
    return src[:end] + ins + src[end:]

def patch_2(src, callline, pd_expr, fp_expr):
    ins = ('\n    if (params->format == %s && !(%s)->formatProperties.optimalTilingFeatures)\n'
           '        vulkan_physical_device_from_handle(%s)->instance->p_vkGetPhysicalDeviceFormatProperties2(vulkan_physical_device_from_handle(%s)->host.physical_device, %s, %s);'
           % (D24, fp_expr, pd_expr, pd_expr, D32, fp_expr))
    i = src.find(callline)
    if i < 0:
        raise SystemExit("2 anchor not found: " + callline[:50])
    end = src.find(';', i) + 1
    return src[:end] + ins + src[end:]

# 64-bit plain
src = patch_plain(src,
  "->p_vkGetPhysicalDeviceFormatProperties(vulkan_physical_device_from_handle(params->physicalDevice)->host.physical_device, params->format, params->pFormatProperties);",
  "params->physicalDevice", "params->pFormatProperties")
# 32-bit plain
src = patch_plain(src,
  "->p_vkGetPhysicalDeviceFormatProperties(vulkan_physical_device_from_handle((VkPhysicalDevice)UlongToPtr(params->physicalDevice))->host.physical_device, params->format, (VkFormatProperties *)UlongToPtr(params->pFormatProperties));",
  "(VkPhysicalDevice)UlongToPtr(params->physicalDevice)", "(VkFormatProperties *)UlongToPtr(params->pFormatProperties)")
# 64-bit properties2
src = patch_2(src,
  "->p_vkGetPhysicalDeviceFormatProperties2(vulkan_physical_device_from_handle(params->physicalDevice)->host.physical_device, params->format, params->pFormatProperties);",
  "params->physicalDevice", "params->pFormatProperties")

open(f, 'w').write(src)
print("D24 patch applied count:", src.count("VK_FORMAT_D24_UNORM_S8_UINT"))
