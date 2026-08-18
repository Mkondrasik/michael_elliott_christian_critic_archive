# The Michael Elliott / Christian Critic Archive

Static public repository for the film reviews written by **Michael Ondrasik** under the byline **Michael Elliott**.

## Version 1

- 50 author-verified review pages (`Elliott_0001`–`Elliott_0050`)
- Client-side search by film title, Scripture, review ID, publication date, and sermon/spiritual topic
- Scripture → Film index
- Sermon/Spiritual Topic index
- Structured JSON data under `/data`
- Internet Archive URL field reserved for each review
- Source scans intentionally excluded until public-facing copies are approved

## Repository structure

- `index.html` — searchable review index
- `scripture.html` — Scripture → Film index
- `themes.html` — theme index
- `about.html` — provenance/editorial policy
- `reviews/` — permanent review pages
- `data/reviews.json` — public metadata
- `data/scripture-index.json` — generated Scripture index
- `data/theme-index.json` — generated theme index
- `assets/` — CSS and JavaScript

## Date policy

The public site does **not** expose legacy printed/reprint/template dates. Only an established original publication date is displayed. At this stage, dates established by the author for `Elliott_0041`–`Elliott_0050` are included; other dates remain “To be established.”

## Internet Archive

Each review record contains `internet_archive_url: null`. After an approved archival scan is deposited at Internet Archive, replace that value with the item URL and update the corresponding review page. See `INTERNET_ARCHIVE_WORKFLOW.md`.

## GitHub Pages

This repository is plain HTML/CSS/JavaScript and requires no build system. Upload these files to the root of a GitHub repository and enable Pages from the repository root. See `PUBLISHING.md`.
