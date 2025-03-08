#nullable enable
using System;
using System.Collections.Generic;
using System.Management; // Requires reference to System.Management.dll
using System.Text;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Diagnostics;

class Program
{
    static void Main()
    {
        // Only run on Windows
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            return;

        StringBuilder output = new StringBuilder();
        
        PrintSystemSummary(output);
        PrintHardwareResources(output);
        PrintComponents(output);
        PrintSoftwareEnvironment(output);
        PrintLocaleAndEncodingInfo(output);
        PrintInstalledProgrammingLanguages(output);

        File.WriteAllText("system_info.txt", output.ToString());
    }

    static void PrintSystemSummary(StringBuilder sb)
    {
        PrintSectionHeader(sb, "System Summary");
        
        // OS Information
        QueryWMI(sb, "Win32_OperatingSystem", new List<WmiProperty> {
            new("Caption", "OS Name"),
            new("Version", "Version"),
            new("BuildNumber", "Build"),
            new("OSArchitecture", "Architecture"),
            new("SerialNumber", "Serial"),
            new("InstallDate", "Install Date")
        });

        // BIOS Information
        QueryWMI(sb, "Win32_BIOS", new List<WmiProperty> {
            new("Manufacturer", "BIOS Vendor"),
            new("Name", "BIOS Version"),
            new("ReleaseDate", "Release Date"),
            new("SMBIOSBIOSVersion", "SMBIOS Version")
        });

        // System Manufacturer
        QueryWMI(sb, "Win32_ComputerSystem", new List<WmiProperty> {
            new("Manufacturer", "System Manufacturer"),
            new("Model", "System Model"),
            new("SystemType", "System Type"),
            new("TotalPhysicalMemory", "Total Physical Memory (GB)", v => $"{Convert.ToUInt64(v) / (1024 * 1024 * 1024):N1}")
        });
    }

    static void PrintHardwareResources(StringBuilder sb)
    {
        PrintSectionHeader(sb, "Hardware Resources");
        
        // Memory
        QueryWMI(sb, "Win32_PhysicalMemory", new List<WmiProperty> {
            new("Capacity", "Memory Capacity (GB)", v => $"{Convert.ToUInt64(v) / (1024 * 1024 * 1024):N1}"),
            new("Speed", "Speed (MHz)"),
            new("Manufacturer", "Manufacturer")
        }, "Memory Devices");

        // Processor
        QueryWMI(sb, "Win32_Processor", new List<WmiProperty> {
            new("Name", "Processor"),
            new("NumberOfCores", "Cores"),
            new("NumberOfLogicalProcessors", "Logical Processors"),
            new("MaxClockSpeed", "Max Speed (MHz)"),
            new("L2CacheSize", "L2 Cache (MB)", v => $"{Convert.ToUInt64(v) / 1024:N1}"),
            new("L3CacheSize", "L3 Cache (MB)", v => $"{Convert.ToUInt64(v) / 1024:N1}")
        }, "Processor Details");
    }

    static void PrintComponents(StringBuilder sb)
    {
        PrintSectionHeader(sb, "Components");
        
        // Graphics
        QueryWMI(sb, "Win32_VideoController", new List<WmiProperty> {
            new("Name", "Adapter"),
            new("AdapterRAM", "VRAM (GB)", v => $"{Convert.ToUInt64(v) / (1024 * 1024 * 1024):N1}"),
            new("DriverVersion", "Driver Version"),
            new("VideoProcessor", "GPU Chip")
        }, "Display");

        // Storage
        QueryWMI(sb, "Win32_DiskDrive", new List<WmiProperty> {
            new("Model", "Disk Model"),
            new("Size", "Capacity (GB)", v => $"{Convert.ToUInt64(v) / (1024 * 1024 * 1024):N1}"),
            new("InterfaceType", "Interface")
        }, "Storage");
    }

    static void PrintSoftwareEnvironment(StringBuilder sb)
    {
        PrintSectionHeader(sb, "Software Environment");
        
        // Installed Updates
        QueryWMI(sb, "Win32_QuickFixEngineering", new List<WmiProperty> {
            new("HotFixID", "Update"),
            new("InstalledOn", "Install Date"),
            new("Description", "Description")
        }, "Windows Updates");

        // Network Adapters
        QueryWMI(sb, "Win32_NetworkAdapterConfiguration", new List<WmiProperty> {
            new("Description", "Adapter"),
            new("IPAddress", "IP Address"),
            new("MACAddress", "MAC")
        }, "Network", "IPEnabled = TRUE");
    }

    static void PrintLocaleAndEncodingInfo(StringBuilder sb)
    {
        PrintSectionHeader(sb, "Locale and Encoding");
        sb.AppendLine($"System Locale: {CultureInfo.CurrentCulture.Name}");
        sb.AppendLine($"Default Encoding: {Encoding.Default.EncodingName}");
    }

    /// <summary>
    /// Checks for commonly used programming languages by trying to locate 
    /// their main executable(s) with the 'where' command in Windows.
    /// Only prints the ones that are actually found.
    /// </summary>
    static void PrintInstalledProgrammingLanguages(StringBuilder sb)
    {
        PrintSectionHeader(sb, "Installed Programming Languages");

        // Each entry: (Name, list of executables that might indicate it's installed)
        var languages = new (string Name, string[] Candidates)[]
        {
            ("C", new []{"cl.exe","gcc.exe","clang.exe"}),
            ("C++", new []{"cl.exe","g++.exe","clang++.exe"}),
            ("C#", new []{"csc.exe"}),
            ("Java", new []{"java.exe","javac.exe"}),
            ("Go", new []{"go.exe"}),
            ("Rust", new []{"rustc.exe","cargo.exe"}),
            ("Python", new []{"python.exe","python3.exe"}),
            ("Perl", new []{"perl.exe"}),
            ("PHP", new []{"php.exe"}),
            ("Ruby", new []{"ruby.exe"}),
            ("Node.js", new []{"node.exe"}),
            ("R", new []{"R.exe"}),
            ("Haskell (GHC)", new []{"ghc.exe","ghci.exe"}),
            ("Swift", new []{"swift.exe"})
        };

        // For each language in the above list, see if at least one candidate is found
        foreach (var (name, executables) in languages)
        {
            // We'll store all found paths, then print them.
            List<string> foundPaths = new();

            foreach (var exe in executables)
            {
                var paths = WhereCommand(exe);
                if (paths != null && paths.Count > 0)
                    foundPaths.AddRange(paths);
            }

            if (foundPaths.Count > 0)
            {
                sb.AppendLine($"{name} is installed at:");
                foreach (var path in foundPaths)
                    sb.AppendLine($"   {path}");
                sb.AppendLine();
            }
        }
    }

    /// <summary>
    /// Runs the 'where' command for a given executable name. 
    /// Returns a list of full paths if found, or null/empty if not found.
    /// </summary>
    private static List<string>? WhereCommand(string exeName)
    {
        try
        {
            var psi = new ProcessStartInfo("where", exeName)
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using var proc = Process.Start(psi);
            proc.WaitForExit();

            if (proc.ExitCode == 0) // Found
            {
                var output = proc.StandardOutput.ReadToEnd();
                // 'where' can return multiple lines if the exe is in multiple places
                var lines = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                return new List<string>(lines);
            }
        }
        catch
        {
            // If there's an error (shouldn't typically happen), just ignore
        }
        return null;
    }

    static void PrintSectionHeader(StringBuilder sb, string title)
    {
        sb.AppendLine();
        sb.AppendLine($"===== {title.ToUpper()} =====");
        sb.AppendLine();
    }

    static void PrintSubSectionHeader(StringBuilder sb, string title)
    {
        sb.AppendLine();
        sb.AppendLine($"[{title}]");
    }

    // The updated WMI query method that uses a list of WmiProperty objects
    static void QueryWMI(
        StringBuilder sb,
        string className,
        List<WmiProperty> properties,
        string? sectionTitle = null,
        string? condition = null)
    {
        try
        {
            if (sectionTitle != null)
                PrintSubSectionHeader(sb, sectionTitle);

            var query = $"SELECT * FROM {className}";
            if (!string.IsNullOrEmpty(condition))
                query += $" WHERE {condition}";

            using var searcher = new ManagementObjectSearcher(query);
            foreach (ManagementObject obj in searcher.Get())
            {
                foreach (var prop in properties)
                {
                    object value = obj[prop.PropertyName];
                    if (value == null) continue;

                    string formattedValue = prop.Formatter != null
                        ? prop.Formatter(value)
                        : value.ToString();

                    sb.AppendLine($"{prop.DisplayName}: {formattedValue}");
                }
                sb.AppendLine();
            }
        }
        catch (Exception ex)
        {
            sb.AppendLine($"Error querying {className}: {ex.Message}");
        }
    }

    // Helper class for describing WMI properties
    class WmiProperty
    {
        public string PropertyName { get; }
        public string DisplayName { get; }
        public Func<object, string>? Formatter { get; }

        public WmiProperty(string prop, string display, Func<object, string>? formatter = null)
        {
            PropertyName = prop;
            DisplayName = display;
            Formatter = formatter;
        }
    }
}
