# Design Spec: Onboarding and Agent Familiarization Files
Date: 2026-06-25
Status: Pending Approval

## 1. Objective
Create standard onboarding documentation (`README.md`, `CLAUDE.md`, `.agents/AGENTS.md`) at the workspace root to facilitate instant project understanding and setup for both human developers and future AI coding agents (`agy`/`Antigravity`).

## 2. Architecture & Outline

### 2.1 README.md (Root)
- **Purpose:** Human-facing entry point and high-level project guide.
- **Outlines:**
  - Project Title & Thesis Context (Model-Driven Digital Twins via AAS).
  - Directory Structure Overview (`AAS Client`, `AAS Docker`, `DT Unity`, `Documentos`, `docs`).
  - Architecture flow diagram (AAS $\leftrightarrow$ BaSyx $\leftrightarrow$ Unity).
  - Quick setup instructions for the infrastructure and Unity simulation.

### 2.2 CLAUDE.md (Root)
- **Purpose:** Agent command cheat sheet and coding standards.
- **Outlines:**
  - Docker execution commands (`docker-compose up -d`, etc.).
  - Python AAS Client commands (running scripts, compilation using Nuitka).
  - LaTeX thesis compilation commands (using `latexmk` or `pdflatex` via the Makefile).
  - Programming standards (Python 3.10+ compatibility rules, Unity C# style, rich console logging).

### 2.3 .agents/AGENTS.md
- **Purpose:** Automated rule injection for future `agy`/`Antigravity` agents.
- **Outlines:**
  - Code preservation rules (always respect compatibility patches, do not break BaSyx REST endpoints).
  - Unity behavioral model integration rules (referencing Empties, TranslateContinuous, RotateContinuous, RotateHinge).
  - Language rules (the thesis is written in English, but developer instructions/queries can be in Portuguese).
  - Acronym conventions.

## 3. Success Criteria
- [ ] `C:/Users/LazyT/Desktop/Tese/README.md` created with comprehensive content.
- [ ] `C:/Users/LazyT/Desktop/Tese/CLAUDE.md` created with accurate commands and code patterns.
- [ ] `C:/Users/LazyT/Desktop/Tese/.agents/AGENTS.md` created with clear agent instructions.
- [ ] All paths, repository references, and commands match actual workspace settings.
