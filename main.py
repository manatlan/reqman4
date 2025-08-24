import os
import click
import sys
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


@click.command()
@click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
#@click.option('--count', default=1, help='Number of greetings.')
def main(files:list) -> int:
    """Simple program that greets NAME for a total of COUNT times."""
    reqman_conf = guess_reqman_conf(files)
    if reqman_conf is None:
        print("No reqman.conf found")
    else:
        print(f"Using reqman.conf: {reqman_conf}")
        conf = load_reqman_conf(reqman_conf)
        print(conf)
    return 0

if __name__ == "__main__":
    sys.exit(main())