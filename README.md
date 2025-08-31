# RQ (reqman4)

a complete rewrite (prototype)

diff:
- licence gnu gpl v2 -> MIT
- "uv" & (a lot) simpler (less features)
- use httpx !
- options are inverted (--i -> -i & (switch) -dev --> --dev)
- one SWITCH only (may change)
- scenars(yml/rml) & reqman.conf are yaml/dict only !
- scenars must(/can for compat) have a "RUN:" section (others keys are the global env)
- tests are python statements
- no more BEGIN/END & .BEGIN/.END
- no more XML testing (may change)
- no more junit xml output (may change)

## to tests

    uvx --from git+https://github.com/manatlan/RQ rq --help

## to test a scenario (new version)

    uvx --from git+https://github.com/manatlan/RQ rq scenario.yml -o
