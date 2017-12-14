import time
import json
import urllib.request
from PIL import Image
import io
import os
import numpy as np
import skvideo.io
import requests

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 9999 # Arbitrary non-privileged port

storage_link = 'http://object-store-app.eu-gb.mybluemix.net/objectStorage?file='
image_url = 'http://object-store-app.eu-gb.mybluemix.net/objectStorage?file=Floods.2016.CyToloxWQAEgZ52.jpg'

def download_from_storage(image_url):
    A = urllib.request.urlopen(image_url)
    data = A.read()
    data2 = io.BytesIO(data)
    img = Image.open(data2)
    img = img.convert(mode='RGB')
    img_np = np.array(img)
    to_write = Image.fromarray(img_np)
    to_write.save('./output/timetest_output.jpg')
    return

def save_to_storage(bobj, filename):
    #Upload to storage
    r = requests.post(storage_link+filename, bobj)
    if not r.ok:
        print('Didn\'t happen')


start = time.time()
download_from_storage(image_url)
bimg_output = open('./output/timetest_output.jpg', 'rb')
bjson_output = open('./output/timetest_output.json', 'rb')
save_to_storage(bimg_output, 'timetest_output.jpg')
save_to_storage(bjson_output, 'timetest_output.json')
end = time.time()
runtime = end-start
print("Download & Upload complete. Runtime: {0}".format(runtime))

time.sleep(10)
print("Second print")

time.sleep(10)
print("Third print")

time.sleep(10)
print("Fourth print")

time.sleep(10)
print("Fifth print")

time.sleep(10)
print("Sixth print")
