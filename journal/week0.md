# Week 0 Billing and Architechture

### Diagrams 

[Logical Diagram](https://lucid.app/lucidchart/044d54be-c09b-4c09-a18f-f1ddf1b44387/edit?viewport_loc=-221%2C13%2C2261%2C1116%2C0_0&invitationId=inv_04dab94d-d5c4-4b5d-b7eb-eaa960765da1)
![Logical Diagram](./assets/Cruddur-Conceptual%20Diagram.png)

[Architectural Diagram](https://lucid.app/lucidchart/ec7097f7-4001-4f8b-999c-3e8081fcba10/edit?viewport_loc=-116%2C11%2C2261%2C1116%2C0_0&invitationId=inv_cef4b7df-11ee-41a9-8785-39c3bade6d48)
![Architetural Diagram](./assets/Crudder%20Logical%20Architectural%20Diagram.png)

###  User setup

MFA was created for IAM 

![IAM_MFA](./assets/IAM_MFA.png)


and *__the ROOT account__*

![ROOT_MFA](./assets/MAF_fin.png)

Created IAM user with Admin access, the ability to change their own password, and a *__security audit policy__* to track the users activity.

![IAM Polices](./assets/AdminPolicy.png)


Created *__organizations__* to manage any future accounts

![ORG_CART](./assets/Org_Chart.png)

Created two *__Service Control Policies (SCP)__* for an extra layer of security. The first prevents an account from removing itself from a organization and the second restricts IAM access.

![SCPs](./assets/SCP.png)

### System Setup

AWS CLI installation can be found in the .gitpod.yml file

```
tasks:
  - name: aws-cli
    env:
      AWS_CLI_AUTO_PROMPT: on-partial
    init: |
      cd /workspace
      curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
      unzip awscliv2.zip
      sudo ./aws/install
      cd $THEIA_WORKSPACE_ROOT
```

Check the status of the aws cli with gitpod
```
aws sts get-caller-identity
```

Output
```
{
    "UserId": "AIDAZM7LQBKLVCVL2PVKU",
    "Account": "########9143",
    "Arn": "arn:aws:iam::########9143:user/Crudder_user"
}
```

### Monitoring

Billing alarms were created using the CLI when price is at or above $1.00


![Billing_Alarm](./assets/bill_raw.png)

SNS topic was created using the CLI to receive the billing alarm
```
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-2:########9143:billing-alarm \
    --protocol email \
    --notification-endpoint $EMAIL
```
![SNS_topic](./assets/SNS_topic.png)

Budget is set at $1.00 using the CLI
```
aws budgets create-budget \
    --account-id $aws_ACCOUNT_ID \
    --budget file://aws/json/budget.json \
    --notifications-with-subscribers file://aws/json/notifications-with-subscribers.json
```
![Budget](./assets/Budget.png)

*__CloudTrail__* was set up to record the API calls in AWS and store the log files in an S3 Bucket
![Cloud_Trail](./assets/CloudTrail.png)

I subsequently deleted the CloudTrail log because it was using up a large portion of my free tier for S3 by storing log files.


### Challenges

[CI/CD Architectural Diagram](https://lucid.app/lucidchart/19a3aca2-8157-406d-a03c-b5e9d1d2c3c1/edit?viewport_loc=-268%2C-31%2C2261%2C1116%2C0_0&invitationId=inv_a18fe3aa-726c-4104-bba0-a6e70c66923e)
![CI/CD Diagram](./assets/CI_CD%20Diagram.png)



EC2 Health alert was created for the us-east-2 region with AWS eventbridge used to monitor EC2 heatlh and a SNS topic is used to notify me by email of the changes
![EC_2 Health](./assets/EC2_status.png)

Some applications may require an increase in the amount of resources AWS allows it to use.  This can be done by acessing the aws service quotas console. You can log in to your user account and a dashboard will display of all the curret services in use and their associated limits.  

[Service Quota Console](https://console.aws.amazon.com/servicequotas/home)


This console will display all the services being used by a particular account and describe each service and indicate its service limits.
![Service Quota Dashboard](./assets/Service_Console.png)

From this console you can request an increase to the service limits.
In the image below I have requested an increase in DynamoDB from 40000 read operations to 50000

![Request for Increase Service](./assets/DynamoDB_request.png)



### References

[Health Update](https://docs.aws.amazon.com/health/latest/ug/cloudwatch-events-health.html)

[CI/CD Diagram](https://github.com/acantril/learn-cantrill-io-labs/tree/master/aws-codepipeline-catpipeline)




