import os
import re
import requests
import botocore
import boto3
from bs4 import BeautifulSoup

WEB_URL = str(os.environ['WEB_URL'])
REGEX = str(os.environ['REGEX'])
BUCKET = str(os.environ['BUCKET'])
FILE_URL_PREFIX = str(os.environ['FILE_URL_PREFIX'])

s3 = boto3.resource('s3')

def file_scrapper(event, context):

    print("Getting file name from {}".format(WEB_URL))
    xlsx_file_name = filter_content(WEB_URL)

    print("Checking if {} file was already processed".format(xlsx_file_name))
    if was_already_processed(xlsx_file_name):
        return "Done. File {} was already processed".format(xlsx_file_name)
    
    print("Save file to S3")
    save_file_to_s3(xlsx_file_name)

    return "Done. All tasks were processed succefully!"

def filter_content(url):
    try:
        result = requests.get(url)
        soup = BeautifulSoup(result.text, "lxml")
        links = soup.find_all(href=filter_filename)
        if len(links) <= 1:
            raise Exception('Cannot find link to xlsx file')
        link = links[0]['href']
        match = re.search(REGEX, link)
        return match.group(0)
    except Exception as exception:
        print(exception)
        raise exception

def filter_filename(href):
    return href and re.compile(REGEX).search(href)

def was_already_processed(filename):
    try:
        s3.Object(BUCKET, filename).load()
    except botocore.exceptions.ClientError as exception:
        if exception.response['Error']['Code'] == "404":
            print("{} file is NOT processed yet!".format(filename))
            return False
        else:
            # Something else has gone wrong.
            raise
    else:
        print("{} file already processed! Nothing to do...".format(filename))
        return True

def save_file_to_s3(file_name):

    bucket = BUCKET
    key = file_name

    try:
        tmp_file_name = '/tmp/'+key
        data = requests.get(FILE_URL_PREFIX+key)

        file = open(tmp_file_name, "wb")
        file.write(data.content)
        file.close()
        with open(tmp_file_name, "rb") as write_file:
            s3.meta.client.upload_fileobj(write_file, bucket, key)

    except Exception as exeption:
        print(exeption)
        print('Error uploading object {} to bucket {}.'.format(key, bucket))
        raise exeption
