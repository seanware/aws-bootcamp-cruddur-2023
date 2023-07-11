# Week X Final Fixes

The goal is to get the application back into a working state and fix any other problems with the application. Also, the application frontend was hosted using aws static hosting service.

### Topics

- [Build Frontend](#build-frontend)
- [Sync Frontend](#sync-frontend)
- [Fix Backend](#fix-backend)
- [Connect Database](#connect-database)
- [Handle CORS](#handle-cors)
- [Create Activity Form](#create-activity-form)
- [CICD](#cicd)
- [JWT Refactor](#jwt-refactor)
- [Initialization Refactor](#initialization-refactor)
- [Routes Refactor](#routes-refactor)
- [Implement Replies](#implement-replies)
- [Error Handling](#error-handling)
- [Activity Page](#activity-page)
- [Message Button](#message-button)
- [Deploy to Production](#deploy-to-production)



### Build Frontend 

Moving from an ECS container to hosting the frontend with an s3 bucket and placing it behind cloudfront CDN will save costs.

The frontend needs to be compiled so it can be stored and served from the frontend bucket

create build script

bin/frontend/static-build

This script will contain npm run build

Modification to the code is required to get it to compile and try to remove as many errors as possible.

add '==='

align-items: flex-start

zip the contents of the build folder before it is downloaded.
```sh
zip -r build.zip build/
```

upload the build zip to the bucket via clickops 

drummer-test-app.online


### Sync Frontend

Sync the build folder from local developer environment with an S3 bucket

Install the sync tool "aws s3 website sync"

1. Create Gemfile and Rakefile at the top level

2. Install the gemfile
```sh
gem install aws_s3_website_sync
```
3. Create a Rakefile
```rb
aws-bootcamp-cruddur-2023/Rakefile
```
4. install dotenv gem

```sh
gem install dotenv
```
5. Sync data
```sh
bundle exec sync
```

Create a sync script in the bin directory

bin/frontend/sync

Create bucket related environment variables to be used by the sync script. This is done with a sync.env file and generated with erb files

sync.env.erb
Add the following env
- SYNC_S3_BUCKET
- SYNC_S3_BUCKET
- SYNC_BUILD_DIR
- SYNC_OUTPUT_CHANGESET_PATH
- SYNC_AUTO_APPROVE

Create a tmp/.keep directory and add it to the git repository
```sh
git add -f tmp/.keep
```

Update frontend env generation scripts to add sync env generation

```rb
require 'erb'

template = File.read 'erb/frontend-react-js.env.erb'
content = ERB.new(template).result(binding)
filename = "frontend-react-js.env"
File.write(filename, content)

template = File.read 'erb/sync.env.erb'
content = ERB.new(template).result(binding)
filename = "sync.env"
File.write(filename, content)
```

Create frontend sync tool bin/frontend/sync

Make a change to the frontend to test the sync tool

Build the new frontend and run the sync tool


### Fix Backend

The backend need to be rebuilt so it is not in debug mode, which is a security issue for the site. However, there is an issue with the app.py code where the version needs to be updated.


Build a new backend image and push it

Register the new image

Make a superficial change to the service template to update and execute the new changeset.

To rollback fargate state the service must not be running so set the desired tasks to 0.

Change CICD template and remove the cross referenced stack tear down service independently 

Deploy changes

```yaml
 #Remove cross stack to eliminate dependencies
                ServiceName: backend-flask
                #  Fn::ImportValue:
                #    !Sub ${ServiceStack}ServiceName
```

Delete Backend service stack

Add the production docker file to the docker-compose.yml
```yaml
build:
    context: ./dir
    dockerfile: Dockerfile.prod
```

Alter app.py code and 

```py
with app.app_context():
```

build new production image with deploy scripts

push the new image to the aws ecr

*__Setup Envs for Cors__*

Alter the config.toml file for the service to use the URL parameters
```toml
EnvFrontendUrl = 'https://drummer-test-app.online'
EnvBackendUrl = 'https://api.drummer-test-app.online'
```

Alter the service deployment script to accept the parameters

```sh

PARAMETERS=$(cfn-toml params v2 -t $CONFIG_PATH)

--parameter-overrides $PARAMETERS \
```

Deploy update to the backend service



### Connect Database

Connect the postgres database to the backend service

Change the PROD_ CONNECTION_URL variable

Open the 5432 port in the Security Group CrdDBRDSG
- Description : GITPOD
- Type : PostgreSQL
- Port Range : 5432
- Source : MyIP


set the DB_SG_ID
```sh
export DB_SG_ID="sg-0998932038573####"
gp env DB_SG_ID="sg-0998932038573####"
```

set the DB_SG_RULE_ID
```sh
export DB_SG_RULE_ID="sgr-0310cdca92744####"
gp env DB_SG_RULE_ID="sgr-0310cdca927442####"
```

Set the GITPOD_ID

run the update_sg_rule script


*__Load the schema__*
  

```sh
./bin/db/db-schema-load prod
```

Run the migration script using the production connection URL

```sh
CONNECTION_URL=$PROD_CONNECTION_URL ./bin/db/migrate
```

Clear all cognito users and sign-up to the app


Create a Single page application on cloudFront

update the frontend cloudformation template.yaml to redirect to https

```yaml
 SslSupportMethod: sni-only
        CustomErrorResponses:
          - ErrorCode: 403
            ResponseCode: 200
            ResponsePagePath: /index.html
```

Change the connection_url in the lambda function to the new value

Create a security group for the lambda that connects to the RDS
- CognitoLambdaSG

Add inbound rule te the RDS security group
- Type : PosgrestSQL
- 
- COGNITO POST

modify lambda function

### Handle CORS

```toml
[parameters]
EnvFrontendUrl = 'https://drummer-test-app.online'
EnvBackendUrl = 'https://api.drummer-test-app.online'

```


### Create Activity Form

Work in the development db environment.

Alter the create activities route

Alter app.py to infer the message creation from the other user and remove hardcoding.

Modify the create_activity.py and create_message.py function

Modify the create.sql file to take the cognito_user_id

use bin/db/kill_all script to drop users

run db_setup to setup the development database

### CICD

Since the backend has changed it is a good idea to update the cicd pipeline so it can continue to function with the cloudformation changes made previously.

Modify the cicd config.toml file and add the full GithubRepo name

```toml
GithubRepo = 'seanware/aws-bootcamp-cruddur-2023'
```

Get the name of the codebuild project and add it to the codebuild.yaml file.

Add batch get build permissions to the template.yaml

```yaml
codebuild:BatchGetBuilds
```

Add bucket permissions to the template.yaml file
```yaml
- PolicyName: !Sub ${AWS::StackName}S3ArtifactAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Action:
                - s3:*
                Effect: Allow
                Resource:
                  - !Sub arn:aws:s3:::${ArtifactBucketName}
                  - !Sub arn:aws:s3:::${ArtifactBucketName}/*

```

Also add bucket permissions to the codebuild.yaml file
```yaml
- PolicyName: !Sub ${AWS::StackName}S3ArtifactAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Action:
                - s3:*
                Effect: Allow
                Resource:
                  - !Sub arn:aws:s3:::${ArtifactBucketName}
                  - !Sub arn:aws:s3:::${ArtifactBucketName}/*
```

Add string reference to the codebuild.yaml file
```yaml
ArtifactBucketName:
    Type: String
```

override the buildspec.yml location using the template.yaml file
```yaml
 Parameters:
        ArtifactBucketName: !Ref ArtifactBucketName
        BuildSpec: !Ref BuildSpec
```

set the path of the buildspec.yml file in the config.toml file
```toml
BuildSpec = 'backend-flask/buildspec.yml'
```

Deploy the new cicd cloudformation stack

Create new pull request at github

base:prod 

compare: main

Create and merge the pull request

On the AWS management console Release change


### JWT refactor

Add replies functionality to the cruddur app

Modify the ReplyForm.js to close popups

```js
const close = (event)=> {
    if (event.target.classList.contains("reply_popup")) {
      props.setPopped(false)
    }
  }

....

<div className="popup_form_wrap reply_popup" onClick={close}>
```


Add a replies endpoint in the backend by using a JWT decorator function. This will simplify the codebase by allowing for code reuse

modify the cognito_jwt_token.py by adding a jwt decorator

```py
jwt_required
```

modify the app.py file and add a defualt home feed funtion
```py
def default_home_feed(e):
  # unauthenicatied request
  app.logger.debug(e)
  app.logger.debug("unauthenicated")
  data = HomeActivities.run()
  return data, 200
```


### Initialization Refactor

The code for app.py has some redundancies that can be refactored for easy maintenance.


Import the app into the cognito_jwt_token.py file

```py
from flask import current_app as app
```

Add logged_in logic to the HomeFeedPage.js

Factor out rollbar functionality to its own file

lib/rollbar.py

Factor out aws-xray functionality to its own file

lib/xray.py

Factor out honeycomb OTEL functionality to its own file

lib/honeycomb.py

Factor out CORS functionality to its own file

lib/cors.py

Factor out CloudWatch functionality to its own file

lib/cloudwatch.py


### Routes Refactor

Break the routes up into separate routes to make code management easier.  

Alter the docker-compose file to use the development docker file.
```yaml
services:
  backend-flask:
    env_file:
      - backend-flask.env
    build:
      context:  ./backend-flask
      dockerfile: Dockerfile
```

Create a routes folder in the backend-flask folder

/routes

create an activities file

routes/activities.py

Factor out the routes that are related to activities and move them to the routes/activities.py file


Create a helpers file to handle the model json

lib/helpers.py

Factor out the routes that are related to the users ad move them to a new file

routes/users.py


Factor out the routes that are relate to the massages and move them to a new file.

routes/messages.py


Factor out the health check and move it to a general file

routes/general.py


### Implement Replies

The reply feature is implemented using by creating routes in the app backend

Modify the ReplyForm.js to stop using local storage and add message passing functionality.

```js
body: JSON.stringify({
          activity_uuid: props.activity.uuid,
          message: message
        }),
```
Add authentication to the jwt_required token
```py
from functools import wraps, partial

def jwt_required(f=None, on_error=None):
    if f is None:
        return partial(jwt_required, on_error=on_error)

    @wraps(f)
    def decorated_function(*args, **kwargs):
        cognito_jwt_token = CognitoJwtToken(
            user_pool_id=os.getenv("AWS_COGNITO_USER_POOL_ID"), 
            user_pool_client_id=os.getenv("AWS_COGNITO_USER_POOL_CLIENT_ID"),
            region=os.getenv("AWS_DEFAULT_REGION")
        )
        access_token = extract_access_token(request.headers)
        try:
            claims = cognito_jwt_token.verify(access_token)
            # is this a bad idea using a global?
            g.cognito_user_id = claims['sub']  # storing the user_id in the global g object
        except TokenVerifyError as e:
            # unauthenticated request
            app.logger.debug(e)
            if on_error:
                on_error(e)
            return {}, 401
        return f(*args, **kwargs)
    return decorated_function
```

Modify create_reply to remove the user handle

Add flask custom validation


Create reply sql schema to store the reply messages in the postgres database

sql/activities/reply.sql

Modify ActivityActionReply.js and add access 

Modify create_reply.py 

Generate migration to update the schema and change uuid from integer to string

```sh
./bin/generate/migration reply_to_activity_uuid_to_string
```

Remove hardcoding in the migration generation file

backend-flask/bin/generate/migration

```py
migration = {klass}Migration
```

Add replies column to home schema

/db/sql/activities/home.sql

```sql
(SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
  SELECT
    replies.uuid,
    reply_users.display_name,
    reply_users.handle,
    replies.message,
    replies.replies_count,
    replies.reposts_count,
    replies.likes_count,
    replies.reply_to_activity_uuid,
    replies.created_at
  FROM public.activities replies
  LEFT JOIN public.users reply_users ON reply_users.uuid = replies.user_uuid
  WHERE
    replies.reply_to_activity_uuid = activities.uuid
  ORDER BY  activities.created_at ASC
  ) array_row) as replies
```

modify rollback file and cast file_time to str

Modify migration file to run migrations when file_time is greater than last successful run

./bin/db/migrate

Modify ActivityContent.js to change the content wrap of the activities

Add .replies and .activity_item css to the ActivityItem.css

Modify ActivityFeed.js to add check for a reply and change the activityfeed styling.

Create a show query for activities

backend-flask/db/sql/activities/show.sql



### Error Handling

Handling errors on the frontend react app to assist users when interacting with the application. Changes were made to all frontend forms.


Add error handling to ReplyForm.js
```js
setErrors: setErrors
```

Create a new component to render errors

FormErrors.js

Create a new component to render a single error

FormErrorItem.js

Modify the fetch functionality in ActivityForm.js to catch error responses

Factor out the fetching functionality and create a Request.js file and update all fetches on the frontend that fetch from the backend.

lib/Request.js 

Modify ReplyForm.js to factor out repetitive code

Modify MessageForm.js and add post request functionality

Modify SigninPage.js to add form errors 

```js
<FormErrors errors={errors} />
```

Modify SignupPage.js to add form errors 


### Activity Page

Alter te db migrations file to add a reply to activity uuid file

```sql
ALTER TABLE activities ADD COLUMN reply_to_activity_uuid uuid;
```
Update activityContent.js  and ActivityContent.css to display links to the display name and handle name.


Modify the ActivityActionReply.js, like.js,  to prevent default events

Create ActivityShow.js and ActivityShow.css to show activities on a page.

Create a component to handle the replies functionality called Replies.js and Replies.css which borrows from the activity feed.

Modify ActivityShowPage.js to add replies and activity items


Add a new show activities route is the users.py file
```py
@app.route
```

Create a new service that will show activities

services/show_activity.py
```py
sql = db.template('activities', 'show')
results = db.query_array_json(sql.{
 'uuid':activity_uuid
})
return results
```

Modify show.sql to turn activities output into an array

Refactor the Authentication functionality of the request.js lib

Modify the update profile.py to use the query object json function 

Remove link from ActivityItem.js and change to click event to redirect
```js
```

Alter the useHistory function the useNavigate function in the ActivityItem.js

Modify ActivityShowPage.js

Modify ActivityItem.js to change the datetime format

Modify DateTimeFormat.js to update minutes posted to the future.

*__Migrations__*

drop database

./bin/db/kill-all

Modify the migrations file to provide more information at the console and only compare changes to the last successful run.



### Message Button

Implement the message button on the app frontend

Update seed data to add another record

seed.sql

```sql

```

Add back button to the show page on ActivityShowPage.js

```js
```

Create CSS for the back div at ActivityShowPage.css


### Deploy to Production

Deploy the final app to production


Test the production database to see if it is up to date

Run db migrations against production database after

```sh
CONNECTION_URL=$PROD_CONNECTION_URL ./bin/db/migrate
```
Make sure replies can be created.

Roll out backend changes to production

Create pull request and merge main into prod

base: prod  <- compare: main

Build and Sync the Frontend

./bin/frontend/static-build

Modify the changeset variable in the erb file

./bin/frontend/sync


Connect to the dynamodb table

modify the ddb.py file to get the table name from envs

```py
table_name = os.getenv("DDB_MESSAGE_TABLE")
```

Set the env in the backend-flask.env.erb file

```erb
DDB_MESSAGE_TABLE=
```

Add DDBMessageTable to the service CloudFormation Template



Test the connection in the dev environment

Update the template with the new envs

.

Merge the changes into prod and update codepipeline

Create a new user with cloudformation with permission to read and write from dynamodb


cfn/machine-user/template.yaml

```yaml
```

cfn/machine-user/config.toml

create deploy script for the machine-user

./bin/cfn/machineuser

Generate Security Credentials for the machine user cli via click ops 

and add the values to the 
/cruddur/backend-flask/AWS_ACCESS_KEY_ID in parameter store

Trigger codepipeline to pull in new parameters via click ops Release Change

Delete values from the production dynamo database.

Clear values from AWS Cognito 


Execute changeset


### Update CruddurAvatarUpload 

The lambda function that loads the images used for the application

REACT_APP_URL_GATEWAY_ENDPOINT = https://ubkd1i4ebc.execute-api.us-east-2.amazonaws.com



