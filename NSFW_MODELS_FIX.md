# NSFW Models - Troubleshooting & Configuration

## The Problem

You're getting: `sao10k/l3.3-70b-euryale-v2.2 is not a valid model ID`

This means the model is either:
1. Not available on OpenRouter anymore
2. Model ID changed
3. Model requires special access/credits

## Quick Fix Options

### Option 1: Use Standard Models (No NSFW Restriction)

Switch to a non-NSFW preset in the sidebar:
- **"balanced"** - Uses Claude Sonnet (high quality, no censorship for creative writing)
- **"creative"** - Higher temperature for creative prose
- **"premium"** - Uses Gemini Flash (good quality, fast)

Claude and Gemini can write mature content when given proper context - they just need clear instructions in your style guide.

### Option 2: Check Available NSFW Models

Run this to see what NSFW models are currently available:

```bash
python check_models.py list
```

Or search for specific models:

```bash
python check_models.py search euryale
python check_models.py search hermes
python check_models.py search uncensored
```

### Option 3: Test a Specific Model

```bash
python check_models.py test sao10k/l3.1-euryale-70b
```

### Option 4: Manually Configure Custom Model

In the web UI sidebar, you're using preset "premium_nsfw". You have options:

**A) Change preset to one that works:**
- Select "premium" or "balanced" from dropdown
- Add NSFW instructions in your style guide instead

**B) Check OpenRouter dashboard:**
- Visit https://openrouter.ai/models
- Search for "euryale" or "uncensored"
- Find available model IDs
- Note the exact model ID

**C) Update config manually:**
Edit `utils/model_config.py` and change the prose model to a working one.

## Currently Configured NSFW Models

After the fix, these models are configured:

- **balanced_nsfw, creative_nsfw, precise_nsfw**: `sao10k/l3.1-euryale-70b`
- **cost_optimized_nsfw**: `sao10k/l3-lunaris-8b`
- **premium_nsfw**: `nousresearch/hermes-3-llama-3.1-405b`

## Recommended Working Models for NSFW

Based on common availability, try these in order:

1. **sao10k/l3.1-euryale-70b** (good quality, uncensored)
2. **sao10k/l3-lunaris-8b** (smaller, cheaper, uncensored)
3. **nousresearch/hermes-3-llama-3.1-405b** (very large, premium)
4. **undi95/toppy-m-7b** (fast, uncensored)
5. **gryphe/mythomax-l2-13b** (classic uncensored)

## Alternative: Use Claude/Gemini with Clear Instructions

Modern AI models like Claude 3.5 Sonnet and Gemini 2.0 can write mature content when:

1. Given clear context that it's fiction
2. Told the target audience is adults
3. Provided with a style guide that includes mature content

**In your style guide, add:**
```
CONTENT NOTICE: This is adult fiction (18+) with explicit sexual content.
Target audience: Adult readers familiar with mature romance/erotica.

Write explicit intimate scenes with:
- Detailed physical sensations and reactions
- Specific body language and movement
- Character emotion and desire
- Natural, passionate dialogue
- [Other specific instructions...]
```

Then use "balanced" or "premium" preset with Claude/Gemini.

## How to Reload Configuration

After changing models in `model_config.py`:

1. **Stop the Streamlit app** (Ctrl+C in terminal)
2. **Restart it**: `python -m streamlit run web_ui.py`
3. **Model config will reload** with new settings

Or in the UI:
1. Change the preset dropdown in sidebar
2. Project will use new models going forward

## Testing Your Fix

1. Run: `python check_models.py test <model-id>`
2. If it returns ✅ and a response, the model works
3. Update `model_config.py` with that model ID
4. Restart Streamlit
5. Try prose generation again

## Need Help?

1. Check model availability: `python check_models.py list`
2. Search for alternatives: `python check_models.py search uncensored`
3. Test before using: `python check_models.py test <model-id>`
4. Check OpenRouter: https://openrouter.ai/models
5. Use regular models with detailed style guide as fallback
