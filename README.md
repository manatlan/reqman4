# RQ (reqman4)

a complete rewrite

diff:
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

RUN:
    - set:
        host: https://x.com
        toto: 42
        headers:
            content-type: application/json
            user-agent: me
    
    - POST: /fdgfdgfds
      doc: fdsqfdsqfds fdsqfdsq <<caisse>>
      headers:
           content-type: application/json
      body:
         caisse: <<caisse>>
         idremise: 16616
      tests:
        - $status == 200
        - $.result == "ok"
    
    - set:
        result: $
    
    - call: SCENAR1
      params:
         - i: 2
         - i: 4

```