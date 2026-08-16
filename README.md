[![Check TUM student jobs](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-jobs.yml/badge.svg)](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-jobs.yml)
[![Check TUM Living](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-living.yml/badge.svg)](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-living.yml)
[![Check Isar Aerospace student jobs](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-isar.yml/badge.svg)](https://github.com/Kvazac/HiWi-Notifier/actions/workflows/check-isar.yml)

# Munich Student Opportunity Notifiers

A collection of lightweight Python notifiers for monitoring student jobs, housing listings, and internship / working-student opportunities around Munich.

The project currently monitors:

* 🎓 **TUM HiWi / student jobs** — via the official TUM student-job RSS feed
* 🏠 **TUM Living** — for matching student housing listings
* 🚀 **Isar Aerospace** — for working-student and internship positions via Greenhouse

Matching results are sent to Discord using webhooks. The monitors run automatically through GitHub Actions, so no local machine or always-on server is required.

## Features

* Automatic scheduled checks using GitHub Actions
* Discord webhook notifications
* Independent filters for each source
* Persistent deduplication state
* First-run protection against notification floods
* Manual Discord test notifications
* Real-listing test mode for supported monitors
* Direct links to matching listings
* Independent Discord channels/webhooks
* Daily combined health heartbeat
* Immediate Discord alerts when a monitored workflow fails
* No Discord bot or continuously running process required

## Project structure

```text
.
├── .github/
│   └── workflows/
│       ├── check-jobs.yml
│       ├── check-living.yml
│       ├── check-isar.yml
│       └── notifier-status.yml
│
├── src/                    # TUM HiWi notifier
├── living/                 # TUM Living notifier
├── isar/                   # Isar Aerospace notifier
├── tests/
│
├── data/
│   ├── state.json
│   ├── living-state.json
│   └── isar-state.json
│
├── config.yml              # TUM HiWi configuration
├── living-config.yml       # TUM Living configuration
├── isar-config.yml         # Isar Aerospace configuration
├── requirements.txt
└── README.md
```

## Monitors

### 🎓 TUM HiWi notifier

The original monitor reads the official TUM student-job RSS feed:

`https://portal.mytum.de/schwarzesbrett/hiwi_stellen/asRss`

RSS is machine-readable XML, so opening the feed directly in a browser may display raw XML. This is expected.

The notifier parses the feed, applies the rules in `config.yml`, checks previously processed entries, and sends newly discovered matches to Discord.

The scheduled GitHub Actions workflow is:

```text
.github/workflows/check-jobs.yml
```

It currently runs once per hour at minute `17`.

### HiWi filtering

`config.yml` supports:

* `include_any`
* `include_all`
* `exclude_any`
* `title_include_any`
* `regex_any`
* `weighted_terms`
* `minimum_score`

Matching is case-insensitive and operates on the listing title and description.

Empty inclusion lists disable that particular restriction.

---

### 🏠 TUM Living notifier

The TUM Living monitor checks currently available housing listings and applies the filters configured in:

```text
living-config.yml
```

Its implementation is contained in:

```text
living/
```

The monitor maintains a separate state file:

```text
data/living-state.json
```

This prevents the same housing listing from being repeatedly posted to Discord.

Matching Discord notifications contain useful listing information and a link back to the TUM Living listing.

The scheduled workflow is:

```text
.github/workflows/check-living.yml
```

It currently runs once per hour at minute `10`.

The workflow also supports two manual testing modes:

```text
Send only a Discord test notification
Fetch and send a real matching listing as a test
```

The first verifies Discord delivery without processing a listing.

The second fetches a real currently matching listing and sends it to Discord so that the complete notification — including the listing link — can be tested without altering normal deduplication state.

---

### 🚀 Isar Aerospace notifier

The Isar Aerospace monitor checks the company's Greenhouse job board for student-oriented positions.

Its implementation is contained in:

```text
isar/
```

with configuration in:

```text
isar-config.yml
```

The default title filters detect terms including:

```text
Working Student
Werkstudent
Intern
Internship
Praktikant
Praktikum
```

This allows both English and German student-position titles to be detected.

The monitor uses:

```text
data/isar-state.json
```

for deduplication.

Matching notifications contain the job title, location, job ID, matching reason, description, and a direct link to the Greenhouse job posting.

The scheduled workflow is:

```text
.github/workflows/check-isar.yml
```

It currently runs once per hour at minute `30`.

Like the TUM Living monitor, it supports both a generic Discord notification test and a real-current-listing test.

## GitHub Actions schedules

The repository currently uses the following schedules:

| Monitor          | Workflow              | Schedule             |
| ---------------- | --------------------- | -------------------- |
| TUM Living       | `check-living.yml`    | Hourly at `:10`      |
| TUM HiWi         | `check-jobs.yml`      | Hourly at `:17`      |
| Isar Aerospace   | `check-isar.yml`      | Hourly at `:30`      |
| Status heartbeat | `notifier-status.yml` | Daily at `07:40 UTC` |

GitHub Actions cron schedules use UTC.

Scheduled workflows execute on GitHub-hosted runners. Your computer does **not** need to remain powered on after the repository has been configured.

## Discord setup

These notifiers use Discord webhooks rather than a full Discord bot.

A webhook is sufficient because the application only needs to send messages. It does not require a persistent Discord Gateway connection, bot account, or continuously running application.

To create one:

1. Open the desired Discord channel.
2. Select **Edit Channel**.
3. Open **Integrations → Webhooks**.
4. Create a webhook.
5. Copy its webhook URL.

Do not commit webhook URLs directly into the repository.

## GitHub secrets

Open:

**Repository → Settings → Secrets and variables → Actions**

and create the repository secrets referenced by the workflow files.

The workflows intentionally obtain webhook URLs through GitHub Actions secrets rather than storing them in source code.

Different monitors can therefore use different Discord channels simply by assigning their corresponding secret to a webhook created in the desired channel.

The status monitor uses its own status webhook secret, allowing health reports and failure alerts to be separated from normal listing notifications.

> **Security:** Discord webhook URLs should be treated as credentials. Anyone possessing a webhook URL may be able to post through that webhook. Never place real webhook URLs in source code, commits, issues, screenshots, or documentation.

## Installation for local development

Python 3.12 is used by the GitHub Actions workflows.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

or Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running locally

Set the appropriate Discord webhook URL in the environment before attempting to send notifications.

Linux/macOS:

```bash
export DISCORD_WEBHOOK_URL="your-webhook-url"
```

Windows PowerShell:

```powershell
$env:DISCORD_WEBHOOK_URL="your-webhook-url"
```

### TUM HiWi

Dry run:

```bash
python -m src.main --dry-run
```

Normal run:

```bash
python -m src.main
```

Discord test:

```bash
python -m src.main --test-notification
```

### TUM Living

Dry run:

```bash
python -m living.main --dry-run
```

Normal run:

```bash
python -m living.main
```

Discord test:

```bash
python -m living.main --test-notification
```

Real matching listing test:

```bash
python -m living.main --test-listing
```

### Isar Aerospace

Dry run:

```bash
python -m isar.main --dry-run
```

Normal run:

```bash
python -m isar.main
```

Discord test:

```bash
python -m isar.main --test-notification
```

Real matching job test:

```bash
python -m isar.main --test-listing
```

## First-run behavior

The monitors maintain state so that already processed listings are not repeatedly sent to Discord.

On the first normal run, existing entries are recorded as seen rather than immediately posted.

This is intentional.

Without first-run initialization, deploying a new notifier could cause every currently available matching listing to be interpreted as new and flood the Discord channel.

After initialization, newly discovered matching entries generate notifications normally.

## State and deduplication

The monitors maintain independent state files:

```text
data/state.json
data/living-state.json
data/isar-state.json
```

These store identifiers for previously processed entries.

The corresponding GitHub Actions workflows commit state changes back to the repository after successful checks.

As a result:

```text
Source → Fetch → Filter → Check state → Notify → Update state
```

A listing already recorded in state will not normally generate another notification.

The monitors use separate state files so activity from one source cannot interfere with another.

## Testing notifications

The workflows can be manually launched from the repository's **Actions** tab.

Select the desired workflow and choose **Run workflow**.

Where available, the workflow presents options for test notifications.

A generic test notification verifies:

```text
GitHub Actions
      ↓
Python notifier
      ↓
Discord webhook
      ↓
Discord channel
```

without treating an actual listing as new.

The real-listing test additionally verifies fetching, parsing, filtering, Discord embed generation, and direct listing URLs.

Test-listing operations are designed not to modify normal deduplication state.

## Monitoring and heartbeat

The repository includes:

```text
.github/workflows/notifier-status.yml
```

This monitors the health of:

* 🎓 TUM HiWi notifier
* 🏠 TUM Living notifier
* 🚀 Isar Aerospace notifier

### Daily heartbeat

A combined Discord status message is generated daily at:

```text
07:40 UTC
```

The heartbeat reports the latest workflow result, last-run time, trigger type, and a link to the corresponding GitHub Actions run.

A healthy heartbeat resembles:

```text
💚 Notifiers — Daily Status

🎓 TUM HiWi notifier
🟢 SUCCESS

🏠 TUM Living notifier
🟢 SUCCESS

🚀 Isar Aerospace notifier
🟢 SUCCESS
```

The status workflow can also be manually executed from the Actions tab to test the heartbeat.

### Failure alerts

The status workflow also listens for completion of each monitored workflow.

If one finishes with a conclusion other than `success`, an immediate Discord failure alert is generated containing:

* workflow name
* conclusion
* run number
* branch
* link to the failed GitHub Actions run

This means failures do not have to wait until the next daily heartbeat to become visible.

## Changing notification channels

Each notifier can post to a different Discord channel.

Create a webhook in each desired Discord channel and assign the corresponding webhook URL to the GitHub Actions secret referenced by that notifier's workflow.

No Python changes are required simply to move notifications between channels.

The status monitor can likewise use a dedicated administrative/status channel.

## Adding another monitor

The existing monitors follow a reusable architecture:

```text
Fetch source
    ↓
Normalize data
    ↓
Apply source-specific filters
    ↓
Compare against persisted state
    ↓
Send Discord notification
    ↓
Persist processed identifiers
```

A new source should generally receive:

```text
new-source/
    client.py
    discord.py
    main.py
    matcher.py
    models.py
    state.py

new-source-config.yml
data/new-source-state.json
.github/workflows/check-new-source.yml
```

If the new workflow should also be monitored, add its workflow name and workflow file to `notifier-status.yml`.

Prefer official feeds or public structured APIs over HTML scraping whenever they are available.

## Troubleshooting

### Workflow is green but no Discord message appears

This can be normal.

A successful workflow means the check completed successfully; it does not necessarily mean a new matching listing existed.

Check the workflow logs for the number of fetched and matched entries.

### First run sends nothing

Expected behavior. Existing entries are marked as seen during initialization to prevent a notification flood.

Use a test-notification or real-listing test when you want to verify Discord delivery immediately.

### Discord test fails

Check that:

1. the repository secret exists,
2. the workflow references the intended secret,
3. the webhook still exists in Discord,
4. the webhook belongs to the intended channel, and
5. the webhook URL has not been regenerated.

### Scheduled run does not appear at exactly the expected second

GitHub Actions schedules should not be treated as real-time timers. A cron expression determines when a workflow becomes eligible to run; GitHub may start the job somewhat later depending on service load.

### Duplicate notification

Check the corresponding file under `data/` and confirm that the workflow's state-persistence step successfully committed the latest state.

### Workflow fails while pushing state

Confirm that the workflow has:

```yaml
permissions:
  contents: write
```

and inspect the final state-persistence step in the failed Actions run.

## Design notes

The project deliberately uses relatively small, independent Python modules rather than one large monitoring process.

This keeps each source isolated:

* source-specific API/feed handling stays in its own package,
* filters can evolve independently,
* a failure in one scheduled monitor does not stop the others,
* each monitor can use a separate Discord destination,
* state remains independent,
* individual monitors can be disabled or extended without redesigning the whole project.

GitHub Actions provides the execution environment, while Discord webhooks provide notification delivery.

There is therefore no permanently running application instance between checks.

## Responsible use

This project is intended as a personal notification and filtering tool.

It does not reserve housing, submit applications, contact landlords, apply for jobs, or perform actions on behalf of the user.

When adding or modifying sources, respect the relevant site's terms, access controls, rate limits, and intended use. Prefer documented/public APIs and feeds where available, and keep polling intervals reasonable.

## Disclaimer

This is an independent personal project.

It is **not affiliated with, endorsed by, or operated by the Technical University of Munich, TUM Living, Isar Aerospace, Greenhouse, Discord, or GitHub**.

Availability and accuracy of notifications depend on the upstream services and may change if those services modify their feeds, APIs, websites, or access requirements.

Always verify important information on the original listing before acting on a notification.

## Repository

The project source and current configuration are available on [GitHub — Kvazac/HiWi-Notifier](https://github.com/Kvazac/HiWi-Notifier?utm_source=chatgpt.com).

Processed listing IDs are stored in `data/state.json`. The GitHub workflow commits state updates back to the repository, so listings are not posted repeatedly.
