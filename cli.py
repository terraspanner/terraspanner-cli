from optparse import OptionParser
import os
import tempfile
from git import Repo

TOKEN="token"
DOMAIN="domain"
REPO="repo"

default_git_user=os.getenv('GIT_USER')
default_git_token=os.getenv('GIT_TOKEN')
default_git_repo=os.getenv('GIT_REPO')
default_git_domain=os.getenv('GIT_DOMAIN')

def validate_update_terraform_repo(options):
    if options[TOKEN]=None or options[DOMAIN]=None or options[REPO]=None:
        raise Exception("some parameters are missing")

def update_terraform_repo(args, options):
    validate_update_terraform_repo(options)
    with tempfile.TemporaryDirectory() as temp_repo_dir:
        git_url=f"https://{options[TOKEN]}@{options[DOMAIN]}/{options[REPO]}.git"
        print("update terraform repo", args, options)
        repo = Repo.clone_from(git_url, temp_repo_dir)
        repo.git.commit('-m', '[terraspanner]')
        repo.git.push('origin', branch)

commands = {
    "update": update_terraform_repo
}

def main():
    parser = OptionParser()
    parser.add_option('-t','--git-token', dest=TOKEN, help="git token", metavar="GIT_TOKEN", default=default_git_token)
    parser.add_option('-d','--git-domain', dest=DOMAIN, help="git domain (ex. github.com)", metavar="GIT_DOMAIN", default=default_git_domain)
    parser.add_option('-r','--git-repo', dest=REPO, help="git repo (ex. )", metavar="GIT_DOMAIN", default=default_git_domain)
    (options, arguments) = parser.parse_args()
    command=arguments[0]
    command_args=arguments[1:len(arguments)]
    try:
        commands[command](command_args,options)
    except Exception as ex:
        print("command does not exist or failed with:", ex)

main()