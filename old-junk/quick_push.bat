@echo off
echo Pushing model fix...
cd C:\Users\cheta\OneDrive\Desktop\pros\skillsling
git add app.py
git commit -m "Fix: Update Gemini models - remove deprecated gemini-pro"
git push origin main
echo ✅ Pushed!
echo Wait 30 seconds then refresh your phone
pause
