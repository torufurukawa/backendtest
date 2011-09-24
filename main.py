import logging
import time
import random
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import backends
from google.appengine.api.urlfetch import fetch

KEY_NAME = 'spam'
DATA = 'spam' * 10
MEMDB_BACKEND_ID = 'memdb'
MEMDB_HOSTNAME = backends.get_hostname(MEMDB_BACKEND_ID)

def get_key_name():
    return ''.join([random.choice('abcdefghijklmnopqrstuvwzyz') for x in range(10)])

class Data(db.Model):
    data = db.StringProperty()

def stop_watch(op_name):
    def outer(func):
        def wrapper(self):
            start_at = time.time()
            func(self)
            end_at = time.time()
            log = '[%s] %s' % (op_name, end_at-start_at)
            logging.info(log)
            self.response.out.write(log)
        return wrapper
    return outer

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')
        self.response.out.write('backend: %s' % backends.get_hostname('memdb'))

class DatastoreWriteHandler(webapp.RequestHandler):
    @stop_watch('datastore:write')
    def get(self):
        Data(key_name=get_key_name(), data=DATA).put()

class DatastoreReadHandler(webapp.RequestHandler):
    @stop_watch('datastore:read')
    def get(self):
        obj = Data.get_by_key_name(get_key_name())
        if obj:
            data = obj.data
        else:
            data = ""

class MemcacheWriteHandler(webapp.RequestHandler):
    @stop_watch('memcache:write')
    def get(self):
        memcache.set(get_key_name(), DATA)

class MemcacheReadHandler(webapp.RequestHandler):
    @stop_watch('memcache:read')
    def get(self):
        data = memcache.get(get_key_name())

class BackendWriteHandler(webapp.RequestHandler):
    @stop_watch('backend:write')
    def get(self):
        hostname = MEMDB_HOSTNAME
        response = fetch('http://%s/memdb/set/%s/%s' % (hostname, get_key_name(), DATA))

class BackendReadHandler(webapp.RequestHandler):
    @stop_watch('backend:read')
    def get(self):
        hostname = MEMDB_HOSTNAME
        response = fetch('http://%s/memdb/get/%s' % (hostname, get_key_name()))
        data = response.content

class MemdbGetHandler(webapp.RequestHandler):
    def get(self, key):
        import memdb
        value = memdb.DATA.get(key)
        self.response.out.write(value)

class MemdbSetHandler(webapp.RequestHandler):
    def get(self, key, value):
        import memdb
        memdb.DATA[key] = value
        self.response.out.write(value)

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/datastore/write', DatastoreWriteHandler),
                                          ('/datastore/read', DatastoreReadHandler),
                                          ('/memcache/write', MemcacheWriteHandler),
                                          ('/memcache/read', MemcacheReadHandler),
                                          ('/backend/write', BackendWriteHandler),
                                          ('/backend/read', BackendReadHandler),
                                          ('/memdb/set/(.+)?/(.+)', MemdbSetHandler),
                                          ('/memdb/get/(.+)', MemdbGetHandler),
                                         ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
