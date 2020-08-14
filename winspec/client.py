"""
Client for Winspec communication

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
        self.connected = threading.Event()
    
    # Context manager methods

    def __enter__(self): 
        self.connect()
        return self
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        self.disconnect()
        return False

    def connect(self):
        if self.connected.is_set():
            return
        self.stop.clear()
        self.connected.clear()
        threading.Thread(target=self._start_async_thread).start()
        self.connected.wait()

    def disconnect(self):
        self.stop.set()

    #####################
    # Synchronous methods
    #####################

    def set_wavelength(self, wavelength, block=True):
        f = asyncio.run_coroutine_threadsafe(self._set_wavelength_async(wavelength), self.loop)
        return f.result(self.timeout)

    ################
    # Async methods
    ################

    def _start_async_thread(self):
        asyncio.run(self._connect_async())

    async def _connect_async(self):
        self.loop = asyncio.get_running_loop()
        async with websockets.connect(self.host) as websocket:
            self.websocket = websocket
            self.connected.set()
            await self.loop.run_in_executor(None, self.stop.wait)
        self.connected.clear()

    async def _set_wavelength_async(self, wavelength):
        cmd = {'cmd':'set', 'wavelength':wavelength}
        await self.websocket.send(json.dumps(cmd))
        while True:
            response = json.loads(await self.websocket.recv())
            if 'error' in response.keys():
                self._handle_error(response['error'], response['errormsg'])
            if 'complete' in response.keys():
                break

    def _handle_error(self, err, errmsg):
        raise WinspecError('{}: {}'.format(err, errmsg))
