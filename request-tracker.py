#!/usr/bin/env python
import unittest
#from  rt import RT as RequestTracker
import rt
import datetime
from datetime import timedelta
import requests
import os
import re

########################################
#           Configuration              #
########################################

rt_queue='TechSupport'
rt_host='todo.freegeek.org'
rt_user='tsrobot'
rt_password='EucNabs4'
rt_url='http://' + rt_host + '/REST/1.0/'
########## Configuration ends ##########

#class RT(RequestTracker):
#    '''Extends base class'''
#    def foo():
#        pass

class MyTests(unittest.TestCase):
    def setUp(self):
        self.rqt = RT(rt_url, rt_user, rt_password)
        self.rqt.login()

    def test_is_valid_ticket(self):
        result = self.rqt.is_valid_ticket('34716')
        self.assertTrue(result)

    def test_is_active_ticket(self):
        result = self.rqt.is_active_ticket('34716')
        self.assertTrue(result)
    
    def test_is_active_ticket_false(self):
        result = self.rqt.is_active_ticket('21950')
        self.assertFalse(result)

    def test_asearch(self):
        result = self.rqt.asearch('TechSupport',"""status='pending'""")
        if len(result)>0:
            has_results = True
        else:
            has_results = False
        self.assertTrue(has_results)

class RT(rt.Rt):
    '''Extends rt.Rt Provides additional functions'''

    def asearch(self, Queue='TechSupport', *args):
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



    def is_valid_ticket(self, ticket):
        ''' Returns true if ticket number supplied exists in the 
        tech support queue'''
        try:
            search_results = self.search('TechSupport',id=ticket)
            if len(search_results) > 0:
                return True
            else:
                return False
        except:
                return False

    def is_active_ticket(self, ticket):
        '''Returns true if ticket number supplied exists in the 
        tech support queue and is not resolved'''
        # the rt module doesn't work with e.g. Status!='resolved'
        # so this is a double test, checking if resolved
        # if not check it is in tech support
        try:
            search_results = self.search('TechSupport',status='resolved', id=ticket)
            if len(search_results) > 0:
                is_not_resolved = False
            else:
                search_results = self.search('TechSupport', id=ticket)
                if len(search_results) > 0:
                    is_not_resolved = True
            return is_not_resolved
        except:
                return False


    def is_older_than(self, statustype, days):
        today = datetime.date.today()
        timedelta = datetime.timedelta(days)
        cutoff = today - timedelta
        search_string = 'Status=\'' + statustype + '\'ANDLastUpdated<\'' + str(cutoff) + '\''
        search_results = self.asearch('TechSupport', search_string) 
        return search_results



if __name__ == "__main__":
    #unittest.main()

    rqt = RT(rt_url, rt_user, rt_password)
    rqt.login()
    older = rqt.is_older_than('pending', 3)
    for i in older:
        tid = i['id'].split('/')
        print( tid[1] +  ':' + i['Subject'])
