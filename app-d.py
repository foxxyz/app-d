#!/usr/bin/env python
from getpass import getpass
from os.path import expanduser
from paramiko import SSHConfig, SSHClient, AutoAddPolicy


class Server:
    "Wrapper for a remote server"

    def __init__(self, hostname):
        self.hostname = hostname
        ssh_config = SSHConfig()
        ssh_config.parse(open(expanduser('~/.ssh/config')))
        self.info = ssh_config.lookup(self.hostname)
        try:
            self.user = self.info['user']
        except KeyError:
            raise KeyError('Your SSH Config is missing! Ensure an entry is present for {} in ~/.ssh.config'.format(self.hostname))
        self._client = None
        self.password = getpass('Server user password: ')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.connection.close()
        self._client = None

    @property
    def connection(self):
        if self._client:
            return self._client
        self._client = SSHClient()
        # Important! This is vulnerable to MITM attacks, but unfortunately the
        # only way to deal with ECDSA keys until paramiko is patched
        # See https://github.com/paramiko/paramiko/pull/473
        self._client.set_missing_host_key_policy(AutoAddPolicy())
        self._client.connect(self.info['hostname'], username=self.info['user'], password=self.password or None, key_filename=self.info.get('identityfile'))
        return self._client

    def run(self, command, include_input=None):
        stdin, stdout, stderr = self.connection.exec_command(command)
        if include_input:
            stdin.write(include_input)
            stdin.flush()
        # Abort on errors
        errors = stderr.readlines()
        if errors:
            raise Exception('\n'.join(errors))
        return '\n'.join(stdout.readlines())

    def sudo(self, command):
        return self.run('sudo -S -p "" {}'.format(command), '{}\n'.format(self.password))


if __name__ == '__main__':
    app_name = input('Name of app: ')
    server_name = input('Hostname to deploy on: ')
    group_name = input('Group to use [{}]: '.format(app_name)) or app_name

    # Get deploy directory
    default_deploy_dir = '/opt/{}/'.format(app_name)
    deploy_dir = input('Directory to deploy in [{}]: '.format(default_deploy_dir)) or default_deploy_dir

    # Get directory to put remote repo in
    default_repo_dir = '/opt/{}_remote/'.format(app_name)
    repo_dir = input('Directory to deploy in [{}]: '.format(default_repo_dir)) or default_repo_dir

    # Connect to server
    server = Server(server_name)

    with server:
        # Create group
        print('Adding group `{}`...'.format(group_name))
        server.sudo('groupadd {}'.format(group_name))

        # Add user to group
        print('Adding yourself (`{}`) to group `{}`...'.format(server.user, group_name))
        server.sudo('usermod -a -G {} {}'.format(group_name, server.user))

    # We log in again here to ensure the group permissions are set per the last command
    with server:
        # Create remote repo dir
        print('Creating remote repo directory at `{}`...'.format(repo_dir))
        server.sudo('mkdir {}'.format(repo_dir))

        # Update permissions
        print('Setting directory group to `{}`...'.format(group_name))
        server.sudo('chown :{} {}'.format(group_name, repo_dir))
        print('Adding ACL permissions for group propagation...')
        server.sudo('setfacl -m d:g:{0}:rwx,g:{0}:rwx,d:m:rwx {1}'.format(group_name, repo_dir))
        print('Adding setgid...')
        server.sudo('chmod g+ws {}'.format(repo_dir))

        # Create app dir
        print('Creating application directory at `{}`...'.format(deploy_dir))
        server.sudo('mkdir {}'.format(deploy_dir))

        # Update permissions
        print('Setting directory group to `{}`...'.format(group_name))
        server.sudo('chown :{} {}'.format(group_name, deploy_dir))
        print('Adding ACL permissions for group propagation...')
        server.sudo('setfacl -m d:g:{0}:rwx,g:{0}:rwx,d:m:rwx {1}'.format(group_name, deploy_dir))
        print('Adding setgid...')
        server.sudo('chmod g+ws {}'.format(deploy_dir))

        # Create bare repo
        print('Creating bare git repository in `{}`...'.format(repo_dir))
        server.run('cd {} && git init --bare'.format(repo_dir))

        # TODO - Select & install post-receive hook

    remote_path = '{}:{}'.format(server_name, repo_dir)
    print('Done! You can now add a new git remote {}:'.format(remote_path), end="\n\n")
    print("\tgit remote add public {}".format(remote_path), end="\n\n")
