# Reqman4

<a href="https://pypi.org/project/reqman4/">
    <img src="https://badge.fury.io/py/reqman4.svg" alt="Package version">
</a>


A complete rewrite of [reqman](https://github.com/manatlan/reqman). __It's a **prototype/poc**__ ! Don't know yet if it will replace the original, but I wanted to have a new/cleaner/simpler version, 
with all good ideas from the original. 

**MAJOR CHANGES**: This prototype is more python based for vars & tests, and can display html in http-verb's doc (to be able to make human readable html reports). Syntax is simpler/cleaner (to be able to have a json-schema to valid yml/rml). And debugging is simpler.

Currently, the package provide a `rq` command (but will be `reqman` in the future)

Major differences :
- licence gnu gpl v2 -> MIT
- "uv" & (a lot) simpler (less features)
- use httpx !
- options are inverted (--i -> -i & (switch) -dev --> --dev)
- one SWITCH param only (may change)
- scenars(yml/rml) & reqman.conf are yaml/dict only !
- scenars must(/can for compat) have a "RUN:" section (others keys are the global env)
- tests are simple python statements
- no break!
- no if 
- no more .BEGIN/.END
- no more RMR
- no more comparison side by side
- no more XML testing (may change)
- no more junit.xml output (may change)

Here is a valid scenario, which give you an overview :
[scenario.yml](https://github.com/manatlan/reqman4/blob/main/scenario.yml)

If you use [uvx](https://docs.astral.sh/uv/guides/tools/), you cant test this scenario in your context :

    uvx reqman4 https://raw.githubusercontent.com/manatlan/reqman4/refs/heads/main/scenario.yml -o

It will open an html report in your default browser, and you can easily check what's going ...

## From github

### to test command line

    uvx --from git+https://github.com/manatlan/reqman4 rq --help

### to run a scenario

    uvx --from git+https://github.com/manatlan/reqman4 rq scenario.yml -o

## From pypi

### to test command line

    uvx reqman4 --help

### to run a scenario with a local scenario

    uvx reqman4 scenario.yml -o



