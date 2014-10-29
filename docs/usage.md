
# WARNING

> 
> Spike ist still very early alpha.
>
> NEVER run Spike! on a public facing Server; there's absolutely 
> no protection or user-login atm; exposing Spike! to the public could
> lead into damaged or deleted rules 
>
> Really
>
>

If you are new to naxsi, please read the [Naxsi Rules Syntax Howto](https://github.com/nbs-system/naxsi/wiki/rulessyntax)
and the [Writing Naxsi Sigs Handbook](/docs/writing_naxsi_sigs.md)



# Edit Rules /rules/edit/SID

- General Hint: "Quotations" will be stripped from the interface but added into the signatures
- you can switch between edit and view-mode; edit -> change values, view -> see the final rule after saving

- SID (Signature ID) will be given automatically
- MSG: mnessag-strang that will be included as "msg:MESSAGE_STRING"
- Detect: detection - string/rx; if omitted, str:DETECTION_STRING will be added, if you want to use regular expression you need to 
  use the designator rx:YOUR_REGEX; 

- MZ: select a given MatchingZone or create a custom one; you might use multiple MatchingZones; you might add custom MatchingZones via 
  /settings/mz
- Score: select at least one score; you might add custom Scores via /settings/score
- Remarks: will be added into the export before the rule
- RuleSet: select a ruleset for this rule; you might change/add rulesets via /rules/rulesets/

~~~ 
#
# rmks 
#
MainRule "str:/gatedesc.xml" "msg:UPNP-Scan" "mz:URL" "s:$UWA:8" id:42000390  ;

~~~



# Server-Usage 

- run `./server run`

- if you want to run spike as daemon, use `nohup ./server run > spike.log &`

- point your browser to http://localhost:5555/ (or whatever APP_PORT you 
  configured)
- the navigation should be self-explaining
- create new rules as needed
- export rulesets or all rulesets -> will be exported 
- process your exported files as needed 

# Workflow

we use spike with doxi and the following workflow:

- edit rules
- when done, run a script on the console, that
    - triggers http://spike.local:5555/rules/export/
    - rsyncs spike/export/*.rules to sig_store/doxi-rules/
    - cd sig_store/doxi-rules/ && git add *.rules && git commit -a -m "commit-message" && git push origin master
    - runs a fabric-fabfile finally that updates all our servers with doxi-tools





# untested function

- the import hasent been tested very well yet; it worked, but i wouldnt guarantee it



