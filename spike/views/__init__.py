__all__ = [ 'default', 'rules', 'settings', 'docs' ]

from flask.ext.login import current_user
from functools import wraps
from flask import current_app, redirect, url_for, flash, session
from time import localtime, strftime, time 
import simplejson as json
from os.path import isfile 
from markdown import markdown
charset ="utf-8"

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
      
def render_md(md_file):
  cfile = "%s" % md_file
  if not isfile(cfile):
    return("")

  fx = "".join(open(cfile, "r").readlines()).decode(charset)
  return(return_md(fx))
  
def return_md(md_input):
  ext = ['meta', 'extra', 'fenced_code', 'tables', 'codehilite', 'toc', 'attr_list']
  #md = markdown2.Markdown(extras=ext)
  #md = markdown2.Markdown(extras=ext)
  
  #print fx
  md_out = markdown(md_input, extensions=ext)
    
  return(md_out)


def now():
  return(int(time()))
  
def render_content(in_put):
  """
  
  
  
  """
  fp = "%s/%s.*" % (basedir, in_put)
  is_file = glob.glob(fp)
  if not is_file:
    print "cannot access %s" % fp
    resp = """
    <div align="center">
    <h1>404 - DONT PANIC</h1>
    the file you requested was not found
    <img src="/static/images/marvin4.jpg" width="70%">
    </div>
    """
    return(resp)
  else:
    
    in_file = is_file[0]
    ext = ['meta', 'extra', 'fenced_code', 'tables', 'codehilite', 'toc', 'attr_list']
    fxi = ""
    fx = "".join(open(in_file, "r").readlines()).decode(charset)
    
    #print fx
    fxout = markdown.markdown(fx, extensions=ext)
    return(fxout)
  
  return("marvin is VERY tired")

