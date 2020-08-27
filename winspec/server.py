"""Websockets server for controlling WinSpec over the network.

This module contains the server object WinspecServer. This runs continuously,
accepting connections and passing incoming commands through to Winspec.

Note that there is no security or authentication, so it is a good idea to run
this behind a firewall with a whitelist of the PCs required to access it.

John Jarman <jcj27@cam.ac.uk>
"""
import asyncio
import concurrent.futures
import logging
import websockets
import json
import winspec
import winspec.winspec_com

class WinspecServer:
    """Websockets server for controlling Winspec

    Provide the IP address and TCP port to listen for connections.

    Args:
        ip (str): IP address
        port (int): TCP port

    Example::
        ws = WinspecServer(ip, port)
        asyncio.run(ws.run())
    """

    def __init__(self, ip='localhost', port=1234):
        self.connections = set()
        self.ip = ip
        self.port = port
        self.shutdown_request = False

        self.winspec = winspec.winspec_com.WinspecCOM()

        self.vars = {
            'wavelength':   {'getter':self.winspec.get_wavelength,
                             'setter':self.winspec.set_wavelength},
            'exposure_time':{'getter':self.winspec.get_exposure_time,
                             'setter':self.winspec.set_exposure_time},
            'spectrum':     {'getter':self.winspec.acquire_spectrum,
                             'setter':None},
            'detector_temp':{'getter':self.winspec.get_detector_temp,
                             'setter':None}
        }

    async def run(self):
        """Run websocket server.
        
        Call using asyncio.run()

        Returns when server shuts down.
        """
        server = await websockets.serve(self._serve, self.ip, self.port)
        logging.info('Server started at {}:{}'.format(self.ip, self.port))
        logging.info('Press Ctrl+C to shut down')
        await server.wait_closed()
        logging.info('Server shutdown')

    async def _serve(self, websocket, path):
        """Server connection handler

        Handles incoming connections, decodes commands and passes to the command
        handler.

        Args:
            websocket (WebSocketServerProtocol): Client object.
            path (str): URI (Unused).
        """
        try:
            self.connections.add(websocket)

            # This loop will handle incoming messages until the client disconnects
            async for command in websocket:
                try:
                    # Decode and handle incoming commands
                    cmd = json.loads(command)
                    logging.debug('{}: {}'.format(websocket.remote_address[0], cmd))
                    await self._handle_command(websocket, cmd)
                except json.JSONDecodeError as err:
                    await self._handle_error(websocket, winspec.WinspecError(
                                             winspec.WinspecErrorCodes.JSONDecodeError, 
                                             str(err)))
        finally:
            self.connections.discard(websocket)

    async def _handle_command(self, websocket, command):
        """Handle commands from connected clients
        
        Command format::
            {'cmd':<command>, '<variable_name>':<value>, ...}

        'cmd' is one of:
            - 'set': set variables
            - 'get': request value of specified variables

        Args:
            websocket (WebSocketServerProtocol): Client object
            command (dict): Command
        """
        try:
            return_vals = dict()
            if command['cmd'] in ('set', 'get'):
                keys = command.keys()
                for key in keys:
                    # Loop through requested variables
                    try:
                        if key == 'cmd':
                            continue

                        # Retrieve the getter and setter functions for this variable
                        var = self.vars[key]

                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            # Getter/setter are blocking functions, so use a thread pool
                            # to run them
                            if command['cmd'] == 'set':
                                if var['setter'] is None:
                                    raise winspec.WinspecError(
                                        winspec.WinspecErrorCodes.ParameterError,
                                        '{} is read-only'.format(key))
                                await loop.run_in_executor(executor, var['setter'], command[key])
                            
                            if command['cmd'] == 'get':
                                if var['getter'] is None:
                                    raise winspec.WinspecError(
                                        winspec.WinspecErrorCodes.ParameterError,
                                        '{} is write-only'.format(key))
                                return_vals[key] = await loop.run_in_executor(executor, var['getter'])

                    except winspec.WinspecError as err:
                        await self._handle_error(websocket, err)

                    except KeyError as err:
                        await self._handle_error(websocket, winspec.WinspecError(
                                    winspec.WinspecErrorCodes.UnrecognisedVariable, 
                                    'Unrecognised variable {}'.format(str(err))))
                    
                    except ValueError as err:
                        await self._handle_error(websocket, winspec.WinspecError(
                                    winspec.WinspecErrorCodes.ParameterError,
                                    '{}'.format(str(err))))
            else:
                await self._handle_error(websocket, winspec.WinspecError(
                                    winspec.WinspecErrorCodes.UnrecognisedCommand, 
                                    'Unrecognised command {}'.format(command['cmd'])))
        finally:
            # Always send 'complete' message, regardless of errors
            await self._send_message(websocket, {'complete':True, **return_vals})

    async def _handle_error(self, websocket, err):
        """Transmits error messages to the client and logs them.

        Args:
            websocket (WebSocketServerProtocol): Client object
            err (WinspecError): Error to send

        """
        logging.error(str(err))
        await self._send_message(websocket, {'error':err.errno, 'errormsg':err.msg})

    async def _send_message(self, websocket, msg):
        """Encodes and sends messages to the client.
        
        Args:
            websocket (WebSocketServerProtocol): Client object
            msg (dict): Object to send. Must be JSON serializable
        """

        try:
            await websocket.send(json.dumps(msg))
        except websockets.ConnectionClosed:
            logging.warn('Client disconnected before response sent')