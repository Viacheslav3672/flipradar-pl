# FlipRadar PL — starter MVP

This is a safe starter for `@FlipRadarPolandBot`. It provides:
- `/start` help
- `/add BUY RESALE SHIPPING OTHER_COSTS URL` profit calculator
- `/stats` simple history
- SQLite duplicate tracking for links submitted by the user

**It does not automatically fetch Vinted listings.** Connect only a source that you are authorized to use and that complies with Vinted's current terms. Do not use unofficial private APIs, evade anti-bot controls, or share your Telegram token.

## Run locally

1. Install Python 3.11+.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. In BotFather, create the bot and copy its token privately.
4. Set the token as an environment variable:

   macOS/Linux:
   ```bash
   export TELEGRAM_BOT_TOKEN='paste-token-here'
   python bot.py
   ```

   Windows PowerShell:
   ```powershell
   $env:TELEGRAM_BOT_TOKEN='paste-token-here'
   python bot.py
   ```

5. Open `@FlipRadarPolandBot` and press Start.

## Example

```text
/add 150 400 15 15 https://www.vinted.pl/
```

Calculation: 400 - 150 - 15 - 15 = 220 zł estimated profit.

## Notes

- Never commit `.env`, tokens, or session cookies to GitHub.
- For 24/7 uptime, deploy to a trusted host and set `TELEGRAM_BOT_TOKEN` as a secret/environment variable.
- The profit calculation is a simple estimate. Add actual platform fees, returns, taxes, discounts and other costs where applicable.
- A legitimate source of new listing data is required before building instant alerts.
