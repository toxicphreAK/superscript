import typer
import yaml
import shutil
import git
from pathlib import Path

from constants import APP_NAME, DEFAULT_CONFIG, GITENDING, UNCATEGORIZED
from fshandling import check_path_create
from printing import write_verbose, write_error, write_question, write_success


def create_config(
    path: Path,
    installpath: str,
    autosave: bool,
    gitvcs: bool,
    gitsaveurl: str | None
):
    """
    Create the script configuration file.
    """
    global superconfig
    write_verbose("Writing initial config file")
    if installpath is None:
        installpath = str(path.parent / "tools")
    write_verbose(f"Installpath is set to {installpath}")
    if not superconfig:
        superconfig = {
            'config': {
                'defaultpath': installpath,
                'autosave': autosave,
                'gitvcs': gitvcs,
                'gitsaveurl': gitsaveurl}
        }
    save_superconfig(path, "Add initial configuration file", True)


def load_superconfig(path):
    global superconfig
    if path.is_file():
        with open(path, 'r') as f:
            supercontent = f.read()
        superconfig = yaml.load(supercontent, Loader=yaml.Loader)
        # TODO: error handling if file could not be loaded, e.g. no yaml format!
    else:
        write_error(f"No such file {path} to load superconfig from")
        # Q: maybe exit?


def save_superconfig(
    path=Path(typer.get_app_dir(APP_NAME)) / DEFAULT_CONFIG,
    commitcontent="Add changes in superscript config",
    initializerepo=False
):
    global superconfig
    check_path_create(path.parent)
    if superconfig["config"]["gitvcs"]:
        repo: git.Repo
        if initializerepo:
            # proof if a git repo already exists and delete if user accepts
            gitpath = path.parent / GITENDING
            # Q: maybe outsource to function check_file_overwrite()
            if gitpath.is_file():
                write_verbose(f"Found existing git repository at {gitpath}")
                overwrite = write_question("A git repository is already in place, do you want to overwrite it?")
                if overwrite:
                    shutil.rmtree(gitpath)
                    write_success(f"Removed existing git repository successfully")
            # initialize git repository
            repo = git.Repo.init(str(path.parent))
            if superconfig["config"]["gitsaveurl"]:
                origin = repo.create_remote('origin', superconfig["config"]["gitsaveurl"])
                # Q: really needed on new repo?
                origin.fetch()
        else:
            write_verbose(f"Using existing repo to save config")
            repo = git.Repo(str(path.parent))
    with open(path, 'w+') as f:
        f.write(yaml.dump(superconfig, Dumper=yaml.Dumper))
    if superconfig["config"]["gitvcs"]:
        repo.index.add(str(path))
        repo.index.commit(commitcontent)
    if superconfig["config"]["gitvcs"] and superconfig["config"]["gitsaveurl"] and superconfig["config"]["autosave"]:
        repo.push()
    write_verbose("Config file successfully written")


def config_path_adjust(base, category=UNCATEGORIZED):
    global superconfig
    if base not in superconfig:
        write_verbose(f"{base} is actually not in config file, going to create it")
        superconfig[base] = None
    if not superconfig[base]:
        write_verbose(f"{base} has value None in config file, going to set to {category}")
        superconfig[base] = {category: None}
    elif category not in superconfig[base]:
        write_verbose(f"{category} is actually not under {base} in config file, going to create it")
        # TODO: check if an similar category already exists (use difflib, like in search)
        superconfig[base].update({category: None})
