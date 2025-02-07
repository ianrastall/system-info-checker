#!/usr/bin/env python3
import platform
import subprocess
import re
import sys
import os
import io

###############################################################################
# Utilities
###############################################################################

def print_and_write(f, text=""):
    """
    Write the provided text to the file-like object.
    (Console output is suppressed.)
    """
    f.write(text + "\n")

def parse_key_value_lines(output):
    """
    Takes text like:
        Key=Value
        AnotherKey=Value2
    Returns a dict: {"Key": "Value", "AnotherKey": "Value2"}
    """
    info = {}
    for line in output.splitlines():
        line = line.strip()
        if '=' in line:
            key, val = line.split('=', 1)
            info[key.strip()] = val.strip()
    return info

###############################################################################
# Windows
###############################################################################

def get_windows_memory_mb():
    """
    Attempts to retrieve total system memory (in MB) on Windows via WMIC.
    Returns a float or None on failure.
    """
    try:
        mem_cmd = ["wmic", "OS", "get", "TotalVisibleMemorySize", "/format:list"]
        mem_output = subprocess.check_output(mem_cmd, universal_newlines=True, stderr=subprocess.DEVNULL)
        mem_info = parse_key_value_lines(mem_output)
        kb_str = mem_info.get("TotalVisibleMemorySize", "")
        if kb_str.isdigit():
            return float(kb_str) / 1024.0  # Convert from KB to MB
    except:
        pass
    return None

def print_windows_info(f):
    """
    Gathers CPU & memory info on Windows (using WMIC) and writes to the file-like object.
    """
    try:
        cpu_cmd = [
            'wmic', 'cpu', 'get',
            'Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,L2CacheSize,L3CacheSize,VirtualizationFirmwareEnabled',
            '/format:list'
        ]
        cpu_output = subprocess.check_output(cpu_cmd, universal_newlines=True, stderr=subprocess.DEVNULL)
        cpu_info = parse_key_value_lines(cpu_output)

        print_and_write(f, "=== CPU Information (Windows) ===")
        print_and_write(f, f"CPU Name: {cpu_info.get('Name', 'Unknown')}")
        if 'MaxClockSpeed' in cpu_info and cpu_info['MaxClockSpeed'].isdigit():
            print_and_write(f, f"Base Speed: {cpu_info['MaxClockSpeed']} MHz")
        if 'NumberOfCores' in cpu_info:
            print_and_write(f, f"Cores: {cpu_info['NumberOfCores']}")
        if 'NumberOfLogicalProcessors' in cpu_info:
            print_and_write(f, f"Logical processors: {cpu_info['NumberOfLogicalProcessors']}")
        if 'L2CacheSize' in cpu_info and cpu_info['L2CacheSize'].isdigit():
            l2_kb = int(cpu_info['L2CacheSize'])
            print_and_write(f, f"L2 cache: {l2_kb / 1024.0:.1f} MB")
        if 'L3CacheSize' in cpu_info and cpu_info['L3CacheSize'].isdigit():
            l3_kb = int(cpu_info['L3CacheSize'])
            print_and_write(f, f"L3 cache: {l3_kb / 1024.0:.1f} MB")
        virt_str = cpu_info.get('VirtualizationFirmwareEnabled', '')
        if virt_str.lower() == 'true':
            print_and_write(f, "Virtualization: Enabled (BIOS/firmware)")
        else:
            print_and_write(f, "Virtualization: Not reported as enabled")
    except FileNotFoundError:
        print_and_write(f, "wmic command not found on this system.")
    except subprocess.SubprocessError:
        print_and_write(f, "Failed to retrieve CPU info via wmic.")

    mem_mb = get_windows_memory_mb()
    if mem_mb:
        print_and_write(f, f"Total System RAM: {mem_mb:.1f} MB")
    else:
        print_and_write(f, "Total System RAM: Unknown (wmic OS call failed)")

###############################################################################
# Linux
###############################################################################

def parse_lscpu_output(lscpu_text):
    """
    Parse lines from `lscpu` output (format: "Key: Value").
    Returns a dict of {key: value}.
    """
    info = {}
    for line in lscpu_text.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip()
            info[key] = val
    return info

def get_linux_memory_bytes():
    """
    Attempts to retrieve total system memory (in bytes) on Linux via `free -b` or /proc/meminfo.
    Returns an integer or None on failure.
    """
    try:
        free_output = subprocess.check_output(["free", "-b"], universal_newlines=True, stderr=subprocess.DEVNULL)
        for line in free_output.splitlines():
            if line.lower().startswith("mem:"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1])
    except:
        pass
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        match = re.search(r"^MemTotal:\s+(\d+)\skB", meminfo, re.MULTILINE)
        if match:
            return int(match.group(1)) * 1024
    except:
        pass
    return None

def print_linux_info(f):
    """
    Gathers CPU & memory info on Linux (using lscpu/free) and writes to the file-like object.
    """
    try:
        lscpu_output = subprocess.check_output(["lscpu"], universal_newlines=True)
        info = parse_lscpu_output(lscpu_output)

        print_and_write(f, "=== CPU Information (Linux) ===")
        print_and_write(f, f"CPU Name: {info.get('Model name', 'Unknown')}")
        if 'Socket(s)' in info:
            print_and_write(f, f"Sockets: {info['Socket(s)']}")
        if 'Socket(s)' in info and 'Core(s) per socket' in info:
            try:
                total_cores = int(info['Socket(s)']) * int(info['Core(s) per socket'])
                print_and_write(f, f"Cores: {total_cores}")
            except ValueError:
                print_and_write(f, f"Cores (per socket): {info.get('Core(s) per socket', 'Unknown')}")
        if 'CPU(s)' in info:
            print_and_write(f, f"Logical processors: {info['CPU(s)']}")
        if 'CPU MHz' in info:
            print_and_write(f, f"Reported Speed: {info['CPU MHz']} MHz")
        virt_report = "Unknown"
        if 'Virtualization' in info:
            virt_report = f"Supported: {info['Virtualization']}"
        flags = info.get('Flags', '')
        if flags:
            if re.search(r"\bvmx\b", flags) or re.search(r"\bsvm\b", flags):
                virt_report = "Enabled (VMX/SVM flag present)"
            else:
                virt_report = "Not found in CPU flags"
        print_and_write(f, f"Virtualization: {virt_report}")

        l1d = info.get('L1d cache')
        l1i = info.get('L1i cache')
        if l1d and l1i:
            print_and_write(f, f"L1 cache: {l1d} (data), {l1i} (instruction)")
        elif l1d:
            print_and_write(f, f"L1 data cache: {l1d}")
        elif l1i:
            print_and_write(f, f"L1 instruction cache: {l1i}")
        if 'L2 cache' in info:
            print_and_write(f, f"L2 cache: {info['L2 cache']}")
        if 'L3 cache' in info:
            print_and_write(f, f"L3 cache: {info['L3 cache']}")
    except FileNotFoundError:
        print_and_write(f, "lscpu not found; falling back to minimal /proc/cpuinfo parsing.")
        try:
            with open("/proc/cpuinfo", "r") as cpu_file:
                cpuinfo = cpu_file.read()
            print_and_write(f, "=== CPU Information (Linux - fallback) ===")
            model_name = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, re.MULTILINE)
            if model_name:
                print_and_write(f, f"CPU Name: {model_name.group(1)}")
            physical_ids = re.findall(r"^physical id\s*:\s*(\d+)$", cpuinfo, re.MULTILINE)
            sockets = len(set(physical_ids)) if physical_ids else 1
            print_and_write(f, f"Sockets: {sockets}")
            core_ids = re.findall(r"^core id\s*:\s*(\d+)$", cpuinfo, re.MULTILINE)
            if core_ids and physical_ids:
                unique_pairs = set(zip(physical_ids, core_ids))
                print_and_write(f, f"Cores: {len(unique_pairs)}")
            processors = re.findall(r"^processor\s*:\s*(\d+)$", cpuinfo, re.MULTILINE)
            print_and_write(f, f"Logical processors: {len(processors)}")
            if re.search(r'^flags\s*:.*\b(vmx|svm)\b', cpuinfo, re.MULTILINE):
                print_and_write(f, "Virtualization: Enabled (vmx/svm flag present)")
            else:
                print_and_write(f, "Virtualization: Not detected in flags")
            cache_size = re.search(r"^cache size\s*:\s*(\d+\s*[Kk][Bb])", cpuinfo, re.MULTILINE)
            if cache_size:
                print_and_write(f, f"Cache (likely L2 or L3): {cache_size.group(1)}")
        except Exception:
            print_and_write(f, "Could not parse /proc/cpuinfo properly.")
    mem_bytes = get_linux_memory_bytes()
    if mem_bytes:
        print_and_write(f, f"Total System RAM: {mem_bytes} bytes")
    else:
        print_and_write(f, "Total System RAM: Unknown (could not retrieve)")

###############################################################################
# macOS (Darwin)
###############################################################################

def print_macos_info(f):
    """
    Gathers CPU & memory info on macOS (Darwin) by calling sysctl.
    """
    print_and_write(f, "=== CPU Information (macOS) ===")
    try:
        brand_cmd = ["sysctl", "-n", "machdep.cpu.brand_string"]
        brand_str = subprocess.check_output(brand_cmd, universal_newlines=True).strip()
        print_and_write(f, f"CPU Name: {brand_str}")
    except:
        print_and_write(f, "CPU Name: Unknown (sysctl machdep.cpu.brand_string failed)")
    try:
        logical_cmd = ["sysctl", "-n", "hw.ncpu"]
        logical_str = subprocess.check_output(logical_cmd, universal_newlines=True).strip()
        print_and_write(f, f"Logical processors: {logical_str}")
    except:
        print_and_write(f, "Logical processors: Unknown")
    try:
        physical_cmd = ["sysctl", "-n", "hw.physicalcpu"]
        physical_str = subprocess.check_output(physical_cmd, universal_newlines=True).strip()
        print_and_write(f, f"Physical cores: {physical_str}")
    except:
        print_and_write(f, "Physical cores: Unknown")
    virt_cmd = ["sysctl", "-n", "machdep.cpu.features"]
    virtualization = "Unknown"
    try:
        features_str = subprocess.check_output(virt_cmd, universal_newlines=True).strip()
        if "VMX" in features_str:
            virtualization = "Enabled (VMX flag present)"
        else:
            virtualization = "Not found in CPU features"
    except:
        pass
    print_and_write(f, f"Virtualization: {virtualization}")
    print_and_write(f, "=== Memory Information (macOS) ===")
    try:
        mem_cmd = ["sysctl", "-n", "hw.memsize"]
        mem_bytes = subprocess.check_output(mem_cmd, universal_newlines=True).strip()
        if mem_bytes.isdigit():
            print_and_write(f, f"Total System RAM: {mem_bytes} bytes")
        else:
            print_and_write(f, "Total System RAM: Unknown (hw.memsize not valid)")
    except:
        print_and_write(f, "Total System RAM: Unknown (sysctl hw.memsize failed)")

###############################################################################
# FreeBSD
###############################################################################

def print_freebsd_info(f):
    print_and_write(f, "=== CPU Information (FreeBSD) ===")
    try:
        model_str = subprocess.check_output(["sysctl", "-n", "hw.model"], universal_newlines=True).strip()
        print_and_write(f, f"CPU Name: {model_str}")
    except:
        print_and_write(f, "CPU Name: Unknown")
    try:
        ncpu_str = subprocess.check_output(["sysctl", "-n", "hw.ncpu"], universal_newlines=True).strip()
        print_and_write(f, f"Logical processors: {ncpu_str}")
    except:
        print_and_write(f, "Logical processors: Unknown")
    virtualization = "Unknown"
    try:
        features = subprocess.check_output(["sysctl", "-n", "machdep.cpu_features"], universal_newlines=True).strip()
        if 'VMX' in features:
            virtualization = "VMX (Intel VT-x) present"
        elif 'SVM' in features:
            virtualization = "SVM (AMD-V) present"
    except:
        pass
    print_and_write(f, f"Virtualization: {virtualization}")
    print_and_write(f, "=== Memory Information (FreeBSD) ===")
    try:
        mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.physmem"], universal_newlines=True).strip())
        print_and_write(f, f"Total System RAM: {mem_bytes / (1024**3):.1f} GB")
    except:
        print_and_write(f, "Total System RAM: Unknown")

###############################################################################
# OpenBSD
###############################################################################

def print_openbsd_info(f):
    print_and_write(f, "=== CPU Information (OpenBSD) ===")
    try:
        model_str = subprocess.check_output(["sysctl", "-n", "hw.model"], universal_newlines=True).strip()
        print_and_write(f, f"CPU Name: {model_str}")
    except:
        print_and_write(f, "CPU Name: Unknown")
    try:
        ncpu_str = subprocess.check_output(["sysctl", "-n", "hw.ncpu"], universal_newlines=True).strip()
        print_and_write(f, f"Logical processors: {ncpu_str}")
    except:
        print_and_write(f, "Logical processors: Unknown")
    virt_status = "Unknown"
    try:
        vendor = subprocess.check_output(["sysctl", "-n", "hw.vendor"], universal_newlines=True).strip().lower()
        features = subprocess.check_output(["sysctl", "-n", "machdep.cpu.features"], universal_newlines=True).strip()
        if 'vmx' in features.lower() and 'intel' in vendor:
            virt_status = "VMX (Intel VT-x) present"
        elif 'svm' in features.lower() and 'amd' in vendor:
            virt_status = "SVM (AMD-V) present"
    except:
        pass
    print_and_write(f, f"Virtualization: {virt_status}")
    print_and_write(f, "=== Memory Information (OpenBSD) ===")
    try:
        mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.physmem"], universal_newlines=True).strip())
        print_and_write(f, f"Total System RAM: {mem_bytes / (1024**3):.1f} GB")
    except:
        print_and_write(f, "Total System RAM: Unknown")

###############################################################################
# NetBSD
###############################################################################

def print_netbsd_info(f):
    print_and_write(f, "=== CPU Information (NetBSD) ===")
    try:
        model_str = subprocess.check_output(["sysctl", "-n", "machdep.cpu_brand"], universal_newlines=True).strip()
        print_and_write(f, f"CPU Name: {model_str}")
    except:
        print_and_write(f, "CPU Name: Unknown")
    try:
        ncpu_str = subprocess.check_output(["sysctl", "-n", "hw.ncpu"], universal_newlines=True).strip()
        print_and_write(f, f"Logical processors: {ncpu_str}")
    except:
        print_and_write(f, "Logical processors: Unknown")
    virt_status = "Unknown"
    try:
        features = subprocess.check_output(["sysctl", "-n", "machdep.cpu_features"], universal_newlines=True).strip()
        if 'VMX' in features:
            virt_status = "VMX (Intel VT-x) present"
        elif 'SVM' in features:
            virt_status = "SVM (AMD-V) present"
    except:
        pass
    print_and_write(f, f"Virtualization: {virt_status}")
    print_and_write(f, "=== Memory Information (NetBSD) ===")
    try:
        mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.physmem64"], universal_newlines=True).strip())
        print_and_write(f, f"Total System RAM: {mem_bytes / (1024**3):.1f} GB")
    except:
        print_and_write(f, "Total System RAM: Unknown")

###############################################################################
# Solaris (and Illumos)
###############################################################################

def print_solaris_info(f):
    """
    Minimal attempt for CPU & memory info on Solaris-like systems.
    """
    print_and_write(f, "=== CPU Information (Solaris) ===")
    try:
        psr_output = subprocess.check_output(["psrinfo", "-pv"], universal_newlines=True)
        for line in psr_output.splitlines():
            print_and_write(f, line.strip())
    except:
        print_and_write(f, "psrinfo command failed or not found.")
    print_and_write(f, "=== Memory Information (Solaris) ===")
    try:
        prtconf_output = subprocess.check_output(["prtconf"], universal_newlines=True)
        match = re.search(r"Memory size:\s+(\d+)\s+Megabytes", prtconf_output, re.IGNORECASE)
        if match:
            print_and_write(f, f"Total System RAM: {match.group(1)} MB")
        else:
            print_and_write(f, "Total System RAM: Unknown (not found in prtconf)")
    except:
        print_and_write(f, "prtconf command failed or not found.")

###############################################################################
# AIX
###############################################################################

def print_aix_info(f):
    print_and_write(f, "=== CPU Information (AIX) ===")
    try:
        cpu_info = subprocess.check_output(["lsconf"], universal_newlines=True)
        print_and_write(f, cpu_info.strip())
    except Exception:
        print_and_write(f, "Failed to retrieve CPU info on AIX.")
    print_and_write(f, "=== Memory Information (AIX) ===")
    try:
        mem_info = subprocess.check_output(["lsattr", "-El", "sys0"], universal_newlines=True)
        print_and_write(f, mem_info.strip())
    except Exception:
        print_and_write(f, "Failed to retrieve memory info on AIX.")

###############################################################################
# Haiku
###############################################################################

def print_haiku_info(f):
    print_and_write(f, "=== CPU Information (Haiku) ===")
    try:
        cpu_info = subprocess.check_output(["sysinfo", "--cpu"], universal_newlines=True)
        print_and_write(f, cpu_info.strip())
    except Exception:
        print_and_write(f, "Failed to retrieve CPU info on Haiku.")
    print_and_write(f, "=== Memory Information (Haiku) ===")
    try:
        mem_info = subprocess.check_output(["sysinfo", "--mem"], universal_newlines=True)
        print_and_write(f, mem_info.strip())
    except Exception:
        print_and_write(f, "Failed to retrieve memory info on Haiku.")

###############################################################################
# DragonFly BSD
###############################################################################

def print_dragonfly_info(f):
    print_and_write(f, "=== CPU Information (DragonFly BSD) ===")
    try:
        model_str = subprocess.check_output(["sysctl", "-n", "hw.model"], universal_newlines=True).strip()
        print_and_write(f, f"CPU Name: {model_str}")
    except:
        print_and_write(f, "CPU Name: Unknown")
    try:
        ncpu_str = subprocess.check_output(["sysctl", "-n", "hw.ncpu"], universal_newlines=True).strip()
        print_and_write(f, f"Logical processors: {ncpu_str}")
    except:
        print_and_write(f, "Logical processors: Unknown")
    virt_status = "Unknown"
    try:
        features = subprocess.check_output(["sysctl", "-n", "machdep.cpu_features"], universal_newlines=True).strip()
        if 'VMX' in features:
            virt_status = "VMX (Intel VT-x) present"
        elif 'SVM' in features:
            virt_status = "SVM (AMD-V) present"
    except:
        pass
    print_and_write(f, f"Virtualization: {virt_status}")
    print_and_write(f, "=== Memory Information (DragonFly BSD) ===")
    try:
        mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.physmem"], universal_newlines=True).strip())
        print_and_write(f, f"Total System RAM: {mem_bytes / (1024**3):.1f} GB")
    except:
        print_and_write(f, "Total System RAM: Unknown")

###############################################################################
# Plan 9
###############################################################################

def print_plan9_info(f):
    """
    Attempt to retrieve CPU and memory info on Plan 9 systems.
    Note: Python on Plan 9 is rare; if running, this is a minimal implementation.
    """
    print_and_write(f, "=== CPU and Memory Information (Plan 9) ===")
    try:
        # Example: Use 'plumber' to retrieve system info if available.
        info = subprocess.check_output(["plumber", "ls"], universal_newlines=True)
        print_and_write(f, info.strip())
    except:
        print_and_write(f, "Plan 9 system info retrieval not implemented.")

###############################################################################
# Minix
###############################################################################

def print_minix_info(f):
    """
    Attempt to retrieve CPU and memory info on Minix systems.
    Note: Python on Minix is uncommon; if running, this is a minimal implementation.
    """
    print_and_write(f, "=== CPU and Memory Information (Minix) ===")
    try:
        info = subprocess.check_output(["uname", "-a"], universal_newlines=True)
        print_and_write(f, info.strip())
    except:
        print_and_write(f, "Minix system info retrieval not implemented.")

###############################################################################
# Android
###############################################################################

def print_android_info(f):
    """
    Gathers CPU and memory info on Android.
    Since Android supports Python (via various ports), this function falls back to Linux info.
    """
    print_and_write(f, "=== CPU and Memory Information (Android) ===")
    print_and_write(f, "Android detected. Using Linux system info retrieval:")
    print_linux_info(f)

###############################################################################
# Main (OS Detection and Minimal Console Output)
###############################################################################

def main():
    output = io.StringIO()
    os_type = platform.system().lower()
    
    # Python must be present; if the OS doesn't support Python, this script wouldn't run.
    # Therefore, we only include systems where Python is available.
    if os_type.startswith("win"):
        print_windows_info(output)
    elif os_type == "linux":
        print_linux_info(output)
    elif os_type == "darwin":
        print_macos_info(output)
    elif os_type == "freebsd":
        print_freebsd_info(output)
    elif os_type == "openbsd":
        print_openbsd_info(output)
    elif os_type == "netbsd":
        print_netbsd_info(output)
    elif os_type == "sunos":
        print_solaris_info(output)
    elif os_type == "aix":
        print_aix_info(output)
    elif os_type == "haiku":
        print_haiku_info(output)
    elif os_type == "dragonfly":
        print_dragonfly_info(output)
    elif os_type.startswith("plan9"):
        print_plan9_info(output)
    elif os_type == "minix":
        print_minix_info(output)
    elif os_type == "android":
        print_android_info(output)
    else:
        print_and_write(output, "Unsupported platform. Contributions welcome!")
    
    info_text = output.getvalue()
    output.close()
    
    with open("system_info.txt", "w", encoding="utf-8") as f:
        f.write(info_text)
    
    detected_os = platform.system()
    print(f"Detected operating system: {detected_os}")
    print("System information written to system_info.txt")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
