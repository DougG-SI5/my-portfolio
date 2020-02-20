import boto3
import io
import zipfile
import mimetypes

def lambda_handler(event, context):

    print ("Starting Portfolio Build")
    s3 = boto3.resource('s3')
    sns = boto3.resource("sns")
    topic = sns.Topic('arn:aws:sns:us-east-1:240467610569:deployedPortfolioTopic')

    topic.publish(Subject="Portfolio Code Deployment - Starting", Message="Portfolio published Starting.")

    location = {
        "bucketName": 'portfoliobuild.strategicintelligence5.info',
        "objectKey": 'portfolioBuild.zip'
    }

    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print ("Building portfolio from " + str(location))

        topic.publish(Subject="Portfolio Code Deployment - Note", Message="Building portfolio from " + str(location))

        portfolio_bucket = s3.Bucket('portfolio.strategicintelligence5.info')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                    ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        topic.publish(Subject="Portfolio Code Deployment - Success", Message="Portfolio published successfully.")
        if job:
            codepipeline = boto3.client("codepipeline")
            codepipeline.put_job_success_result(jobId=job["id"])

    except:
        topic.publish(Subject="Portfolio Code Deployment - Failure", Message="Portfolio publishing failed.  Fix it!")
        raise

    return "Import Completed"
    
