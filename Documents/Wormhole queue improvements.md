Functional improvements to the Wormhole queue system

These are improvements we would like to see in the Wormhole queue system functionality.  This is above and beyond the larger objectives of converting to Python, making the code more human readable, and providing clear documentation so that a new administrator familiar with Python could take over supervison.

Administrator functions

* Allow an administrator to reset the ticket counter  
  * When Admin clears the queue, reset ticket count to 1…  
* In the new user set-up:  
  * Ask only for the ONID, and then set the email to ONID“@oregonstate.edu”  
  * Default the password to *Wormhole*  
  * Have the system issue a message stating whether or not the set-up was successful  
    * If successful, return the administrator to the TA/LA list  
    * If unsuccessful, return the administrator to the new user set-up  
* Rename the “TA/LA List”to “WA List”  
* Sort the TA/LA list by last name

Assistant functions

* Repair the function to change a password  
* Add a Refresh button to the Hardware Status page  
* Only issue one audible ping when a new request comes in  
* Send an automated message to the WA if a request is left open for more than one hour

Data

* Identify WAs in the queue by name rather than ONID  
* Don’t anonymize which WA handles each ticket at the end of the day

Note from 10/31  
Append instead of create new archive file  
