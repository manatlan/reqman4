import os
import yaml

REQMAN_CONF='reqman.conf'

def guess_reqman_conf(paths:list[str]) -> str|None:
    cp = os.path.commonpath([os.path.dirname(os.path.abspath(p)) for p in paths])

    rqc = None
    while os.path.basename(cp) != "":
        if os.path.isfile(os.path.join(cp, REQMAN_CONF)):
            rqc = os.path.join(cp, REQMAN_CONF)
            break
        else:
            cp = os.path.realpath(os.path.join(cp, os.pardir))
    return rqc

def load_reqman_conf(path:str) -> dict:
    with open(path, 'r') as f:
        conf = yaml.load( f, Loader=yaml.SafeLoader)
    assert isinstance(conf, dict), "reqman.conf must be a mapping"
    return conf
