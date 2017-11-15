
# coding: utf-8

# # v01
# - created 15-11-17
# - final version for the cont integration uc102 (short version)
# - processes a single image locally stored
# - stores locally an output image and json with the same filename as the image
# - currently using FasterRCNN trained on COCO model
# - place in /usr/src/listener/
# - there are internal parameters

# In[ ]:


import numpy as np
import os
import six.moves.urllib as urllib
import tensorflow as tf
import pandas
from collections import defaultdict
from PIL import Image
import cv2
from tqdm import tqdm
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
import json

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = './model/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = './model/label_map.pbtxt'
NUM_CLASSES = 90
        
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')
        
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

print('Analyzer imported')

#PARAMETERS
confidence_drop = 0.6 #bellow this confidence score boxes will be dropped
upper_size_thres = 0.9 #above this size (percentage of screen) boxes will be dropped

def box_trans(box, height, width): #transform from (ymin, xmin, ymax, xmax)[norm] to (left, top, width, height)[non-norm]
    box = [box[0] * height, box[1] * width, box[2] * height, box[3] * width]
    box = list(map(int, box))
    box = [box[1], box[0], abs(box[3]-box[1]), abs(box[2]-box[0])]
    return box

def analyze(img_np, file_name):
    #LOAD IMAGE
    frame_np = img_np
    write_on = frame_np.copy()
    height = frame_np.shape[0]
    width = frame_np.shape[1]
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
            frame_np_expanded = np.expand_dims(frame_np, axis=0)
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            scores = detection_graph.get_tensor_by_name('detection_scores:0')
            classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')
            (boxes, scores, classes, num_detections) = sess.run(
                [boxes, scores, classes, num_detections],
                feed_dict={image_tensor: frame_np_expanded})
            to_del=()
            #delete unwanted boxes (too large, non car labels, etc)
            for i in range(boxes.shape[1]):
                if((np.abs(boxes[0][i][0]-boxes[0][i][2])*np.abs(boxes[0][i][1]-boxes[0][i][3]) >= upper_size_thres) or 
                    (scores[0][i] < confidence_drop) or
                    (classes[0][i] not in [1, 2, 3, 4, 6, 8, 9])):
                    to_del = to_del + (i,)
                    num_detections[0] = num_detections[0] - 1
            boxes = np.delete(boxes, to_del, axis=1)
            scores = np.delete(scores, to_del, axis=1)
            classes = np.delete(classes, to_del, axis=1)
            boxes_t=[] #initiallize transformed bozes storage
            for box in np.squeeze(boxes, axis=0): # transform detected boxes
                box = box_trans(box, height, width)
                boxes_t = boxes_t + [box]
                        
        #visualize detection        
        vis_util.visualize_boxes_and_labels_on_image_array(
            write_on,
            np.squeeze(boxes, axis=0),
            np.squeeze(classes, axis=0).astype(np.int32),
            np.squeeze(scores, axis=0),
            category_index,
            use_normalized_coordinates=True,
            max_boxes_to_draw=500,
            line_thickness=1,
            min_score_thresh=confidence_drop)
        to_write = Image.fromarray(write_on)
        to_write.save('./output/'+file_name+'_output.jpg')
        target_dict = []
        for idx, box in enumerate(np.squeeze(boxes, axis=0)):
            box = box_trans(box, height, width)
            target_dict += [{"left":box[0], 
                            "top":box[1], 
                            "width":box[2], 
                            "height":box[3], 
                            "type":category_index[int(np.squeeze(classes, axis=0)[idx])]['name'],
                            "confidence":float("{0:.3f}".format(np.squeeze(scores, axis=0)[idx]))}]
        son = {'image':{"name":file_name, "width":width, "height":height,"target":target_dict}}
        with open('./output/'+file_name+'_output.json', 'w') as outfile:
            json.dump(son, outfile, sort_keys=False, indent=1)
        outfile.close()

