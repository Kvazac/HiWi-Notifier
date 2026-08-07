# TUM HiWi Discord Notifier

Checks the official TUM student-job RSS feed once per hour, applies configurable filters, and posts new matching listings to Discord.

## Why the RSS page looks like raw XML

That is normal. RSS is machine-readable XML, and browsers often display it without styling. This project reads that XML directly.

## Deployment

### 1. Create a Discord webhook

In the target Discord channel:

1. Open **Edit Channel → Integrations → Webhooks**.
2. Create a webhook.
3. Copy its URL.

A webhook is preferable here to a full Discord bot because this notifier only needs to post messages. It needs no gateway connection, bot token, or always-on process.

### 2. Create a GitHub repository

Upload this project to a new repository.

### 3. Add the webhook secret

In the repository, open:

**Settings → Secrets and variables → Actions → New repository secret**

Create:

```text
DISCORD_WEBHOOK_URL
```

Paste the Discord webhook URL as its value.

### 4. Configure filters

Edit `config.yml`. Empty inclusion lists mean “do not restrict by this rule.”

### 5. Enable the workflow

The workflow runs hourly at minute 17. It can also be run manually from the **Actions** tab.

On its first normal run, existing feed entries are recorded without sending notifications. This prevents an initial flood. To test Discord immediately, run:

```bash
python -m src.main --test-notification
```

or launch the GitHub workflow manually with `send_test_notification` enabled.

## Local usage

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python -m src.main --dry-run
python -m src.main
```

## Filter behavior

A listing must satisfy all enabled rule groups:

- `include_any`: at least one term must occur.
- `include_all`: every term must occur.
- `exclude_any`: none of the terms may occur.
- `title_include_any`: at least one term must occur in the title.
- `regex_any`: at least one regular expression must match.
- `minimum_score`: weighted keyword score must reach the threshold.

Matching is case-insensitive and searches the RSS title and description.

## State

Processed listing IDs are stored in `data/state.json`. The GitHub workflow commits state updates back to the repository, so listings are not posted repeatedly.
