# Contributing Guide

This document explains how to contribute to the Wormhole Queue System project so that all work meets our Definition of Done (DoD) and Quality Gates defined in the Team Charter.  
It will be updated after the technical design phase (scheduled for November 23, 2025).

---

## Code of Conduct
All contributors are expected to uphold Oregon State University’s academic and professional conduct standards.  
Team communication occurs primarily through **Discord** and weekly in-person meetings.  

---

## Getting Started
**Prerequisites**
- Python
- pip and Git

**Setup (to be finalized after development begins)**
```bash
1. Clone the Repository:
   git clone <your-repo-url>
   cd <your-repo-name>

2. Create and Activate a Virtual Environment:
   python -m venv venv
   On macOS/Linux:
       source venv/bin/activate
   On Windows:
       venv\Scripts\activate

3. Install Dependencies:
   pip install -r requirements.txt
   (If requirements.txt is empty, you can install manually using:)
   pip install flask pytest flask_sqlalchemy

Database Setup
--------------
If running locally, initialize your database with:
   flask db upgrade

Running the Application
-----------------------
Start the Flask development server:
   flask run
The app will be available at http://localhost:5000 by default.
