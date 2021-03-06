from optparse import OptionParser
import os
import tempfile
from git import Repo
from python_terraform import *
import logging
import json
import re
import copy

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

tf = Terraform()

default_git_user=os.getenv('GIT_USER')
default_git_token=os.getenv('GIT_TOKEN')
default_git_repo=os.getenv('GIT_REPO')
default_git_domain=os.getenv('GIT_DOMAIN')

def tf_plan(arguments, options):
    path=arguments[0]
    return_code, stdout, stderr = tf.plan(path, 
        compact_warnings = options.compact_warnings,
        destroy = options.destroy,
        detailed_exitcode = options.detailed_exitcode,
        lock = options.lock,
        no_color = options.no_color,
        lock_timeout = options.lock_timeout,
        out = options.out,
        state = options.state,
        parallelism = options.parallelism,
        refresh = options.refresh,
        target = options.target,
        var_file = options.var_file,
        var={var.split()[0] : var.split()[1] for var in options.var} if options.var is not None else None
        )
    if stdout is not None:
        logging.info(stdout)
    if return_code != 0:
        raise Exception(stderr)

def tf_apply(arguments, options):
    path=arguments[0]
    return_code, stdout, stderr = tf.plan(path, 
        auto_approve = options.auto_approve,
        backup = options.backup,
        state_out = options.state_out,
        compact_warnings = options.compact_warnings,
        lock = options.lock,
        no_color = options.no_color,
        lock_timeout = options.lock_timeout,
        state = options.state,
        parallelism = options.parallelism,
        refresh = options.refresh,
        target = options.target,
        var_file = options.var_file,
        var={var.split()[0] : var.split()[1] for var in options.var}
        )
    if stdout is not None:
        logging.info(stdout)
    if stderr is not None:
        raise Exception(stderr)

def try_get_target_from_commit(local_repo_path):
    try:
        repo = Repo(local_repo_path)
        last_commit_message = repo.head.commit.message
        if "[terraspanner]" not in last_commit_message:
            return None
        parameters=json.loads(last_commit_message[len("[terraspanner]")+1:len(last_commit_message)-2])
        return parameters['target']
    except Exception as ex:
        logging.debug(ex)
        return None

def try_get_var_from_commit(local_repo_path):
    try:
        repo = Repo(local_repo_path)
        last_commit_message = repo.head.commit.message
        if "[terraspanner]" not in last_commit_message:
            return None
        parameters=json.loads(last_commit_message[len("[terraspanner]")+1:len(last_commit_message)-2])
        return parameters['var']
    except Exception as ex:
        logging.debug(ex)
        return None

tf_commands = {
    'plan': tf_plan,
    'apply': tf_apply
}

def run_tf_command(arguments, options):
    if options.target is None:
        options.target = try_get_target_from_commit(options.local_repo_path)
    if options.var is None:
        options.var = try_get_var_from_commit(options.local_repo_path)
    command=arguments[0]
    command_arguments=arguments[1:len(arguments)]
    tf_commands[command](command_arguments, options)

def validate_trigger_terraform_repo(options):
    if options.token is None or options.domain is None or options.repo is None:
        raise Exception('some parameters are missing')

def trigger_terraform_repo(_, options):
    validate_trigger_terraform_repo(options)
    with tempfile.TemporaryDirectory() as temp_repo_dir:
        git_url=f'https://{options.token}@{options.domain}/{options.repo}.git'
        repo = Repo.clone_from(git_url, temp_repo_dir)
        repo.git.commit('--allow-empty','-m', f'"[terraspanner]{json.dumps({ "target": options.target, "var": options.var })}"')
        repo.git.push()

commands = {
    'trigger': trigger_terraform_repo,
    'tf': run_tf_command
}

def main():
    parser = OptionParser()
    #trigger options
    parser.add_option('-t','--git-token', dest='token', help='git token', metavar='GIT_TOKEN', default=default_git_token)
    parser.add_option('-d','--git-domain', dest='domain', help='git domain (ex. github.com)', metavar='GIT_DOMAIN', default=default_git_domain)
    parser.add_option('-r','--git-repo', dest='repo', help='git repo (ex. )', metavar='GIT_DOMAIN', default=default_git_domain)
    #repo finder
    parser.add_option('-l','--local-repo-path', dest='local_repo_path', help='local repository path (defaults to local folder)', metavar='GIT_DOMAIN', default=os.getcwd())
    #terraform plan options
    parser.add_option('--compact-warnings', dest='compact_warnings', action='store_true', help='If Terraform produces any warnings that are not accompanied by errors, show them in a more compact form that includes only the summary messages.')
    parser.add_option('--destroy', dest='destroy', action='store_true', help='If set, a plan will be generated to destroy all resources managed by the given configuration and state.')
    parser.add_option('--detailed-exitcode', dest='detailed_exitcode', action='store_true', help='return detailed exit codes when the command exits.')
    parser.add_option('--lock', dest='lock', action='store_true', help='Lock the state file when locking is supported.')
    parser.add_option('--no-color', dest='no_color', action='store_true', help='If specified, output won\'t contain any color.')
    parser.add_option('--lock-timeout', dest='lock_timeout', help='Duration to retry a state lock.', metavar='TF_LOCK_TIMEOUT')
    parser.add_option('--out', dest='out', help='Write a plan file to the given path. This can be used as input to the "apply" command.', metavar='TF_OUT')
    parser.add_option('--state', dest='state', help='Path to a Terraform state file to use to look up Terraform-managed resources. By default it will use the state "terraform.tfstate" if it exists.', metavar='TF_STATE')
    parser.add_option('--parallelism', dest='parallelism', help='Limit the number of concurrent operations. Defaults to 10.', metavar='TF_PARALLELISM')
    parser.add_option('--refresh', dest='refresh', action='store_true', help='Update state prior to checking for differences.', metavar='TF_REFRESH')
    parser.add_option('--target', dest='target', action='append', help='Resource to target. Operation will be limited to this resource and its dependencies. This flag can be used multiple times.', metavar='TF_TARGET')
    parser.add_option('--var', dest='var', action='append', help='Set a variable in the Terraform configuration. This flag can be set multiple times.', metavar='TF_VAR')
    parser.add_option('--var-file', dest='var_file', help='Set variables in the Terraform configuration from a file.', metavar='TF_VAR_FILE')    
    #terraform apply options
    parser.add_option('--auto-approve', dest='auto_approve', action='store_true', help='Skip interactive approval of plan before applying.', default=True)
    parser.add_option('--backup', dest='backup', help='Path to backup the existing state file before modifying. Defaults to the "-state-out" path with ".backup" extension. Set to "-" to disable backup.')
    parser.add_option('--state-out', dest='state_out', help='Path to write state to that is different than "-state". This can be used to preserve the old state.')
    # parser.add_option('--compact-warnings', dest='compact_warnings', action='store_true', help='If Terraform produces any warnings that are not accompanied by errors, show them in a more compact form that includes only the summary messages.')
    # parser.add_option('--lock', dest='lock', action='store_true', help='Lock the state file when locking is supported.')
    # parser.add_option('--no-color', dest='no_color', action='store_true', help='If specified, output won\'t contain any color.')
    # parser.add_option('--lock-timeout', dest='lock_timeout', help='Duration to retry a state lock.', metavar='TF_LOCK_TIMEOUT')
    # parser.add_option('--state', dest='state', help='Path to a Terraform state file to use to look up Terraform-managed resources. By default it will use the state \"terraform.tfstate\" if it exists.', metavar='TF_STATE')
    # parser.add_option('--parallelism', dest='parallelism', help='Limit the number of concurrent operations. Defaults to 10.', metavar='TF_PARALLELISM')
    # parser.add_option('--refresh', dest='refresh', action='store_true', help='Update state prior to checking for differences.', metavar='TF_REFRESH')
    # parser.add_option('--target', dest='target', action='append', help='Resource to target. Operation will be limited to this resource and its dependencies. This flag can be used multiple times.', metavar='TF_TARGET')
    # parser.add_option('--var', dest='var', action='append', help='Set a variable in the Terraform configuration. This flag can be set multiple times.', metavar='TF_VAR')
    # parser.add_option('--var-file', dest='var_file', help='Set variables in the Terraform configuration from a file.', metavar='TF_VAR_FILE')
    (options, arguments) = parser.parse_args()
    command=arguments[0]
    command_args=arguments[1:len(arguments)]
    try:
        commands[command](command_args,options)
    except Exception as ex:
        logging.error('command does not exist or failed with:', ex)

main()