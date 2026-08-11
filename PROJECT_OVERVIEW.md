# Taiwan Cafe Work Finder - Project Overview

## What This Project Is

`taiwan-cafe-work-finder` is intended to become an evidence-first greater Taipei
cafe finder for quiet solo work and study. Online meetings are excluded until
the project can directly verify network quality, noise, and cafe policy.

The final product should not be a generic cafe directory. It should help users answer practical questions such as:

- Can I stay for a long time?
- Are outlets and Wi-Fi available?
- Is the environment quiet enough for focused solo work?
- Is the cafe suitable for solo laptop work, reading, or study?
- How reliable is this information, and when was it last verified?

## Phase 1 Objective

Phase 1 is only the research and data foundation. The goal is to build a repeatable way to discover, collect, normalize, validate, deduplicate, and manually review cafe records from public or accessible sources.

This phase produces:

- source research and collection strategy
- data schema and confidence model
- automated and optional collectors
- normalization and deduplication tooling
- validation scripts
- curated seed dataset with source links and confidence notes
- clear limitations and Phase 2 handoff notes

## Out Of Scope For Phase 1

- Final web UI design
- Product navigation, filters, maps, or visual branding
- User accounts, reviews, saved lists, or personalization
- Paid scraping services
- Login-gated, private, CAPTCHA-protected, paywalled, or anti-bot-protected data
- Claims that a cafe is currently work-friendly without source evidence or verification dates

## Skill And Tooling Check

Available skills were inspected before implementation. Relevant skills for this phase:

- `deep-research`: used for source discovery, access constraints, and source quality classification.
- `superpowers:brainstorming`: used to keep the build scoped to Phase 1 and avoid final UI work.
- `superpowers:writing-plans`: used to structure the implementation plan.
- `superpowers:test-driven-development`: used for the core normalization, validation, and deduplication logic.
- `superpowers:verification-before-completion`: used before reporting completion.

Frontend and browser UI skills are intentionally not used for implementation because the final website is out of scope for Phase 1.
