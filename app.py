import argparse
import io
import os
from PIL import Image
import cv2
import numpy as np
import torch

from flask import Flask, render_template, request, redirect, Response, json
from draw import PolygonDrawer
import pandas as pd
from datetime import datetime

app = Flask(__name__)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
model.conf = 0.25  # NMS confidence threshold
model.iou = 0.45  # NMS IoU threshold
model.classes = [0]
model.eval()
model.conf = 0.5
model.iou = 0.45
cap = cv2.VideoCapture('rtsp://admin:tagtag@1@192.168.1.200/Streaming/Channels/2')
# cap = cv2.VideoCapture(0)
points = np.zeros([4, 2], dtype = int)
# points = [[650,650],[1180,645],[1195,58],[696,72]]
pointsdf1 = pd.DataFrame(points, columns=['x', 'y'])
pointsdf1 = (pointsdf1 / 2).astype(int)
xmax = max(pointsdf1['x'])
xmin = min(pointsdf1['x'])
ymax = max(pointsdf1['y'])
ymin = min(pointsdf1['y'])
object = {'xmin': [xmin], 'ymin': [ymin], 'xmax': [xmax], 'ymax': [ymax], 'confidence': [1.0], 'class': [-1],
          'name': ['object']}
objectdf = pd.DataFrame(object)
object = objectdf.iloc[0]
points1 = np.array(points)
points1 = (points1 / 2).astype(int)
points2 = points1.reshape(-1,1,2)
# for image saving
num=0

def gen_frames():  # generate frame by frame from camera
    c = 1
    global old_count
    old_count = 0
    while(True):
        success, frame = cap.read()
        if c%20==0:
            if success == True:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                img = Image.open(io.BytesIO(frame))
                results = model(img, size=610)
                record = results.pandas().xyxy[0]
                df = pd.DataFrame(record, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class', 'name'])
                rslt_df1 = df.loc[df['name'] == 'person']
                c1 = rslt_df1.shape[0]
                img = np.squeeze(results.render())
                c2 = 0
                for i in range(len(rslt_df1)):
                    person = rslt_df1.iloc[i]
                    xA = max(person[0], object[0])
                    yA = max(person[1], object[1])
                    xB = min(person[2], object[2])
                    yB = min(person[3], object[3])
                    interArea = abs(max((xB - xA, 0)) * max((yB - yA), 0))
                    if interArea > 0:
                        c2 += 1
                s1 = 'Total People = '+str(c1)
                s2 = 'Total People in Vicinity = '+str(c2)
                if c2 != old_count:
                    print(datetime.now().strftime("%H:%M:%S"), ' Changed : ', s2)
                    old_count = c2
                # print('Current Count : ', old_count)
                img = cv2.putText(img, s1, (20, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                img = cv2.putText(img, s2, (20, 355), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                img = cv2.polylines(img, [points2], True, (255, 0, 0), 2)
                img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                break
            frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        c+=1

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if not file:
            return
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        results = model(img, size=640)
        results.render()
        for img in results.imgs:
            img_base64 = Image.fromarray(img)
            img_base64.save("static/image0.jpg", format="JPEG")
        return redirect("static/image0.jpg")
    return render_template("index.html")

@app.route('/paint', methods=['GET'])
def paint():
    if request.method == 'GET':
        return render_template("paint.html")

@app.route("/postmethod", methods=["POST"])
def postmethod():
    jsdata = request.form["canvas_data"]
    clicks = json.loads(jsdata)
    clicksdf1 = pd.DataFrame(clicks)
    clicksdf1["x"] = 1 * clicksdf1["x"]
    clicksdf1["y"] = 0.9 * clicksdf1["y"]
    clicksdf1 = (clicksdf1).astype(int)
    pts = clicksdf1.to_numpy()
    global points2
    points2 = pts.reshape(-1, 1, 2)
    xmax = max(clicksdf1['x'])
    xmin = min(clicksdf1['x'])
    ymax = max(clicksdf1['y'])
    ymin = min(clicksdf1['y'])
    global object
    object = {'xmin': [xmin], 'ymin': [ymin], 'xmax': [xmax], 'ymax': [ymax], 'confidence': [1.0], 'class': [-1],
              'name': ['object']}
    objectdf = pd.DataFrame(object)
    object = objectdf.iloc[0]
    return '', 204

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=True, port=port, threaded=True)