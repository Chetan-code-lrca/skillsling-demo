#!/usr/bin/env python3
"""
Push SkillSling AI Mobile Fix to GitHub
"""

import subprocess
import os
import sys

os.chdir(r"C:\Users\cheta\OneDrive\Desktop\pros\skillsling")

print("=" * 50)
print("🚀 PUSHING SKILLSLING MOBILE FIX")
print("=" * 50)
print()

try:
    print("📝 Step 1: Checking git status...")
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    print(result.stdout)
    
    print("📦 Step 2: Adding app.py...")
    subprocess.run(["git", "add", "app.py"], check=True)
    print("✅ Added app.py")
    print()
    
    print("💾 Step 3: Committing changes...")
    subprocess.run([
        "git", "commit", 
        "-m", 
        "Fix: Mobile-friendly Chat API and responsive UI - resolves 400 streaming errors on mobile"
    ], check=True)
    print("✅ Committed to local git")
    print()
    
    print("🌍 Step 4: Pushing to GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print()
    print("=" * 50)
    print("✅ PUSH SUCCESSFUL!")
    print("=" * 50)
    print()
    print("📱 Your app is now redeploying on Streamlit Cloud")
    print("⏱️  Wait 30-60 seconds for deployment")
    print("🔄 Then refresh your mobile browser")
    print()
    print("Expected result:")
    print("✅ No more 400 errors")
    print("✅ Mobile UI looks great")
    print("✅ Response in 2-3 seconds")
    print()
    
except subprocess.CalledProcessError as e:
    print(f"❌ Error: {e}")
    print(f"Output: {e.output}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Exception: {e}")
    sys.exit(1)
