import argparse
import asyncio
import json
import logging
import os
import platform
import ssl

import math
import cv2
import numpy
from av import VideoFrame

from utils import ArducamUtils
import subprocess
import time

from aiohttp import web

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer

ROOT = os.path.dirname(__file__)


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

def show_info(arducam_utils):
    _, firmware_version = arducam_utils.read_dev(ArducamUtils.FIRMWARE_VERSION_REG)
    _, sensor_id = arducam_utils.read_dev(ArducamUtils.FIRMWARE_SENSOR_ID_REG)
    _, serial_number = arducam_utils.read_dev(ArducamUtils.SERIAL_NUMBER_REG)
    print("Firmware Version: {}".format(firmware_version))
    print("Sensor ID: 0x{:04X}".format(sensor_id))
    print("Serial Number: 0x{:08X}".format(serial_number))


def resize(frame, dst_width):
    width = frame.shape[1]
    height = frame.shape[0]
    scale = dst_width * 1.0 / width
    return cv2.resize(frame, (int(scale * width), int(scale * height)))

class FlagVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!
        self.counter = 0
        height, width = 1280, 800


        self.frames = []
        ret, frame = cap.read()
        frame = frame.reshape(int(h), int(w))
        frame = arducam_utils.convert(frame)
        cv2.imwrite('test'+'coucou'+'.jpg',frame)

        img = cv2.imread('test'+'coucou'+'.jpg')
        self.frames.append(VideoFrame.from_ndarray(numpy.array(img)))



    async def recv(self):
        ret, frame = cap.read()
        #list_frame.append(frame)
        frame = frame.reshape(int(h), int(w))
        frame = arducam_utils.convert(frame)
        cv2.imwrite('test'+'coucou'+'.jpg',frame)

        img = cv2.imread('test'+'coucou'+'.jpg')
        self.frames.append(VideoFrame.from_ndarray(numpy.array(img)))
        pts, time_base = await self.next_timestamp()

        frame = self.frames[self.counter]
        frame.pts = pts
        frame.time_base = time_base
        self.counter += 1
        return frame

    def _create_rectangle(self, width, height, color):
        data_bgr = numpy.zeros((height, width, 3), numpy.uint8)
        data_bgr[:, :] = color
        return data_bgr


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
        
    await pc.setRemoteDescription(offer)
    #for t in pc.getTransceivers():
    pc.addTrack(FlagVideoStreamTrack())

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


pcs = set()


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC webcam demo")
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None
    #Init camera
    cmd1 = 'v4l2-ctl -d 0 -c exposure=160'
    cmd2 = 'v4l2-ctl -d 0 -C exposure'
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    arducam_utils = ArducamUtils(0)
    cap.set(cv2.CAP_PROP_CONVERT_RGB, arducam_utils.convert2rgb)
    show_info(arducam_utils)

    # Aquisition des dimentions de l'image en provenance du capteur
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # needed to purge the frame with default exposure
    for i in range(6):
        subprocess.call(cmd1, shell=True)
        ret, frame = cap.read()


    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)