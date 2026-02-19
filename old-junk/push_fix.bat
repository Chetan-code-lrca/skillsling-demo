@echo off
cd /d "C:\Users\cheta\OneDrive\Desktop\pros\skillsling"
echo ========================================
echo Pushing SkillSling Mobile Fix
echo ========================================
echo.
echo Step 1: Adding app.py...
git add app.py
echo ✅ Added
echo.
echo Step 2: Committing changes...
git commit -m "Fix: Mobile-friendly Chat API and responsive UI - resolves 400 streaming errors on mobile"
echo ✅ Committed
echo.
echo Step 3: Pushing to main...
git push origin main
echo ✅ Pushed!
echo.
echo ========================================
echo 🚀 FIX DEPLOYED!
echo ========================================
echo.
echo Your app is now redeploying on Streamlit Cloud
echo Wait 30-60 seconds for deployment to complete
echo Then refresh your mobile browser
echo.
pause
