__all__ = [ 'default', 'naxsi_rules' ]

from flask.ext.login import current_user
from functools import wraps
from flask import current_app, redirect, url_for, flash, session
from time import localtime, strftime, time 
import simplejson as json

def role_required(*roles):
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if hasattr(current_user, 'role'):
        role_statement = current_user.role
      else:
        role_statement = None
    
      if (not role_statement) or (not (role_statement in roles)):
          flash(u'You are not allowed to access this page', 'error')
          return redirect(url_for('default.login'))
      # debug-only:print session_store to console

      default.check_user_session_freshness()

      # debug_output
      print "\n--------------------------------------\nsession_info: \n\n"
      print session 
      print "\n\n--------------------------------------\n\n"
    
      
    
      return f(*args, **kwargs)
    return decorated_function
  return decorator
  
def date_id(value, format='%F'):
    try:
      return strftime(format, localtime(float(str(value))))
    except:
      print "[-] cannot datetime %s, defaulting to now()" % value 
      return strftime(format, localtime(time()))


def now():
  return(int(time()))
