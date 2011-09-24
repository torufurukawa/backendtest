from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

DATA = {}

class InitializeHandler(webapp.RequestHandler):
    def get(self):
        global DATA
        DATA['foo'] = 'foo'

application = webapp.WSGIApplication([('/_ah/start', InitializeHandler)],
                                     debug=True)
util.run_wsgi_app(application)

