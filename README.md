# RQ (reqman4)

a complete rewrite

diff:
- "uv" & (a lot) simpler (less features)
- scenars(yml/rml) & reqman.conf are yaml/dict only !
- scenars must have a "RUN:" section (others keys are the global env)
- tests are python statements
- no more BEGIN/END & .BEGIN/.END


~~currently :~~

```yaml
SCENAR1:
    - GET: /gfdsgfdsg
    - GET: /gfdsgfdsg?a=a
    
METHODPY: |
    return x*42

host: https://x.com
toto: 42
headers:
    content-type: application/json
    user-agent: me

RUN:
    - set:
        toto: toto + 1

    - POST: /fdgfdgfds
      doc: fdsqfdsqfds fdsqfdsq <<toto>>
      headers:
           content-type: application/json
      body:
         code: <<code>>
         id: 16616
      tests:
        - $status == 200    # $status & $headers are the last http status&headers
        - $.result == "ok"
    
    - set:
        result: $           # '$' is the last http body response
    
    - call: SCENAR1
      params:               # (was the foreach)
         - i: 2             # call SCENAR1 with {"i":2}
         - i: 4             # call SCENAR1 with {"i":4}

```