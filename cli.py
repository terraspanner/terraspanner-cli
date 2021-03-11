from optparse import OptionParser
import os

default_git_user=os.getenv('GIT_USER')
default_git_token=os.getenv('GIT_TOKEN')
default_git_repo=os.getenv('GIT_REPO')
default_git_domain=os.getenv('GIT_DOMAIN')

def update_terraform_repo(args, options):
    print("update terraform repo", args, options)

commands = {
    "update": update_terraform_repo
}

def main():
    parser = OptionParser()
    parser.add_option('-u','--git-user', dest="user", help="git user", metavar="GIT_USER", default=default_git_user)
    parser.add_option('-t','--git-token', dest="token", help="git token", metavar="GIT_TOKEN", default=default_git_token)
    parser.add_option('-r','--git-repo', dest="repo", help="git repo", metavar="GIT_REPO", default=default_git_repo)
    parser.add_option('-d','--git-domain', dest="domain", help="git domain (ex. github.com)", metavar="GIT_DOMAIN", default=default_git_domain)
    (options, arguments) = parser.parse_args()
    command=arguments[0]
    command_args=arguments[1:len(arguments)]
    try:
        commands[command](command_args,options)
    except Exception as ex:
        print("command does not exist or failed with:", ex)

main()