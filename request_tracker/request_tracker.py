#!/usr/bin/env python
'''wrapper module for rt (python RT api module'''

import rt
import datetime
import os
import re
import smtplib
import ConfigParser
from email.mime.text import MIMEText


#################################################
#           Configuration                       #
#                                               #
#   The following are usefull as globals        #
#   set here,or in the calling script.          #
#   The load_config function is provided        #
#   so you can load them in from a file.        #
#   At the very least you should set RT_HOST    #
#                                               #
#   -----------------------------------------   #
#                                               #
#  RT_QUEUE = ''                                #  
#  RT_HOST = ''                                 #
#  RT_USER = ''                                 #  
#  RT_PASSWORD = ''                             #
#  RT_FROM = ''                                 # 
#  RT_TO = ''                                   #
#  RT_URL = 'http://' + RT_HOST + '/REST/1.0/'  #
#  MAIL_HOST = ''                               #
#  # email address for unit tests               #
#  EMAIL = ''                                   #
#                                               #
#################################################

# Globals
RT_HOST = 'todo.freegeek.org'
RT_URL = 'http://' + RT_HOST + '/REST/1.0/'

# Extended Class

class RT(rt.Rt):
    # pylint: disable=R0904
    '''Extends rt.Rt Provides additional functions'''
    

    def asearch(self, queue, *args):
        """ Search in queue using arbitary strings so that you can
        pass search strings directly. Strings will be joined using AND
        but OR etc can be passed directly. Note you will need to use triple
        quote strings in order to pass single quotes or escape them.

        This is sort of a bad idea BECAUSE it's passing arbitary strings,
        with no checking. You will need to ensure strings are valid before 
        passing them in. Don't pass in any directly from user input.
        Also I just cut and paste most of it from the orginal search 
        function.
        
        :keyword queue: Queue where to search
        :keyword args: Other search strings to pass  

        :returns: List of matching tickets. Each ticket is the same dictionary
                  as in :py:meth:`~Rt.get_ticket`.
        :raises Exception: Unexpected format of returned message.
        """
        query = 'search/ticket?query=(Queue=\'%s\')' % (queue,)
        for item in args:
            item = item.replace(" ","+")
            query += "+AND+(%s)" % item
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
                if not req_id:
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
                for i in range(req_id, len(msg)):
                    colon = msg[i].find(': ')
                    if colon:
                        pairs[msg[i][:colon].strip()] = msg[i][colon+1:].strip()
                if pairs:
                    items.append(pairs)    
            return items
        except:
            return []

    def is_valid_ticket(self, queue, ticket):
        ''' Returns true if ticket number supplied exists in the 
        tech support queue'''
        try:
            search_results = self.search(queue, id=ticket)
            if search_results:
                return True
            else:
                return False
        except:
            return False

    def is_active_ticket(self, queue, ticket):
        '''Returns true if ticket number supplied exists in the 
        queue and is not resolved'''
        # the rt module doesn't work with e.g. Status!='resolved'
        # so this is a double test, checking if resolved
        # if not check it is in the tech support queue
        try:
            search_results = self.search(queue, status='resolved', 
                    id=ticket)
            if search_results:
                is_not_resolved = False
            else:
                search_results = self.search(queue, id=ticket)
                if search_results:
                    is_not_resolved = True
                else:
                    is_not_resolved = False
                return is_not_resolved
        except:
            return False

    def last_updated_by_status(self, queue, statustype, days):
        '''Returns a list of tickets (i.e. id, Subject etc)
        with status [statustype], last updated  [days]  or more days ago '''
        today = datetime.date.today()
        tdelta = datetime.timedelta(days)
        cutoff = today - tdelta
        if statustype == 'active' or statustype == 'Active':
            status_string = '(Status=\'new\' OR Status=\'open\' OR Status=\'stalled\' OR Status=\'pending\' OR Status=\'contact\')' 
        else:
            status_string = 'Status=\'' + statustype + '\''
        search_string = status_string + 'ANDLastUpdated<\'' + str(cutoff) + '\''
        search_results = self.asearch(queue, search_string) 
        return search_results

    def updated_by_status_daterange(self, queue, statustype, start, end):
        '''return a list of ticket updated between start and end 
        where Status == statustype. Takes datetime object for start and end'''
        if statustype == 'active' or statustype == 'Active':
            status_string = '(Status=\'new\' OR Status=\'open\' OR Status=\'stalled\' OR Status=\'pending\' OR Status=\'contact\')' 
        else:
            status_string = 'Status=\'' + statustype + '\''
        search_string = status_string + 'ANDLastUpdated>\'' + str(start) + '\'ANDLastUpdated<\'' + str(end) + '\''
        search_results = self.asearch(queue, search_string) 
        return search_results



    def last_updated_by_field(self, queue, statustype, field, fieldtype, days):
        '''Returns a list of tickets (i.e. id, Subject etc)
        by field, last updated  [days] or more days ago. Status type can be active '''
        today = datetime.date.today()
        tdelta = datetime.timedelta(days)
        cutoff = today - tdelta
        if statustype == 'active' or statustype == 'Active':
            status_string = '(Status=\'new\' OR Status=\'open\' OR Status=\'stalled\' OR Status=\'pending\' OR Status=\'contact\')' 
        else:
            status_string = 'Status=\'' + statustype + '\''
        regex = re.compile('CF')
        if regex.match(field):
            field_string = '\'' + field + '\'' + '=\'' + fieldtype + '\''
        else:
            field_string = '\'' + field + '\''+ '=\'' + fieldtype + '\''
        updated_string = 'LastUpdated<\'' + str(cutoff) + '\''
        search_results = self.asearch(queue, status_string, field_string, updated_string) 
        return search_results

    def get_creation_date(self, ticket_id):
        '''returns creation date of ticket''' 
        ticket = self.get_ticket(ticket_id)
        date = ticket['Created']
        return date

    def get_created_before(self, queue ,statustype, days):
        '''returns list of tickets created before x days. 
        Status can be active or live(open,new) the most useful'''
        today = datetime.date.today()
        tdelta = datetime.timedelta(days)
        cutoff = today - tdelta
        if statustype == 'active' or statustype == 'Active':
            status_string = '(Status=\'new\' OR Status=\'open\' OR Status=\'stalled\' OR Status=\'pending\' OR Status=\'contact\')' 
        elif statustype == 'live' or statustype == 'Live':
            status_string = '(Status=\'new\' OR Status=\'open\')' 
        else:
            status_string = 'Status=\'' + statustype + '\''
        search_string = status_string + 'ANDCreated<\'' + str(cutoff) + '\''
        search_results = self.asearch(queue, search_string) 
        return search_results
    
    def get_status(self, ticket_id):
        '''returns status of ticket'''
        ticket = self.get_ticket(ticket_id)
        status = ticket['Status']
        return status

    def set_status(self, ticket_id, status):
        '''sets status of ticket'''
        if not status in ['new', 'open', 'stalled', 'pending', 'contact', 
                'resolved', 'rejected', 'deleted']:
            return False
        else:
            return self.edit_ticket(ticket_id, Status=status)
 
    def get_subject(self, ticket_id):
        '''returns subject of ticket'''
        ticket = self.get_ticket(ticket_id)
        subject = ticket['Subject']
        return subject

    def get_field(self, ticket_id, field):
        '''returns arbitrary field from  ticket'''
        ticket = self.get_ticket(ticket_id)
        result = ticket[field]
        return result


       
    def add_comment(self, ticket_id, msg):
        result = self.comment(ticket_id, text=msg)
        if result:
            if self.get_status(ticket_id) == 'new':
                self.set_status(ticket_id, 'open')
        return result

    def add_comment_nosc(self, ticket_id, msg):
        # don't check or change status
        result = self.comment(ticket_id, text=msg)
        return result

   

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

def get_id_list(results):
    '''returns list of id's in results'''
    output = []
    for line in results:
        tid = line['id'].split('/')
        output.append(tid[1]) 
    return output


def send_email(mail_host, from_addr, mailto, subject, body):
    '''sends an email'''
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = mailto
    msg.add_header('X-Mailer', 'request-tracker.py')
    msg.add_header('X-Sent-By-Robot', 
            'The city\'s central computer told you? R2D2, you know \
                    better than to trust a strange computer!')
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
    '''useful for sending email of result outputs -- 
    use for sending things that are lists'''
    if send_email(mailhost, from_addr, mailto, subject, 
            '\n'.join([str(i) for i in body])):
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


