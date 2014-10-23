
# Usage 

- run `./server run`

- if you want to run spike as daemon, use `nohup ./server run > spike.log &`

- point your browser to http://localhost:5555/ (or whatever APP_PORT you 
  configured)
- the navigation should be self-explaining
- create new rules as needed
- export rulesets or all rulesets -> will be exported 
- process your exported files as needed 

we use spike with doxi and the following workflow:

- edit rules
- when done, run a script on the console, that
    - triggers http://spike.local:5555/rules/export/
    - rsyncs spike/export/*.rules to sig_store/doxi-rules/
    - cd sig_store/doxi-rules/ && git add *.rules && git commit -a -m "commit-message" && git push origin master
    - runs a fabric-fabfile finally that updates all our servers with doxi-tools


# untested function

- the import hasent been tested very well yet; it worked, but i wouldnt guarantee it



