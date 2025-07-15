# Project-inspector
A Python utility to prepare and segment codebases into structured `.txt` files optimized for ChatGPT ingestion and analysis — including cross-references, TOC, and logic-preserving chunking.

---

## Features

- Auto-detects project type via `--stack` or custom inclusion.
- Recursively traverses code structure while excluding unnecessary clutter.
- Splits large files smartly (if >100MB) while preserving:
  - Project structure
  - Logical continuity
  - Cross-references
  - Mini TOC
- Warns when a file exceeds the safe token limit for direct copy-paste into ChatGPT prompts, helping users decide whether to paste manually or upload as a `.txt` file instead.
- Optimized output for ChatGPT context tracking and navigation.
- Supports `--output`, `--include` and `--exclude`.

---

## Supported Stacks (`--stack` option)

- `python`: Python-only projects
- `java`: Java with XML and `.properties`
- `cs`, `dotnet`: C# and .NET
- `cpp`, `c`: C/C++
- `rust`: Rust projects with Cargo
- `js`: JavaScript / TypeScript frontends
- `fullstack`: Smart combo for real-world apps:
  - Backend: Python, Java, C#, Go, Rust, PHP, Ruby
  - Frontend: JS, TS, React, Vue, Angular
  - DevOps: Terraform, Shell, YAML, CI/CD
  - Docs: Markdown, TXT, SQL, CSV, JSON

---

## How It Works

1. **Stack Detection / Filtering**  
   Based on `--stack`, it includes relevant file extensions, folders, and excludes clutter like `.git`, `bin`, `node_modules`, etc.

2. **Project Structure Generation**  
   At the beginning of the output file, a visual tree of the project is included to assist with navigation and understanding of the repo layout.

3. **File Splitting Logic (if >100MB)**  
   - The entire project is chunked into logical `.txt` files.
   - Each chunk includes:
     - Its place in the global TOC
     - Cross-references to indicate which files are included
     - Continuity so ChatGPT can track classes/functions spanning files

4. **Mini TOC and Cross-Referencing**  
   - A TOC is prepended in each split file
   - Every file lists the original files it contains
   - This improves context continuity across uploads

---

## Usage Examples

### Basic usage
```bash
python3 project-inspector.py --path ./my_project
```

### Choose a tech stack
```bash
python3 project-inspector.py --path ./backend --stack python
```

### Web app project
```bash
python3 project-inspector.py --path ./full_app --stack fullstack
```

### Manually include/exclude file types
```bash
python3 project-inspector.py --path ./src --include html,css,js --exclude dist,.git
```

---

## Design Decisions

- **Why not rely on token count?**  
  File-based `.txt` uploads bypass ChatGPT token limits. Splitting occurs only if a file exceeds 100MB.

- **Why preserve structure in `.txt` format?**  
  This helps ChatGPT understand the architectural context of the code — improving reviews, debugging, or extraction tasks.

- **Why cross-referencing?**  
  Allows linking back to original files when functions/classes span multiple files or folders.

---

## Output Format

If below 100MB:
```
project-structure.txt
```

If above 100MB:
```
project-part_0.txt   ⟶ includes TOC + main structure
project-part_1.txt   ⟶ e.g., utils.py, main.py
project-part_2.txt   ⟶ e.g., config files
...
```

Each split file includes:
- Mini TOC
- Logical groupings
- Source file references (e.g., `Included: utils.py, helpers.py`)

---

## Contributions 

Contributions are wellcome! 

---

© 2025 — Project-inspector by q3alique
