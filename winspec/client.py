"""
Client for Winspec communication

John Jarman <jcj27@cam.ac.uk>
"""
import websockets
import json
import asyncio
import threading
import logging
import winspec

class WinspecClient:
    def __init__(self, server_address, timeout = 100, retry_interval=1, retry_count=10):
        self.host = server_address
        self.loop = None
        self.timeout = timeout
        self.stop = threading.Event()
        self.connected = threading.Event()
        self.running = threading.Event()

        self._recv_timeout = 1
        self.retry_count = retry_count
        self.retry_interval = retry_interval
    
    # Context manager methods

    def __enter__(self): 
        self.connect()
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        self.disconnect()
        return False

    def connect(self):
        if self.running.is_set():
            return
        self.stop.clear()
        threading.Thread(target=self._start_async_thread).start()
        while not self.connected.is_set():
            try:
                self.connected.wait(timeout=0.1)
            except TimeoutError:
                pass
            if not self.running.is_set():
                raise ConnectionError('Unable to connect to server')

    def disconnect(self):
        self.stop.set()

    #####################
    # Synchronous methods
    #####################

    def set_parameters(self, **params):
        if not self.connected.is_set():
            self.stop.set()
            raise ConnectionError('Cannot set parameters: server not connected')
        f = asyncio.run_coroutine_threadsafe(self._set_parameters_async(**params), self.loop)
        return f.result(self.timeout)

    def acquire(self):
        if not self.connected.is_set():
            self.stop.set()
            raise ConnectionError('Cannot acquire: server not connected')
        f = asyncio.run_coroutine_threadsafe(self._acquire_async(), self.loop)
        return f.result(self.timeout)

    ################
    # Async methods
    ################

    def _start_async_thread(self):
        self.running.set()
        asyncio.run(self._run_async())
        self.running.clear()

    async def _run_async(self):
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
                        # Get message from socket, decode it and put it on the receive queue
                        msg = json.loads(await asyncio.wait_for(websocket.recv(), 
                                                            self._recv_timeout))
                        await self._recv_queue.put(msg)

                    except json.JSONDecodeError as err:
                        logging.error('Bad JSON from server: {}'.format(err))

                    except asyncio.TimeoutError:
                        # Expect regular timeouts so we can check stop flag
                        pass
            
        finally:
            logging.info('Connection closed')
            self.connected.clear()
            self._websocket = None

    async def _set_parameters_async(self, **params):
        logging.info('Set')
        return await self._send_and_wait({'cmd':'set', **params})

    async def _acquire_async(self):
        return await self._send_and_wait({'cmd':'acquire'})

    async def _send_and_wait(self, cmd):
        await self._clear_recv_queue()
        await self._websocket.send(json.dumps(cmd))
        while True:
            response = await self._recv_queue.get()
            if 'error' in response.keys():
                self._handle_error(response['error'], response['errormsg'])
            if 'complete' in response.keys():
                return response

    async def _clear_recv_queue(self):
        try:
            while True:
                await self._recv_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

    def _handle_error(self, err, errmsg):
        raise winspec.WinspecError(err, errmsg)
