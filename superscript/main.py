import typer
import yaml
import git
import re

from pathlib import Path, PurePath
import shutil

import requests
import difflib
from rich.console import Console
from rich.markdown import Markdown


__version__ = "0.1.0"

APP_NAME = "superscript"
DEFAULT_CONFIG = "superconfig.yml"
app = typer.Typer(
    help="Awesome superscript to dynamically manage your portable software components.")
console = Console()
state = {"verbose": False}
superconfig = None

pos = typer.style("[+] ", fg=typer.colors.GREEN, bold=True)
inf = typer.style("[*] ", fg=typer.colors.WHITE, bold=True)
neg = typer.style("[-] ", fg=typer.colors.RED, bold=True)
vrb = typer.style("[~] ", fg=typer.colors.CYAN)
qst = typer.style("[?] ", fg=typer.colors.YELLOW)
cnt = "{}[{}] "

# ssh://git@pentest-git.myatos.net:2222/Reporting/Knowledgebase.git
GITSSH_BLUEPRINT = re.compile(
    r'^(?:git|ssh|https?|git@[-\w.]+):(\/\/)?(.*?)(\.git)(\/?|\#[-\d\w._]+?)$', re.IGNORECASE)
URL_BLUEPRINT = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

UNCATEGORIZED = "(uncategorized)"

GITENDING = ".git"

TYPES = {
    "git": "git",
    "gitrelease": "gitrelease",
    "urlfile": "urlfile"
}


def convert_versionstring(versionstring):
    versionstring_regex = re.compile("[vV]?(?P<major>[0-9]+)[.,-_]?(?P<minor>[0-9]*)[.,-_]?(?P<fix>[0-9]*)")
    version_match = versionstring_regex.match(versionstring.strip())
    if not version_match:
        # TODO: handle error in regex and print versionstring with the info that this version conversion is not supported at the moment
        pass
    version = {
        'major': 0,
        'minor': 0,
        'fix': 0
    }
    if version_match.group('major'):
        version['major'] = int(version_match.group('major'))
        if version_match.group('minor'):
            version['minor'] = int(version_match.group('minor'))
            if version_match.group('fix'):
                version['fix'] = int(version_match.group('fix'))
    return version


class Version():
    def __init__(self, *args, **kwargs):
        default_version = {
            'major': 0,
            'minor': 0,
            'fix': 0
        }
        if len(args) == 1:
            default_version = convert_versionstring(args[0])
        self.major = kwargs.get('major', default_version['major'])
        self.minor = kwargs.get('minor', default_version['minor'])
        self.fix = kwargs.get('fix', default_version['fix'])

    def get_versionstring(self):
        return "v{}.{}.{}".format(self.major, self.minor, self.fix)

    def next_major(self):
        return int(self.major) + 1

    def next_minor(self):
        return int(self.minor) + 1

    def next_fix(self):
        return int(self.fix) + 1


def version_callback(value: bool):
    if value:
        typer.echo(f"Awesome CLI Version: {__version__}")
        raise typer.Exit()


def write_success(message):
    typer.echo(pos + message)


def write_info(message):
    typer.echo(inf + message)


def write_error(message):
    typer.echo(neg + typer.style(message, fg=typer.colors.RED))


def write_verbose(message):
    if state["verbose"]:
        typer.echo(vrb + message)


def write_question(message, abort=True):
    return typer.confirm(qst + message, abort=abort)


def write_count(content, counter=None, level=1):
    if counter is not None:
        typer.echo(cnt.format(level * "    ", counter) + content)
    else:
        typer.echo(level * "    " + content)


def get_gitname(giturl):
    return giturl.rstrip("/").split("/")[-1].replace(GITENDING, "")


def check_path_create(path, ask=False):
    if not isinstance(path, PurePath):
        path = Path(path)
    if not path.is_dir():
        if ask:
            create_folders = write_question("The provided path {path} does currently not exist, do you want to create the neccessary folders?")
            if not create_folders:
                write_error(f"The provided path {path} does not exist and should not be created")
                raise typer.Exit()
        write_verbose(f"Creating path {path} as it does not exist")
        Path.mkdir(path)


def create_config(
    path,
    installpath,
    autosave,
    gitvcs,
    gitsaveurl
):
    """
    Create the script configuration file.
    """
    global superconfig
    write_verbose("Writing initial config file")
    if installpath is None:
        installpath = str(path.parent / "tools")
    write_verbose("Installpath is set to {installpath}")
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


def get_toolconfig(toolname):
    global superconfig
    if "components" in superconfig:
        for category in superconfig["components"].keys():
            if toolname in superconfig["components"][category]:
                if category == UNCATEGORIZED:
                    return superconfig["components"][category][toolname], None
                else:
                    return superconfig["components"][category][toolname], category
    # Q: handle not initialized config
    return None, None


def get_all_tools():
    global superconfig
    tools = []
    categories = []
    if "components" in superconfig:
        for category in superconfig["components"].keys():
            for tool in superconfig["components"][category].keys():
                tools.append(tool)
                categories.append(category)
    return tools, categories


def add_component(
    component_name,
    component_url,
    component_path,
    branch="master",
    recursive=False,
    subfolder=True,
    custompath=None,
    component_type=TYPES["git"],
    category=UNCATEGORIZED,
    version=None
):
    global superconfig
    config_path_adjust("components", category)
    # Q: maybe only update will handle None content? try it out
    addition = {component_name: {"url": component_url, "type": component_type}}
    if (category != UNCATEGORIZED and not subfolder) or custompath:
        addition[component_name].update({"custompath": str(component_path)})
    # save branch if it is not master
    if branch != "master":
        addition[component_name].update({"branch": branch})

    if recursive:
        addition[component_name].update({"recursive": recursive})

    if version:
        addition[component_name].update({"version": version })

    if "components" in superconfig:
        if category in superconfig["components"] and superconfig["components"][category]:
            write_verbose(f"Category {category} already exists")
            superconfig["components"][category].update(addition)
        else:
            superconfig["components"][category] = addition
    else:
        write_error("components not initialized in superconfig, going to exit")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    installpath: str = None,
    gitvcs: bool = True,
    gitsaveurl: str = None,
    autosave: bool = True,
    verbose: bool = False,
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    )
):
    """
    Manage portable components in the awesome CLI app.
    """
    if verbose:
        write_verbose("Verbose output activated...")
        state["verbose"] = True
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / DEFAULT_CONFIG
    if ctx.invoked_subcommand is None:
        write_info("Initializing superscript")
        write_verbose(f"Using path {config_path}")
        if config_path.is_file():
            write_error("Config file does already exist!")
            overwrite = write_question("Do you want to overwrite the existing config?")
            # breaks here if the user don't wants to overwrite existing config
            if not overwrite:
                write_info("Not overwriting, going to exit...")
                raise typer.Abort()
            write_info("Overwriting config file")
        write_info("Initialize script config")
        # create the config file, also if file already exists
        create_config(config_path, installpath, autosave, gitvcs, gitsaveurl)
    else:
        # TODO: manage to show help of subcommand if config is not initialized
        # TODO: manage to restore from file/url if no config file in place
        if not config_path.is_file():
            write_error("No config file found. First initialize superscript to make it work.")
            raise typer.Exit()
        write_verbose("Config file found")
        load_superconfig(config_path)
        # runs script with args normally if config file found


@app.command()
def clone(
    giturl: str,
    branch: str = "master",
    recursive: bool = False,
    category: str = UNCATEGORIZED,
    subfolder: bool = True,
    custompath: str = None
):
    """
    Clones a git repository to the install path.

    Install path could be defaultpath or a user specified one.
    """
    global superconfig

    # proof if web or git URL
    if not (re.match(URL_BLUEPRINT, giturl) or re.match(GITSSH_BLUEPRINT, giturl)):
        # warning that no valid git url was provided by the user
        write_error(f"The provided Git URL {giturl} is not valid")
        raise typer.Exit()

    gitname = get_gitname(giturl)
    # use reponame as subpath
    basepath = superconfig["config"]["defaultpath"]
    # handle custom user path
    if custompath:
        check_path_create(custompath, ask=True)
        basepath = custompath

    gitrepopath = Path(basepath)
    if category != UNCATEGORIZED and subfolder:
        gitrepopath = gitrepopath / category
    gitrepopath = gitrepopath / gitname
    # proof if repository is not already cloned
    if gitrepopath.is_dir():
        write_error(f"A git repository with the name {gitname} is already in place in path {superconfig['config']['defaultpath']}")
        raise typer.Exit()
    write_info(f"Cloning repository {gitname} into {gitrepopath}")
    # recursion depth clone options
    repo = git.Repo.clone_from(giturl, str(gitrepopath), branch=branch)
    write_success(f"Successfully cloned repository {gitname} into {category}" if category != UNCATEGORIZED and subfolder else f"Successfully cloned repository {gitname}")
    # recursion depth clone options
    if recursive:
        repo.submodule_update(recursive=True)

    # TODO: try to parse README.md or .rst if one exists to get install information for pip or check if requirements.txt exists and install with pipenv
    # Q: chose environment prog (e.g. pipenv) in config file; if none defined chose pipenv as default?

    # POST cloning
    # TODO: add addition adjustment

    add_component(
        gitname,
        giturl,
        gitrepopath,
        branch=branch,
        recursive=recursive,
        subfolder=subfolder,
        custompath=custompath,
        category=category
    )

    commitmessage = f"Add cloned git repository {gitname}"
    if category:
        commitmessage += f" to {category}"
    save_superconfig(commitcontent=commitmessage)


@app.command()
def gitrelease(
    giturl: str,
    showdetails: bool = True,
    download: bool = False,
    install: bool = False,
    tag: str = None
):
    """
    Searches for releases of git url.
    """
    # TODO: check URL could be one of:
    # (https://github.com/SecureAuthCorp/impacket/releases, https://github.com/SecureAuthCorp/impacket, https://github.com/SecureAuthCorp/impacket.git)
    # TODO: handle <username>/<repo>
    # TODO: get latest 3 releases with details (date, description, attachment listing) and make them selectable by the user
    # url (latest): https://api.github.com/repos/<user>/<repo>/releases/latest
    # url (all): https://api.github.com/repos/<user>/<repo>/releases/latest
    # TODO: get user + repo out of URL
    gituserrepo = giturl
    api_url = "https://api.github.com/repos/{}/releases/latest".format(gituserrepo)
    releases_page = requests.get(api_url)
    print(releases_page.content)
    # TODO: check if only packed source code is available as attachment or also some release package
    # TODO: check if it is needed to extract (.zip, .7z, .tar.gz)
    # TODO: if installation is wanted by user: check after all if the content filetype is accepted (python installation or something like .whl)
    pass


@app.command()
def pip(
    pypackage: str
):
    """
    Installs a python package globally, tracked via pip.
    """
    # TODO: check if pip is callable via cmd (path is set to python `scripts`)
    # TODO: otherwise check if python path is configured
    # TODO: if one of both matches execute command with installation
    pass

# TODO: add path parameter to save file to
@app.command()
def urlfile(
    fileurl: str,
    category: str = UNCATEGORIZED,
    subfolder: bool = True,
    custompath: Path = typer.Argument(
        None,
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True
    )
):
    """
    Downloads a file, e.g. a PoC script to local filesystem.
    """
    global superconfig
    # TODO: check URL for existence
    # TODO: implement a logic to check for newer versions, e.g. by Didier Stevens:
    #   https://didierstevens.com/files/software/oledump_V0_0_53.zip # 52 is also avail, 54 also
    #   possible workflow:
    #   actual = 0.0.53
    #   try_1 = 0.0.54 --> if found, try until no "next" version is found
    #   try_2 = 0.1.0
    #   try_3 = 1.0.0
    #   additional = ask
    # TODO: check if filename contains version (maybe there is no versioning)
    # TODO: if no version provided ask for it or do no versioning, but then no automatic update is possible
    #       just checking the same URL for different content and save with date
    #       (maybe add a date when last checked for updates in config to all downloads)
    name_version_ending_string = fileurl.rsplit("/", 1)[1]
    name, version_ending_string = name_version_ending_string.split("_", 1)
    version_string, ending = version_ending_string.rsplit(".", 1)
    version = convert_versionstring(version_string)
    print(name, version, ending)
    file = requests.get(fileurl)
    # last_updated = now()
    print(file.status_code)
    # proof if file is available
    if file.status_code == 200:
        # print(file.content)
        basepath = superconfig["config"]["defaultpath"]
        # handle custom user path
        if custompath:
            check_path_create(custompath, ask=True)
            basepath = custompath
        # save file to corresponding path
        with open(basepath / name_version_ending_string, "w+") as downloadfile:
            downloadfile.write(file.content)

        # add component to config file
        add_component(
            name,
            urlfile,
            basepath,
            subfolder=subfolder,
            custompath=custompath,
            category=category,
            component_type=TYPES['urlfile'],
            version=version
        )

        commitmessage = f"Add urlfile of {name} with version "
        if category:
            commitmessage += f" to {category}"
        save_superconfig(commitcontent=commitmessage)
    # TODO: track file in config and include version number


@app.command()
def collect(
    filepath: Path = typer.Argument(
        None,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True
    ),
    category: str = UNCATEGORIZED,
    recursive: bool = False
):
    """
    Collects git tools in given path and adds to config file.
    """
    filepaths = []
    # actually searches only for a depth of one
    if recursive:
        for child in filepath.iterdir():
            childgitpath = child / GITENDING
            childgitpathconfig = childgitpath / "config"
            # checks if git directory points really to git
            # something like git-svn will be ignored
            if child.is_dir() and childgitpath.exists() and "[remote " in childgitpathconfig.read_text():
                filepaths.append(child)
    else:
        filepaths.append(filepath)
    # for filepath in filepaths:
    with typer.progressbar(filepaths, label="Processing path") as progress:
        for filepath in progress:
            write_verbose(f"Checking directory {filepath} for git repository")
            # TODO: need to check if tool and path not already in config!
            gitpath = filepath / GITENDING
            if not gitpath.exists():
                write_error(f"No git path found in {filepath}")
                raise typer.Abort()
            write_verbose(f"Git path {gitpath} found")
            repo = git.Repo(str(filepath))
            remote = repo.remote()
            repourl = remote.url
            branch = repo.active_branch.name
            reponame = get_gitname(repourl)
            # check if path could be reversed with defaultpath, category and subfolder to adjust add_component arguments
            subfolder = False
            if superconfig["config"]["defaultpath"] in filepath.parents and (category in filepath.parent or category is UNCATEGORIZED):
                subfolder = True
            # TODO: custompath not working if "/opt/" is used under linux/kali; check workflow
            add_component(
                reponame,
                repourl,
                filepath,
                branch=branch,
                subfolder=subfolder,
                custompath=filepath,
                category=category
            )
            write_info(f"Adding {reponame} to config")
            commitmessage = f"Add collected git repository {reponame}"
            if category:
                commitmessage += f" to {category}"
            save_superconfig(commitcontent=commitmessage)


@app.command()
def update(
    category: str = None,
    toolname: str = None
):
    """
    Updates all configured or a specified tool.
    """
    # TODO: search if the given tool/category exists in config file (if provided)
    # TODO: if nothing specified update all
    # git:(git pull + needed installation steps)
    # pip:(pip install --upgrade pypackage)
    # urlfile:(backup old file; requests.get(<fileurl>) and diff content, if same, delete backup)
    pass


@app.command()
def save():
    """
    Saves the current config to git (e.g. git push).
    """
    # TODO: check if local dir is git initialized and URL is provided for remote
    # TODO: do a commit if needed and push changes
    pass


@app.command()
def export(
    filepath: Path = typer.Argument(
        None,
        writable=True
    ),
    compress: bool = False
):
    """
    Exports the local config file to another path.
    """
    # TODO: check if local dir exists
    # TODO: if wanted compress the file
    pass


@app.command()
def restore(
    configpath: Path = typer.Argument(
        None,
        exists=True,
        file_okay=True,
        readable=True
    ),
    installpath: Path = typer.Argument(
        None,
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True
    ),
    url: str = None,
    category: str = None,
    toolname: str = None
):
    """
    Restores configs, categories and/or tools from given configs.
    """
    # TODO: match cases, where a git URL is provided or a general URL for file access/download e.g. from web server
    # TODO: proof if file exists
    # TODO: if exists, check if it is a valid config file (maybe check for mandatory attributes) --> maybe a function as it has to be used multiple times
    # TODO: if everything is fine, copy content to the local one
    if installpath is None:
        # installpath = superconfig["defaultpath"]
        pass
    tools, = get_all_tools()
    for i, tool in enumerate(tools):
        toolconfig, category = get_toolconfig(tool)
        # rearrange if conditions
        if "custompath" in toolconfig:
            if toolconfig["type"] == TYPES["git"]:
                # clone to custom path
                branch = "master"
                recursive = False
                if "branch" in toolconfig:
                    branch = toolconfig["branch"]
                if "recursive" in toolconfig:
                    recursive = True
                # subfolder = True if toolname in last path snippet
                # custompath = custompath or installpath, whereas installpath is more important
                clone(toolconfig["url"], branch, recursive, category, installpath)
                pass
        else:
            pass
            # clone to default path with category and check for subfolder
    # TODO: ask if imported tools should be downloaded and installed directly
    # TODO: if git, ask if the url should also be used for changes on local config to push to remote


@app.command()
def readme(
    toolname: str
):
    """
    Prints the markdown readme to the console.
    """
    toolconfig, toolcategory = get_toolconfig(toolname)
    if toolconfig:
        write_verbose(f"Found {toolname} in superconfig")
        if "custompath" in toolconfig:
            write_verbose(f"Custom path set for {toolname}")
            default_readme = Path(toolconfig["custompath"]) / "README.md"
        else:
            write_verbose(f"Default path used for {toolname}")
            toolpath = Path(superconfig["config"]["defaultpath"])
            if toolcategory:
                toolpath = toolpath / toolcategory
            default_readme = toolpath / toolname / "README.md"
        if default_readme.is_file():
            write_verbose(f"README file exists for {toolname}")
            with open(default_readme, 'r') as f:
                markdown_content = f.read()
            write_verbose(f"Converting and printing markdown to console")
            md = Markdown(markdown_content)
            console.print(md)


@app.command()
def wiki(
    toolname: str,
    openwebpage: bool = False
):
    """
    Tries to get online wiki of the tool (currently only GitHub supported).

    Checks the existence online, as the state may changes between cloning and wiki execution.
    Better than storing this value (exists/not exists) to the config.
    """
    toolconfig, toolcategory = get_toolconfig(toolname)
    if toolconfig:
        write_verbose(f"Found {toolname} in superconfig")
        if toolconfig["url"]:
            write_info(f"Searching for wiki of tool {toolname}")
            wikiurl = "{url}/{wikipath}".format(url=toolconfig["url"].replace(GITENDING, ""), wikipath="wiki")
            wikipage = requests.get(wikiurl, allow_redirects=False)
            # proof if wiki is activated for the repository
            # returns 200 if exists, 302 if not
            write_verbose(f"Wiki URL {wikiurl} returned status code {wikipage.status_code}")
            if wikipage.status_code == 200:
                write_info(f"Wiki exists for {toolname}")
                if openwebpage:
                    typer.launch(wikiurl)
                # TODO: list all wiki pages available online e.g. for mimikatz as good example
            else:
                write_info(f"Wiki does not exist for {toolname}")


@app.command()
def list(categorized: bool = False, category: str = None):
    """
    Lists all tools in config.
    """
    all_tools, categories = get_all_tools()
    write_info("The following tools are installed:")
    last_category = ""
    level = 1
    # Q: reenumerate if category output, otherwise the numbering may confuse?
    for i, tool in enumerate(all_tools):
        if category:
            if categories[i] == category:
                pass
        if categorized:
            if last_category != categories[i]:
                if category is None:
                    write_count(categories[i])
                last_category = categories[i]
            level = 2
        if category and (categories[i] == category) or category is None:
            write_count(tool, i, level)
        last_category = categories[i]


@app.command()
def search(searchtoolname: str):
    """
    Searches for toolname in superconfig.
    """
    all_tools, categories = get_all_tools()
    tool_matches = difflib.get_close_matches(searchtoolname, all_tools, n=5)
    if tool_matches:
        write_info("Found the following tools:")
        for i, tool in enumerate(tool_matches):
            write_count(tool, i)
    else:
        write_info("There was no matching tool found")


# with typer.progressbar(range(100)) as progress:
#   for value in progress:
#       pass
# with typer.progressbar(iterate_user_ids(), length=100) as progress:
# with typer.progressbar(range(100), label="Processing") as progress:

if __name__ == "__main__":
    app()
