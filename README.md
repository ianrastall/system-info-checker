# System Info Checker

**System Info Checker** is now a Windows-only tool written in Rust that collects detailed information about your system's CPU, memory, OS, networking, and programming languages environment, and writes it to a text file (`system_info.txt`). It leverages native Windows utilities (via WMIC, PowerShell, etc.) to gather accurate data and provide comprehensive system details—all without opening a console window.

## What It Does

- **CPU Information:**  
  Retrieves details such as the CPU name, base clock speed, number of cores, logical processors, cache sizes, and virtualization support.

- **Memory Information:**  
  Gathers the total system RAM as reported by Windows.

- **Additional System Information:**  
  Collects OS details (caption, version, build number), system uptime, processor architecture, and basic networking info (hostname and local IP address).

- **Programming Languages Environment:**  
  Scans for installed programming languages (e.g., Python, Java, Rust, etc.), retrieves their version information, and reports the executable paths.

- **Locale and Encoding:**  
  Determines the system's default locale and preferred encoding via PowerShell and native commands.

- **Output:**  
  All collected information is saved to a text file (`system_info.txt`). The tool runs silently without opening any console or GUI windows.

## Supported Operating System

- **Windows**

## How to Use

### Running the Prebuilt Executable

Download the prebuilt executable from the [GitHub Releases](https://github.com/yourusername/system-info-checker/releases) page and run it. The tool will silently generate `system_info.txt` in the same directory.

### Building from Source

1. **Install Rust:**  
   Follow the instructions at [https://rustup.rs](https://rustup.rs) to install Rust.

2. **Clone the Repository:**
   ```bash
   git clone https://github.com/ianrastall/system-info-checker.git
