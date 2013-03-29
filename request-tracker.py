#!/usr/bin/env python
import unittest
#from  rt import RT as RequestTracker
import rt
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
    def test_is_valid_ticket(self):
        result = is_valid_ticket('34716')
        self.assertTrue(result)

    def test_is_active_ticket(self):
        result = is_active_ticket('34716')
        self.assertTrue(result)
    
    def test_is_active_ticketi_false(self):
        result = is_active_ticket('21950')
        self.assertFalse(result)

### FUNCTIONS ###

def is_valid_ticket(ticket):
    ''' Returns true if ticket number supplied exists in the 
    tech support queue'''
    rqt = rt.Rt(rt_url, rt_user, rt_password)
    rqt.login()
    try:
        search_results = rqt.search('TechSupport',id=ticket)
        if len(search_results) > 0:
            return True
        else:
            return False
    except:
            return False

def is_active_ticket(ticket):
    '''Returns true if ticket number supplied exists in the 
    tech support queue and is not resolved'''
    rqt = rt.Rt(rt_url, rt_user, rt_password)
    rqt.login()
    # the rt module doesn't work with e.g. Status!='resolved'
    # so this is a double test, checking if resolved
    # if not check it is in tech support
    try:
        search_results = rqt.search('TechSupport',status='resolved', id=ticket)
        if len(search_results) > 0:
            is_not_resolved = False
        else:
            search_results = rqt.search('TechSupport', id=ticket)
            if len(search_results) > 0:
                is_not_resolved = True
        return is_not_resolved
    except:
            return False


def is_older_than(status, days):
    # Status = 'contact' AND LastUpdated < '2013-03-27' AND Queue = 'TechSupport'
    rqt = rt.Rt(rt_url, rt_user, rt_password)
    rqt.login()

if __name__ == "__main__":
    unittest.main()

