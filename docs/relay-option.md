# Optional: split machines (Hermes on a server, face/backtalk on a client)
#
# This is NOT needed for the single-Windows-box setup in the README. It exists
# for people who run Hermes on a remote/server machine (like a homelab) and
# want the face + voice on their local Windows PC.

## Architecture
#
#   [ client: backtalk (ears/mouth) ]  ->  Hermes OpenAI API on the SERVER
#        |                                (e.g. http://<server>:8642/v1)
#        |  writes .voice_state locally
#        v
#   [ tiny relay on client ]  ->  POST /state  ->  [ tiny relay on server ]
#                                                    writes .voice_state into the
#                                                    face's bus_dir
#        ^
#   backtalk ALSO mirrors its local signals to the relay
#
# The face lives on the SERVER; the voice lives on the CLIENT. Because the
# state files (bus_dir) are on the server, a small HTTP relay is used so the
# client's backtalk can push state updates to the server's face.

## Two small pieces (no secrets shipped; generate keys yourself)

### Server side (where the face runs)
# 1. Run a tiny relay that listens for POST /state and writes `.voice_state`
#    into the face's bus_dir. It authenticates with X-Hermes-Face-Key.
# 2. Bind it to the LAN (0.0.0.0) and firewall it to trusted clients only.

### Client side (where backtalk runs)
# 1. Point backtalk's signals mirror at the server relay URL + key
#    (HERMES_FACE_URL / HERMES_FACE_KEY env or sidecar file).
# 2. backtalk sends listening/thinking/speaking/idle changes to the relay,
#    which lands in the face bus on the server.

## Security notes
# - Generate your own relay key per install; never commit it.
# - Keep the Hermes API and the relay bound to trusted networks.
# - The Hermes API server with the terminal backend runs as the host user with
#   full file/command access -- bind it to 127.0.0.1 (or firewall it) unless you
#   explicitly need LAN access, and never expose it to the public internet.