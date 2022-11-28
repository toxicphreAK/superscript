import typer
from constants import POS, INF, NEG, VRB, QST, CNT


def write_success(message):
    typer.echo(POS + message)


def write_info(message):
    typer.echo(INF + message)


def write_error(message):
    typer.echo(NEG + typer.style(message, fg=typer.colors.RED))


def write_verbose(message):
    # TODO: add global state
    # if state["verbose"]:
    #    typer.echo(VRB + message)
    typer.echo(VRB + message)


def write_question(message, abort=True):
    return typer.confirm(QST + message, abort=abort)


def write_count(content, counter=None, level=1):
    if counter is not None:
        typer.echo(CNT.format(level * "    ", counter) + content)
    else:
        typer.echo(level * "    " + content)
