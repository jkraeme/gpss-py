# GPSS/Py — Master Project Brief

**Session 6 Handoff Document**
Updated: February 24, 2026 — End of Session 5

---

## Table of Contents

1. [Critical Facts — Read First](#1-critical-facts--read-first)
2. [Hardware, Software and Environment](#2-hardware-software-and-environment)
3. [Directory Structure](#3-directory-structure)
4. [System Architecture](#4-system-architecture)
5. [Parser Implementation — Current Status](#5-parser-implementation--current-status)
6. [JOEBARB.GPS — First Grammar Target](#6-joebarbgps--first-grammar-target)
7. [Known Issues and Gotchas](#7-known-issues-and-gotchas)
8. [Verified Test Cases](#8-verified-test-cases)
9. [Current Project Status](#9-current-project-status)
10. [Session Log](#10-session-log)

---

## 1. Critical Facts — Read First

### 1.1 What This Project Is

GPSS/Py is an open-source tool that parses GPSS/H simulation models,
transpiles them to SimPy Python code, and presents results through a
Jupyter Notebook magic command interface (`%%gpss`). The user writes
GPSS/H. Python runs underneath. The user never sees the Python.

### 1.2 The Human Collaborator

- **GPSS Experience:** Experienced with IBM S/360 assembly language and op codes
- **References:** Owns both Schriber textbooks physically — can photograph listings
- **Oracle Machine:** Student GPSS/H Release 2.01 (UG172) running under DOSBox on i9 iMac
- **Dev Machine:** M4 iMac — miniforge/conda SET UP (Session 3). All packages installed.

### 1.3 Closed Decisions — Do Not Reopen

| Decision | Choice |
|----------|--------|
| Target dialect | GPSS/H Release 2.01 |
| Parser library | Lark |
| Simulation engine | SimPy (Phase 1 native; PREEMPT/CEC-FEC revisited later) |
| Primary UI | Jupyter `%%gpss` magic |
| Python version | 3.12 via miniforge ARM-native for M4 |
| Oracle machine | i9 iMac + DOSBox x86 native, confirmed working |
| Output format | Match GPSS/H exactly |
| Test framework | pytest |
| Version control | Git + GitHub — COMPLETE |

### 1.4 How to Start Each New Session

- Confirm you have read this brief completely.
- Check Section 9 (Current Status) for where things stand.
- Check Section 10 (Session Log) for what was done last.
- Ask what the project owner wants to accomplish today.
- **Do not suggest alternatives to closed decisions.**
- When writing GPSS/H code use column format: Label col 1-8, Block col 10-18, Operands col 19+.
- When writing Python use PEP 8, type hints, and docstrings on all public functions.

---

## 2. Hardware, Software and Environment

### 2.1 The Two Machines

**M4 iMac (Dev)**
- Apple M4 ARM, 24 GB RAM, 1 TB SSD
- miniforge installed at `~/miniforge3`
- conda env: `gpssenv` (Python 3.12)
- Packages: lark 1.3.1, simpy 4.1.1, pytest 9.0.2, jupyter, jupyterlab

**i9 iMac (Oracle)**
- Intel Core i9, 64 GB RAM
- DOSBox 0.74-3-3
- Student GPSS/H Release 2.01 (UG172) — ORACLE OPERATIONAL

### 2.2 iCloud Drive Sharing — COMPLETE (Session 3)

Both machines share `gpss_dev` via iCloud Drive:

- i9: `gpss_dev` moved to iCloud Drive, symlink created at `~/gpss_dev`
- M4: symlink created at `~/gpss_dev` pointing to iCloud Drive copy
- Confirmed path on M4: `~/gpss_dev/models/classic/JOEBARB.GPS` resolves correctly

> WARNING: Do not run DOSBox batch jobs that write output rapidly
> while iCloud is actively syncing the same directory.

### 2.3 iCloud Link Verification Procedure (Session 4)

Before starting any session that involves moving files between machines,
verify the iCloud link is active in both directions.

**Step 1 - Write sentinel from M4:**
```bash
date > ~/gpss_dev/icloud_sync_test.txt
cat ~/gpss_dev/icloud_sync_test.txt   # note the timestamp
```

**Step 2 - Verify on i9 (allow 30-60 seconds for sync):**
```bash
cat ~/gpss_dev/icloud_sync_test.txt   # must match M4 timestamp
```
If the file does not appear within 2 minutes, iCloud sync is not
working — do not proceed with oracle runs.

**Step 3 - Write sentinel back from i9:**
```bash
echo 'i9 ack' >> ~/gpss_dev/icloud_sync_test.txt
```
On M4, confirm both lines are present:
```bash
cat ~/gpss_dev/icloud_sync_test.txt   # should show timestamp + 'i9 ack'
```

**Step 4 - Clean up:**
```bash
rm ~/gpss_dev/icloud_sync_test.txt
```

If sync fails: check System Settings > Apple ID > iCloud on both
machines. Confirm iCloud Drive is enabled and not paused. Neither
machine should be in Low Power Mode.

### 2.4 Critical GPSSH.EXE Behavioral Facts

- Invocation: `GPSSH MODELNAME.GPS` (no path, no redirect)
- Output: `MODELNAME.LIS` created in same directory as `.GPS` file
- `GPSSHERR.MSG` must be in same directory as `GPSSH.EXE` or program fails
- NEVER use `>` redirect in `RUNALL.BAT` — DOSBox intercepts it (637 GB disaster lesson)
- DOSBox enforces 8.3 filenames — names longer than 8 chars get truncated

### 2.5 GitHub Repository — COMPLETE (Session 5)

- **URL:** https://github.com/jkraeme/gpss-py
- **Default branch:** `main`
- **Authentication:** Personal Access Token stored in Apple Passwords app
  and macOS Keychain (`credential.helper=osxkeychain`)
- **Daily workflow:**
```bash
git add .
git commit -m "description of what changed"
git push
```

---

## 3. Directory Structure

### 3.1 gpss_dev (Shared via iCloud)

```
~/gpss_dev/
  engine/            <- GPSSH.EXE, GPSSHERR.MSG
  models/classic/    <- JOEBARB, barber, inspect, toolcrib, widgets, widgets2
  models/homework/   <- HW1-HW5
  models/examples/   <- EX3-1 through EX15-1
  verified/
    GI_001_JOEBARB/
  logs/              <- timestamped run logs
  gpss_py/           <- Python project (this repo)
    gpss/
      __init__.py
      grammar.lark
      parser.py
    tests/
      __init__.py
      test_parser.py
    PROJECT_BRIEF.md <- live repo copy
    .gitignore

~/gpssh_docs/        <- personal archive (outside repo)
  GPSSH_PY_Project_Brief_v1.md  (not created — pre-archive sessions)
  GPSSH_PY_Project_Brief_v6.md  <- current
```

---

## 4. System Architecture

### 4.1 Three-Layer Design

```
LAYER 1: GPSS/H Source Code  (user writes this)
              |
         Lark parser + grammar
              |
LAYER 2: Abstract Syntax Tree  (internal)
              |
         Transpiler + statistics wrapper
              |
LAYER 3: SimPy Python Code  (runs automatically)
```

### 4.2 SimPy Engine Decision

Phase 1 uses SimPy's native process model. The GPSS/H CEC/FEC scan
phase with restart-on-change will be revisited when PREEMPT support is
added. For all Tier 1 blocks (no priorities, no preemption), SimPy
native is correct.

RNG Note: GPSS/H uses a specific Linear Congruential Generator.
Python random uses Mersenne Twister. GPSS/Py will achieve statistical
agreement, not identical traces. This is documented and accepted.

### 4.3 GPSS/H Column Format Rules

| Columns | Field | Notes |
|---------|-------|-------|
| 1-8 | Label | Optional; must start in col 1 |
| 9 | Separator | Mandatory blank |
| 10-18 | Keyword | |
| 19+ | Operands + comment | |

Labels must not duplicate any GPSS/H keyword or SNA name.
KEY is an SNA — this caused ERROR 94 in widgets.gps (lesson learned).

---

## 5. Parser Implementation — Current Status

### 5.1 Critical Architecture Lesson (Session 4)

The grammar describes NORMALIZED text, not raw GPSS/H column format.

The preprocessor strips leading whitespace from each line before
building normalized text for Lark. Therefore unlabeled_stmt must
NOT require a leading WS token — the preprocessor already removed it.
This was the root cause of the two failing tests fixed in Session 4.

Normalized form fed to Lark:
- Unlabeled statement: `KEYWORD operands` (no leading whitespace)
- Labeled statement: `LABEL KEYWORD operands`
- Comment: passed through as raw (`*...`)
- Blank: passed through as empty string

### 5.2 File: `gpss/grammar.lark` — COMPLETE

> Always write this file with cat heredoc from terminal.
> Never use VS Code or any editor — they introduce // comments
> or em-dash characters that break Lark silently.

```
start: statement+
statement: comment_stmt | blank_stmt | labeled_stmt | unlabeled_stmt
comment_stmt:   COMMENT NEWLINE
blank_stmt:     NEWLINE
labeled_stmt:   LABEL WS KEYWORD (WS operand_list)? NEWLINE
unlabeled_stmt: KEYWORD (WS operand_list)? NEWLINE
operand_list: slot ("," slot)*
slot: operand?
operand: NUMBER | NAME
LABEL:   /[A-Z$#@][A-Z0-9$#@]{0,7}/
KEYWORD: /[A-Z]+/
NAME:    /[A-Z][A-Z0-9]*/
NUMBER:  /[0-9]*\.[0-9]+|[0-9]+/
WS:      /[ \t]+/
COMMENT: /\*[^\n]*/
NEWLINE: /\r?\n/
%ignore /[ \t]+(?=\n)/
```

Changes from v4 brief:
- `operand_list: slot ("," slot)*` and `slot: operand?` — slot is
  optional, enabling empty operand positions: `,,,4` / `5,,1` / `,BACK`
- `NUMBER: /[0-9]*\.[0-9]+|[0-9]+/` — enables leading-dot decimals
  like `.15` (TRANSFER probability)

### 5.3 File: `gpss/parser.py` — COMPLETE

Key responsibilities:
1. Read raw GPSS/H lines
2. Classify each line: comment / blank / statement
3. Extract label, keyword, operands, comment fields
4. Validate labels against reserved word + SNA tables
5. Build normalized text (no leading whitespace)
6. Feed normalized text to Lark

RESERVED = GPSS_KEYWORDS | GPSS_SNAS. KEY is confirmed in GPSS_SNAS.
validate_label() checks labels against RESERVED and returns ERROR 94
message on collision.

### 5.4 File: `tests/test_parser.py` — 15/15 PASSING

| Test | Model | Stmt Count |
|------|-------|-----------|
| test_joebarb_file_exists | JOEBARB | - |
| test_joebarb_parses_clean | JOEBARB | - |
| test_joebarb_produces_tree | JOEBARB | - |
| test_joebarb_statement_count | JOEBARB | 9 |
| test_reserved_includes_key | synthetic | - |
| test_label_collision_rejected | synthetic | - |
| test_barber_file_exists | barber | - |
| test_barber_parses_clean | barber | - |
| test_barber_statement_count | barber | 12 |
| test_widgets_file_exists | widgets | - |
| test_widgets_parses_clean | widgets | - |
| test_widgets_statement_count | widgets | 17 |
| test_inspect_file_exists | inspect | - |
| test_inspect_parses_clean | inspect | - |
| test_inspect_statement_count | inspect | 20 |

Run the suite:
```bash
conda activate gpssenv
cd ~/gpss_dev/gpss_py
pytest tests/test_parser.py -v
```

Expected: `15 passed in ~0.09s`

---

## 6. JOEBARB.GPS — First Grammar Target

File uses tabs as field separators (verify with `cat -v` on macOS).

```
[TAB]SIMULATE
*
*[TAB]ONE-LINE, SINGLE-SERVER QUEUEING MODEL
*
[TAB]GENERATE[TAB]18,6[TAB]ARRIVALS EVERY 18 +- 6 MINUTES
[TAB]ADVANCE[TAB][TAB]0.5[TAB]HANG UP COAT
[TAB]SEIZE[TAB][TAB]JOE[TAB]CAPTURE THE BARBER
[TAB]ADVANCE[TAB][TAB]15,3[TAB]HAIRCUT TAKES 15 +- 3 MINUTES
[TAB]RELEASE[TAB][TAB]JOE[TAB]FREE THE BARBER
[TAB]TERMINATE[TAB]1[TAB]EXIT THE SHOP
*
[TAB]START[TAB][TAB]100
[TAB]END
```

13 lines total: 9 statement lines, 4 comment/blank lines. No labels.

Schriber confirmed:
- SIMULATE Time Limit operand is optional and ignored by GPSS/H
- TERMINATE A operand decrements the Termination Counter (TC)
- START 100 sets TC = 100; simulation ends when TC reaches zero

---

## 7. Known Issues and Gotchas

### Grammar file encoding
Must be written with cat heredoc from terminal — never with VS Code
or any text editor. Editors silently introduce // comments or em-dash
characters that cause Lark parse errors with no clear message.

### macOS cat vs GNU cat
macOS (BSD) cat has no -A flag. Use cat -v instead. Use od -c for
full byte-level inspection. cat -A is Linux/GNU only.

### Grammar vs preprocessor split
The grammar describes normalized text output by the preprocessor,
not raw GPSS/H column-format input. Never add WS requirements to
unlabeled_stmt. The preprocessor already stripped it.

### sed on macOS requires empty-string argument after -i
macOS BSD sed requires `sed -i ''` (with explicit empty string).
Linux GNU sed uses `sed -i` with no argument. Always use `sed -i ''`
on the M4.

### Two conda installations
Anaconda at /opt/anaconda3 (pre-existing) and Miniforge at
~/miniforge3 (installed Session 3). After conda init zsh, miniforge
is the default. Always confirm prompt shows (gpssenv) before running
project code.

### GitHub PAT authentication
GitHub does not accept account passwords for Git operations — a
Personal Access Token is required. PAT is stored in Apple Passwords
app and macOS Keychain. If needed again: GitHub > Settings >
Developer settings > Personal access tokens > Tokens (classic).
Scope needed: repo only.

WARNING: NEVER paste a PAT into any chat window or document.
If accidentally exposed, delete it immediately at GitHub and
generate a fresh one. This happened in Session 5 — immediately
remediated.

### DOSBox 637 GB disaster
NEVER use > redirect in RUNALL.BAT. NEVER create files with names
longer than 8 characters from a DOSBox batch file.

### Stray files in wrong directories
Session 5: stray gpss/test_parser.py accidentally committed. Removed
in commit f57a391. Always run git status before git add . to verify
only intended files are staged.

### EX10-1 SERVICE.DAT
Gets ERROR 572 (missing data file). Needs manual test with SERVICE.DAT
placed in examples/ directory.

### HW5 queue bug
WARNING 414 and ERROR 413 — DEPART without matching QUEUE. Bug is in
the original .GPS file, not the infrastructure.

---

## 8. Verified Test Cases

Phase 0 complete: 25/25 models run clean on oracle
(two consecutive 219 KB logs confirmed).

### GI_001 JOEBARB — Verified Values

| Metric | Value |
|--------|-------|
| Relative Clock | 1780.6667 |
| Facility JOE Utilization | 0.851 |
| Entries | 100 |
| Avg Time/Xact | 15.149 |
| Block 1 Total | 101 |
| Total Executions | 602 |
| RNG Stream 1 Chi-Square | 0.70 |

### Verification Triangle

For each model, all three must agree before the test case is marked VERIFIED:

```
Schriber book printed output
        +
GPSSH.EXE oracle run
        +
GPSS/Py output
  = VERIFIED
```

---

## 9. Current Project Status

Updated: End of Session 5 — February 24, 2026

| Component | Status |
|-----------|--------|
| Phase 0 — Oracle Infrastructure | COMPLETE |
| iCloud Drive sharing (both Macs) | COMPLETE |
| M4 miniforge + conda gpssenv | COMPLETE |
| gpss_py project structure | COMPLETE |
| parser.py | COMPLETE |
| grammar.lark | COMPLETE — 15/15 tests passing |
| test_parser.py | COMPLETE — 15/15 passing, 4 models covered |
| GitHub Repository | COMPLETE — github.com/jkraeme/gpss-py |
| Transpiler | NEXT ACTION |
| Jupyter Magic | PENDING |

### 9.1 Deploy This Brief

Run these commands to deploy every new version of this brief:

```bash
# 1. Copy to GitHub repo (public record):
cp ~/Downloads/PROJECT_BRIEF.md ~/gpss_dev/gpss_py/PROJECT_BRIEF.md

# 2. Copy to personal archive (increment version number):
cp ~/Downloads/PROJECT_BRIEF.md ~/gpssh_docs/GPSSH_PY_Project_Brief_v6.md

# 3. Commit and push:
cd ~/gpss_dev/gpss_py
git add PROJECT_BRIEF.md
git commit -m "Update PROJECT_BRIEF.md to v6.0 — Session 5 complete"
git push
```

### 9.2 Immediate Next Actions — In Priority Order

1. Begin transpiler — JOEBARB.GPS to SimPy code. Target blocks for
   Phase 1: GENERATE, ADVANCE, SEIZE, RELEASE, TERMINATE, START, END.
   Output must be a self-contained Python file that produces statistics
   matching GI_001 verified values.

2. Add transpiler.py to gpss/ — walks the Lark AST and emits SimPy
   code. Add tests/test_transpiler.py with at minimum a test that the
   transpiler produces runnable Python and that the JOEBARB simulation
   terminates with TC=0.

3. Verify JOEBARB transpiler output against oracle — Relative Clock
   ~1780, Facility JOE Utilization ~0.851. Statistical agreement
   (not identical traces) is the target.

4. Expand transpiler to barber.gps after JOEBARB is verified.

---

## 10. Session Log

### Session 1 — February 20, 2026
- Complete project scoping and architecture design
- Discovered Henriksen (2019) and Crain (2023) both deceased — project
  is a preservation effort
- Located GPSSH.EXE in ucoruh/gpssh-system-simulation GitHub repo
- DOSBox installed and confirmed working on i9 iMac
- Student GPSS/H Release 2.01 (UG172) confirmed RUNNING under DOSBox
- JOEBARB.GPS run successfully — GI_001 becomes first verified test case
- Full directory structure built: engine/ models/ data/ verified/ logs/

### Session 2 — February 22, 2026
- Diagnosed and fixed all 5 failing models (barber, widgets, widgets2,
  inspection, tool-crib)
- run_suite.sh iterated v2 through v5 — sleep 180 solution confirmed
- COPY NUL sentinel disaster: RUNALL_D.TXT grew to 637 GB — averted
- Achieved 25/25 OK on two consecutive confirmed runs (219 KB logs)
- Phase 0 declared COMPLETE

### Session 3 — February 23, 2026
- Received and analyzed GPSS/H internal execution logic document
- Decision: use SimPy native model for Phase 1; revisit PREEMPT later
- Installed Miniforge3 on M4 iMac (ARM native, conda-forge channel)
- Resolved conflict between pre-existing Anaconda and new Miniforge
- Created gpssenv conda environment with all required packages
- Set up iCloud Drive sharing — both Macs share gpss_dev via symlinks
- Created gpss_py project structure with all __init__.py files
- Wrote parser.py and test_parser.py — 6 tests, 4 passing
- grammar.lark: logic correct but encoding issues caused 2 failures
- Session ended: grammar.lark fix pending

### Session 4 — February 23, 2026
- Root cause of 2 failures: unlabeled_stmt required WS but preprocessor
  strips it — grammar described raw format not normalized format
- Fix: removed WS from unlabeled_stmt in grammar.lark
- Verified with cat -v (macOS; cat -A is Linux only — documented)
- pytest: 6/6 PASSING
- Converted project brief from .docx to Markdown for GitHub
- Added iCloud sync verification procedure (Section 2.3)

### Session 5 — February 24, 2026
- First GitHub repo ever for the project owner — milestone
- Git configured: identity, init.defaultBranch=main, osxkeychain
- .gitignore written — excludes DS_Store, pyc, pycache, *.lis, *.LIS
- Stray backslash file (gpss/\) found and deleted before first commit
- First commit: beaecbf — 7 files, 867 insertions
- PAT accidentally posted in chat — immediately deleted and regenerated
  LESSON: never paste PAT anywhere but the terminal prompt
- Repo pushed to github.com/jkraeme/gpss-py — public, open source
- Grammar expanded: slot rule for empty operand positions, NUMBER
  fixed for leading-dot decimals (.15)
- Tests expanded from 6 to 15 — barber (12), widgets (17), inspect (20)
- All four classic models parse clean: 15/15 PASSING
- Stray gpss/test_parser.py committed accidentally — removed in f57a391
- Three commits pushed: beaecbf, 654757c, f57a391
- Personal archive directory created: ~/gpssh_docs/
- Deploy procedure added to Section 9.1 of all future briefs

---

*In memory of James O. Henriksen (1946-2019) and Robert C. Crain (1947-2023)*

---
**End of Master Project Brief — Version 6.0**
