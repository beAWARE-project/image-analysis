import socket
import sys
from _thread import *
import time
import json
import urllib.request
from PIL import Image
import io
import os
import numpy as np
import requests
import skvideo.io
import image_analyzer

f = open('log.txt', 'a')
# orig_stdout = sys.stdout
# sys.stdout = f

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 9999 # Arbitrary non-privileged port

storage_link = 'http://object-store-app.eu-gb.mybluemix.net/objectStorage?file='

def download_from_storage(image_url):
    A = urllib.request.urlopen(image_url)
    data = A.read()
    data2 = io.BytesIO(data)
    img = Image.open(data2)
    img = img.convert(mode='RGB')
    img_np = np.array(img)
    return img_np

def process_image(img_np, file_name):
    global f
    #do the analysis and return void
    start = time.time()
    image_analyzer.analyze(img_np, file_name)
    end = time.time()
    runtime = end-start
    f.write("Image analysis done. Runtime: {0}".format(runtime))
    start = time.time()
    bimg_output = open('./output/'+file_name+'_output.jpg', 'rb')
    bjson_output = open('./output/'+file_name+'_output.json', 'rb')
    save_to_storage(bimg_output, file_name+'_output.jpg')
    save_to_storage(bjson_output, file_name+'_output.json')
    end = time.time()
    runtime = end-start
    f.write("Upload complete. Runtime: {0}".format(runtime))
    dict_to_send = {"message":{"img_analyzed":storage_link+file_name+'_output.jpg', "img_analysis":storage_link+file_name+'_output.json'}}
    bjson_links = json.dumps(dict_to_send).encode()
    #os.remove('./output/'+file_name+'_output.jpg')
    #os.remove('./output/'+file_name+'_output.json')
    return bjson_links
    
def save_to_storage(bobj, filename):
    global f
    #Upload to storage
    r = requests.post(storage_link+filename, bobj)
    if not r.ok:
        f.write('Didn\'t happen')

def send_to_certh_hub(bjson_links, conn):
    conn.send(bjson_links)

def handle_message(bmsg, conn):
    global f
    msg = bmsg.decode()
    mydict = json.loads(msg)
    image_url = mydict['message']['URL']
    #timestamp = mydict['message']['startTimeUTC']
    start = time.time()
    img_np = download_from_storage(image_url)
    end = time.time()
    runtime = end - start
    f.write("Download complete. Runtime: {0}".format(runtime))
    file_name = mydict['message']['URL'].split(sep='file=')[1].rsplit(sep='.', maxsplit=1)[0]
    bjson_links = process_image(img_np, file_name)
    send_to_certh_hub(bjson_links, conn)
    return

#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #f = open('log.txt', 'a')
    global f
#     orig_stdout = sys.stdout
#     sys.stdout = f
    while 1:
        bmsg = conn.recv(1024)
        msg = bmsg.decode()
        f.write("Hub says: ",msg)
        if(msg=="Msg from IA received"):
            #to_send = "Bye hub!"
            #conn.sendall(to_send.encode())
            break
        else:
            to_send = "Msg received from Hub"
            conn.sendall(to_send.encode())
            start = time.time()
            handle_message(bmsg, conn)
            end = time.time()
            runtime = end - start
            f.write("Message handling done. Runtime: {0}".format(runtime))
    conn.close()
    f.write('Connection closed')
    f.write(time.strftime('%X %x %Z'))
    #sys.stdout = orig_stdout
    f.close()
    blog = open('log.txt', 'rb')
    save_to_storage(blog, "image-analysis.log")
    return

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
f.write('Socket created')
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    f.write('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()
     
f.write('Socket bind complete')
 
#Start listening on socket
s.listen(10)
f.write('Socket now listening')
#now keep talking with the client
#sys.stdout = orig_stdout
f.close()
while 1:
    #f = open('log.txt', 'a')
    #orig_stdout = sys.stdout
    #sys.stdout = f
    #wait to accept a connection - blocking call
    #f.write('Waiting for a new connection...')
    conn, addr = s.accept()
    f = open('log.txt', 'a')
    f.write('Connected with ' + addr[0] + ':' + str(addr[1]))
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    #sys.stdout = orig_stdout
    #f.close()
    start_new_thread(clientthread ,(conn,))

s.close()
