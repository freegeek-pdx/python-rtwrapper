#!/usr/bin/env python
''' unit tests for wrapper module for rt (python RT api module)'''

import unittest
#import datetime
#import os
#import re
#import smtplib
#import ConfigParser
#from email.mime.text import MIMEText
#import rt

from request_tracker.request_tracker import RT, RT_URL, format_results, email_results, send_email, load_config, get_id_list

# Globals
RT_HOST = 'todo.freegeek.org'
RT_URL = 'http://' + RT_HOST + '/REST/1.0/'

# unit tests

class MyTests(unittest.TestCase):
    # pylint: disable=R0904
    '''Unit tests for extra functions'''
    def setUp(self):
        self.config = load_config('rt.cfg')
        rtconf = self.config['rt']
        rt_user = rtconf['rt_user']
        rt_password = rtconf['rt_password']
        self.rt_queue = rtconf['rt_queue']
        mail = self.config['mail']
        self.email = mail['email']
        self.mailhost = mail['mail_host']
        self.rqt = RT(RT_URL, rt_user, rt_password)
        self.rqt.login()

    #def tearDown(self):
    #    self.rqt.set_status('37146','new')

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
        self.assertTrue(result)

    def test_last_updated_by_status(self):
        result = self.rqt.last_updated_by_status(self.rt_queue, 'pending', 3)
        self.assertTrue(result)
    
    def test_last_updated_by_status_active(self):
        result = self.rqt.last_updated_by_status(self.rt_queue, 'active', 1)
        self.assertTrue(result)


    def test_last_updated_by_field(self):
        result = self.rqt.last_updated_by_field(self.rt_queue, 'new', 'Owner', 'nobody', 0)
        self.assertTrue(result)

    def test_last_updated_by_field_status_active(self):
        result = self.rqt.last_updated_by_field(self.rt_queue, 'active', 'Owner', 'nobody', 0)
        self.assertTrue(result)

 
    def test_last_updated_by_field_custom(self):
        result = self.rqt.last_updated_by_field(self.rt_queue, 'open', 'CF.{Ticket Source}', 'Box Brought In', 0)
        self.assertTrue(result)

    def test_get_creation_date(self):
        date = self.rqt.get_creation_date('34716')
        self.assertEquals(date, 'Thu Mar 28 15:30:26 2013')

    def test_get_created_before(self):
        result = self.rqt.get_created_before(self.rt_queue, 'live', 1)
        self.assertTrue(result)
 
    def test_format_results(self):
        older = self.rqt.last_updated_by_status(self.rt_queue, 'pending', 3)
        result = format_results(older, 'id', 'Subject')
        self.assertTrue(result)
    
    def test_get_id_list(self):
        older = self.rqt.last_updated_by_status(self.rt_queue, 'pending', 3)
        result = get_id_list(older)
        self.assertTrue(result)

    def test_send_email(self):
        #email = raw_input('Enter an email address to send a message to: ')
        self.assertTrue(send_email(self.mailhost, self.email, self.email, 
            'Test', 'Test  to see if email gets sent'))

    # this passes, commenting out to avoid having to wait for user prompt
    '''
    def test_email_results(self):
        older = self.rqt.last_updated_by_status(self.rt_queue, 'pending', 3)
        result = format_results(older, 'id', 'Subject')
        #email = raw_input('Enter an email address to send a message to: ')
        email_results(self.mailhost, self.email, self.email, 'Unit Test', 
                result)
        answer = raw_input(
                'Did you receive an email with the subject: Unit test? [y/n] ')
        regex = re.compile('y', re.I)
        self.assertTrue(regex.match(answer))
    '''

    def test_load_config(self):
        config = load_config('example.cfg')
        rtconf = config['rt']
        rt_user = rtconf['rt_user']
        self.assertEquals(rt_user, 'user')

    def test_get_status(self):
        status = self.rqt.get_status('34716')
        self.assertEquals(status, 'new')

    def test_set_status(self):
        rval = self.rqt.set_status(34716,'open')
        status = self.rqt.get_status('34716')
        self.rqt.set_status(34716,'new')
        self.assertEquals(status, 'open')

    def test_set_status_true(self):
        rval = self.rqt.set_status(34716,'open')
        self.rqt.set_status(34716,'new')
        self.assertTrue(rval)

    def test_add_comment(self):
    #    import time
        # note commenting on a ticket will set status to open
        # if new so we can use that for tests
        self.rqt.set_status(34716,'new')
        self.rqt.add_comment(34716, 'test comment')
        status = self.rqt.get_status('34716')
        self.rqt.set_status(34716,'new')
        self.assertEquals(status, 'open')

    def test_add_comment_true(self):
        rval = self.rqt.add_comment(34716, 'test comment')
        self.rqt.set_status(34716,'new')
        self.assertTrue(rval)

# Main

if __name__ == "__main__":
    unittest.main()

    # this won't run unless unittest.main() is commented out
#    config = load_config('rt.cfg')
#    rtconf = config['rt']
#    rt_user = rtconf['rt_user']
#    rt_password = rtconf['rt_password']
#    rt_queue = rtconf['rt_queue']
#    mail = config['mail']
#    email = mail['email']
#    mailhost = mail['mail_host']
#    rqt = RT(RT_URL, rt_user, rt_password)
#    print(rqt.login())
    #print(rqt.get_status(34716))
    #print(rqt.add_comment(34716,'test'))
    
    #print(rqt.last_updated_by_field(rt_queue, 'open', 'CF.{Ticket+Source}', 'Box+Brought+In', 0))
    #rqt.last_updated_by_field(rt_queue, 'new', 'Owner', 'nobody', 0)
    #print(rqt.search(Queue='TechSupport', Status='open', CF_='Box Brought In'))
    
    #print(rqt.last_updated_by_field(rt_queue, 'new', 'Owner', 'nobody', 0))
    #print(rqt.get_status(34716))
