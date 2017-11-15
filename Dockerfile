FROM ppgiannak/obd:latest

COPY src/image_analyzer.py /usr/src/listener/
COPY src/image_listener.py /usr/src/listener/
COPY src/model/frozen_inference_graph.pb /usr/src/listener/model/
COPY src/model/label_map.pbtxt /usr/src/listener/model/

WORKDIR /usr/src/listener/model/

RUN wget -O frozen_inference_graph.pb https://www.dropbox.com/s/g301ym64oruo6u2/frozen_inference_graph.pb?dl=0

WORKDIR /usr/src/listener/

ENV PYTHONPATH="/usr/local/lib/python3.5/site-packages/tensorflow/models/:/usr/local/lib/python3.5/site-packages/tensorflow/models/slim:${PYTHONPATH}"

CMD python3 image_listener.py
