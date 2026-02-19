# SkillSling AI - Mobile Deployment Guide

## Latest Fix (Feb 14, 2026)

### What Was Wrong
- Gemini API streaming was causing **400 errors** on mobile networks
- UI was not optimized for small screens
- Chat context wasn't being properly preserved

### What's Fixed ✅
1. **Switched to Gemini Chat API** - More stable, no streaming timeouts
2. **Mobile-first UI** - Centered layout, touch-friendly buttons, responsive text
3. **Better context handling** - Proper multi-turn conversation support
4. **Fallback models** - Tries flash → flash-latest → pro

---

## Setup Instructions

### For Streamlit Cloud

1. **Add API Key to Secrets**
   ```bash
   # In Streamlit Cloud dashboard:
   # Settings → Secrets Management → Add this line:
   GOOGLE_API_KEY = "your-google-api-key-here"
   ```

2. **Deploy the app**
   ```bash
   git push origin main
   ```

### For Local Testing

1. **Set environment variable**
   ```bash
   export GOOGLE_API_KEY="your-google-api-key-here"
   ```

2. **Run Streamlit**
   ```bash
   streamlit run app.py
   ```

3. **Test the API**
   ```bash
   python test_gemini_api.py
   ```

---

## How to Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Add to Streamlit secrets or environment variable

---

## Testing on Mobile

### iPhone
1. Go to Streamlit Cloud app URL
2. Open in Safari
3. Add to home screen for app-like experience
4. Test chat with "hey" or any question

### Android
1. Go to Streamlit Cloud app URL
2. Open in Chrome
3. Add to home screen
4. Test chat

### What to Test
- ✅ Chat input visible above keyboard
- ✅ Messages display correctly
- ✅ Buttons are easy to tap
- ✅ Text is readable
- ✅ Responses come back without error

---

## Troubleshooting

### Still Getting 400 Error?
1. **Restart the app** - Changes to code require restart
2. **Check API key** - Make sure GOOGLE_API_KEY is set
3. **Test in isolation**:
   ```bash
   python test_gemini_api.py
   ```

### UI Still Bad on Mobile?
1. Check browser zoom level (should be 100%)
2. Try different device/browser
3. Clear browser cache
4. Try incognito mode

### Context Not Showing?
1. Upload PDF notes in sidebar
2. Make sure file is readable
3. Check file size (max 200MB)

---

## Architecture

```
User Input (Mobile)
    ↓
Streamlit Chat Input
    ↓
Python Logic:
  - Build conversation history
  - Add system instruction
  - Add context from notes
  - Add facts from database
    ↓
Gemini Chat API
  (NO streaming - more stable)
    ↓
Response back to Mobile UI
    ↓
Markdown rendered on mobile
```

---

## Performance Tips

- **First response**: 2-3 seconds (Cold start)
- **Subsequent responses**: 1-2 seconds (Warm)
- **Mobile networks**: Works on 3G/4G/5G, even slow connections
- **Offline**: Won't work (requires Gemini API)

---

## Files Modified

- `app.py` - Main application (Chat API, UI CSS, error handling)
- `requirements.txt` - Dependencies (no changes)
- `current_facts.py` - Fact database (no changes)

---

## Version History

- **v2.0 (Current)**: Gemini Chat API, mobile UI rewrite
- **v1.0**: Ollama + Gemini fallback with streaming

