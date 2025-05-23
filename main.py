import cv2
import time
import math
import numpy as np
import mediapipe as mp
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Suppress warnings and set environment variable
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Suppress TensorFlow Lite delegate warnings
import sys
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
import tensorflow as tf
sys.stderr = stderr

from absl import logging
logging.set_verbosity(logging.ERROR)

pTime = 0
cTime = 0
cap = cv2.VideoCapture(0)
detector = htm.handDetector()

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()

minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

try:
    while True:
        success, img = cap.read()
        if not success:
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)
        if len(lmList) != 0:
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

            length = math.hypot(x2 - x1, y2 - y1)
            vol = np.interp(length, [25, 270], [minVol, maxVol])
            volBar = np.interp(length, [25, 270], [400, 150])
            volPer = np.interp(length, [25, 270], [0, 100])
            volume.SetMasterVolumeLevel(vol, None)

            if length < 50:
                cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        cv2.putText(img, f"{int(volPer)} %", (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, f"FPS: {int(fps)}", (10, 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Process interrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
