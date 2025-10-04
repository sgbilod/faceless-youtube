#!/usr/bin/env python
"""Test database connections for Prompt #3."""

import sys

print("\n" + "="*60)
print("🔍 TESTING DATABASE CONNECTIONS - PROMPT #3")
print("="*60 + "\n")

# Test PostgreSQL
print("1️⃣  Testing PostgreSQL...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='postgres',
        password='FacelessYT2025!'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    conn.close()
    print(f"   ✅ PostgreSQL: Connected")
    print(f"   📌 Version: {version.split(',')[0]}")
    postgres_ok = True
except Exception as e:
    print(f"   ❌ PostgreSQL: {e}")
    postgres_ok = False

# Test MongoDB
print("\n2️⃣  Testing MongoDB...")
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    info = client.server_info()
    print(f"   ✅ MongoDB: Connected")
    print(f"   📌 Version: {info['version']}")
    mongodb_ok = True
except Exception as e:
    print(f"   ❌ MongoDB: {e}")
    mongodb_ok = False

# Test Redis (bonus)
print("\n3️⃣  Testing Redis (optional)...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
    r.ping()
    print(f"   ✅ Redis: Connected")
    redis_ok = True
except Exception as e:
    print(f"   ⚠️  Redis: {e} (not critical)")
    redis_ok = False

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)

if postgres_ok and mongodb_ok:
    print("✅ PostgreSQL: OPERATIONAL")
    print("✅ MongoDB: OPERATIONAL")
    if redis_ok:
        print("✅ Redis: OPERATIONAL (bonus)")
    print("\n🎉 All critical databases are working!")
    print("➡️  Ready for Prompt #4: Environment Configuration")
    sys.exit(0)
else:
    print(f"{'✅' if postgres_ok else '❌'} PostgreSQL: {'OPERATIONAL' if postgres_ok else 'NOT AVAILABLE'}")
    print(f"{'✅' if mongodb_ok else '❌'} MongoDB: {'OPERATIONAL' if mongodb_ok else 'NOT AVAILABLE'}")
    print("\n⚠️  Some databases are not available")
    print("📖 Review PROMPT_03_DATABASE_SETUP_GUIDE.md for installation instructions")
    sys.exit(1)
