# 🚀 How to Deploy This App (Simple Guide)

This app uses Headless Chrome, so it needs a server that supports Docker containers. Here are the two easiest options:

---

## ✅ Option 1: Railway.app (Recommended)

**Cost:** ~$5-10/month | **Setup Time:** 5 minutes

### Steps:

1. **Create Railway Account:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy:**
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose `crackstreamcracker`
   - Railway auto-detects the `Dockerfile` and builds
   - Wait 2-3 minutes for build to complete

3. **Get Your URL:**
   - Click on your deployed service
   - Go to "Settings" → "Generate Domain"
   - Your app is live at `https://your-app.railway.app`

4. **Optional - Custom Domain:**
   - In Railway Settings → Domains
   - Add your custom domain
   - Update your DNS to point to Railway

**Cost Breakdown:**
- Free $5 credit to start
- Then ~$5-10/month depending on usage
- Pay only when the app is running

---

## ✅ Option 2: Render.com (Has Free Tier)

**Cost:** Free (slow) or $7/month (fast) | **Setup Time:** 5 minutes

### Steps:

1. **Create Render Account:**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Deploy:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Select `crackstreamcracker`
   - Render auto-detects Docker
   - Choose plan:
     - **Free:** Slow cold starts (15-30 seconds), sleeps after inactivity
     - **Starter ($7/mo):** Fast, always on

3. **Get Your URL:**
   - After deploy, you'll get `https://your-app.onrender.com`

4. **Optional - Custom Domain:**
   - Go to "Settings" → "Custom Domain"
   - Add your domain
   - Update your DNS records

**Free Tier Limitations:**
- Spins down after 15 min of inactivity
- Takes 30-60 seconds to wake up
- Good for testing, not for production

---

## 🛠️ What These Files Do

- **`Dockerfile`** - Instructions for building the app container (installs Chrome, Python, dependencies)
- **`railway.toml`** - Railway-specific configuration
- **`render.yaml`** - Render-specific configuration
- **`requirements.txt`** - Python dependencies (now includes `gunicorn` for production)

---

## 📝 After Deployment

### Test Your App:
1. Visit your deployed URL
2. Paste a stream URL (e.g., from crackstreams.ms)
3. Click "Analyze Page"
4. Should work exactly like localhost!

### Monitor Usage:
- **Railway:** Dashboard shows CPU, Memory, and monthly cost
- **Render:** Dashboard shows build logs and metrics

### Troubleshooting:
- **Build fails?** Check logs in Railway/Render dashboard
- **App slow?** Upgrade to a bigger plan (more RAM/CPU)
- **Timeout errors?** The 120s timeout in gunicorn should handle Selenium delays

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Railway** | $5 credit | ~$5-10/mo | Simplest, most reliable |
| **Render** | Yes (slow) | $7/mo | Testing on free, then upgrade |

**Recommendation:** Start with Railway's $5 credit to test, then decide if you want to continue at ~$5-10/month.

---

## 🔒 Security Notes

- This tool is for **educational purposes only**
- Consider adding basic auth if you want to keep it private
- Monitor usage to prevent abuse
- Keep in mind hosting costs if many people use it

---

## ❓ Need Help?

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **Issues with this app:** Open a GitHub issue

---

Happy deploying! 🎉

