#!/usr/bin/env python
import unittest
import rt
import datetime
from datetime import timedelta
import requests
import os
import re
import smtplib
import ConfigParser
from email.mime.text import MIMEText

#################################################
#           Configuration                       #
#                                               #
#   The following globals can be set here,      #
#   or in the calling script.                   #
#   The load_config function is provided        #
#   so you can load them in from a file.        #
#                                               #
#   -----------------------------------------   #
#                                               #
#  rt_queue = ''                                #  
#  rt_host = ''                                 #
#  rt_user = ''                                 #  
#  rt_password = ''                             #
#  rt_from = ''                                 # 
#  rt_to = ''                                   #
#  rt_url = 'http://' + rt_host + '/REST/1.0/'  #
#  mail_host = ''                               #
#  # email address for unit tests               #
#  email = ''                                   #
#                                               #
#################################################

# Globals
rt_host = 'todo.freegeek.org'
rt_url='http://' + rt_host + '/REST/1.0/'

# unit tests

class MyTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config('rt.cfg')
        rt = self.config['rt']
        rt_user = rt['rt_user']
        rt_password = rt['rt_password']
        self.rt_queue = rt['rt_queue']
        mail = self.config['mail']
        self.email = mail['email']
        self.mailhost = mail['mail_host']
        self.rqt = RT(rt_url, rt_user, rt_password)
        self.rqt.login()

    def test_is_valid_ticket(self):
        result = self.rqt.is_valid_ticket(self.rt_queue, '34716')
        self.assertTrue(result)

    def test_is_active_ticket(self):
        result = self.rqt.is_active_ticket(self.rt_queue, '34716')
        self.assertTrue(result)
    
    def test_is_active_ticket_false(self):
        result = self.rqt.is_active_ticket(self.rt_queue, '21950')
        self.assertFalse(result)

    def test_asearch(self):
        result = self.rqt.asearch(self.rt_queue, """status='pending'""")
        if len(result)>0:
            has_results = True
        else:
            has_results = False
        self.assertTrue(has_results)

    def test_is_older(self):
        result = self.rqt.is_older_than(self.rt_queue, 'pending', 3)
        if len(result)>0:
            has_results = True
        else:
            has_results = False
        self.assertTrue(has_results)

    def test_format_results(self):
        older = self.rqt.is_older_than(self.rt_queue, 'pending', 3)
        result = format_results(older, 'id', 'Subject')
        if len(result)>0:
            has_results = True
        else:
            has_results = False
        self.assertTrue(has_results)

    def test_send_email(self):
        #email = raw_input('Enter an email address to send a message to: ')
        self.assertTrue(send_email(self.mailhost, self.email, self.email, 'Test', 'Test  to if email gets sent'))

    def test_email_results(self):
        older = self.rqt.is_older_than(self.rt_queue, 'pending', 3)
        result = format_results(older, 'id', 'Subject')
        #email = raw_input('Enter an email address to send a message to: ')
        email_results(self.mailhost, self.email, self.email, 'Unit Test', result)
        answer = raw_input('Did you receive an email with the subject: Unit test? [y/n] ')
        regex = re.compile('y', re.I)
        self.assertTrue(regex.match(answer))

    def test_load_config(self):
        pass


# Extended Class

class RT(rt.Rt):
    '''Extends rt.Rt Provides additional functions'''

    def asearch(self, Queue, *args):
        """ Search in queue using arbitary strings so that you can
        pass search strings directly. Strings will be joined using AND
        but OR etc can be passed directly. Note you will need to use triple
        quote strings in order to pass single quotes or escape them.

        This is sort of a bad idea BECAUSE it's passing arbitary strings,
        with no checking. You will need to ensure strings are valid before 
        passing them in. Don't pass in any directly from user input.
        Also I just cut and paste most of it from the orginal search 
        function.
        
        :keyword Queue: Queue where to search
        :keyword args: Other search strings to pass  

        :returns: List of matching tickets. Each ticket is the same dictionary
                  as in :py:meth:`~Rt.get_ticket`.
        :raises Exception: Unexpected format of returned message.
        """
        query = 'search/ticket?query=(Queue=\'%s\')' % (Queue,)
        for item in args:
            query += "AND%s" % item
        query += "&format=l"
        # Accessing a private method from the parent here
        # but whatever, I'm not going to write my own 
        # to do exactly the same thing. This is really something
        # that should go in the parent module.
        msgs = self._Rt__request(query)
        msgs = msgs.split('\n--\n')
        
        items = []
        try:
            if not hasattr(self, 'requestors_pattern'):
                self.requestors_pattern = re.compile('Requestors:')
            for i in range(len(msgs)):
                pairs = {}
                msg = msgs[i].split('\n')

                req_id = [id for id in range(len(msg)) if self.requestors_pattern.match(msg[id]) is not None]
                if len(req_id)==0:
                    raise Exception('Non standard ticket.')
                else:
                    req_id = req_id[0]
                for i in range(req_id):
                    colon = msg[i].find(': ')
                    if colon > 0:
                        pairs[msg[i][:colon].strip()] = msg[i][colon+1:].strip()
                requestors = [msg[req_id][12:]]
                req_id += 1
                while (req_id < len(msg)) and (msg[req_id][:12] == ' '*12):
                    requestors.append(msg[req_id][12:])
                    req_id += 1
                pairs['Requestors'] = requestors
                for i in range(req_id,len(msg)):
                    colon = msg[i].find(': ')
                    if colon > 0:
                        pairs[msg[i][:colon].strip()] = msg[i][colon+1:].strip()
                if len(pairs) > 0:
                    items.append(pairs)    
            return items
        except:
            return []



    def is_valid_ticket(self, queue, ticket):
        ''' Returns true if ticket number supplied exists in the 
        tech support queue'''
        try:
            search_results = self.search(queue,id=ticket)
            if len(search_results) > 0:
                return True
            else:
                return False
        except:
                return False

    def is_active_ticket(self, queue, ticket):
        '''Returns true if ticket number supplied exists in the 
        tech support queue and is not resolved'''
        # the rt module doesn't work with e.g. Status!='resolved'
        # so this is a double test, checking if resolved
        # if not check it is in the tech support queue
        try:
            search_results = self.search('TechSupport',status='resolved', id=ticket)
            if len(search_results) > 0:
                is_not_resolved = False
            else:
                search_results = self.search(queue, id=ticket)
                if len(search_results) > 0:
                    is_not_resolved = True
            return is_not_resolved
        except:
                return False

    def is_older_than(self, queue, statustype, days):
        '''Returns a list of tickets (i.e. id, Subject etc)
        with status [statustype], Last updated  [days] days ago '''
        today = datetime.date.today()
        timedelta = datetime.timedelta(days)
        cutoff = today - timedelta
        search_string = 'Status=\'' + statustype + '\'ANDLastUpdated<\'' + str(cutoff) + '\''
        search_results = self.asearch(queue, search_string) 
        return search_results

# Additional Functions

def format_results(results, *args):
    '''returns list of formatted lines for results
    for fields defined in *args'''
    output = []
    for line in results:
        outputline = []
        for field in args:
            if field == 'id':
                tid = line['id'].split('/')
                outputline.append(field +':' + tid[1] + ' ') 
            else:
                outputline.append(field +':' +  line[field] + ' ')
        output.append(''.join(outputline))
    return output

def send_email(mail_host, from_addr, mailto, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = mailto
    msg.add_header('X-Mailer', 'request-tracker.py')
    msg.add_header('X-Sent-By-Robot', 'The city\'s central computer told you? R2D2, you know better than to trust a strange computer!')
    s = smtplib.SMTP(mail_host)
    try:
        s.sendmail(from_addr, mailto, msg.as_string())
        sent = True
    except:
        sent = False
    s.quit()
    if sent == True:
        return True
    else:
        return False

def email_results(mailhost, from_addr, mailto, subject, body):
    if send_email(mailhost, from_addr, mailto, subject,  '\n'.join(body)):
        return True
    else:
        return False
    

def load_config(config_file = None):
    '''Reads in configuration file.'''
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    configlist = {}
    for section in config.sections():
        configlist[section] = {}
        for name, value in config.items(section):
            configlist[section].update({name: value})
    return configlist
# Main

if __name__ == "__main__":
    unittest.main()
    #config = load_config('rt.cfg')
    #rt = config['rt']
    #rt_user = rt['rt_user']
    #print rt_user
    #rqt = RT(rt_url, rt_user, rt_password)
    #rqt.login()
