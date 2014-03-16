

# Spike! - Naxsi Rules Builder

Spike! is a simple webapp that generates Naxsi-Rules.
Rules are stored in a sqlite-db and might be exported
into separate ruleset-files for further processing. 

This Software is intended for people or dc-operators who
already use Naxsi and are familiar with writing Naxsi-Signatures
and was intially created to help with keeping the Doxi-Rulesets
up-to-date. 


# Install

## Requirements

- python 2.6 or above
- python-virtulenv
- probably some build-essentials: gcc, make'n' stuff

- git clone https://bitbucket.org/nginx-goodies/spike.git
- cd spike && bash install.sh

# Setup

- edit config.cfg and adjust NAXSI_RULES_EXPORT to point to a dircetory where 
  your exported Naxsi-Rulesets should be stored; can be either a absolute or relative path

- run `./server init`

you should be ready now to start using Spike!

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


# Usage

- run `./server run`

- if you want to run spike as daemon, use `nohup ./server run > spike.log &`

- point your browser to http://localhost:5555/ (or whatever APP_PORT you 
  configured)
- the navigation should be self-explaining



# Links

- [Naxsi-Sources](https://github.com/nbs-system/naxsi)
- [Doxi-Rules](https://bitbucket.org/lazy_dogtown/doxi-rules/src)
- [Naxsi-Wiki](https://github.com/nbs-system/naxsi/wiki)
