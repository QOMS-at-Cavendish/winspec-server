"""Client to communicate with Winspec server

This module contains the client object WinspecClient. This object manages a
connection to the Winspec websockets server, and provides methods to get and set
parameters, and to trigger acquisition. The provided public methods block until
the requested operation has completed.

The class is designed to be used in a context manager to ensure the connection is
disconnected correctly.

Methods raise `winspec.WinspecError` in case of server-side errors.

Example::
    with winspec.WinspecClient as ws_client:
        ws_client.set_parameters(wavelength=650, exp_time=10)
        central_wavelength = ws_client.get_parameter('wavelength')
        spectrum = ws_client.acquire()

John Jarman <jcj27@cam.ac.uk>
"""
import websockets
import json
import asyncio
import threading
import logging
import winspec

class WinspecClient:
    """Winspec client class

    Args:
        server_address (str): Hostname of the server. E.g. `ws://192.168.0.1:1234`
        timeout (float, optional): Max waiting time for server operations. Default
            to 100 secs.
    """
    def __init__(self, server_address, timeout = 100):
        self.host = server_address
        self.loop = None
        self.timeout = timeout
        self.stop = threading.Event()
        self.connected = threading.Event()
        
        self.thread = None

        self._recv_timeout = 1

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context manager exit"""
        self.disconnect()
        return False

    def connect(self):
        """Start client thread and connect to the websockets server.

        Returns when the client thread has connected and is ready to send commands.
        """
        if self.thread is not None:
            raise ConnectionError('Already connected')
        self.stop.clear()
        self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.thread.start()
        while not self.connected.is_set():
            try:
                self.connected.wait(timeout=0.1)
            except TimeoutError:
                pass
            if not self.thread.is_alive():
                raise ConnectionError('Unable to connect to server')

    def disconnect(self):
        """Stop client thread to disconnect from the server.

        Return when the thread has stopped.
        """
        self.stop.set()
        self.thread.join()
        self.thread = None

    def set_parameters(self, **params):
        """Set parameters.

        Kwargs:
            `<param_name>=<value>` pairs

        Raises:
            winspec.WinspecError for any server or hardware error
            ConnectionError if the server is not connected
        """
        self._check_connected()
        f = asyncio.run_coroutine_threadsafe(self._set_parameters_async(**params), self.loop)
        f.result()

    def get_parameter(self, param):
        """Get parameter.

        Args:
            param (str): Name of parameter to retrieve
        
        Returns:
            Value of the requested parameter

        Raises:
            winspec.WinspecError for any server or hardware error
            ConnectionError if the server is not connected
        """

        self._check_connected()
        f = asyncio.run_coroutine_threadsafe(self._get_parameters_async(param), self.loop)
        return f.result()[param]

    def acquire(self):
        """Acquire spectrum.

        Returns::
            [wavelength[], intensity[]]

        Raises:
            winspec.WinspecError for any server or hardware error
            ConnectionError if the server is not connected
        """
        return self.get_parameter('spectrum')

    def _check_connected(self):
        """Check if the server is connected.

        If not connected, raise a ConnectionError.
        """
        if not self.connected.is_set():
            self.stop.set()
            raise ConnectionError('Server not connected')

    ################
    # Async methods
    ################

    def _start_async_loop(self):
        """Starts the event loop for asyncio websocket operations.

        Blocks execution until the event loop completes.
        """
        asyncio.run(self._run_async())

    async def _run_async(self):
        """Main loop for websocket client.

        Connects to the server, setting `self.connected` once the connection is
        established.

        Then continually checks for new messages for the server, decodes them and 
        puts them on a queue for processing.

        Set `self.stop` to end the event loop and disconnect.
        """
        self.loop = asyncio.get_running_loop()
        self._recv_queue = asyncio.Queue()
        # Loop checking for messages on the websocket
        try:
            async with websockets.connect(self.host) as websocket:
                self._websocket = websocket
                self.connected.set()
                logging.info('Connected to server')
                while not self.stop.is_set():
                    try:
                        # Get message from socket and decode it, with short timeout
                        # so the stop flag can be checked periodically
                        msg = json.loads(await asyncio.wait_for(websocket.recv(), 
                                                            self._recv_timeout))
                        # Put the message on the receive queue for processing
                        await self._recv_queue.put(msg)

                    except json.JSONDecodeError as err:
                        logging.error('Bad JSON from server: {}'.format(err))

                    except asyncio.TimeoutError:
                        pass

        except websockets.ConnectionClosed as err:
            logging.error('Unexpected disconnect {}'.format(err))
            
        finally:
            logging.info('Connection closed')
            self.connected.clear()
            self._websocket = None

    async def _set_parameters_async(self, **params):
        """Set parameters (async method)

        See `set_parameters` docstring for more info
        """
        return await self._send_and_wait({'cmd':'set', **params})

    async def _get_parameters_async(self, *params):
        """Get parameters (async method)

        See `get_parameter` docstring for more info
        """
        cmd = {'cmd':'get'}
        for param in params:
            cmd[param] = None
        return await self._send_and_wait(cmd)

    async def _send_and_wait(self, cmd):
        """Send a message and wait for the 'complete' response.
        """
        await self._clear_recv_queue()
        await self._websocket.send(json.dumps(cmd))
        while True:
            response = await asyncio.wait_for(self._recv_queue.get(), 
                                              timeout=self.timeout)
            if 'error' in response.keys():
                self._handle_error(response['error'], response['errormsg'])
            if 'complete' in response.keys():
                response.pop('complete')
                return response

    async def _clear_recv_queue(self):
        """Flush all messages out of the receive queue.
        """
        try:
            while True:
                await self._recv_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

    def _handle_error(self, err, errmsg):
        """Raise a WinspecError for errors received from server.

        Args:
            err (int): winspec.WinspecErrorCodes error code
            errmsg (str): Supplementary error message
        """
        raise winspec.WinspecError(err, errmsg)
