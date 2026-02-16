# Contributing Guide

Thank you for your interest in contributing to the **Wormhole Queue System**! 🙌  
This guide explains how to get started, the expected workflow, and how to contribute in a way that aligns with our **Definition of Done (DoD)** and quality expectations.

---

## Code of Conduct
All contributors are expected to uphold Oregon State University’s academic and professional conduct standards.  
Team communication occurs primarily through **Discord** and weekly in-person meetings.  

---

## Table of Contents

1. [Prerequisites & Setup](#-prerequisites--setup)  
2. [Local Development & Commands](#-local-development--commands)  
3. [CI / Formatting / Linting](#-ci--formatting--linting)  
4. [How to Contribute – Workflow](#-how-to-contribute--workflow)  
5. [Definition of Done (DoD)](#-definition-of-done-dod)  
6. [Reporting Bugs & Feature Requests](#-reporting-bugs--feature-requests)  
7. [Asking for Help](#-asking-for-help)

---

## Prerequisites & Setup

Before contributing, make sure you have the following installed:

- **Python 3.8+**
- **pip**
- **Git**
- Optional but recommended: a Python virtual environment

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/FarisNasse/CS461-wormhole-queue-system.git
   cd CS461-wormhole-queue-system
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**

   ```bash
   flask db upgrade
   ```

5. **Run the application**

   ```bash
   flask run
   ```

   The app should be available at `http://localhost:5000` by default.

---

## Local Development & Commands

### Run Tests

```bash
pytest
```

---

## CI / Formatting / Linting

All pull requests must pass Continuous Integration (CI) checks before merging. CI verifies:

- All tests pass
- No linting errors
- Code formatting standards are met

If CI fails, fix the issues locally and push updates to your branch.

---

## How to Contribute – Workflow

Please follow this contribution process:

1. **Fork the repository** and clone your fork.
2. **Create a new branch** for your work:

   ```bash
   git checkout -b feature/<short-description>
   ```

   Branch naming conventions:
   - `feature/<name>`
   - `bugfix/<name>`
   - `docs/<name>`
   - `refactor/<name>`

3. Write your code, tests, and documentation.
4. Run all tests and linters locally.
5. Commit with clear, descriptive messages:

   ```bash
   git commit -m "feat: add short description of feature"
   ```

6. Push your branch:

   ```bash
   git push origin feature/<short-description>
   ```

7. Open a Pull Request (PR) targeting the `main` branch.

---

## Pull Request Expectations & Definition of Done (DoD)

A Pull Request is considered ready for merge when:

-  All tests pass locally and in CI
-  New features include appropriate test coverage
-  Code passes linting and formatting checks
-  No merge conflicts exist
-  The PR description clearly explains:
  - What was changed
  - Why it was changed
  - How it was tested
-  At least one reviewer has approved the PR

### Code Review Expectations

During review:

- Be respectful and constructive.
- Address reviewer comments promptly.
- Do not merge your own PR without approval.
- Small, focused PRs are preferred over large ones.

---

## Reporting Bugs & Feature Requests

To report a bug or request a feature:

1. Go to the **Issues** tab on GitHub.
2. Click **New Issue**.
3. Use the appropriate template (if available).
4. Include:

   - A clear and descriptive title
   - Detailed explanation of the issue or feature
   - Steps to reproduce (for bugs)
   - Expected behavior vs. actual behavior
   - Screenshots or logs (if applicable)

Label issues appropriately (e.g., `bug`, `enhancement`, `documentation`).

---

## Asking for Help

If you need help:

- Open a GitHub Issue with the label `question`

We encourage collaboration and questions — don’t hesitate to ask!

---

Thank you for contributing to the Wormhole Queue System! 🚀
Your work helps improve the project for everyone.
