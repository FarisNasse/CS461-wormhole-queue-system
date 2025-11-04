# Problem Statement & Scope:

The current queueing system used at the Wormhole relies on an outdated programming language, does not include sufficient documentation for debugging and improvement, and lacks fully functioning elements. Our system aims to use a common, easily understandable language (Python) supported with adequate documentation that allows any new administrator to understand the system. In addition, it will include more functionality and provide different methods for tracking data.

## Users & Context:

* Primary Users: Undergraduate students requesting tutoring help for physics courses  
* Secondary Users: Tutors (Wormhole Assistants), Administrators/Wormhole Supervisor  
* Context of Use: A web-based platform accessible through computers and mobile devices

## System Boundaries:

This project focuses only on updating and improving the current Wormhole queue software used in the Physics Help Center. It includes the online student queue, tutor tools, and admin features. It will not go beyond the Wormhole system or change how tutoring works in person.

* In Scope:  
  * The system will include the same core functionalities that the Laravel system currently has  
  * Documentation will be made for all areas of the system to improve understanding  
  * New admin, WA, and data tracking features will be added to improve usability and oversight  
* Out of Scope:  
  * The system frontend will remain mostly the same, with only minor changes for new features  
  * Performance metrics are not a huge priority, as functionality is the main goal

## Non-Goal:

* This project will not redesign or replace the physical Wormhole lab operations or tutoring procedures; it only updates the software queue system.

## Success Criteria:

* **Feature Parity:** The new Python-based system maintains 100% of the existing core functional capabilities of the current Laravel Wormhole system.  
* **Coverage of System Documentation:** Documentation must cover 100% of administrator workflows and at least 90% of core system functionalities, including user management, ticket handling, data access, and troubleshooting procedures.  
* **Success Criterion:** A new administrator with no prior wormhole experience can set up and run the system within 2 hours using the provided documentation.

### Functional requirements:

**Requirement 001: Maintain existing functionality**   
The Python system shall maintain all functional workflows currently on the Laravel system.  
This ensures that the new system will still have similar functionality without losing any features that are necessary for its users.

**Requirement 002: Clear Documentation**  
Documentation needs to be accessible and usable for people in physics background with some Python experience.  
This frames our audience for the documentation and ensures that the documentation remains accessible for future administrators.

**Requirement 003: Add Wormhole Account**  
The system will allow the system administrator to create new accounts for wormhole assistants or new admins using their ONID and a password (classified)  
The system will automatically set the email to [ONID@oregonstate.edu](mailto:ONID@oregonstate.edu)  
The Default password will be set to “Wormhole”

- Register multiple users   
  - Rationale: Makes adding new WAs faster and easier for admins.

**Requirement 004: Ticket Management**  
Tickets can be managed by Admin and Wormhole Assistants  
The system will allow admin and wormhole assistants to perform CRUD operations on the tickets in the queueing system. Anyone can read and create a ticket.  
Providing CRUD operations for admins and wormhole assistants allows them to keep track of the live queue and edit/remove duplicates or “completed” tickets  
\-          custom values  
o   reason for removal (duplicate, complete)  
\-          tickets are ordered by submission time

**Requirement 005: Reset the ticket counter**  
(Must) The system shall allow admins to reset the ticket counter in the admin page and record who did it and when.  
Rationale: Keeps ticket numbers organized and shows who made changes.

Under admin utilities on the website:  
Change TA/LA List to WA List

**Requirement 006: Add Ticket with Button**  
All four of the buttons on the button-boxes submit a ticket to the queue.

**Requirement 007: Account Creation Messages**   
(Should) After creating a WA account, the system shall show a clear success or error message. If successful, it goes to the WA List. If not, it returns the admin to the new user setup page with an explanation.  
On submit message indicating success  
If successful, return the administrator to the TA/LA list  
Rationale: Helps admins know what happened and avoids confusion.  
This allows easy user creation that the system admin can monitor and keep track of.

### Non-Functional requirements

**Requirement 008: Intuitive Design** (Non-functional)  
The code should follow modular and documented design patterns.  
This improves the readability and maintainability of the Python code for future updates  
The new code needs to be easy to read and follow for users.  
This ensures that future users will be able to easily identify maintenance issues when debugging the application.  
The new code needs to be heavily commented and organized.  
This maintains the ease of maintainability and keeps the code readable for administrators.

**Requirement 010: Secure Transport Protocol** (Non-functional)  
All communication should use secure transport protocols to ensure no sensitive information can be accessed by unauthorized users  
This maintains security and ensures that confidential information in safely hidden

**Requirement 011: Response Times** (Non-functional)  
Under normal circumstances, the system should be able to respond to user requests within 2 seconds.  
Keeping a quick response time will improve the performance of the system.

**Requirement 012: Accessible Documentation** (Non-functional)  
Documentation needs to be accessible and usable for people in physics background with some Python experience.  
This frames our audience for the documentation and ensures that the documentation remains accessible for future administrators.

### Additional Requirements

**Requirement 013: Change password**  
(Must) The system shall allow WAs to change their password and log in with the new one right away.  
Rationale: Gives WAs control of their account and keeps it secure.  
Refresh hardware status page

**Requirement 014: Online help requests can be submitted**  
custom values  
o   input name  
o   select class (dropdown)  
o   select method/location of tutoring session (dropdown)  
o   ALL input values are sanitized

**Requirement 015: Live Queue**  
Live queue is observable on the website at [wormhole.physics.oregonstate.edu/livequeue](http://wormhole.physics.oregonstate.edu/livequeue)  
(Should) The system shall show students their place in the line and whether a WA is currently looking at their ticket.  
Rationale: Helps students feel informed and less stressed while waiting.

**Requirement 016: Notification sound**  
Notification sounds **once** to the wormhole computer when a new ticket is submitted.

**Requirement 017: Unresolved tickets reminder**  
Automated message sent to WA for unresolved help request(1 hour)  
(Should) The system shall send a reminder to a WA if a ticket assigned to them has been open for more than 60 minutes, asking them to follow up or release it.  
Rationale: Stops tickets from being forgotten and helps students get help sooner.

**Requirement 018: Identify WAs in the queue by name rather than ONID** (Non-functional)  
(Must) The system shall show the WA’s full name (not just their ONID) on all current and past tickets.  
Rationale: Helps students know who is helping them

**Requirement 019: AWS server deployment**  
The system should be deployed on AWS after all testing has been completed  
This allows the server to be accessed the same way as before and keeps the connection simple for the admins and assistants.

**Requirement 020: Anonymize Data**  
Don’t anonymize which WA handles each ticket automatically. Remove this function\!  
The system should keep a log of all tickets that have been created, with an option to make the data anonymous  
This maintains safety requirements in case the system is compromised, and outside users gain access to the data

**Requirement 021: Login/Logout**  
The system should allow administrators and assistants to log in and log out of their accounts that have special abilities  
The requirement keeps the system secure from students requesting help and does not allow them to overwrite any of the data. 

**Requirement 022: Data summary generation**  
The system should create summaries of data for the administrators to view and analyze  
This allows the admin users to review trends and change the application based on what is most beneficial to users

**Requirement 023: Ubuntu Compatibility**  
All new software must be compatible with Ubuntu 20+.  
This ensures that the software will remain maintainable for a much longer period of time on the deployment platform, AWS EC2.

**Requirement 024: Database Functionality**  
(Must) The system shall correctly create, assign, and close tickets so that no tickets are lost or duplicated.  
Rationale: Keeps the queue fair and trustworthy for everyone.

**Requirement 025: Log File generation**  
(Must) The system shall save a full record of each ticket, including when it was made, which WA handled it, what actions were taken, and how it ended.  
Rationale: Makes it easy to look back at past tickets and understand what happened.

**Requirement 026: WA personal History**  
(Should) The system shall give WAs a personal history page showing how many tickets they’ve handled, how long they usually take, and which courses they helped with.  
Rationale: Helps WAs learn from their work and improve over time.

## Prioritization Method & Results

We chose MoSCoW as our prioritization method because it is straightforward and easy to define. This method will allow us to focus on first things first, while not being hyperspecific or strict.

| Requirement ID | Priority | Dependencies | Acceptance Criteria |
| :---- | :---- | :---- | :---- |
| 001-Maintain Existing Functionality | Must | Access to current Wormhole system and full list of existing features | All current functionality that is present in the Laravel system will remain in the new Python system |
| 002-Clear Documentation | Must | Core features implemented and documented (**R001**) | A new admin can set up and run the system within 2 hours using only the documentation |
| 003-Add Wormhole Account | Must | Automated email system, working database for storing users (**R001**) | Creating an account automatically sends an email to the new user with a default password.  |
| 004-Ticket Management | Must | Backend infrastructure for ticket system, user interface for ticket interaction (**R001**) | User (Admin or WA) can create, update, assign, and delete tickets from the user interface. |
| 005-Reset Ticket Counter | Must | Ticket Counter functionality, Admin account backend (**R001**) | The ticket counter resets and assistant/administrator who reset the count is logged |
| 006-Add Ticket with Button | Must | Button Box communication channels, Backend structure for queue system (**R001**) | Each button on the boxes will add a ticket to the end of the queue. The tickets will correctly identify the class for the button pressed |
| 007-Account Creation Messages | Should | User account creation process \+ WA List page must exist (**R003**) | Success returns the user to TA/LA list, failure returns the user to the create account page. |
| 008-Intuitive Design | Must | Full code solution (**R001**) | The code needs to be organized, simple to follow, and heavily commented. |
| 009-Response Times | Must | Functional backend and connected user interface. (**R001**) | The user interface should provide response times that are less than or equal to two seconds. |
| 010-Accessible Documentation | Must | Finalized backend implementation Documentation Written (**R002**) | The target audience should have no nagging issues when trying to navigate documentation. |

**Prioritization Rational:**

**Must Have:** Items labeled as Must were selected because they are required to meet the project’s core Success Criteria and ensure a functioning release. These requirements preserve all existing system functionality, support the main workflows for students, WAs, and admins, and ensure the new Python system can operate on day one without disruptions. Without these items, the queue system would fail to run or would not meet stakeholder expectations.

**Should Have:** Items labeled as Should were prioritized as secondary enhancements that improve efficiency, clarity, or usability but are not required for the system’s initial launch. These items were chosen based on stakeholder feedback and common usability issues within the current system. They provide meaningful improvements but can be delivered after the core system is stable.

**Tie-Break:**

When two requirements had similar MoSCoW priority, we broke ties using the following criteria:

1. Stakeholder Value  
   1. Higher priority was given to items that could provide value to the primary stakeholders, or prevent frequent friction.  
      Ex: Enhancing the admin account creation flow ranked above the WA History page because it directly affects onboarding and reduces recurring admin workload.  
2. Dependencies  
   1. If a requirement needed to exist before others could function, it was ranked higher  
      Ex: “Maintain Existing Functionality” ranked above UI/UX improvements because failure to preserve core workflows would prevent the system from functioning at all.  
3. Risk Reduction  
   1. If one requirement reduces the chance of a system failure or confusion, it was given more of a priority  
      Ex: Ticket CRUD had to be implemented before the 60-minute WA reminder, because the reminder feature relies on ticket assignment and tracking.

## Ethics, Risks, and Constraints

Identify the biggest project risks and add brief notes on how to handle or just accept them

* **FERPA/Privacy:** The system must protect student information by limiting personal data (such as names and ticket details) to authorized WAs and admins only. Data exports should avoid exposing unnecessary student information.  
  **Traceability:** This affects REQ-004 Ticket Management, Log File generation, and Anonymize Data because these requirements control what data is stored, displayed, and exported.  
* **Accessibility:** The system must be usable for all students, including those with disabilities, by following basic accessibility practices such as readable text, clear labels, and easy navigation.  
  **Traceability:** This connects to REQ-008 Intuitive Design, REQ-010 Accessible Documentation, and Live Queue visibility for students since these features directly impact usability and clarity.  
* **Security:** WA and admin accounts must be protected through secure login and password processes to prevent unauthorized access to student tickets or internal data.  
  **Traceability:** This relates to REQ-003 Add Wormhole Account, Change Password, Login/Logout, and Secure Transport Protocol because these requirements ensure proper account creation and protection.  
* **Top Risks & Mitigations:** A key risk is unclear WA and admin workflows, which may cause user confusion; this can be reduced by early usability testing with real WAs. Another risk is inaccurate ticket records during development, which can be prevented with early testing of ticket flows and regular data backups.

**Constraints:**

**Python Implementation:** We have been asked specifically to use python as the primary programming language for the implementation of this project. This will make the wormhole software should be readable for a novice programmer or anyone familiar with python programming.

**Traceability:** This constraint impacts REQ-002 Clear Documentation and REQ-010 Accessible Documentation, since documentation must match the skill level of future Python maintainers and ensure long-term maintainability.

# Merging & Change Record

* Alexey Created Document and added outline sections:  
  * Problem Statement & Scope  
  * Users and Context  
  * System Boundaries  
  * Success Criteria  
* Graham added sections to outline  
  * Prioritization Method & Results  
  * Ethics Risks, and Constraints  
  * Merging & Change Record  
* Jonathan wrote problem statement and described users and context  
* Faris added non-goal  
* Everyone added individual top 10 requirements  
* Jonathan established system boundaries  
* Faris wrote Ethics, Risks, and Constraints  
* Identical duplicate requirements combined  
  * When combining individual requirement lists, if two members proposed similar or overlapping requirements, we merged them by keeping the clearer and more complete version to avoid redundancy and ensure consistency.  
* Add Wormhole account(003) and Account Creation Messages(007) separated  
* Collaborated to organize prioritization method and results table  
* Faris wrote Prioritization Rational section

# Individual Contributions:

### Graham Glazner

**Admin**

1. Reset the ticket counter  
2. Register new users(admins and WA accounts)  
   \-          Autofill email ONID@oregonstate.edu  
   \-          Default password Wormhole  
   \-          On submit message indicating success

   o   If successful, return the administrator to the TA/LA list  
   o   If unsuccessful, return the administrator to the new user set-up  
3. Register multiple users

Under admin utilities on the website:

4. Change TA/LA List to WA List

**WA**

5. Tickets can be removed from the queue  
   \-          custom values

   o   reason for removal (duplicate, complete)

   \-          tickets are ordered by submission time  
6. Change password on account  
7. Refresh hardware status page

**Student**

8.  All four of the buttons on the button-boxes submit a ticket to the queue.  
9. Online help requests can be submitted  
- custom values

  o   input name

  o   select class (dropdown)

  o   select method/location of tutoring session (dropdown)

  o   ALL input values are sanitized

10. Live Queue is observable on the website at [wormhole.physics.oregonstate.edu/livequeue](https://wormhole.physics.oregonstate.edu/livequeue)

### Jonathan Hotchkiss

**Functional Requirements:**

1.  The Python system shall maintain all functional workflows currently on the Laravel system.  
   1. This ensures that the new system will still have similar functionality and provide the necessary features  
2. The system will allow admin and wormhole assistants to perform CRUD operations on the tickets in the queueing system. Anyone can read and create a ticket.  
   1. Providing CRUD operations for admins and wormhole assistants allows them to keep track of the live queue and edit/remove duplicates or “completed” tickets  
3. The system should be deployed on AWS after all testing has been completed  
   1. This allows the server to be accessed the same way as before and keeps the connection simple for the admins and assistants.  
4. The system will allow the system administrator to create new accounts for wormhole assistants using their ONID and a password (classified)  
   1. This allows easy user creation that the system admin can monitor and keep track of.  
5. The system should keep a log of all tickets that have been created, with an option to make the data anonymous  
   1. This maintains safety requirements in case the system is compromised, and outside users gain access to the data  
6. The system should allow administrators and assistants to log in and log out of their accounts that have special abilities  
   1. The requirement keeps the system secure from students requesting help and does not allow them to overwrite any of the data.   
7. The system should create summaries of data for the administrators to view and analyze  
   1. This allows the admin users to review trends and change the application based on what is most beneficial to users

**Non-Functional Requirements:**

1. The code should follow modular and documented design patterns.  
   1. This improves the readability and maintainability of the Python code for future updates  
2. All communication should use secure transport protocols to ensure no sensitive information can be accessed by unauthorized users  
   1. This maintains security and ensures that confidential information in safely hidden  
3. Under normal circumstances, the system should be able to respond to user requests within 2 seconds.  
   1. Keeping a quick response time will improve the performance of the system.

### Alexey Leeper

functional  
**System**

1. All new software must be compatible with Ubuntu 20+.  
   1. This ensures that the software will remain maintainable for a much longer period of time on the deployment platform, AWS EC2.  
2. The python code will maintain all existing program functionality.  
   1. This ensures that the wormhole maintains its necessary functionality without losing any parts that are necessary for its users.  
3. Notification sounds **once** to wormhole computer.  
   1. This corrects an existing issue with the wormhole where one request can cause the sound effect in the wormhole to trigger four times.  
4. Automated message sent to WA for unresolved help request(1 hour)  
   1. This ensures that any outstanding requests are addressed instead of remaining open.  
5. Identify WAs in the queue by name rather than ONID.  
   1. This improves usability for administrators and wormhole assistants when using the application, as well as students when interacting with TAs in the wormhole.  
6. Don’t anonymize which WA handles each ticket automatically at the end of the day.  
   1. This addresses a current issue with the usability of the program, allowing TAs and the administrator to get a more accurate log of ticket history.

**Admin**

1. Admin needs to perform CRUD operations on tickets.  
   1. The administrator needs to be able to delete, create, and assign tickets in real time to manage the ticket system.

**Admin**

1. Documentation needs to be accessible and usable for people in physics background with some Python experience.  
   1. This frames our audience for the documentation and ensures that the documentation remains accessible for future administrators.  
2. The new code needs to be easy to read and follow for users.  
   1. This ensures that future users will be able to easily identify maintenance issues when debugging the application.  
3. The new code needs to be heavily commented and organized.  
   1. This maintains the ease of maintainability and keeps the code readable for administrators.

### Faris Nasse

**System-Wide Functional Requirements**

1. (Must) The system shall correctly create, assign, and close tickets so that no tickets are lost or duplicated.  
   Rationale: Keeps the queue fair and trustworthy for everyone.  
2. (Must) The system shall save a full record of each ticket, including when it was made, which WA handled it, what actions were taken, and how it ended.  
   Rationale: Makes it easy to look back at past tickets and understand what happened.

**Student-Facing Functional Requirements**

3. (Must) The system shall show the WA’s full name (not just their ONID) on all current and past tickets.  
   Rationale: Helps students know who is helping them  
4. (Should) The system shall show students their place in the line and whether a WA is currently looking at their ticket.  
   Rationale: Helps students feel informed and less stressed while waiting.

**WA (Tutor) Functional Requirements**

5. (Must) The system shall allow WAs to change their password and log in with the new one right away.  
   Rationale: Gives WAs control of their account and keeps it secure.  
6. (Should) The system shall send a reminder to a WA if a ticket assigned to them has been open for more than 60 minutes, asking them to follow up or release it.  
   Rationale: Stops tickets from being forgotten and helps students get help sooner.  
7. (Should) The system shall give WAs a personal history page showing how many tickets they’ve handled, how long they usually take, and which courses they helped with.  
   Rationale: Helps WAs learn from their work and improve over time.

**Admin Functional Requirements**

8. (Must) The system shall allow admins to reset the ticket counter in the admin page and record who did it and when.  
   Rationale: Keeps ticket numbers organized and shows who made changes.  
9. (Must) The system shall allow admins to create a WA account using only the ONID, and the system will automatically set the email to ONID@oregonstate.edu  
   Rationale: Makes adding new WAs faster and easier for admins.  
10. (Should) After creating a WA account, the system shall show a clear success or error message. If successful, it goes to the WA List. If not, it returns to the setup page with an explanation.  
    Rationale: Helps admins know what happened and avoids confusion.