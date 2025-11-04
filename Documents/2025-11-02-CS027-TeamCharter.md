## Team Members & Roles

Policy Owner: Jonathan Hotchkiss  
Review Date:11/14/2025

### Alexey Leeper

* Testing Coordinator  
  * Software Development/Code Reviewer

### Faris Nasse

* Hardware Coordinator  
  * Software Development/Code Reviewer

### Graham Glazner

* Documentation Coordinator  
  * Software Development/Code Reviewer

### Jonathan Hotchkiss

* Team Lead/Communicator  
  * Software Development/Code Reviewer

## Decision-Making Model

Policy Owner: Alexey Leeper  
Review Date:11/14/2025

* We will use a majority vote to make the major decisions in our project. When our decisions are split 50/50, we will ask our mentor for his vote to make the final decision.  
* Decisions Requiring extra discussion:  
  * Architecture changes  
  * Deadline adjustments  
  * Altering project scope

## Meeting Cadence & Tools

Policy Owner: Jonathan Hotchkiss  
Review Date:11/14/2025

* Weekly Team Meeting: 60-minute meeting on Mondays with Mentor  
* Each meeting will focus on upcoming class deadlines and providing progress updates  
* Tools:  
  * Version Control: GitHub  
  * Task Board: Trello  
  * Communication:  
    * Discord among group members \+ TA  
    * Email between the group and project mentor  
  * Documentation: Google Docs

## Risk Management & Escalation Path

Policy Owner: Faris Nasse  
Review Date:11/14/2025  
	Known Risks:

* Schedule/Availability Issues  
* Workload Distribution

	Escalation Steps:

1. Discuss with Team Members  
2. Clarify expectations for all individuals  
3. Introduce the TA to determine the best solutions  
4. Last Resort: Notify instructors

## Conflict Resolution & Accountability

Policy Owner: Graham Glazner  
Review Date:11/14/2025  
Potential Triggers:

* Missed Deadlines  
* Inactive Member  
* Scope Creep  
* Accountability Issues

	Steps for Resolution:

1. Discuss what went wrong/ accountability (Review attendance and contributions)  
2. Evaluate potential barriers  
3. Come up with new plans/deadlines  
4. Document any changes  
5. Evaluate progress after 1 week

## Definition of Done (DoD) & Quality Gates

Policy Owner: Graham Glazner  
Review Date:11/14/2025

### 

### DoD

A task or feature is **done** when…

* Unit tests pass in CI  
* Integration tests pass in CI  
* No import errors  
* Project starts successfully  
* Documentation is updated

### Quality Gates

Below is an outline of the stages and potential tools for establishing clean commits. 

| Stage | Tool / Command | Purpose / Gate Criteria |
| ----- | ----- | ----- |
| **Build / Setup** | `pip install -r requirements.txt` and `python -m compileall .` | Ensures dependencies install and code is syntactically valid. |
| **Server Startup Check** | `python -m app & curl -f http://localhost:8000/health` | Confirms the web server starts successfully and health endpoint responds. |
| **Linting & Formatting** | `flake8`, `black --check .` | Code follows style and formatting rules; no linting errors. |
| **Static & Security Analysis** | `bandit -r app/` | No high-severity security issues detected. |
| **Testing** | `pytest --cov=app tests/` | All tests pass; ≥80% coverage. |
| **Review Gate** | GitHub branch protection | Requires ≥1 approved peer review before merge. |

## Accessibility & Inclusion Practices

Policy Owner: Alexey Leeper  
Review Date:11/14/2025  
	Meetings will:

* Be in-person with an optional Discord voice chat for online members  
* To accommodate for potential time-zone discrepancies, such as travel, all members will accept responsibility for communicating scheduling issues at least one meeting in advance of the meeting they expect to miss.

	Scheduling:

* Communication within the group to determine the best availability for all members

	Accomodation:

* If members unexpectedly miss meetings, group members will provide, upon request, important meeting notes via the group discord server.

	Inclusion:

* We will allow everyone to weigh in on important topics and we will have a final check in before moving on, in order to get a whole group consensus.  
* We will also check the discord server for comments from any members that are listening online, before moving on from discussion topics.

## Links & Artifacts

* *Include evidence links to:*  
  * CI configuration (e.g., workflow file) and a public link to a successful run log (or a screenshot if the repo is private)  
    * Development will start after technical design is done (11/23).  
  * Linter/formatter config committed to the repo  
    * Graham will take on the responsibility of putting together linting configuration.  
    * Linting configuration will be done by the end of week 1 Winter Term.  
  * Where tests live and how they’re run  
    * [FarisNasse/CS461-wormhole-queue-system: OSU Physics tutoring queue system](https://github.com/FarisNasse/CS461-wormhole-queue-system)  
    * Pytest components will be grouped together with corresponding software components, and will be implemented in alignment with the planned development work.