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

def csp_id(vtime):
  return('csp-reports/%s' % date_id(vtime))

def now():
  return(int(time()))

def convert_redis(in_put):
  display_data = []
  for entry in in_put:
    data = json.loads(entry.replace("""\'""", """'"""))
    try:
      my_report = data["csp-report"]
    except:
      continue
    r_domain = my_report["domain"]
    r_reporter = my_report["reporter"]
    r_document_uri = my_report["document-uri"]
    r_referrer = my_report["referrer"]
    r_blocked_uri = my_report["blocked-uri"]
    r_violated_directive = my_report["violated-directive"]
    r_line_nr = my_report["line-number"]
    r_status_code = my_report["status-code"]
    r_uuid = my_report["uuid"]
    r_mtime = my_report["datetime"]
    
    display_data.append((r_reporter, r_document_uri, r_referrer, r_blocked_uri, 
                          r_violated_directive, r_line_nr, r_status_code, r_mtime, r_uuid, r_domain ))

  # report-fields:
  #~ 0 - reporter
  #~ 1 - document_uri
  #~ 2 - referrer
  #~ 3 - blocked_uri
  #~ 4 - violated_directive
  #~ 5 - line_nr
  #~ 6 - status_code
  #~ 7 - mtime
  #~ 8 - uuid 
  #~ 9 - domain 

  return(display_data)

def get_dash_areas():
  return(["ip", "domain", "uri", "ref", "blocked", "violated", "status"])

def get_dashboards():
  redis = current_app.redis

  dash_areas = get_dash_areas()

  dash_times = {
    '24hrs': 1,
    '7days': 7,
    '1month': 30,
  }
  
  
  def dashboard_data():
    cash_dict = {} 
    for t in dash_times:
      r_hash = "dash/%s" % t 
      for ax in dash_areas:
        print " > retrieving dash %s / %s " % (t, ax)
        s_k = "%s/%s" % (r_hash, ax)
        ax_len = redis.llen(s_k)
        ax_res = redis.lrange(0, -1)
        cash_dict[s_k] = ax_res
    return(cash_dict)
      #~ i_h = "%s/ip" % r_hash
      #~ d_h = "%s/domain" % r_hash
      #~ u_h = "%s/uri" % r_hash
      #~ r_h = "%s/ref" % r_hash
      #~ b_h = "%s/blocked" % r_hash
      #~ v_h = "%s/violated" % r_hash
      #~ s_h = "%s/status" % r_hash
#~ 
      #~ # ip_list
      #~ i_d = {}
      #~ i_k = redis.hkeys(i_h)
      #~ for k in i_k:
        #~ kv = redis.hget(i_h, k)
        #~ i_d[k] = kv 
      #~ i_d = sorted(i_d.values(), reverse=True)[0:10]
#~ 
      #~ # domain_list
      #~ d_d = {}
      #~ d_k = redis.hkeys(d_h)
      #~ for k in d_k:
        #~ kv = redis.hget(d_h, k)
        #~ d_d[k] = kv 
      #~ d_d = sorted(d_d.values(), reverse=True)
#~ 
      #~ # domain_list
      #~ d_d = {}
      #~ d_k = redis.hkeys(d_h)
      #~ for k in d_k:
        #~ kv = redis.hget(d_h, k)
        #~ d_d[k] = kv 
      #~ d_d = sorted(d_d.values(), reverse=True)


  
  dash = redis.hget("dashboards", "24hrs")
  #~ if dash == None:
    #~ print "[i] regeneration dashboards"
  #~ else:
    #~ print "[i] dashboards cached "
    #~ return(dashboard_data())
  mnow = now()
  
  # collecting stats
  for t in dash_times:
    r_hash = "dash/%s" % t 
    print "  > dash: %s " % t
    dash_id = t
    last = int(mnow - (dash_times[t] * 86400))
    csp_union = []
    for ct in xrange(last, mnow + 60, 86400):
      csp_union.append("%s" % csp_id(ct))
    #print csp_req
    dash_reports =  redis.sunion(csp_union)
    print "  > %7s reports " % len(dash_reports)
    dash_data = convert_redis(dash_reports)

    # default cleanup
    p = redis.pipeline()
    p.hset("dashboards", "24hrs", "OK")
    p.expireat("dashboards", 300)
    p.delete("%s/ip" % r_hash, "%s/domain" % r_hash, "%s/uri" % r_hash, "%s/ref" % r_hash, 
          "%s/blocked" % r_hash, "%s/violated" % r_hash, "%s/status_code" % r_hash)
    p.execute()

    # inserting data
    p = redis.pipeline()
    for d in dash_data:
      # reporter-ip
      p.hincrby("%s/ip" % r_hash,  d[0], 1)
      p.hincrby("%s/domain" % r_hash,  d[9], 1)
      p.hincrby("%s/uri" % r_hash,  d[1], 1)
      p.hincrby("%s/ref" % r_hash,  d[2], 1)
      p.hincrby("%s/blocked" % r_hash,  d[3], 1)
      p.hincrby("%s/violated" % r_hash,  d[4], 1)
      p.hincrby("%s/status" % r_hash,  d[6], 1)
    
    # should we expireat keys???  
    #p.expireat(report_key, expires)
    p.execute()

    # getting data


    # caching dashboard_data
    result_dict = {} 
    for t in dash_times:
      r_hash = "dash/%s" % t 
      for ax in dash_areas:
        print " > dashing %s / %s " % (t, ax)
        s_k = "%s/%s" % (r_hash, ax)
        dd = {}
        ax_res = redis.hkeys(s_k)
        for k in ax_res:
          kv = redis.hget(s_k, k)
          dd[k] = kv 
        dd = sorted(dd.items(), key=lambda x:x[1], reverse=True)[0:10]
        result_dict[s_k] = dd

    p = redis.pipeline()

    for entry in result_dict:
      print "caching: %s " % entry
      p.sadd(entry, result_dict[entry])
      p.expire(entry, 3600)
    
    p.execute()
    
    cache_data = dashboard_data()
      
    #~ for t in dash_times:
      #~ r_hash = "dash/%s" % t 
      #~ for ax in dash_areas:
        #~ print " > dashing %s / %s " % (t, ax)
        #~ s_k = "%s/%s" % (r_hash, ax)
        #~ dd = {}
        #~ ax_res = redis.hkeys(s_k)
        #~ for k in ax_res:
          #~ kv = redis.hget(s_k, k)
          #~ dd[k] = kv 
        #~ dd = sorted(dd.values(), reverse=True)[0:10]
        #~ result_dict[s_k] = dd
    #print result_dict


  for cd in cache_data:
    print " cached: %s" % cd
    
    
  
  return(cache_data)
  
