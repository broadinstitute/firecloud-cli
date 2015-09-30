#!/usr/bin/env python
################################################################################
# methods_repo.py
# 
# A CLI providing convenient access to the FireCloud methods repository REST API.
#
# author: Bradt
# contact: dsde-engineering@broadinstitute.org
# 2015
# 
# Run 
#  methods_repo -h to get usage info
#
# Must authenticate via gcloud first, you can check by running 'gcloud auth list' 
# first and seeing if there is a credentialled account, and if not login using
# 'gcloud auth login'
#
# NOTES:
# 
# Supports the push, get-by-reference, and list methods
# Supports both configurations and workflows
#
# 
################################################################################


from oauth2client.client import GoogleCredentials
from oauth2client.client import AccessTokenRefreshError
import httplib2

from argparse import ArgumentParser
import os, sys, tempfile, subprocess
import getpass
import json


global_error_message = """    ******************************************************************************
* ERROR: Unable to access your google credentials.                           *
*                                                                            *
* This is most often caused by either                                        *
*     (a) not having gcloud installed (see https://cloud.google.com/sdk/)    *
*     (b) gcloud is not logged in (run 'gcloud auth login')                  *
******************************************************************************"""

def fail(message):
    print message
    sys.exit(1)

def get_endpoint(configurations, methods):
    if configurations:
        return "/configurations"
    elif methods:
        return "/methods"
    else:
        fail("No appropriate endpoint specified")

def get_push_namespace(namespace):
    if namespace:
        return namespace
    else:
        return getpass.getuser() 

def get_push_name(name, payloadFile):
    if name:
        return name
    else:
        base = os.path.basename(payloadFile)
        return os.path.splitext(base)[0]

def get_push_documentation(docsFile):
    if docsFile:
        print docsFile
        return read_entire_file(docsFile)
    else:
        return ""

# Read the entire contents of the payload file, removing leading/trailing whitespace.
# Performing no validation (methods repo api handles this)
def read_entire_file(inputFile):
    with open(inputFile) as myInput:
        return myInput.read().strip()

# Bring up a text editor to solicit user input for methods post.
# First line of user text is synopsis, rest is documentation.
# Lines starting with # are ignored.
# Mimics git commit functionality
def get_user_synopsis():
    EDITOR = os.environ.get('EDITOR','vim')
    initial_message = "\n# Provide a 1-sentence synopsis (< 80 charactors) in your first line. Subsequent lines are ignored"
    lines = []
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmpfile:
        tmpfile.write(initial_message)
        tmpfile.flush()
        subprocess.call([EDITOR, tmpfile.name])
        with open(tmpfile.name) as userinPut:
            lines = userinPut.readlines()
    
    synopsis = lines[0].strip()
    if len(synopsis) > 80:
        fail("[ERROR] Synopsis must be < 80 charactors")
    return synopsis


def httpRequest(baseUrl, path, insecureSsl, method, requestBody, expectedReturnStatus):
    http = httplib2.Http(".cache", disable_ssl_certificate_validation=(not insecureSsl))

    # get the credentials for the google proxy using the application default, which
    # is described at 
    # https://developers.google.com/identity/protocols/application-default-credentials#howtheywork
    #
    # Most often, this is obtained from the users current 'gcloud' credentials
    try:
        credentials = GoogleCredentials.get_application_default()
        http = credentials.authorize(http)
        headers = {'Content-type':  "application/json"}
        response, content = http.request(
            uri=baseUrl + path,
            method=method,
            headers=headers,
            body=requestBody
        )
    except AccessTokenRefreshError as atre:
        fail(global_error_message)
    except Exception as e:
        print e
        fail("Could not connect to {0}{1} with method {2}".format(baseUrl,path, method))

    if response.status != expectedReturnStatus:
        message = ("[ERROR] HTTP request failed\n"
                   "Request URL: " + path + "\n"
                   "Request body:\n"
                   + str(requestBody) + "\n"
                   "Response:\n"
                   + str(response.status) + " " + response.reason + " " + content
                  )
        fail(message)
    return content

# Performs the actual content POST. Fails on non-201(created) responses.
def entity_post(baseUrl, endpoint, insecureSsl, namespace, name, synopsis, documentation, entityType, payload):
    path = endpoint
    addRequest = {"namespace": namespace, "name": name, "synopsis": synopsis, "documentation": documentation, "entityType": entityType, "payload": payload}
    requestBody = json.dumps(addRequest)
    return httpRequest(baseUrl, path, insecureSsl, "POST", requestBody, 201)

# Perform the actual GET using namespace, name, snapshotId
def entity_get(baseUrl, endpoint, insecureSsl, onlyPayload, namespace, name, snapshot_id):
    path = endpoint + "/" + namespace + "/" + name + "/" + str(snapshot_id)
    if onlyPayload:
        path = path + "?onlyPayload=true"
    return httpRequest(baseUrl, path, insecureSsl,  "GET", None, 200)

# Perform the actual GET to list entities filtered by query-string parameters
def entity_list(baseUrl, endpoint, insecureSsl, queryString):
    path = endpoint + queryString
    return httpRequest(baseUrl, path, insecureSsl,  "GET", None, 200)

# Perform the actual DELETE using namespace, name, snapshotId
def entity_redact(baseUrl, endpoint, insecureSsl, namespace, name, snapshot_id):
    path = endpoint + "/" + namespace + "/" + name + "/" + str(snapshot_id)
    return httpRequest(baseUrl, path, insecureSsl,  "DELETE", None, 200)

# Given program arguments, including a payload file, pushes content
def push(args):
    endpoint = get_endpoint(args.configurations, args.methods)
    namespace = get_push_namespace(args.namespace)  
    name = get_push_name(args.name, args.PAYLOAD_FILE)
    documentation = get_push_documentation(args.docs)   
    payload = read_entire_file(args.PAYLOAD_FILE)
    synopsis = args.synopsis
    if synopsis is None:
        synopsis = get_user_synopsis()
    push_response = entity_post(args.firecloudUrl, endpoint, args.insecureSsl, namespace, name, synopsis, documentation, args.entityType, payload)
    print "Succesfully pushed. Reponse:"
    print push_response

# Given program args namespace, name, id: pull a specific method
def pull(args):
    endpoint = get_endpoint(args.configurations, args.methods)
    print entity_get(args.firecloudUrl, endpoint, args.insecureSsl, args.onlyPayload, args.NAMESPACE, args.NAME, args.SNAPSHOT_ID)

# Given the program arguments, query the methods repository for a filtered list of methods
def list_entities(args):
    baseUrl = args.firecloudUrl
    insecureSsl = args.insecureSsl
    endpoint = get_endpoint(args.configurations, args.methods)
    queryString = "?"
    if args.includedFields:
        for field in args.includedFields:
            queryString = queryString + "includedField=" + field + "&"
    if args.excludedFields:
        for field in args.excludedFields:
            queryString = queryString + "excludedField=" + field + "&"
    excludedFields = args.excludedFields
    args = args.__dict__
    
    knownArgs = ['func','methods','configurations','excludedFields','includedFields','firecloudUrl','insecureSsl']
    trimmedArgs = {key: value for key, value in args.iteritems() if args[key] and key not in knownArgs}
    for key, value in trimmedArgs.iteritems():
        queryString = queryString + key + "=" + value + "&"
    queryString = queryString.rstrip("&")
    if queryString == '?':
        queryString = ''

    print entity_list(baseUrl, endpoint, insecureSsl, queryString)

# Given program args namespace, name, id: redact a specific method
def redact(args):
    endpoint = get_endpoint(args.configurations, args.methods)
    print entity_redact(args.firecloudUrl, endpoint, args.insecureSsl, args.NAMESPACE, args.NAME, args.SNAPSHOT_ID)

def main():
    # The main argument parser
    parser = ArgumentParser(description="CLI for accessing the FireCloud methods repository.")

    # Core application arguments
    parser.add_argument('-u', '--url', dest='firecloudUrl', default='https://firecloud.dsde-dev.broadinstitute.org/service/api', action='store', help='Firecloud API location. Default is https://firecloud.dsde-dev.broadinstitute.org/service/api')
    parser.add_argument('-k', '--insecure', dest='insecureSsl', default='False', action='store_true', help='use insecure ssl (allow self-signed certificates)')
    
    endpoint_group = parser.add_mutually_exclusive_group(required=True)
    endpoint_group.add_argument('-c', '--configurations', action='store_true', help='Operate on task-configurations, via the /configurations endpoint')
    endpoint_group.add_argument('-m', '--methods', action='store_true', help='Operate on tasks and workflows, via the /methods endpoint')    
    subparsers = parser.add_subparsers(help='FireCloud Methods Repository actions')
    
    # POST arguments
    push_parser = subparsers.add_parser('push', description='Push a method to the FireCloud Methods Repository', help='Push a method to the FireCloud Methods Repository')
    push_parser.add_argument('-s', '--namespace', dest='namespace', action='store', help='The namespace for method addition. Default value is your user login name')
    push_parser.add_argument('-n', '--name', dest='name', action='store', help='The method name to provide for method addition. Default is the name of the PAYLOAD_FILE.')
    push_parser.add_argument('-d', '--documentation', dest='docs', action='store', help='A file containing user documentation. Must be <10kb. May be plain text. Marking languages such as HTML or Github markdown are also supported')
    push_parser.add_argument('-t', '--entityType', dest='entityType', action='store', help='The type of the entities you are trying to get', choices=['Task', 'Workflow', 'Configuration'], required=True)
    push_parser.add_argument('-y', '--synopsis', dest='synopsis', action='store', help='The synopsis for the entity you are pushing')
    push_parser.add_argument('PAYLOAD_FILE', help='A file containing the payload. For configurations, JSON. For tasks + workflows, the method description in WDL')
    push_parser.set_defaults(func=push)
    
    # GET (namespace/name/id) arguments
    pull_parser = subparsers.add_parser('pull', description='Get a specific method snapshot from the FireCloud Methods Repository', help='Get a specific method snapshot from the FireCloud Methods Repository')
    pull_parser.add_argument('-o', '--onlyPayload', dest='onlyPayload', action='store_true', help='Get only the payload for the method of interest (ie the WDL or configuration JSON)')
    pull_parser.add_argument('NAMESPACE', action='store', help='The namespace for the entity you are trying to get')
    pull_parser.add_argument('NAME', action='store', help='The name of the entity you are trying to get')
    pull_parser.add_argument('SNAPSHOT_ID', type=int, action='store', help='The snapshot-id of the entity you are trying to get')
    pull_parser.set_defaults(func=pull)
    
    # GET (query-paremeters) arguments
    list_parser = subparsers.add_parser('list', description='List methods in the FireCloud Methods Repository based on metadata', help='List methods in the FireCloud Methods Repository based on metadata')
    list_parser.add_argument('-f', '--includedFields', dest='includedFields', nargs='*', action='store', help='Any specific metadata fields you wish to be included in the response entities')
    list_parser.add_argument('-e', '--excludedFields', dest='excludedFields', nargs='*', action='store', help='Any specific metadata fields you wish to be excluded from the response entities')
    list_parser.add_argument('-s', '--namespace', dest='namespace', action='store', help='The namespace for the entities you are trying to get')
    list_parser.add_argument('-n', '--name', dest='name', action='store', help='The name of the entities you are trying to get')
    list_parser.add_argument('-i', '--snapshotId', dest='snapshotId', type=int, action='store', help='The snapshot-id of the entities you are trying to get')    
    list_parser.add_argument('-y', '--synopsis', dest='synopsis', action='store', help='The exact synopsis of the entities you are trying to get')
    list_parser.add_argument('-d', '--documentation', dest='docs', action='store', help='The exact documentation of the entities you are trying to get')
    list_parser.add_argument('-o', '--owner', dest='owner', action='store', help='The owner of the entities you are trying to get')
    list_parser.add_argument('-p', '--payload', dest='payload', action='store', help='The exact payload of the entities you are trying to get')
    list_parser.add_argument('-t', '--entityType', dest='entityType', action='store', help='The type of the entities you are trying to get',choices=['Task', 'Workflow', 'Configuration'])
    list_parser.set_defaults(func=list_entities)

    # DELETE (namespace/name/id) arguments
    redact_parser = subparsers.add_parser('redact', description='Redact a specific method snapshot and all of its associated configurations from the FireCloud Methods Repository', help='Redact a specific method snapshot and all of its associated configurations from the FireCloud Methods Repository')
    redact_parser.add_argument('NAMESPACE', action='store', help='The namespace for the entity you are trying to redact')
    redact_parser.add_argument('NAME', action='store', help='The name of the entity you are trying to redact')
    redact_parser.add_argument('SNAPSHOT_ID', type=int, action='store', help='The snapshot-id of the entity you are trying to redact')
    redact_parser.set_defaults(func=redact)

    # Call the appropriate function for the given subcommand, passing in the parsed program arguments
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
    



