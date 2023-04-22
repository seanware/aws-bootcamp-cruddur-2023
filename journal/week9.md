# Week 9 — CI/CD with CodePipeline, CodeBuild and CodeDeploy

*Motivations*

Continuos Integration and Continuos Development was implemented to ease the deployment of features to the application.  The first portion of the application that was automated was the backend flask app.  When the CI/CD pipeline is triggered the backend-flask docker container is updated in the Elastic Container Repository, which automatically updates AWS Fargate.

### Codepipeline Console

AWS Codepipeline was used to load and deploy the code from the Github repository containing the application

The name of the pipeline is cruddur-backend-fargate

When initially creating the pipeline all default options were accepted

*Add Source stage*

The Source stage fetches the code from the github repo and loads it into AWS
