# System Info Checker

System Info Checker is a universal Python script that collects detailed information about your system's CPU and memory and writes it to a text file (`system_info.txt`). It leverages native, platform-specific tools to gather data and supports a wide range of operating systems.

## What It Does

- **CPU Information:**  
  Retrieves details such as the CPU name, base clock speed, number of cores, logical processors, and virtualization support (if available).

- **Memory Information:**  
  Gathers the total system RAM.

- **Platform-Specific Data Collection:**  
  Utilizes native system utilities (e.g., WMIC on Windows, `lscpu` and `/proc/meminfo` on Linux, `sysctl` on macOS, etc.) to accurately obtain system details.

- **Output:**  
  The collected information is saved to a text file (`system_info.txt`). The console displays only minimal messages—indicating the detected operating system and confirming that the file has been written—before pausing for user input.

## Supported Operating Systems

- **Windows** (via WMIC)
- **Linux** (via `lscpu`, `free`, and `/proc/meminfo`)
- **macOS (Darwin)** (via `sysctl`)
- **FreeBSD**
- **OpenBSD**
- **NetBSD**
- **Solaris/Illumos**
- **AIX**
- **Haiku**
- **DragonFly BSD**
- **Plan 9** (minimal implementation)
- **Minix** (minimal implementation)
- **Android** (falls back to Linux info)

> **Note:** This script is intended for systems where Python is available. On platforms that do not support Python, this script will not run.

## How to Use

1. **Ensure Python 3 is installed.**

2. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/system-info-checker.git

## Note

This script and readme authored by ChatGPT 03-mini-high. Please do report any problems, as my only OS is Windows.
