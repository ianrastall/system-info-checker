# System Info Checker

System Info Checker is a Python script that collects detailed CPU and memory information from your system and writes it to a text file (`system_info.txt`). It is designed to work on a wide range of operating systems, making it a universal tool for system diagnostics.

## What It Does

- **Collects CPU Information:**  
  Retrieves details such as the CPU name, base speed, number of cores, and logical processors.
  
- **Collects Memory Information:**  
  Gathers the total system RAM.

- **Platform-Specific Data Collection:**  
  Uses native system utilities (like WMIC on Windows, `lscpu` and `/proc/meminfo` on Linux, and `sysctl` on macOS) to gather the information.

- **Output:**  
  The complete system information is saved to a text file (`system_info.txt`). Minimal console output is provided just to indicate the detected operating system and confirm that the file has been written. The script also pauses before exiting, which is helpful when launched via double-click.

## Supported Operating Systems

- **Windows** (using WMIC)
- **Linux** (using `lscpu`, `free`, and `/proc/meminfo`)
- **macOS (Darwin)** (using `sysctl`)
- **FreeBSD**
- **OpenBSD**
- **NetBSD**
- **Solaris/Illumos**
- **AIX**
- **Haiku**
- **DragonFly BSD**
- **Plan 9** (placeholder: not fully implemented)
- **Minix** (placeholder: not fully implemented)
- **Android** (falls back to Linux info)
- **OS/2** (placeholder: not implemented)
- **QNX** (placeholder: not implemented)

## How to Use

1. **Ensure you have Python 3 installed.**

2. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/system-info-checker.git
