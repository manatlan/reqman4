import click
import sys
import config

from colorama import init, Fore, Style

init()

def colorize(color: str, t: str) -> str|None:
    return (color + Style.BRIGHT + str(t) + Fore.RESET + Style.RESET_ALL if t else None)

cy = lambda t: colorize(Fore.YELLOW, t)
cr = lambda t: colorize(Fore.RED, t)
cg = lambda t: colorize(Fore.GREEN, t)
cb = lambda t: colorize(Fore.CYAN, t)
cw = lambda t: colorize(Fore.WHITE, t)


@click.command()
@click.argument('files', type=click.Path(exists=True,), nargs=-1, required=True)
#@click.option('--count', default=1, help='Number of greetings.')
def main(files:list) -> int:
    """Simple program that greets NAME for a total of COUNT times."""
    reqman_conf = config.guess_reqman_conf(files)
    if reqman_conf is None:
        print(cr("No reqman.conf found"))
    else:
        print(f"Using reqman.conf: {reqman_conf}")
        conf = config.load_reqman_conf(reqman_conf)
        print(conf)
    return 0

if __name__ == "__main__":
    sys.exit(main())