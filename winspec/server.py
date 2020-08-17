"""
Websockets server for controlling WinSpec over the network

John Jarman <jcj27@cam.ac.uk>
"""
import asyncio
import concurrent.futures
import logging
import websockets
import json
import winspec

class WinspecServer:
    """
    WinspecServer main class

    Usage:
    ws = WinspecServer(ip, port)
    asyncio.run(ws.run())
    """

    def __init__(self, ip='localhost', port=1234):
        self.connections = set()
        self.ip = ip
        self.port = port
        self.shutdown_request = False

        self.winspec = winspec.winspec_com.WinspecCOM()

        self.winspec_vars = {
            'wavelength':{'getter':self.winspec.get_wavelength,
                          'setter':self.winspec.set_wavelength}
        }

    async def run(self):
        """
        Run websocket server.
        
        Call using asyncio.run()

        Returns when server shuts down.
        """
        server = await websockets.serve(self._serve, self.ip, self.port)
        logging.info('Server started at {}:{}'.format(self.ip, self.port))
        await server.wait_closed()
        logging.info('Server shutdown')

    async def _serve(self, websocket, path):
        """
        Handles incoming connections, decodes commands and passes to the command
        handler.
        """
        try:
            self.connections.add(websocket)
            remote_ip = websocket.remote_address[0]
            logging.info('Client connected ({})'.format(remote_ip))

            # This loop will handle incoming messages until the client disconnects
            async for command in websocket:
                try:
                    # Decode and handle incoming commands
                    cmd = json.loads(command)
                    await self._handle_command(cmd, websocket)
                except json.JSONDecodeError as err:
                    await self._handle_error(websocket, winspec.WinspecError(
                                             winspec.WinspecErrorCodes.JSONDecodeError, 
                                             str(err)))
        finally:
            logging.info('Client disconnected ({})'.format(remote_ip))
            self.connections.discard(websocket)

    async def _handle_command(self, command, websocket):
        """
        Handle commands from connected clients

        Format: {'cmd':<command>, '<variable_name>':<value>, ...}

        'cmd' is one of: 'set', 'get' or 'acquire'
            - 'set': set variables
            - 'get': request value of specified variables
            - 'acquire': trigger acquisition

        """
        ######################
        # Set or get variables
        ######################
        if command['cmd'] in ('set', 'get'):
            try:
                keys = command.keys()
                return_vals = dict()
                for key in keys:
                    # Loop through requested variables
                    try:
                        if key == 'cmd':
                            continue

                        # Retrieve the getter and setter functions for this variable
                        var = self.winspec_vars[key]

                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            # Getter/setter are blocking functions, so use a thread pool
                            # to run them
                            if command['cmd'] == 'set':
                                await loop.run_in_executor(executor, var['setter'], command[key])
                            return_vals[key] = await loop.run_in_executor(executor, var['getter'])

                    except winspec.WinspecError as err:
                        await self._handle_error(websocket, err)

                    except KeyError as err:
                        await self._handle_error(websocket, winspec.WinspecError(
                                    winspec.WinspecErrorCodes.UnrecognisedVariable, 
                                    'Unrecognised variable {}'.format(str(err))))
            finally:
                # Always send 'complete' message, regardless of errors
                await self._send_message(websocket, {'complete':True, **return_vals})

        #####################
        # Trigger acquisition
        #####################
        if command['cmd'] == 'acquire':
            spec = None
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Acquire spectrum in a new thread
                    spec = await loop.run_in_executor(executor, self.winspec.acquire_spectrum)
            
            except winspec.WinspecError as err:
                await self._handle_error(websocket, err)
            
            finally:
                await self._send_message(websocket, {'complete':True, 'spectrum':spec})

    async def _handle_error(self, websocket, err):
        """
        Transmits error messages to the client and logs them
        """
        logging.error(str(err))
        await self._send_message(websocket, {'error':err.errno, 'errormsg':err.msg})

    async def _send_message(self, websocket, msg):
        try:
            await websocket.send(json.dumps(msg))
        except websockets.ConnectionClosed:
            logging.warn('Client disconnected during send')