import typer
from pathlib import Path

from printing import write_question, write_error, write_verbose


def check_path_create(path: Path, ask: bool = False):
    if not path.is_dir():
        if ask:
            create_folders = write_question(
                f"The provided path {path} does currently not exist, do you want to create the neccessary folders?"
            )
            if not create_folders:
                write_error(f"The provided path {path} does not exist and should not be created")
                raise typer.Exit()
        write_verbose(f"Creating path {path} as it does not exist")
        Path.mkdir(path)
