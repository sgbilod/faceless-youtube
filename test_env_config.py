"""Test environment configuration - Prompt #4"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔍 ENVIRONMENT CONFIGURATION TEST - PROMPT #4")
print("=" * 60)
print()

# Check API Keys
pexels = os.getenv('PEXELS_API_KEY', '')
pixabay = os.getenv('PIXABAY_API_KEY', '')
db_password = os.getenv('DB_PASSWORD', '')
debug = os.getenv('DEBUG', 'true')
secret_key = os.getenv('SECRET_KEY', '')

print("1️⃣  API Keys:")
if pexels and len(pexels) > 0:
    print(f"   ✅ Pexels API: Set ({len(pexels)} characters)")
else:
    print(f"   ❌ Pexels API: Missing")

if pixabay and len(pixabay) > 0:
    print(f"   ✅ Pixabay API: Set ({len(pixabay)} characters)")
else:
    print(f"   ❌ Pixabay API: Missing")

print()
print("2️⃣  Database Configuration:")
if db_password and len(db_password) > 0:
    print(f"   ✅ DB Password: Set")
else:
    print(f"   ❌ DB Password: Missing")

print()
print("3️⃣  Application Settings:")
print(f"   DEBUG: {debug}")
if debug.lower() == 'false':
    print(f"   ✅ DEBUG mode: Correctly set to false")
else:
    print(f"   ⚠️  DEBUG mode: Still true (should be false for production)")

print()
print("4️⃣  Security:")
if secret_key and 'dev-secret' not in secret_key:
    print(f"   ✅ SECRET_KEY: Custom secure key set ({len(secret_key)} characters)")
else:
    print(f"   ❌ SECRET_KEY: Still using default dev key")

print()
print("=" * 60)

# Final verdict
issues = []
if not pexels or len(pexels) == 0:
    issues.append("Pexels API key missing")
if not pixabay or len(pixabay) == 0:
    issues.append("Pixabay API key missing")
if not db_password or len(db_password) == 0:
    issues.append("DB password missing")
if debug.lower() != 'false':
    issues.append("DEBUG should be false")
if not secret_key or 'dev-secret' in secret_key:
    issues.append("SECRET_KEY needs update")

if len(issues) == 0:
    print("📊 SUMMARY")
    print("=" * 60)
    print("✅ All required environment variables configured!")
    print("✅ Security settings properly configured!")
    print("✅ API keys ready for use!")
    print()
    print("🎉 PROMPT #4 COMPLETE!")
    print()
    print("⏭️  Next Step: Prompt #5 (YouTube OAuth) or Prompt #6 (Final Verification)")
else:
    print("⚠️  ISSUES FOUND")
    print("=" * 60)
    for issue in issues:
        print(f"   ❌ {issue}")
    print()
    print("Please fix the issues above before proceeding.")

print("=" * 60)
print()
