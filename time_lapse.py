#!/usr/bin/python
import os
import sys
import time
import datetime

DROPBOX_ACCESS_TOKEN_PATH = '/home/pi/py_timelapse/dropbox_access_token.txt'
S3_ACCESS_TOKEN_PATH = '/home/pi/py_timelapse/aws_access_token.txt'


def connect_dropbox():
    import dropbox
    access_token = open(DROPBOX_ACCESS_TOKEN_PATH, 'r').read()
    return dropbox.client.DropboxClient(access_token.rstrip())


def upload_file_dropbox(dropbox_path, f):
    connect_dropbox().put_file(dropbox_path, f)


def download_file_dropbox(dropbox_path, local_path):
    (f, _) = connect_dropbox().get_file_and_metadata(dropbox_path)
    out = open(local_path, 'wb')
    out.write(f.read())
    out.close()

def connect_s3():
    import boto
    lines = open(S3_ACCESS_TOKEN_PATH, 'r').readlines()
    aws_access_key_id = lines[0].split('=')[1].rstrip()
    aws_secret_access_key = lines[1].split('=')[1].rstrip()
    return boto.connect_s3(aws_access_key_id, aws_secret_access_key)

def upload_file_s3(s3_path, f):
    import boto
    bucket = connect_s3().get_bucket('raspberrybucket')
    k = boto.s3.key.Key(bucket)
    k.key = s3_path
    k.set_contents_from_file(f)

def camera_consistent_images():
    import picamera
    camera = picamera.PiCamera()
    camera.resolution = (2592, 1944)
    camera.rotation = 270
    camera.framerate = 30
    # Wait for the automatic gain control to settle
    time.sleep(2)
    # Now fix the values
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    return camera


def capture(local_path):
    camera = camera_consistent_images()
    camera.capture(local_path)

def capture_and_upload():
    capture("/tmp/image.jpg")
    f = open("/tmp/image.jpg", 'rb')
    folder_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d')
    filename = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S')
    upload_file_s3('/' + folder_name +'/' + filename + ".jpg", f)

def archive_date(date, dest_dir, dry_run=False):
    assert date.startswith('/')
    folder_metadata = connect_dropbox().metadata('/')
    os.mkdir(os.path.join(dest_dir, date))
    for child in folder_metadata['contents']:
        assert child['is_dir'] == False
        filename = date + child['path']
        print "downloading %s" % filename
        if not dry_run:
            (f, metadata) = connect_dropbox().get_file_and_metadata(date + child['path'])
            out = open(os.path.join(dest_dir, child['path']), 'wb')
            out.write(f.read())
            out.close()



    
def main():
    import urllib3
    urllib3.disable_warnings()
    capture_and_upload()


if __name__ == "__main__":
    main()

