# Week 6 Deploying Containers

### Set up ECR

*Add container healthchecks*

The backend was given a health-check at api/health-check
```py
@app.route('/api/health-check')
def health_check():
    return {'success': True}, 200
```

A script was create to test the heath of the service in the container
```py
import urllib.request

try:
  response = urllib.request.urlopen('http://localhost:4567/api/health-check')
  if response.getcode() == 200:
    print("[OK] Flask server is running")
    exit(0) #Success = 0
  else:
    print("[BAD] Flask server is not running")
    exit(1) #Failure
except Exception as e:
  print(e)
  exit(1)
```

Another script was create to test the connection to the RDS instance
```py
import psycopg
import os
import sys

connection_url = os.getenv("CONNECTION_URL")

conn = None
try:
  print('attempting connection')
  conn = psycopg.connect(connection_url)
  print("Connection successful!")
except psycopg.Error as e:
  print("Unable to connect to the database:", e)
finally:
  conn.close()
```

### Setup ECS Cluster
*Create a CloudWatch log group*
```sh
aws logs create-log-group --log-group-name cruddur
aws logs put-retention-policy --log-group-name cruddur --retention-in-days 1
```

*Create Cruddur cluster*


Must login before pushing or pulling containers from ECR

```sh
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
```

Create security group for the cluster
```sh
export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

*Build python Container*

Python base image was placed the AWS ECR because Dockerhub may have technical issues

Set ecr environmental variables for AWS ECR for the python base image
```sh
export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"
echo $ECR_PYTHON_URL
```

*Build Production Containers*

Production containers were created with more security and and performance in mind

A Dockerfile.prod was created to pull python from the ECR and and disable the ports

Pull, Tag and Push image to AWS ECR
```sh
docker pull python:3.10-slim-buster

docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster

docker push $ECR_PYTHON_URL:3.10-slim-buster
```

Create Dockerfile.prod to  be used for production for the Backend

This file uses the ECR python image and makes the app more secure
```sh
FROM 646349589143.dkr.ecr.us-east-2.amazonaws.com/cruddur-python:3.10-slim-buster
...
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--no-debug","--no-debugger","--no-reload"]
```

Set ECR environmental variables AWS ECR for the backend
```sh
export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
```

Build , Tag and Push the backend-flask-prod image to AWS ECR
```sh
docker build -f "Dockerfile.prod" -t backend-flask-prod "."

docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest

docker push $ECR_BACKEND_FLASK_URL:latest
```

The Fronted Dockerfile.prod was create and to included and nginx server

A [nginx.conf](https://github.com/seanware/aws-bootcamp-cruddur-2023/blob/main/frontend-react-js/nginx.conf) file was included in the frontend directory

The environmental variables are loaded as arguments to the [Dockerfile.prod](https://github.com/omenking/aws-bootcamp-cruddur-2023/blob/week-6-fargate/frontend-react-js/Dockerfile.prod)

Set ECR environmental variables AWS ECR for the backend
```sh
export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
```

Build, Tag and Push the frontend-react-js-prod to AWS ECR
```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="https://api.drummer-test-app.online" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="us-east-2_Dz6W2ZQu2" \
--build-arg REACT_APP_CLIENT_ID="2h2hh4qoh8us0skksr4ailpq0t" \
-t frontend-react-js-prod \
-f "$FRONTEND_REACT_JS_PATH/Dockerfile.prod" \
"$FRONTEND_REACT_JS_PATH/."

docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest

docker push $ECR_FRONTEND_REACT_URL:latest
```


### Set up Fargate


*Set up AWS Parameter Store*

Parameter store is a low-cost way to store and use secrets on AWS
```sh
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID" --value $AWS_ACCESS_KEY_ID
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY" --value $AWS_SECRET_ACCESS_KEY
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/CONNECTION_URL" --value $PROD_CONNECTION_URL
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" --value $ROLLBAR_ACCESS_TOKEN
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" --value "x-honeycomb-team=$HONEYCOMB_API_KEY"
```

*Set up Task Roles*

CrudderServiceExecutionRole was created for 
```sh
aws iam create-role \
    --role-name CruddurServiceExecutionRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"
```

Create Task policies

```sh
aws iam create-role --role-name CruddurServiceExecutionPolicy --assume-role-policy-document file://aws/json/policy/service-assume-role-execution-policy.json

aws iam put-role-policy   --policy-name CruddurServiceExecutionPolicy   --role-name CruddurServiceExecutionRole   --policy-document file://aws/json/policy/service-execution-policy.json

```

Attach Role policies
```sh
aws iam attach-role-policy --policy-arn POLICY_ARN --role-name CruddurServiceExecutionRole

aws iam attach-role-policy \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    --role-name CruddurServiceExecutionRole
```

Create Task Roles
```sh
aws iam create-role \
    --role-name CruddurTaskRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"

aws iam put-role-policy \
  --policy-name SSMAccessPolicy \
  --role-name CruddurTaskRole \
  --policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[
      \"ssmmessages:CreateControlChannel\",
      \"ssmmessages:CreateDataChannel\",
      \"ssmmessages:OpenControlChannel\",
      \"ssmmessages:OpenDataChannel\"
    ],
    \"Effect\":\"Allow\",
    \"Resource\":\"*\"
  }]
}
"
```

Attach Task Roles
```sh
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess --role-name CruddurTaskRole
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess --role-name CruddurTaskRole
```


*Create Task Definitions*

The [Backend](https://github.com/seanware/aws-bootcamp-cruddur-2023/blob/main/aws/task-definitions/backend-flask.json) and [Frontend](https://github.com/seanware/aws-bootcamp-cruddur-2023/blob/main/aws/task-definitions/frontend-react-js.json) task definitions are json files that contains the configuration of the container used for each task. They also contain the health-checks, environmental variables and secrets 

*Create Services*

The [Backend](https://github.com/seanware/aws-bootcamp-cruddur-2023/blob/main/aws/json/service-backend-flask.json) and [Frontend](https://github.com/seanware/aws-bootcamp-cruddur-2023/blob/main/aws/json/service-frontend-react-js.json) service definitions are json files that contain the network configuration for the tasks to create services for ECS

Register task definitions
```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json

aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json
```

Create Security groups for the ECS services
```sh
export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

Connect to RDS by editing the inbound rules
 ```sh
 aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $CRUD_SERVICE_SG \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=BACKENDFLASK}]'
 ```

 Create or update the services
 ```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json

aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
 ```

 Added Session Manager to manage AWS ECS

 ```sh
 curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
 ```

The session manager commands were added to the gitpod.yml file

*Connect to Containers*


The backend container runs bash so the execute command needs bash
```sh
aws ecs execute-command  \
--region $AWS_DEFAULT_REGION \
--cluster cruddur \
--task $TASK_ID \
--container  $CONTAINER_NAME \
--command "/bin/bash" \
--interactive
```

The fronted container does not run bash
```sh
aws ecs execute-command  \
--region $AWS_DEFAULT_REGION \
--cluster cruddur \
--task $TASK_ID \
--container  $CONTAINER_NAME \
--command "/bin/sh" \
--interactive
```


### Refactor local development scripts

*Move bin to top level*

Utility scripts we moved to the top level

*Generate environment variables*

A ruby script was created to generate environment variables for the docker containers use .env files.


Backend envs generation
```rb
require 'erb'

template = File.read 'erb/backend-flask.env.erb'
content = ERB.new(template).result(binding)
filename = "backend-flask.env"
File.write(filename, content)
```

Frontend envs generation
```rb
require 'erb'

template = File.read 'erb/frontend-react-js.env.erb'
content = ERB.new(template).result(binding)
filename = "frontend-react-js.env"
File.write(filename, content)
```

The docker-compose.yml file was modified to work wth the generated env files.







