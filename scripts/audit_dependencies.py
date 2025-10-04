"""
Dependency Audit Script
Audits all Python dependencies and checks for issues.
"""

import pkg_resources
import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def audit_dependencies():
    """Audit all Python dependencies and check for issues."""
    
    # 1. List installed packages
    print("Collecting installed packages...")
    installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    # 2. Parse requirements.txt
    required = {}
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    
    try:
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '==' in line:
                    pkg, ver = line.split('==')
                    required[pkg.lower()] = ver
                elif '>=' in line:
                    pkg = line.split('>=')[0]
                    required[pkg.lower()] = 'any'
    except FileNotFoundError:
        print("⚠️ requirements.txt not found!")
        return
    
    # 3. Check for mismatches
    print("\n" + "="*60)
    print("DEPENDENCY STATUS")
    print("="*60 + "\n")
    
    missing = []
    mismatched = []
    correct = []
    
    for pkg, req_ver in required.items():
        if pkg not in installed:
            missing.append(f"❌ {pkg}=={req_ver} - NOT INSTALLED")
        elif req_ver != 'any' and installed[pkg] != req_ver:
            mismatched.append(
                f"⚠️ {pkg}: Required {req_ver}, Installed {installed[pkg]}"
            )
        else:
            correct.append(f"✅ {pkg}=={installed.get(pkg, 'any')}")
    
    # Print correct packages
    if correct:
        print("### CORRECTLY INSTALLED:\n")
        for pkg in sorted(correct):
            print(f"  {pkg}")
    
    if missing:
        print("\n### MISSING PACKAGES:\n")
        for pkg in sorted(missing):
            print(f"  {pkg}")
    
    if mismatched:
        print("\n### VERSION MISMATCHES:\n")
        for pkg in sorted(mismatched):
            print(f"  {pkg}")
    
    # 4. Check for unused packages
    unused = []
    for pkg in installed:
        if pkg not in required and pkg not in ['pip', 'setuptools', 'wheel']:
            unused.append(f"🔍 {pkg}=={installed[pkg]} - Not in requirements.txt")
    
    if unused:
        print("\n### POTENTIALLY UNUSED:\n")
        for pkg in sorted(unused):
            print(f"  {pkg}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Required: {len(required)}")
    print(f"Correctly Installed: {len(correct)}")
    print(f"Missing: {len(missing)}")
    print(f"Version Mismatches: {len(mismatched)}")
    print(f"Potentially Unused: {len(unused)}")
    
    if missing or mismatched:
        print("\n⚠️ ISSUES FOUND - Run: pip install -r requirements.txt")
        return 1
    else:
        print("\n✅ ALL DEPENDENCIES OK")
        return 0

if __name__ == "__main__":
    exit_code = audit_dependencies()
    sys.exit(exit_code)
