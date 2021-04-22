import argparse
import asyncio
import json
import logging
import os
import platform
import ssl

from aiohttp import web

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer


ROOT = os.path.dirname(__file__)

logger2 = logging.getLogger("main")
logger2.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()  #interface
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')    #formate (requetes ?) pour l'interface

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger2.addHandler(ch) # ajout des infos de ch au logger





async def index(request): # lance requetes return reponse.toString
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request): #lancement du script
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json() # Attente d'une requete pour interpreter la suite
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"]) # formalise et standardise le traitement du json plus haut

    pc = RTCPeerConnection() #cree toutes les options du RTC
    pcs.add(pc) # Stocke toutes les differentes RTC ? a controler

    @pc.on("connectionstatechange") #actualisation des etats de connection ?
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    # open media source
    if args.play_from:
        player = MediaPlayer(args.play_from) #option pour lire des videos
    else:
        options = {"framerate": "1", "video_size": "1280x800"} # reglage des options par défault, si v4l2,par exemple, ne reecrit pas dessus
        print(platform.system())
        logger2.debug(f'La plateforme est : {platform.system()}')
        if platform.system() == "Darwin":
            player = MediaPlayer("default:none", format="avfoundation", options=options)
        else:
            player = MediaPlayer("/dev/video0", format="v4l2", options=options)

    await pc.setRemoteDescription(offer) #communication
    for t in pc.getTransceivers():
        if t.kind == "audio" and player.audio:
            pc.addTrack(player.audio)
        elif t.kind == "video" and player.video:
            pc.addTrack(player.video)

    answer = await pc.createAnswer()#Acteur de la negociation RTC
    await pc.setLocalDescription(answer)

    return web.Response(#le json de retour
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
    parser = argparse.ArgumentParser(description="Aucune idee de l'utilité de cette string, je recroiserais peut être ce message un jour")
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
        logging.basicConfig(level=logging.DEBUG)#l'option verbose

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)#l'option cert_file, aucune idee de son utilite
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)#demande un client au javascript
    app.router.add_post("/offer", offer)#lance l'echange 
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context) #lance l'app
