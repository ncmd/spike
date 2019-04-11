# Spike - ChangeLog

## 0.5.2 - 2019-04-11
- exposed flask service to run on 0.0.0.0 to be dockerized

## 0.5.1 - 2019-04-10
- fixed import errors with flask.ext.alchemy & flask.ext.bootstrap
- added missing package python-dateutil to requirements.txt


## 0.5 - TBA
- boostrap and jquery update
- removal of backup/import/export features
- cleaup of the code
- unit-testing
- removal of dead-code

## v0.4.1 - 2015-03-22

- bugfixes
- export now only rulesets that got changed, leave unchanged as-is
- "writing naxsi sigs" - manual included
- docs updated
- demo-mode I(spike.nginx-goodies.com) w/out saving/changing stuff
- nicer install-script
- search for sid-id
- sql-editor
- rules can be negated now


## v0.4 - 2014-04-07

- rules-db backup
- ruleset-import 
- sql-editor (very simple yet)


## v0.3 - 2014-03-17

- port from spike v0.8 (snort/naxis-builder)
- rewrote interface in flask
- basic features
    - create/edit rules
    - create/export rulesets
    - maintain settings
    
