# Writing Naxsi rules

NAXSI is a *web application firewall* (WAF) for [Nginx]( https://nginx.org ).
This howto tries to explain how to understand and write rules for it,
and details some use-cases. You should also take a look at the latest
documentation available [here]( https://github.com/nbs-system/naxsi/wiki ).

Beside this, we maintain and develop a set of tools (Doxi-Tools) for
WAF-administration, ruleset-updates and an extended  and updated Ruleset
(Doxi-Rules, based upon Emerging Threats Snort-Signatures.

- [Understand naxsi's philosophy & design (READ FIRST)](https://github.com/nbs-system/naxsi/wiki/philosophy)
- [Naxsi](https://github.com/nbs-system/naxsi)
- [Nasxi-Wiki](https://github.com/nbs-system/naxsi/wiki/)
- [Doxi-Tools](https://bitbucket.org/lazy_dogtown/doxi)
- [Doxi-Rules](https://bitbucket.org/lazy_dogtown/doxi-rules/src)


<div id="acco2" markdown="1">
<h7> TOC </h7>
<div markdown="1">


[TOC]



</div>
</div>

# About the wording

- when using the word SIG we refer to a naxsi-rule/detecting signature
- when using the word SID we refer to a rule/signature-ID
- when we talk about a RULESET we refer to a file with a list of SIGs
- when using the word EVENT we refer to a request that creates a hit on one or more SIGs


## Rules - Writing Naxsi - Sigs - Howto

- MainRule  -> define a detection-pattern and scores
- BasicRule -> define whitelists for MainRules
- CheckRule -> define actions, when a score is met

~~~

# detection-sig
MainRule "msg:this is a message" "str:searchstring"  "mz:URL|BODY|ARGS" "s:$XSS:8" id:12345678990;

# whitelist
BasicRule wl:1100 "mz:$URL:/some/url|URL";

# CheckRule
CheckRule "$SQL >= 8" BLOCK;

~~~

## CheckRule - defining action on Scores






## MainRulePattern

#### Basics on creating Naxsi-Signatures

- Designators and its values **MUST** be wrapped in quotionmarks "dsg:[pattern]", except for id

#### Config

MainRules should be stored in separate files that could be included into nginx-configuration
at html/server-level, like the following:

~~~

include     /etc/nginx/rules/naxsi_core.rules;
include     /etc/nginx/rules/web_server.rules;

~~~


~~~

MainRule "msg:this is a message" "str:searchstring"  "mz:URL|BODY" "s:$XSS:8" id:12345;
 |          |                      |                   |                 |     +-> UNIQE ID     
 |          |                      |                   |                 |
 |          |                      |                   |                 +-> SCORE
 |          |                      |                   |
 |          |                      |                   +-> MZ
 |          |                      |
 |          |                      +-> SearchString/RegEx
 |          |
 |          +-> MESSAGE
 |
 +-> RuleDesignator

~~~


#### RuleDesignator

- must be MainRule; the MainRule - Identifier is used to mark detection-rules, in opposite to 
BasicRules, who are usually used to whitelist certain MainRules. 


- Designator: **MUST** be **MainRule** 

#### Message ( msg:)

- the mesaage is some string/words that explains shortly on what bthe rule dow/should detect; this is mostly
  used for analyzing and to have some human-understandeable text; think of dns for translating hostnames to ips,
  the msg: translates a rules-id to a text 
  

#### SearchString (str:|rx:)

- define a searchstring with "str:searchstr" or regex-pattern with "rx:reg.+ex" 
- Naxsi does case insensitive matching on strings if your string is lowercase!
- string match is *way* faster than regex


- in case you want to use heavy pcre-statements (see https://groups.google.com/group/naxsi-discuss/browse_thread/thread/a6efabbffb6c6b7c)

reply by bui:

    Please don't do this ! 
    I written naxsi exactly in order not to have to do this. 
    I don't want to have complex/evolved rules/patterns, but rather focus 
    on primitives used by attacks.

#### MatchingZones (mz:)

MatchingZones define the  area of a request your search-pattern will apply. Valid MZs are

- URL -> full URI (server-path of a request)
- ARGS -> Request-Arguments (all the stuffe behind ? in a GET-Request 
- BODY -> Request-Data from a POST-Request (http_client_body)
- HEADERS 
- $HEADERS_VAR:[value] -> any HTTP-HEADERS-var that is available, eg
    - $HEADERS_VAR:User-Agent
    - $HEADERS_VAR:Cooie
    - $HEADERS_VAR:Content-Type
    - $HEADERS_VAR:Connection
    - $HEADERS_VAR:Accept-Encoding
- FILE_EXT: Filename (in a multipart POST containing a file)

#### Scores (s:)

Scores define some kind of attack-categories. Each rule has on or more 
scores defined, and whenever one event is generated, the score is increased
by the dfined values. Scores are the evaluated later by the CheckRule - directive.


You are not limited to the Score-Preset ($AQL, §RFI, $TRAVERSAL, $XSS, $EVADE) 

A special score-value is DROP

#### Signature IDs (id:)


## Examples

#### creating a sig for POST:

- include BODY in MZ for searching the body of the POST - request
- include mz:$URL/hallo/test|BODY for a sig on a post to a certain URL, 

~~~

MainRule "msg:detection Submit=Run in POST" "str:Submit=Run" "mz:$URL:/script|$BODY_VAR:Submit" \
    "s:$ATTACK" id: 1230001;

~~~


#### creating a sig for matching access on a certain URL:

- include URL in MZ for searching an URL for what is given in str:|rx

~~~

MainRule "msg:detection URL-Access" "str:/hidden.html" "mz:URL" \
    "s:$ATTACK" id: 1230002;

~~~    

#### detecting a string in a named ARGS - Var

~~~

# detect jjoplmh in var:cms ->  http://blog.example.com/?cms=jjoplmh.
MainRule "str:jjoplmh" "msg:Possible Wordpress-Plugin-Backdoor detected" "mz:ARGS|$ARGS_VAR:cms" "s:$UWA:8" id:42000347  ;

~~~

### create a sig for a certain ARGS_VAR

- e.g. create a generic signature for joomla-exploit-scanners that
use a lot of exploits with requests like ?option=com_*
- include ARGS in MZ for searching the arguments of a request (GET)
- include mz:$ARGS_VAR:option into the matching-zone to define the argument you want to test against 
"str:com_" "mz:$ARGS_VAR:option|ARGS"


## BasicRule - WhiteListing


**ATTENCIONE!!!** Whitelisting should always be done via BasicRule, 
thus MUST be included in location {} - context!

you **CANNOT** Whitelist via MainRule. 

you **CANNOT** Whitelist outside a Location {} 


#### generic whitelist for a certain Sigs

~~~

BasicRule wl:1234; # generic whitelist for rule 1234 for all requests

~~~

#### generic whitelist on a certain URL

~~~

BasicRule wl:1100 "mz:$URL:/some/url|URL";

~~~

# RuleSets

#### Internal Rules

(as of v 0.53)

- 1 - "weird request" : This a generic exception used for improperly formatted requests.
- 2 - "big request" : Request is too big and has been buffered to disk by nginx.
- 10 - "uncommon hex encoding" : Encoding suggests this might be an escape attempt.
- 11 - "uncommon content-type" : Content-type of BODY is unknown / cannot be parsed.
- 12 - "uncommon URL" : URL is malformed
- 13 - "uncommon post format" : malformed boundary or content-disposition
- 14 - "uncommon post boundary" : BODY boundary line is malformed, or boundary breaks RFC
- 15 - invalid JSON - gets parsed when application/json is detected (experimental as of summer 2014)
- 16 - "empty body" : POST with empty BODY (>= 0.53-1 - was merged with id:11 before)

#### naxsi-core.rules

Naxsi ships with a [basic core-rule-set](https://github.com/nbs-system/naxsi/blob/master/naxsi_config/naxsi_core.rules)
that protects against common attacks:

- SQL-Injections (1000-1099)
- Obvious RemoteFileInclusions (1100-1199)
- Directory Traversal (1200-1299)
- Cross Site Scripting (1300-1399)
- Basic Evading tricks (1400-1500)
- File uploads (1500-1600)

Those Core-Rules should always be loaded 

#### Extended RuleSets: Doxi-Rules






# Learning-Mode

when configured with  **LearningMode;** ([see basicsetup for details](https://github.com/nbs-system/naxsi/wiki/basicsetup)), naxsi
will log detected attacks, buit dont block any action. This is very usefull for new Apps or staging/testing-Environments
for automated whitelist-generating. 

Learning-Mode enables you to deploy a naxsi-setup and learn from the detected events without actually blocking any requests
and is very usefull for new WebApps. 


# Naxsi - UseCases


## Integrating automated Whitelisting into deployment-cycles

- tbd 


## centralized Naxsi-Event-Analysis: Logstash + ElasticSearch + Kibana

- tbd 




## Learning-Mode with DROP detected and known attacks

It might be the case, you have a new setup and want to use learning-mode, while 
dropping known an detected attacks. 

You can configure 




# Fail2Ban - Integration

~~~ 

# jail.conf
[naxsi]

enabled = true
port = http,https
filter = naxsi
logpath = /var/log/nginx/error.log
maxretry = 3
banaction = iptables-multiport-log
action = %(action_mwl)s

# filter.d/naxsi.conf

[INCLUDES]
before = common.conf

[Definition]
failregex = NAXSI_FMT: ip=<HOST>
ignoreregex = learning=1

~~~
