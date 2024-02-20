from adisconfig import adisconfig
from log import Log

from flask import Flask, request, Response
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime

class pixel_tracker:
    project_name='adistools-pixel_tracker'
    def __init__(self):
        self._config=adisconfig('/opt/adistools/configs/adistools-pixel_tracker.yaml')
        self._log=Log(
            parent=self,
            backends=['rabbitmq_emitter'],
            debug=self._config.log.debug,
            rabbitmq_host=self._config.rabbitmq.host,
            rabbitmq_port=self._config.rabbitmq.port,
            rabbitmq_user=self._config.rabbitmq.user,
            rabbitmq_passwd=self._config.rabbitmq.password,
        )  

        self._mongo_cli=MongoClient(
            self._config.mongo.host,
            self._config.mongo.port,
        )

        self._mongo_db=self._mongo_cli[self._config.mongo.db]
        self._urls=self._mongo_db['pixel_tracker']
        self._metrics=self._mongo_db['pixel_tracker_metrics']

    def add_metric(self,pixel_tracker_uuid, pixel_tracker_name, remote_addr, user_agent, time):
        document={
            "pixel_tracker_uuid": pixel_tracker_uuid,
            "pixel_tracker_name": pixel_tracker_name,
            "time": {
                "timestamp": time.timestamp(),
                "strtime": time.strftime("%m/%d/%Y, %H:%M:%S")
                },
            "client_details": {
                "remote_addr": remote_addr,
                "user_agent": user_agent,
                }
            }

        self._metrics.insert_one(document)
    def get_pixel_tracker(self, pixel_tracker_uuid):
        query={
            'pixel_tracker_uuid' : pixel_tracker_uuid
        }
        return self._urls.find_one(query)

with open('pixel.png','rb') as pixel_file:
	pixel=pixel_file.read()

pixel_tracker=pixel_tracker()
application=Flask(__name__)

@application.route("/<pixel_tracker_uuid>.png", methods=['GET'])
def track(pixel_tracker_uuid):
    
    data=pixel_tracker.get_pixel_tracker(pixel_tracker_uuid)
    if data:
        time=datetime.now()
        pixel_tracker_uuid=data['pixel_tracker_uuid']
        pixel_tracker_name=data['pixel_tracker_name']
        user_agent=str(request.user_agent)

        if request.headers.getlist("X-Forwarded-For"):
            remote_addr=request.headers.getlist("X-Forwarded-For")[0]
        else:
            remote_addr=str(request.remote_addr)
        
        pixel_tracker.add_metric(
        	pixel_tracker_name=pixel_tracker_name,
            pixel_tracker_uuid=pixel_tracker_uuid,
            remote_addr=remote_addr,
            user_agent=user_agent,
            time=time
            )


        return Response(
        	pixel,
            mimetype='image/gif',
        )
    else:
        return ""
application.route("/", methods=['GET'])
def index():
    return ""