===============
Request-Tracker
===============


request-tracker.py is a wrapper around rt.py a python module for the request tracker REST API. It provides friendlier functions that are more specific to Free Geek Tech Supports work flow. 

It goes with a variety of useful scripts that are bundled elsewhere.

Requirements:

python modules
==============
(these should be installed automatically, this is just for reference)
1. requests: apt-get install python-requests
2. python rt: <https://redmine.labs.nic.cz/projects/python-rt>
(this is bundled with this module)

Functionality
=============

This modules provides the following methods, in addition to the native rt module methods:

asearch( queue, *args)
                takes queue and *args where args is a list of strings to be 
                used in a search. Strings are joined with AND. The strings 
                should be valid search patterns for rt. 
                Returns a list of matching tickets

is_valid_ticket(queue, ticket)
                returns true if tricket exists in queue

last_updated_by_status(queue, statustype, days):
                Returns a list of tickets (i.e. id, Subject etc)
                with status [statustype], last updated  [days] days ago

last_updated_by_field(queue, statustype, field, fieldtype, days):
                Returns a list of tickets (i.e. id, Subject etc)
                by field, last updated  [days] days ago. Status type can be 
                set to active i.e. new, open etc

get_status(ticket_id)
                return ticket status

set_status(ticket_id, status)
                set ticket status

add_comment(ticket_id, msg)
                add msg to ticket

add_comment_nosc(ticket_id, msg)
                add msg, don't change status if ticket is new


Other functions:

format_results(results, *args)
                returns list of formatted lines for results
                for fields defined in *args

get_id_list(results):
                returns list of id's in results

send_email(mail_host, from_addr, mailto, subject, body)
                sends an email

email_results(mailhost, from_addr, mailto, subject, body)
                useful for sending email of result outputs -- 
                use for sending things that are lists

load_config(config_file)
                Reads in configuration file.

