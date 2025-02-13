#![windows_subsystem = "windows"]

use std::env;
use std::fs::File;
use std::io::Write;
use std::net::UdpSocket;
use std::process::Command;
use std::os::windows::process::CommandExt; // for creation_flags

// Append a line (with newline) to our output buffer.
fn print_and_write(output: &mut String, text: &str) {
    output.push_str(text);
    output.push('\n');
}

// Print a blank line then a heading.
fn print_heading(output: &mut String, heading: &str) {
    print_and_write(output, "");
    print_and_write(output, heading);
}

/// Run a command with arguments and return its trimmed output if successful.
/// We add the CREATE_NO_WINDOW flag so no new console windows are created.
fn run_command(cmd: &str, args: &[&str]) -> Option<String> {
    let result = Command::new(cmd)
        .creation_flags(0x08000000) // CREATE_NO_WINDOW
        .args(args)
        .output()
        .ok()?;
    if result.status.success() {
        let s = String::from_utf8_lossy(&result.stdout).to_string();
        let s = s.trim().to_string();
        if !s.is_empty() {
            return Some(s);
        }
    } else {
        let err = String::from_utf8_lossy(&result.stderr).to_string();
        let err = err.trim().to_string();
        if !err.is_empty() {
            return Some(err);
        }
    }
    None
}

// Use WMIC to get total visible memory (in MB)
fn get_windows_memory_mb() -> Option<f64> {
    if let Some(output) =
        run_command("wmic", &["OS", "get", "TotalVisibleMemorySize", "/format:list"])
    {
        for line in output.lines() {
            let line = line.trim();
            if line.starts_with("TotalVisibleMemorySize=") {
                let parts: Vec<&str> = line.split('=').collect();
                if parts.len() == 2 {
                    if let Ok(kb) = parts[1].parse::<f64>() {
                        return Some(kb / 1024.0);
                    }
                }
            }
        }
    }
    None
}

// Print CPU and memory info from WMIC.
fn print_windows_info(output: &mut String) {
    print_heading(output, "=== CPU Information (Windows) ===");
    if let Some(cpu_output) = run_command("wmic", &[
        "cpu",
        "get",
        "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,L2CacheSize,L3CacheSize,VirtualizationFirmwareEnabled",
        "/format:list",
    ]) {
        for line in cpu_output.lines() {
            let line = line.trim();
            if line.starts_with("Name=") {
                print_and_write(output, &format!("CPU Name: {}", &line[5..]));
            } else if line.starts_with("MaxClockSpeed=") {
                print_and_write(output, &format!("Base Speed: {} MHz", &line[14..]));
            } else if line.starts_with("NumberOfCores=") {
                print_and_write(output, &format!("Cores: {}", &line[14..]));
            } else if line.starts_with("NumberOfLogicalProcessors=") {
                print_and_write(output, &format!("Logical processors: {}", &line[26..]));
            } else if line.starts_with("L2CacheSize=") {
                if let Ok(l2_kb) = line[12..].parse::<f64>() {
                    print_and_write(output, &format!("L2 cache: {:.1} MB", l2_kb / 1024.0));
                }
            } else if line.starts_with("L3CacheSize=") {
                if let Ok(l3_kb) = line[12..].parse::<f64>() {
                    print_and_write(output, &format!("L3 cache: {:.1} MB", l3_kb / 1024.0));
                }
            } else if line.starts_with("VirtualizationFirmwareEnabled=") {
                let val = &line[31..].to_lowercase();
                if val == "true" {
                    print_and_write(output, "Virtualization: Enabled (BIOS/firmware)");
                } else {
                    print_and_write(output, "Virtualization: Not reported as enabled");
                }
            }
        }
    } else {
        print_and_write(output, "wmic command not found or failed.");
    }

    print_heading(output, "=== Memory Information (Windows) ===");
    if let Some(mem_mb) = get_windows_memory_mb() {
        print_and_write(output, &format!("Total System RAM: {:.1} MB", mem_mb));
    } else {
        print_and_write(output, "Total System RAM: Unknown (wmic OS call failed)");
    }
}

// Get local IP address using a UDP socket trick.
fn get_local_ip() -> Option<String> {
    let socket = UdpSocket::bind("0.0.0.0:0").ok()?;
    socket.connect("8.8.8.8:80").ok()?;
    let addr = socket.local_addr().ok()?;
    Some(addr.ip().to_string())
}

// Get system uptime in a human–readable format using GetTickCount64.
// We declare the external function from the Windows API as a normal comment.
// GetTickCount64 returns the number of milliseconds since the system started.
extern "system" {
    fn GetTickCount64() -> u64;
}

fn get_uptime() -> String {
    // GetTickCount64 returns milliseconds.
    let ms = unsafe { GetTickCount64() };
    let secs = ms / 1000;
    let days = secs / 86400;
    let hours = (secs % 86400) / 3600;
    let minutes = (secs % 3600) / 60;
    format!("{} days, {} hours, {} minutes", days, hours, minutes)
}

// Print additional system information.
fn print_additional_info(output: &mut String) {
    print_heading(output, "=== Additional System Information ===");

    let arch = env::var("PROCESSOR_ARCHITECTURE").unwrap_or_else(|_| "Unknown".into());
    print_and_write(output, &format!("Processor Architecture: {}", arch));

    if let Some(os_info) = run_command("wmic", &["os", "get", "Caption,Version,BuildNumber", "/format:list"]) {
        for line in os_info.lines() {
            let line = line.trim();
            if line.starts_with("Caption=") {
                print_and_write(output, &format!("OS Caption: {}", &line[8..]));
            } else if line.starts_with("Version=") {
                print_and_write(output, &format!("OS Version: {}", &line[8..]));
            } else if line.starts_with("BuildNumber=") {
                print_and_write(output, &format!("OS Build: {}", &line[12..]));
            }
        }
    }

    print_and_write(output, &format!("System Uptime: {}", get_uptime()));

    print_heading(output, "=== Networking Information ===");
    let hostname = env::var("COMPUTERNAME").unwrap_or_else(|_| "Unknown".into());
    print_and_write(output, &format!("Hostname: {}", hostname));
    if let Some(ip) = get_local_ip() {
        print_and_write(output, &format!("Local IP Address: {}", ip));
    } else {
        print_and_write(output, "Local IP Address: Not available");
    }
}

// Print programming languages environment information.
fn print_programming_languages_environment(output: &mut String) {
    print_heading(output, "=== Programming Languages Environment ===");
    let mut languages = vec![
        ("C (GCC)", vec!["gcc", "--version"]),
        ("C++ (G++)", vec!["g++", "--version"]),
        ("D (DMD)", vec!["dmd", "--version"]),
        ("Go", vec!["go", "version"]),
        ("Java", vec!["java", "-version"]),
        ("Node.js", vec!["node", "--version"]),
        ("PHP", vec!["php", "-v"]),
        ("Perl", vec!["perl", "-e", "print $^V"]),
        ("Python", vec!["python", "--version"]),
        ("R", vec!["R", "--version"]),
        ("Ruby", vec!["ruby", "--version"]),
        ("Rust", vec!["rustc", "--version"]),
    ];
    languages.sort_by(|a, b| a.0.cmp(b.0));

    for (lang, cmd) in languages {
        if let Some(where_output) = run_command("where", &[cmd[0]]) {
            let binary_path = where_output.lines().next().unwrap_or("").trim();
            if binary_path.is_empty() {
                continue;
            }
            print_and_write(output, "");
            print_and_write(output, &format!("{}:", lang));
            if let Some(version_output) = run_command(cmd[0], &cmd[1..]) {
                let version_line = version_output.lines().next().unwrap_or("No version info available").trim();
                print_and_write(output, &format!("  Version: {}", version_line));
            } else {
                print_and_write(output, "  Version: Not available");
            }
            print_and_write(output, &format!("  Path: {}", binary_path));
        }
    }
}

// Print locale and encoding information.
fn print_locale_and_encoding_info(output: &mut String) {
    print_heading(output, "=== Locale and Encoding Information ===");
    let locale = run_command("powershell", &["-Command", "(Get-UICulture).Name"])
        .unwrap_or_else(|| "Not available".into());
    let encoding = run_command("chcp", &[])
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "Not available".into());
    print_and_write(output, &format!("Default Locale: {}", locale));
    print_and_write(output, &format!("Preferred Encoding: {}", encoding));
}

fn main() {
    if !cfg!(windows) {
        return;
    }
    
    let mut output = String::new();
    
    print_windows_info(&mut output);
    print_additional_info(&mut output);
    print_programming_languages_environment(&mut output);
    print_locale_and_encoding_info(&mut output);
    
    if let Ok(mut file) = File::create("system_info.txt") {
        let _ = file.write_all(output.as_bytes());
    }
}
