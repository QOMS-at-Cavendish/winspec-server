"""
Client for Winspec communication

John Jarman <jcj27@cam.ac.uk>
"""
import websockets
import json
import asyncio
import threading
from winspec.exceptions import WinspecError

class WinspecClient:
    def __init__(self, server_address, timeout = 100):
        self.host = server_address
        self.loop = None
        self.timeout = timeout
        self.stop = threading.Event()
        self.running = threading.Event()
    
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
        self.running.wait()

    def disconnect(self):
        self.stop.set()

    #####################
    # Synchronous methods
    #####################

    def set_parameters(self, **params):
        f = asyncio.run_coroutine_threadsafe(self._set_parameters_async(**params), self.loop)
        return f.result(self.timeout)

    def acquire(self):
        f = asyncio.run_coroutine_threadsafe(self._acquire_async(), self.loop)
        return f.result(self.timeout)

    ################
    # Async methods
    ################

    def _start_async_thread(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        self.loop = asyncio.get_running_loop()
        self.running.set()
        await self.loop.run_in_executor(None, self.stop.wait)
        self.running.clear()

    async def _set_parameters_async(self, **params):
        return await self._send_and_wait({'cmd':'set', **params})

    async def _acquire_async(self):
        return await self._send_and_wait({'cmd':'acquire'})

    async def _send_and_wait(self, cmd):
        async with websockets.connect(self.host) as websocket:
            await websocket.send(json.dumps(cmd))
            while True:
                response = json.loads(await asyncio.wait_for(websocket.recv(), self.timeout))
                if 'error' in response.keys():
                    self._handle_error(response['error'], response['errormsg'])
                if 'complete' in response.keys():
                    return response

    def _handle_error(self, err, errmsg):
        raise WinspecError('{}: {}'.format(err, errmsg))
