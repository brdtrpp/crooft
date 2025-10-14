# Secure Deployment Guide for Fiction Pipeline

This guide will help you deploy your Fiction Pipeline app to Streamlit Cloud with secure API key management and authentication.

## Overview of Changes

Your app now includes:
- **Authentication system**: Username/password protection
- **Secure API key management**: Keys stored in Streamlit secrets (not visible to users)
- **Developer override**: Optional testing mode for API keys
- **Comprehensive .gitignore**: Ensures secrets never get committed

## Local Development Setup

### 1. Configure Your API Keys

Edit `.streamlit/secrets.toml` with your actual API keys:

```toml
# API Keys
OPENROUTER_API_KEY = "sk-or-v1-your-actual-key-here"
PINECONE_API_KEY = "your-pinecone-key-here"

# Authentication (optional for local dev)
[passwords]
admin = "your-local-password"
```

### 2. Test Locally

```bash
streamlit run web_ui.py
```

The app will:
- Load API keys from `.streamlit/secrets.toml`
- Require username/password login (if configured)
- Show "API keys loaded from secure storage" message

### 3. Skip Authentication During Development (Optional)

To disable authentication during local development, comment out the `[passwords]` section in your `secrets.toml`:

```toml
# [passwords]
# admin = "password"
```

The app will automatically skip the login screen when no passwords are configured.

## Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

1. Ensure `.streamlit/secrets.toml` is NOT committed:
   ```bash
   git status
   # Should NOT show .streamlit/secrets.toml
   ```

2. Commit your changes (if using git):
   ```bash
   git add .
   git commit -m "Add secure authentication and API key management"
   git push
   ```

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `web_ui.py`
6. Click "Advanced settings"

### Step 3: Configure Secrets

In the "Secrets" section, paste your configuration in TOML format:

```toml
# API Keys (REQUIRED)
OPENROUTER_API_KEY = "sk-or-v1-your-production-key-here"
PINECONE_API_KEY = "your-production-pinecone-key-here"

# Authentication (REQUIRED for production)
[passwords]
admin = "strong-production-password-here"
user1 = "another-strong-password"
```

**Important Security Notes:**
- Use STRONG passwords for production
- Different passwords for each user
- Never share these passwords in public channels
- Different API keys for production vs development (optional but recommended)

### Step 4: Deploy

1. Click "Deploy!"
2. Wait for the app to build and start
3. Test the authentication and functionality

## Authentication System

### How It Works

1. When users visit your app, they see a login screen
2. Username/password are validated against `secrets["passwords"]`
3. Passwords are compared using `hmac.compare_digest()` for security
4. Once authenticated, users can access the full app
5. Session persists until browser is closed or cache is cleared

### Managing Users

To add/remove users, update the `[passwords]` section in Streamlit Cloud secrets:

```toml
[passwords]
admin = "password1"
editor = "password2"
viewer = "password3"
```

Then click "Save" in the Streamlit Cloud secrets editor. The app will restart with the new credentials.

### Disable Authentication (Not Recommended)

To disable authentication entirely, remove the `[passwords]` section from your secrets configuration. The app will automatically skip the login screen.

## API Key Management

### How It Works

1. App tries to load keys from `st.secrets` first (Streamlit Cloud)
2. Falls back to environment variables (local development with .env)
3. Shows a clear status message in the sidebar
4. Developer override available in "Developer Override" expander (for testing)

### Security Features

- API keys are NEVER shown in the UI (type="password")
- Keys are stored in Streamlit's encrypted secrets storage
- Keys are set as environment variables only after loading
- Optional developer override is hidden in expander

### Developer Override

For testing with different API keys without changing secrets:

1. Open the "Developer Override" expander in sidebar
2. Enter temporary API keys
3. These override the default keys for that session only
4. Refresh the page to revert to default keys

## Security Best Practices

### For Production:
- Always use strong, unique passwords
- Use different API keys for production vs development
- Never commit `.streamlit/secrets.toml` to git
- Regularly rotate passwords and API keys
- Monitor your API usage for unexpected activity

### For Development:
- Keep `.streamlit/secrets.toml` for local testing
- Use test/development API keys locally
- Don't share your local secrets file
- Test authentication before deploying

## Troubleshooting

### "No API keys configured" warning
- Check that secrets are properly configured in Streamlit Cloud
- Verify TOML syntax is correct (no quotes issues)
- Ensure secret names match exactly: `OPENROUTER_API_KEY`

### Authentication not working
- Verify `[passwords]` section exists in secrets
- Check username/password for typos
- Clear browser cache and try again
- Check Streamlit Cloud logs for errors

### App won't load after deployment
- Check Streamlit Cloud logs for errors
- Verify `requirements.txt` is up to date
- Ensure all secrets are properly configured
- Try restarting the app from Streamlit Cloud dashboard

### Local development shows login but you want to skip it
- Comment out or remove the `[passwords]` section in `.streamlit/secrets.toml`
- The app will automatically disable authentication

## File Structure

```
your-project/
├── web_ui.py                    # Main app (now with auth + secure keys)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Ignores secrets and sensitive files
├── .streamlit/
│   ├── secrets.toml            # Local secrets (NEVER commit)
│   └── secrets.toml.example    # Template for reference
└── DEPLOYMENT.md               # This file
```

## Quick Reference

### Local Testing:
```bash
# Edit your secrets
nano .streamlit/secrets.toml

# Run the app
streamlit run web_ui.py
```

### Update Production Secrets:
1. Go to Streamlit Cloud dashboard
2. Click your app → Settings → Secrets
3. Edit and save
4. App restarts automatically

### Add New User:
1. Edit secrets (local or cloud)
2. Add line under `[passwords]`: `newuser = "password"`
3. Save and restart

## Support

If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify all secrets are configured correctly
3. Test locally first with the same secrets
4. Check the Streamlit documentation: https://docs.streamlit.io

## Next Steps

After successful deployment:
1. Test all functionality with production credentials
2. Share the app URL with your users
3. Provide them with login credentials securely
4. Monitor usage and performance
5. Regularly update dependencies and rotate secrets

Happy writing!
