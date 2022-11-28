import typer
import re

APP_NAME = "superscript"
DEFAULT_CONFIG = "superconfig.yml"

POS = typer.style("[+] ", fg=typer.colors.GREEN, bold=True)
INF = typer.style("[*] ", fg=typer.colors.WHITE, bold=True)
NEG = typer.style("[-] ", fg=typer.colors.RED, bold=True)
VRB = typer.style("[~] ", fg=typer.colors.CYAN)
QST = typer.style("[?] ", fg=typer.colors.YELLOW)
CNT = "{}[{}] "

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
GITDEFAULTBRANCH = "main"

TYPES = {
    "git": "git",
    "gitrelease": "gitrelease",
    "urlfile": "urlfile"
}