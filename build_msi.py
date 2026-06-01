#!/usr/bin/env python3
"""Build MSI installer for MemoryAgent on Windows."""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_wix_source():
    """Create WiX source file for MSI installer."""
    wxs_content = """<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" 
           Name="MemoryAgent" 
           Language="1033" 
           Version="1.0.0.0" 
           Manufacturer="MemoryAgent" 
           UpgradeCode="12345678-1234-1234-1234-123456789012">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine"
             Description="MemoryAgent - AI Agent with Cognitive Memory Architecture"
             Comments="Installs MemoryAgent application" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." />
    <MediaTemplate EmbedCab="yes" />
    
    <Feature Id="ProductFeature" Title="MemoryAgent" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentRef Id="ApplicationShortcut" />
    </Feature>
    
    <!-- Directory Structure -->
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="MemoryAgent" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="MemoryAgent" />
      </Directory>
      <Directory Id="DesktopFolder" />
    </Directory>
    
    <!-- Components -->
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="*">
        <File Id="MemoryAgentEXE" 
              Source="dist\\\\MemoryAgent\\\\MemoryAgent.exe" 
              KeyPath="yes" />
      </Component>
      
      <Component Id="LauncherBAT" Guid="*">
        <File Id="LauncherBATFile" 
              Source="MemoryAgent.bat" />
      </Component>
      
      <Component Id="LauncherPS1" Guid="*">
        <File Id="LauncherPS1File" 
              Source="MemoryAgent.ps1" />
      </Component>
      
      <Component Id="README" Guid="*">
        <File Id="READMEFile" 
              Source="README_WINDOWS.txt" />
      </Component>
    </ComponentGroup>
    
    <!-- Start Menu Shortcut -->
    <DirectoryRef Id="ApplicationProgramsFolder">
      <Component Id="ApplicationShortcut" Guid="*">
        <Shortcut Id="ApplicationStartMenuShortcut" 
                  Name="MemoryAgent" 
                  Description="MemoryAgent - AI Agent with Cognitive Memory Architecture"
                  Target="[INSTALLFOLDER]MemoryAgent.bat"
                  WorkingDirectory="INSTALLFOLDER" />
        <RemoveFolder Id="CleanUpShortCut" 
                      Directory="ApplicationProgramsFolder" 
                      On="uninstall" />
        <RegistryValue Root="HKCU" 
                       Key="Software\\\\MemoryAgent" 
                       Name="installed" 
                       Type="integer" 
                       Value="1" 
                       KeyPath="yes" />
      </Component>
    </DirectoryRef>
    
    <!-- Desktop Shortcut -->
    <DirectoryRef Id="DesktopFolder">
      <Component Id="DesktopShortcut" Guid="*">
        <Shortcut Id="DesktopApplicationShortcut" 
                  Name="MemoryAgent" 
                  Description="MemoryAgent - AI Agent with Cognitive Memory Architecture"
                  Target="[INSTALLFOLDER]MemoryAgent.bat"
                  WorkingDirectory="INSTALLFOLDER" />
      </Component>
    </DirectoryRef>
    
    <!-- UI -->
    <UIRef Id="WixUI_InstallDir" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
    
    <!-- License -->
    <WixVariable Id="WixUILicenseRtf" Value="License.rtf" />
    
  </Product>
</Wix>
"""
    with open('MemoryAgent.wxs', 'w') as f:
        f.write(wxs_content)
    print("Created MemoryAgent.wxs")


def create_license_rtf():
    """Create RTF license file."""
    rtf_content = """{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033
{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}
{\\*\\generator Riched20 10.0.19041}\\viewkind4\\uc1 
\\pard\\sa200\\sl276\\slmult1\\f0\\fs22\\lang9

MemoryAgent License\\par
\\par
MIT License\\par
\\par
Copyright (c) 2024 MemoryAgent\\par
\\par
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:\\par
\\par
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.\\par
\\par
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.\\par
}
"""
    with open('License.rtf', 'w') as f:
        f.write(rtf_content)
    print("Created License.rtf")


def build_msi():
    """Build MSI using WiX Toolset."""
    print("Building MSI installer...")
    
    # Check if WiX is available
    try:
        subprocess.run(['candle', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WiX Toolset not found. Please install WiX Toolset:")
        print("  https://wixtoolset.org/releases/")
        print("  Or run: choco install wixtoolset")
        return None
    
    # Compile
    try:
        subprocess.run(['candle', 'MemoryAgent.wxs', '-out', 'MemoryAgent.wixobj'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to compile: {e}")
        return None
    
    # Link
    try:
        subprocess.run([
            'light', 
            '-ext', 'WixUIExtension',
            'MemoryAgent.wixobj', 
            '-out', 'MemoryAgent-1.0.0.msi'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to link: {e}")
        return None
    
    print("Created MemoryAgent-1.0.0.msi")
    return "MemoryAgent-1.0.0.msi"


def main():
    """Main function."""
    print("Building MemoryAgent MSI installer...")
    
    # Create WiX source
    create_wix_source()
    create_license_rtf()
    
    # Build MSI
    msi_file = build_msi()
    
    if msi_file:
        print(f"\nBuild complete!")
        print(f"MSI file: {msi_file}")
        print(f"Size: {os.path.getsize(msi_file) / 1024 / 1024:.1f} MB")
    else:
        print("\nMSI build requires WiX Toolset.")
        print("Please install WiX Toolset and try again.")


if __name__ == "__main__":
    main()
