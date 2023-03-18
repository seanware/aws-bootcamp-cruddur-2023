# Week 4 --- Postgres and RDS

### Objectives
Almost all modern web applications have a database that persists data.  This has been historically done using a SQL based database like postgres.  It provides a wide array of functionality and a common query language that is used across different database implementations.
AWS has a service call Relational Database

### Create RDS postgres database for production

I used AWS RDS to create a postgres database instance for our backend.

To create this instance we used the aws cli utility because the console constantly makes changes making it difficult to understand how to properly create and instance.

The command was
```sh
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username cruddurroot \
  --master-user-password ############ \
  --allocated-storage 20 \
  --availability-zone us-east-2a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection
```

![RDS.png](./assets/RDS.png)


*Security Group and Inbound Rules*

The RDS instance needs to be put into our VPC which requires the creation of a security group.  The inbound rules are set to port 5432 which is the default postgres port and the RDS source is set to the GITPOD IP.

To get the GITPOD_IP, you run the command
```sh
GITPOD_IP=$(curl ifconfig.me)
```

Because the IP changes every time the workspace is loaded and script needs to be run that changes the security group and inbound rules on startup.

```sh
aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"

```






### Create local postgres development environment

I install the necessary packages for local Postgres development and change the inbound rules of the RDS instance to be able to properly connect to it.



*psql*

We install postgres in our gitpod workspace through our .gitod.yml
```yml
 - name: postgres
    init: |
      curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
      echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
      sudo apt update
      sudo apt install -y postgresql-client-13 libpq-dev
```

I need to be able to connect to the local and RDS instances of our databases and to do this we used connections URLs for the dev and productions environments

```sh
#local instance
CONNECTION_URL="postgresql://postgres:password@localhost:5432/cruddur"

#production instance
PROD_CONNECTION_URL="postgresql://cruddurroot:###########@cruddur-db-instance.ctrhhf######.us-east-2.rds.amazonaws.com:5432/cruddur"

```

Connecting to the database with psql requires running

```sh
psql CONNECTION_URL
```

*Interact with the database instances*

I created SQL files to create, drop and load the schema of the database instances

SQL files
1. schema.sql
2. seed.sql

The schema.sql file is used to crate the database both locally and in production.  It creates a table for users and activities and generates a universal unique identifier to obscure the number of users in our database.
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS public.users;

DROP TABLE IF EXISTS public.activities;

CREATE TABLE public.users (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  display_name text NOT NULL,
  handle text NOT NULL,
  email text NOT NULL,
  cognito_user_id text NOT NULL,
  created_at TIMESTAMP default current_timestamp NOT NULL
);

CREATE TABLE public.activities (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_uuid UUID NOT NULL,
  message text NOT NULL,
  replies_count integer DEFAULT 0,
  reposts_count integer DEFAULT 0,
  likes_count integer DEFAULT 0,
  reply_to_activity_uuid integer,
  expires_at TIMESTAMP,
  created_at TIMESTAMP default current_timestamp NOT NULL
);
```


We created bash scripts to interact with the local and production database instances 

Bash scripts
- db-create
- db-drop
- db-schema-load
- db-connect
- db-seed
- db-setup
- db-sessions

The bash scripts db-create, db-schema-load, and db-connect are able to be used on the local and production databases.  These scripts are modified with the following code.

```sh
if [ "$1" = "prod" ]; then
   echo "Production Database"
   URL=$PROD_CONNECTION_URL
else
   echo "Local development"
   URL=$CONNECTION_URL
fi
```

The db-schema-load script has to be able to access the schema.sql file and this is done with the following code
```sh
schema_path="$(realpath .)/db/schema.sql"
```  
This code reads the path of the file and loads it into the script.

### Install postgres functionality in python

*Install python postgres driver*

The backend of the applications needs to be able to interact with the postgres database. To do this we install the psycopg[binary]  psycopg[pool]

I added the two libraries to requirements.txt file for the backend application.

The connection to the database is established by passing in the connection url
```py
connection_url = os.getenv("CONNECTION_URL")
```

We used connection pooling in postgres to make accessing our database more efficient.
Connection pooling refers to the method of creating a pool of connections and caching those connections so that it can be reused again[1]

This is implemented in the db.py file
```py
from psycopg_pool import ConnectionPool
...
self.pool = ConnectionPool(connection_url)
```

To execute commands in the database a cursor must be created to interact with the instance.
```py
with self.pool.connection() as conn:
        cur =  conn.cursor()
        cur.execute(sql,params)
```

I use a context manager to automatically close the connection when done.











### Implement lambda function for sign-up


When a user signs-up to use the Cruddur app we need to save the user information in the database automatically. To do this we used a lambda function with a trigger set to cognito sign-up

I store our lambda locally in the aws/lambda locally then copy the file to the AWS console for deployment. In the future we may setup a CI/CD process to make lambda development easier.

*Add psycopg2*

For the lambda function we are required to use psycopg2 and to load it we have to add a layer install the drivers

Use the arn below
```sh
arn:aws:lambda:us-east-2:898466741470:layer:psycopg2-py38:1
```

*Add permissions*

The lambda function needs to be added to the security group and have permissions added to allow it to access the database in our VPC

I created a new role called AWSlambdaVPCAccessexEcutionRole

Adding this role to the lambda will grant it access to the RDS instance
```json
{
"Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:DeleteNetworkInterface",
        "ec2:DescribeInstances",
        "ec2:AttachNetworkInterface"
      ],
      "Resource": "*"
    }
  ]
}
```
 
### Endpoint refactoring

I had to modify are create_activity and home_activity endpoints to fetch data from the database.  To do this we create a db.py file in the lib that creates a connection to the database, insert messages into the database and later display them.  

I created sql files to perform the loading and fetching of data from the database because using sql is more efficient than using an object relational mapper (ORM).

Files

1. create.sql
2. object.sql
3. home.sql

The create.sql file loads the user data into the database and returns the uuid in one action.
```sql
INSERT INTO public.activities (
  user_uuid,
  message,
  expires_at
)
VALUES (
  (SELECT users.uuid 
    FROM public.users 
    WHERE users.handle = %(handle)s
    LIMIT 1
  ),
  %(message)s,
  %(expires_at)s
) RETURNING uuid;
```
The RETURNING uuid is the command that returns


To be able to get the root path in a flask app the following code had to be imported
```py
from flask import current_app as app
...
app.root_path
```

The following functions were added to create_activity.py to save and show messages
```py
 def create_activity(handle, message, expires_at):
    print("Create Handle")
    print(handle)
    sql = db.template('activities','create')
    uuid = db.query_commit(sql,{
      'handle': handle,
      'message': message,
      'expires_at': expires_at
    })
    return uuid

  def query_object_activity(uuid):
    sql = db.template('activities','object')
    return db.query_object_json(sql,{
      'uuid': uuid
    })
```

home_activity.py was modified with the following function that fetching from the database
```py
sql = db.template('activities', 'home')
results = db.query_array_json(sql)
```

*Troubleshooting*

When running the application it was discovered that the previous engineers hardcoded the user_handle with their name and it needed to be changed for the program to operate.

![messages](./assets/messages.png)


### Extras

I modified the lambda function to sanitize the input of the sql queries using postggres built-in execution syntax.

```py
 VALUES(
            %(user_display_name)s,
            %(user_emails)s,
            %(user_handle)s,
            %(user_cognito_id)s
            )
....
            params = {
        'user_display_name' : user['name'],
        'user_emails' : user['email'],
        'user_handle' : user['preferred_username'],
        'user_cognito_id' : user['sub']
      }
```




### References

[1] https://www.ashnik.com/everything-you-need-to-know-about-connection-pooling-in-postgres/

