import argparse
import asyncio
import logging

from aioquic.connection import QuicConnection


class QuicProtocol(asyncio.DatagramProtocol):
    def __init__(self, secrets_log_file):
        self._connection = QuicConnection(secrets_log_file=secrets_log_file)
        self._transport = None

    def connection_made(self, transport):
        self._transport = transport
        self._connection.connection_made()
        self._send_pending()

    def datagram_received(self, datagram, addr):
        self._connection.datagram_received(datagram)
        self._send_pending()

    def _send_pending(self):
        for datagram in self._connection.pending_datagrams():
            self._transport.sendto(datagram)


async def run(address, port, secrets_log_file):
    _, protocol = await loop.create_datagram_endpoint(
        lambda: QuicProtocol(secrets_log_file=secrets_log_file),
        remote_addr=(address, port))

    await asyncio.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='QUIC client')
    parser.add_argument('address', type=str)
    parser.add_argument('port', type=int)
    parser.add_argument('--secrets-log-file', type=str)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.secrets_log_file:
        secrets_log_file = open(args.secrets_log_file, 'a')
    else:
        secrets_log_file = None

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(
        address=args.address,
        port=args.port,
        secrets_log_file=secrets_log_file))