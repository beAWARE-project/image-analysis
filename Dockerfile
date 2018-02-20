FROM ppgiannak/obd:latest

COPY src/image_analyzer.py /usr/src/listener/
COPY src/image_listener.py /usr/src/listener/
COPY src/timing_test.py /usr/src/listener/
COPY src/output/timetest_output.json /usr/src/listener/output/
COPY src/model/label_map.pbtxt /usr/src/listener/model/

WORKDIR /usr/src/listener/model/

RUN wget -O frozen_inference_graph.pb http://object-store-app.eu-gb.mybluemix.net/objectStorage?file=frozen_inference_graph.pb
RUN wget -O vgg_places https://www.dropbox.com/s/53xg37xytrpp8rp/vgg_places?dl=0

WORKDIR /usr/src/
WORKDIR /usr/src/listener/

ENV PYTHONPATH="/usr/local/lib/python3.5/site-packages/tensorflow/models/:/usr/local/lib/python3.5/site-packages/tensorflow/models/slim:${PYTHONPATH}"

CMD python3 image_listener.py
