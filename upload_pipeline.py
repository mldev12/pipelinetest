import re
import requests
from urllib.parse import urlsplit
from kfp import Client, compiler
from kfp.dsl import pipeline
import time
import json
from seldon import *

def get_istio_auth_session(url: str, username: str, password: str) -> dict:
    """
    Determine if the specified URL is secured by Dex and try to obtain a session cookie.
    WARNING: only Dex `staticPasswords` and `LDAP` authentication are currently supported
             (we default default to using `staticPasswords` if both are enabled)

    :param url: Kubeflow server URL, including protocol
    :param username: Dex `staticPasswords` or `LDAP` username
    :param password: Dex `staticPasswords` or `LDAP` password
    :return: auth session information
    """
    # define the default return object
    auth_session = {
        "endpoint_url": url,    # KF endpoint URL
        "redirect_url": None,   # KF redirect URL, if applicable
        "dex_login_url": None,  # Dex login URL (for POST of credentials)
        "is_secured": None,     # True if KF endpoint is secured
        "session_cookie": None  # Resulting session cookies in the form "key1=value1; key2=value2"
    }

    # use a persistent session (for cookies)
    with requests.Session() as s:

        ################
        # Determine if Endpoint is Secured
        ################
        resp = s.get(url, allow_redirects=True)
        if resp.status_code != 200:
            raise RuntimeError(
                f"HTTP status code '{resp.status_code}' for GET against: {url}"
            )

        auth_session["redirect_url"] = resp.url

        # if we were NOT redirected, then the endpoint is UNSECURED
        if len(resp.history) == 0:
            auth_session["is_secured"] = False
            return auth_session
        else:
            auth_session["is_secured"] = True

        ################
        # Get Dex Login URL
        ################
        redirect_url_obj = urlsplit(auth_session["redirect_url"])

        # if we are at `/auth?=xxxx` path, we need to select an auth type
        if re.search(r"/auth$", redirect_url_obj.path): 
            
            #######
            # TIP: choose the default auth type by including ONE of the following
            #######
            
            # OPTION 1: set "staticPasswords" as default auth type
            redirect_url_obj = redirect_url_obj._replace(
                path=re.sub(r"/auth$", "/auth/local", redirect_url_obj.path)
            )
            # OPTION 2: set "ldap" as default auth type 
            # redirect_url_obj = redirect_url_obj._replace(
            #     path=re.sub(r"/auth$", "/auth/ldap", redirect_url_obj.path)
            # )
            
        # if we are at `/auth/xxxx/login` path, then no further action is needed (we can use it for login POST)
        if re.search(r"/auth/.*/login$", redirect_url_obj.path):
            auth_session["dex_login_url"] = redirect_url_obj.geturl()

        # else, we need to be redirected to the actual login page
        else:
            # this GET should redirect us to the `/auth/xxxx/login` path
            resp = s.get(redirect_url_obj.geturl(), allow_redirects=True)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"HTTP status code '{resp.status_code}' for GET against: {redirect_url_obj.geturl()}"
                )

            # set the login url
            auth_session["dex_login_url"] = resp.url

        ################
        # Attempt Dex Login
        ################
        resp = s.post(
            auth_session["dex_login_url"],
            data={"login": username, "password": password},
            allow_redirects=True
        )
        if len(resp.history) == 0:
            raise RuntimeError(
                f"Login credentials were probably invalid - "
                f"No redirect after POST to: {auth_session['dex_login_url']}"
            )

        # store the session cookies in a "key1=value1; key2=value2" string
        auth_session["session_cookie"] = "; ".join([f"{c.name}={c.value}" for c in s.cookies])

    return auth_session


import kfp

KUBEFLOW_ENDPOINT = "http://10.110.210.217:80"
KUBEFLOW_USERNAME = "user@example.com"
KUBEFLOW_PASSWORD = "12341234"

auth_session = get_istio_auth_session(
    url=KUBEFLOW_ENDPOINT,
    username=KUBEFLOW_USERNAME,
    password=KUBEFLOW_PASSWORD
)

print(auth_session["session_cookie"])
client = kfp.Client(host=f"{KUBEFLOW_ENDPOINT}/pipeline", cookies=auth_session["session_cookie"], namespace="kubeflow-user-example-com")
#print(client.list_experiments())

    # Attempt to upload and run the pipeline
# uploaded_pipeline = client.upload_pipeline(pipeline_package_path, pipeline_name='income-pipeline2')
run = client.create_run_from_pipeline_package("income.yaml", arguments={}, namespace="kubeflow-user-example-com")
run_id = run.run_id

# Wait for the pipeline run to complete
try:
    final_status = client.wait_for_run_completion(run_id, 36000)
    print("Here we are!!")
    get_run_response = client.get_run(run_id=run_id)
    print("This is the run id", run_id)
    print(get_run_response)
    final_state = get_run_response.state
    print("Here we end!!")
    #run_status = getattr(getattr(get_run_response, "run"), "status")
    #print(f"Run completed with status: {status}")
except TimeoutError as e:
    print(str(e))

# If the run was successful, retrieve and handle outputs
if final_state == "SUCCEEDED":
    # Fetch run details or specific component outputs as required
    run_result = client.get_run(run_id)
    # Assuming a V2 engine, artifacts are stored under task details. You may need to adjust based on your SDK version.
    # Inspect run_details
    #print(dir(run_detail))
if hasattr(run_result, 'run_details'):
    print("Run Details:")
    print(run_result.run_details)

# Inspect pipeline_spec
if hasattr(run_result, 'pipeline_spec'):
    print("Pipeline Spec:")
    print(run_result.pipeline_spec)




import boto3
from botocore.client import Config

# Configuration variables
endpoint_url = 'http://10.105.239.157:9000'  # Change this to your MinIO server's URL
access_key = 'minio'                   # Your access key
secret_key = 'minio123'                   # Your secret key
bucket_name = 'mlpipeline'                     # Bucket name
object_key = f'v2/artifacts/price-adjustment-pipeline/{run_id}/train-model/output_artifact'  # Object key in the bucket

# Create a MinIO client
client = boto3.client('s3',
                      endpoint_url=endpoint_url,
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key,
                      config=Config(signature_version='s3v4'),
                      region_name='us-east-1')  # Adjust the region if necessary

# Function to get and print the content of the file
def read_and_print_file(bucket, key):
    try:
        # Fetch the object from MinIO
        response = client.get_object(Bucket=bucket, Key=key)
        # Read the content of the file
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        print("Error accessing MinIO: ", e)

# Read and print the file content
print("This is the s3 endpoint")
model_uri = read_and_print_file(bucket_name, object_key)
print("This is model uri", model_uri)

generate_kubernetes_yaml(model_uri, run_id)

