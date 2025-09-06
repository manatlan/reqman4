# Reqman4

a complete rewrite (prototype)

diff:
- licence gnu gpl v2 -> MIT
- "uv" & (a lot) simpler (less features)
- use httpx !
- options are inverted (--i -> -i & (switch) -dev --> --dev)
- one SWITCH param only (may change)
- scenars(yml/rml) & reqman.conf are yaml/dict only !
- scenars must(/can for compat) have a "RUN:" section (others keys are the global env)
- tests are python statements
- no break!
- no if 
- no more .BEGIN/.END
- no more RMR
- no mote comparison side by side
- no more XML testing (may change)
- no more junit xml output (may change)

# from github

## to test command line (from)

    uvx --from git+https://github.com/manatlan/reqman4 rq --help

## to run a scenario (new version)

    uvx --from git+https://github.com/manatlan/reqman4 rq scenario.yml -o

# from pypi

## to test command line (from)

    uvx --from reqman4 rq --help

## to run a scenario (new version)

    uvx --from reqman4 rq scenario.yml -o

