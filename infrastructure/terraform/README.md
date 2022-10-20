## Terraform

### Requirements
- terraform
- ansible-playbook

Create a new public-private keypair used to establish connection between EC2 instance and ansible.
```
ssh-keygen -t rsa
```

### Credentials handling

insert your credentials into the `iac/terraform/set_variables.sh` and run `source iac/terraform/set_variables.sh`

### 1. Provision Services via Terraform

Run
```
cd iac/terraform
terraform init
terraform plan
```
if okay, run
```
terraform apply -auto-approve
```
and follow the instructions to apply the `main.tf` script.


### 2. Configure provisioned services with ansible
### Run playbook manually
```
ansible-playbook -i ansible/hosts ansible/playbooks/setup-ubuntu.yml
```

to receive the public IPv4 DNS run:
```
terraform output -raw eip_public_dns
```

on port 3000 you should get output of database


### SSH into provisioned EC2 machine:
You need to generate a private key pem file in order to be able to ssh into your instance. 
After generation of the key, you need to set the a env variable to point to the path as follows:
```
export TF_VAR_private_key="<path/to/your/private/key.pem>"
```
> This is needed before even running `terraform apply`

```
ssh -i $TF_VAR_private_key ubuntu@$(terraform output -raw eip_public_dns)
```

#### Connect to postgresql inside ec2
```
source setup_environment.sh
PGPASSWORD="hashicorp" psql --host=$DB_DOCKER --port=5432 --username=postgres --dbname=qtrees
```

### Rollback provisioned services if not needed anymore

Run
```
terraform destroy
```
