# Telangana Police SI 2026 — AI Coaching System

A personal, offline-first coaching system for the Telangana Police Sub-Inspector 2026
examination. It is being built to behave like an experienced coaching institute: teach
you to recognise what a question is before solving it, give you standard and fast
methods, warn you about traps, track what you get wrong, and bring it back at the right
time.

## What this project is

Right now it is **infrastructure only**. The folders, rules, and safety checks exist.
The exam content does not.

That is deliberate and worth understanding: this system will only ever teach you things
it can trace back to a real source. It has not been given any Telangana SI facts yet, so
it does not claim any. Nothing in these folders was filled in with a plausible guess.

**Current status:** bootstrap `COMPLETE`. See `PROJECT_STATE.md` for the real,
component-by-component picture.

## The one idea behind everything here

Wrong information is worse than missing information.

A study system that confidently teaches an invented syllabus point, a shortcut that
breaks on some numbers, or a wrong physical standard does more damage than one that says
"I don't know this yet". So every fact in this project carries a label saying where it
came from:

| Label               | Meaning                                                    |
| ------------------- | ---------------------------------------------------------- |
| `T1_OFFICIAL`       | From an official TGPRB document. Trustworthy                |
| `T2_HISTORICAL_PYQ` | From a real past paper. Shows what was actually asked       |
| `T3_EXPERT`         | From a teacher, book, or video. Informed, but checked first  |
| `T4_AI`             | Written by an AI. Not trusted until independently checked    |

Nothing gets promoted to a higher label to make the system look better informed.

## How to check the project is intact

Open a terminal in this folder and run:

```
python scripts/validate_bootstrap.py
```

It prints one line per check and finishes with a summary. If it says `FAIL` anywhere,
something has been moved or deleted — tell your AI assistant and it will investigate.

To run the automated tests as well:

```
python -m unittest discover -s tests -v
```

Neither command needs anything installed beyond Python itself.

## What is in each folder

| Folder             | In plain language                                                  |
| ------------------ | ------------------------------------------------------------------ |
| `docs/`            | Guides and reports written for you to read                          |
| `specs/`           | Plans written before anything is built                              |
| `source_material/` | Original files exactly as they were found. Never edited             |
| `research/`        | Records of what was gathered, and honestly, what was missed         |
| `knowledge/`       | Checked facts and methods. The only thing the tutor is allowed to teach from |
| `pyq/`             | Past papers turned into searchable data, plus weightage analysis     |
| `expert_methods/`  | Techniques from teachers and videos, before they have been checked   |
| `verification/`    | The paper trail proving things were actually checked                 |
| `agents/`          | Which AI does which job, and the rules stopping one AI marking its own homework |
| `backend/`         | The program logic (not built yet)                                   |
| `frontend/`        | The screens you will use (not built yet)                            |
| `database/`        | Instructions for building your database                             |
| `tests/`           | Automatic checks                                                    |
| `scripts/`         | Small tools you can run                                             |
| `config/`          | Settings. Never passwords                                           |
| `physical/`        | Physical event standards and your training log                       |
| `data/`            | Your live database and your study history                            |

Each folder has its own `README.md` explaining its rules in more detail.

## Two things that could lose your work

**1. Your study history is not protected by Git.** Once the app exists, your practice
attempts, timings, and revision schedule will live in `data/si_coach.db`. Git ignores that
file on purpose, because a database is generated, not written by hand. To back it up,
close the app and copy `data/si_coach.db` somewhere else — ideally a different drive or
cloud storage. A copy in the same folder is not a backup.

**2. Large downloaded material is not protected by Git either.** Videos, audio, and
archives under `source_material/` are excluded, because storing hundreds of videos in Git
would make this project unusable. Back that folder up the same way.

## Your API keys

Copy `.env.example` to a new file named `.env` and put your keys in the copy. The `.env`
file is excluded from Git, so your keys never get recorded in the project history.

If a key ever does get committed by accident, treat it as public: revoke it and issue a
new one. Removing it in a later commit does not remove it from Git's history.

## What happens next

The project is at phase 1 of 7. The next step is **not** coding.

The system needs the official TGPRB SI notification and syllabus document. Until it has
that, the syllabus, exam pattern, marks, eligibility rules, and physical standards all
stay marked `BLOCKED`, because the alternative — writing them from memory — is exactly the
failure this project is built to avoid.

The full phase plan and the next action are in `PROJECT_STATE.md`.

## Working with your AI assistant on this project

You do not need to learn Git or run commands. When you start a new session, the assistant
reads `CLAUDE.md` and then `PROJECT_STATE.md` and picks up where the last one stopped —
which is why those files exist. Conversation history disappears; these files do not.

Useful things to ask for:

- "What is the real status of the project?" — it should answer from `PROJECT_STATE.md`
  using only `COMPLETE`, `PARTIAL`, or `BLOCKED`
- "Show me what is blocked and why"
- "Save a checkpoint" — it will commit the current state to Git for you
- "Is this fact verified, and what is the source?" — every fact should have an answer

If you are ever told something is "done" without evidence, ask which acceptance criteria
were checked and how. The project rules require an answer.

## Key files

| File                     | What it holds                                              |
| ------------------------ | ---------------------------------------------------------- |
| `PROJECT_STATE.md`       | Where the project stands. Read this first                   |
| `TASK_LEDGER.md`         | Every task and its status                                   |
| `DECISIONS.md`           | Choices made and the reasoning behind them                  |
| `KNOWLEDGE_LEDGER.md`    | What the system actually knows. Currently zero               |
| `SOURCE_LEDGER.md`       | Every source ever used. Currently zero                       |
| `VERIFICATION_POLICY.md` | How a claim is allowed to become trusted                     |
| `TEST_PLAN.md`           | What must be tested before anything is called complete       |
| `CLAUDE.md`              | The rules your AI assistant must follow                      |

## Scope note

This is a private study tool for one candidate. It does not give medical, dietary, legal,
or recruitment advice, and it is not affiliated with TGPRB. Always confirm official
examination details against the official notification.


