1. Copy public key to server
$ ssh-copy-id -i ~/.ssh/id_rsa.pub dev@<server_ip/host>

2. Install requirements
$ pip install -r ansible/requirements.txt

3. cd to ansible directory
$ cd ansible/

4. Deploy latest code to server
$ ansible-playbook playbooks/app.yml -e "server=dev" -t "deploy"

5. Provision
$ ansible-playbook playbooks/app.yml -e "server=dev"