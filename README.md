# The First-Client Survival Kit

*A plain-English manual for landing and surviving your first freelance client.*

A set of short Markdown guides plus a no-dependency static HTML site, published by **Asdale Dynamics, LLC** as part of a beginner-friendly library of practical manuals in the style of Dylan Asdale's *The Massive AI Manual*: plain English, step by step, never condescending.

## What's inside

Chapters in `docs/`:

| Chapter | What it covers |
| --- | --- |
| [00-start-here.md](docs/00-start-here.md) | The whole manual in five minutes |
| [01-services-one-pager.md](docs/01-services-one-pager.md) | Writing the seven-part services one-pager |
| [02-quoting-projects.md](docs/02-quoting-projects.md) | Quoting by project, not hour-fear — the calm math |
| [03-simple-contracts.md](docs/03-simple-contracts.md) | Simple one-page agreements without lawyer-fear framing |
| [04-invoices-that-get-paid.md](docs/04-invoices-that-get-paid.md) | Invoice anatomy, rhythm, and kind follow-ups |
| [05-scope-guarding.md](docs/05-scope-guarding.md) | Kind scope-guarding: three sentences ready to hand |
| [06-testimonials.md](docs/06-testimonials.md) | Collecting testimonials on delivery day |
| [07-when-llc-makes-sense.md](docs/07-when-llc-makes-sense.md) | When an LLC makes sense — a tool, not a trophy |

Print-and-use companions:

- [quote-worksheet.md](docs/quote-worksheet.md) — fill this in before sending any quote
- [invoice-checklist.md](docs/invoice-checklist.md) — tick every line before you hit send
- [glossary.md](docs/glossary.md) — plain-English definitions

## Build and verify

Requires only Python 3.9+. No packages, no network.

```sh
python3 build.py          # build the static site into site/
python3 build.py --test   # run the self-tests (build + content checks)
```

To browse the site, open `site/index.html` in a browser. Everything is local: no frameworks, no tracking, no external requests.

## Companion projects

- **llc-first-year-handbook** — the first-year owner's manual for a new LLC; a deeper dive on chapter 7.
- **invoice-tracker-webapp** — a local, private web app for tracking invoice numbers, due dates, and follow-ups; pairs with chapter 4.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.

**This project is education only — never legal, medical, or tax advice.**
