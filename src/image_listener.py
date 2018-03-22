import socket
import sys
#from _thread import *
from threading import Lock, Thread
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

#get lock object
lock = Lock()

#open logger
f = open('log.txt', 'a')

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

def process_image(img_np, file_name, timestamp):
    start = time.time()
    image_analyzer.analyze(img_np, file_name, timestamp)
    end = time.time()
    runtime_a = end-start
    #f.write("Image analysis done. Runtime: {0}\n".format(runtime))
    start = time.time()
    bimg_output = open('./output/'+file_name+'_output.jpg', 'rb')
    bjson_output = open('./output/'+file_name+'_output.json', 'rb')
    save_to_storage(bimg_output, file_name+'_output.jpg')
    save_to_storage(bjson_output, file_name+'_output.json')
    bimg_output.close()
    bjson_output.close()
    end = time.time()
    runtime_u = end-start
    #f.write("Upload complete. Runtime: {0}\n".format(runtime))
    dict_to_send = {"message":{"img_analyzed":storage_link+file_name+'_output.jpg', "img_analysis":storage_link+file_name+'_output.json'}}
    bjson_links = json.dumps(dict_to_send).encode()
    return bjson_links, runtime_a, runtime_u
    
def save_to_storage(bobj, filename):
    r = requests.post(storage_link+filename, bobj)
    if not r.ok:
        print('Didn\'t happen')

def send_to_certh_hub(bjson_links, conn):
    conn.send(bjson_links)

def handle_message(bmsg, conn):
    msg = bmsg.decode()
    mydict = json.loads(msg)
    image_url = mydict['message']['URL']
    #TODO: insert real timestamp here
    #timestamp = mydict['message']['startTimeUTC']
    timestamp = "2017-10-13 09:12:42.519408"
    start = time.time()
    img_np = download_from_storage(image_url)
    end = time.time()
    runtime_d = end - start
    #f.write("Download complete. Runtime: {0}\n".format(runtime))
    file_name = mydict['message']['URL'].split(sep='file=')[1].rsplit(sep='.', maxsplit=1)[0]
    bjson_links, runtime_a, runtime_u = process_image(img_np, file_name, timestamp)
    send_to_certh_hub(bjson_links, conn)
    os.remove('./output/'+file_name+'_output.jpg')
    os.remove('./output/'+file_name+'_output.json')
    return runtime_d, runtime_a, runtime_u

#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #global f
    lock.acquire()
    f = open('log.txt', 'a')
    while 1:
        bmsg = conn.recv(1024)
        msg = bmsg.decode()
        f.write("Hub says: "+msg+'\n')
        if(msg=="Msg from IA received"):
            #to_send = "Bye hub!"
            #conn.sendall(to_send.encode())
            break
        else:
            to_send = "Msg received from Hub"
            conn.sendall(to_send.encode())
            start = time.time()
            try:
                run_d, run_a, run_u = handle_message(bmsg, conn)
                end = time.time()
                runtime = end - start
                f.write("Download complete. Runtime: {0}\n".format(run_d))
                f.write("Image analysis done. Runtime: {0}\n".format(run_a))
                f.write("Upload complete. Runtime: {0}\n".format(run_u))
                f.write("Message handling done. Runtime: {0}\n".format(runtime))
            except:
                print("A problem occured, please check the url link or the signal format")
                f.write("Unknown error occured\n")
                break

    conn.close()
    f.write('Connection closed\n')
    f.write(time.strftime('%X %x %Z')+'\n')
    f.close()
    blog = open('log.txt', 'rb')
    save_to_storage(blog, "image-analysis.log")
    lock.release()
    return

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
f.write('Socket created\n')
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    f.write('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1] + '\n')
    sys.exit()    
f.write('Socket bind complete\n')

#Start listening on socket
s.listen(10)
f.write('Socket now listening\n')
f.close()
t = []
#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    #f.write('Waiting for a new connection...')
    conn, addr = s.accept()
    f = open('log.txt', 'a')
    f.write('Connected with ' + addr[0] + ':' + str(addr[1]) + '\n')
    f.close()
    blog = open('log.txt', 'rb')
    save_to_storage(blog, "image-analysis.log")
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    t += [Thread(target=clientthread , args=(conn,))]
    t[-1].start()

s.close()
