# superscript

## Commands

`++` means partly implemented
`+++` means fully implemented

### Initialization

```bash
# initializes an emtpy repo in the current directory for config storage and sync
+++ superscript
# saves the current config to git (e.g. git push)
superscript save
# exports the config file to another directory
superscript export /path/to/export/dir/
```

```bash
# restores from config files
#superscript restore --path /opt/superscript/
# load config file from local file
superscript restore --configpath /opt/superscript/
superscript restore --configpath /opt/superscript/superconfig.yml
superscript restore --url https://domain.de/superscript/superconfig.yml
superscript restore --git https://domain.de/username/mysuperconfig.git

# restore only one category (this will also only add this category to the config file)
superscript restore --category Tunneling --configpath /opt/config --installpath /opt/Tunneling
# restore only one tool
superscript restore --toolname Tooli --configpath /opt/Tunneling
```

```bash
# searches for `.git` directories in the subfolder to add already cloned tools
# gets URL from git remote config
+++ superscript collect --path /opt/cme
# searches recursively for tools to add in all subfolders (will most probably find multiple)
+++ superscript collect --path /opt/ --recursive
# ask for each found which category it should be appended to (maybe list of existing categories each time? - selectable with numbers)
superscript collect --path /opt/ --recursive --ask-category
```

```bash
# updates all tracked software
superscript update
# updates the tools in the category
superscript update --category SMB
# updates one software by name
superscript update --name SSF
```

```bash
+++ superscript clone https://github/user/repo
+++ superscript clone https://github/user/repo --category Test
#superscript clone https://github/user/repo -c category --clone-options "--recursive-depth 2"
+++ superscript clone https://github/user/repo --category Test --recursive
```

```bash
# install options, install and execution
superscript clone https://github/user/repo --install-options "pip install dependancy-1" --install-options "pip install tool-itself"
# creates pipenv for the specified tool
superscript clone https://github/user/repo --install-options "pip install dependancy-1" --install-options "pip install tool-itself" --pipenv
# runs the tool in the desired pipenv, if set in the config file
superscript execute tool
```

```bash
superscript gitrelease https://github.com/user/SSF
superscript gitrelease https://github.com/user/SSF pre-release

superscript pip roadrecon

superscript urlfile https://server/path/file.ending
```

```bash
# shows/gets wiki page link and displays in browser
+++ superscript wiki SSF
# will open the link directly in default browser
+++ superscript wiki SSF --open

# https://rich.readthedocs.io/en/latest/markdown.html
# print the formatted markdown README.md file in the console
+++ superscript readme SSF
```

```bash
# search for tools; prints config/path or some execution stuff
+++ superscript search SSF

# lists all configured tools
+++ superscript list
+++ superscript list --categorized
+++ superscript list --category Tunneling
```

## ADDITIONAL

1. implement `restore` command
2. implement `update` command

* think of a version with a version pattern depending from given string, so that a new version could be inserted / replaced
* think of objects?! --> e.g. get_toolconfig should return the corresponding object (e.g. GitObject for a git repo)
* check if path/folder/file of tool really exists before doing anything (don't trust config file only)
* write testcases
* check for [Path.read_text](https://docs.python.org/3/library/pathlib.html#pathlib.Path.read_text) instead of with open file as...
* CLI Arguments to [typer Options](https://typer.tiangolo.com/tutorial/options/name/)
* [autocompletion](https://typer.tiangolo.com/tutorial/options/autocompletion/) for categories on CLI
* [PW Protected](https://typer.tiangolo.com/tutorial/options/password/) git repo or release
* categoryfolder (boolean) to store the tools based on categories in folders

default linux path: `~/.config/superscript`

`yaml details: {} = "content" ; [] = "- content"`

```yaml
config:
    path: "/opt/superscript"
    autosave: true # autosaves if changes occur

software:
    Tunneling:
        SSF:
            URL: "https://github.com/user/SSF.git"
            Type: git                                    # specifies git as git could be used for version control (e.g. git pull <URL>)
            Wiki: "https://securesocketfunneling.github.io/ssf/#home"
            Path: "/opt/SSF"
            Install:                        # execute from path as working directory
                - "pip install roadlib/"
                - "pip install roadrecon/"
    Test:
        SSF:
            URL: "https://github.com/user/SSF"
            Type: gitrelease                             # specifies to download latest release instead of the repo for install / executeable
            State: "stable"                   # only install latest stable
            Path: "/opt/SSFexec"
            Install:
                - "openssl dhparam 4096 -outform PEM -out dh4096.pem"
                - "echo '[ v3_req_p ]\nbasicConstraints = CA:FALSE\nkeyUsage = nonRepudiation, digitalSignature, keyEncipherment' > extfile.txt"
                - "openssl req -x509 -nodes -newkey rsa:4096 -keyout ca.key -out ca.crt -days 3650"
                - "openssl req -newkey rsa:4096 -nodes -keyout private.key -out certificate.csr"
                - "openssl x509 -extfile extfile.txt -extensions v3_req_p -req -sha1 -days 3650 -CA ca.crt -CAkey ca.key -CAcreateserial -in certificate.csr -out certificate.pem"
    Microsoft365:
        roadrecon:
            Type: pip3
```
