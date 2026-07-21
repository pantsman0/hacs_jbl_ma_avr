import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

# Commands
CMD_POWER = 0x00
CMD_IR_COMMAND = 0x04
CMD_SOURCE = 0x05
CMD_VOLUME = 0x06
CMD_MUTE = 0x07
CMD_INIT = 0x50
CMD_HEARTBEAT = 0x51

# Responses
RSP_SUCCESS = 0x00

class JblApi:
    def __init__(self, host, port=50000):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.callbacks = []
        self._listen_task = None
        self._reconnect_task = None
        self.is_connected = False
        
        # State
        self.power = None
        self.volume = None
        self.mute = None
        self.source = None

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _notify_callbacks(self):
        for callback in self.callbacks:
            callback()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.is_connected = True
            _LOGGER.debug(f"Connected to {self.host}:{self.port}")
            
            # Send init request
            try:
                await self._send_command(CMD_INIT, [0xF0])
            except Exception as e:
                _LOGGER.warning(f"Init command failed: {e}")
                
            await asyncio.sleep(0.1)
            
            self._listen_task = asyncio.create_task(self._listen())
            
            # Request initial state
            await self.update_state()
        except Exception as e:
            self.is_connected = False
            raise e

    async def disconnect(self):
        self.is_connected = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None

    async def _send_command(self, cmd_id, data):
        if not self.writer:
            _LOGGER.error("Not connected")
            return
            
        data_len = len(data)
        packet = bytearray([0x23, cmd_id, data_len] + data + [0x0D])
        _LOGGER.debug(f"Sending: {packet.hex()}")
        try:
            self.writer.write(packet)
            await self.writer.drain()
        except Exception as e:
            _LOGGER.error(f"Failed to send command {hex(cmd_id)}: {e}")
            asyncio.create_task(self._handle_disconnect())

    async def _handle_disconnect(self):
        if not self.is_connected:
            return
        _LOGGER.warning("Disconnected from AVR. Will attempt to reconnect...")
        self.is_connected = False
        self._notify_callbacks()
        
        if self.writer:
            self.writer.close()
            self.writer = None
            self.reader = None
            
        if not self._reconnect_task:
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())
            
    async def _reconnect_loop(self):
        while not self.is_connected:
            _LOGGER.debug("Attempting to reconnect...")
            try:
                await self.connect()
                _LOGGER.debug("Reconnected successfully")
                self._reconnect_task = None
                return
            except Exception as e:
                _LOGGER.debug(f"Reconnect failed: {e}")
                await asyncio.sleep(5)

    async def _listen(self):
        while self.is_connected:
            try:
                # Read until 0x0D (End)
                data = await self.reader.readuntil(b'\x0D')
                if not data:
                    break
                _LOGGER.debug(f"Received: {data.hex()}")
                self._parse_response(data)
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                if self.is_connected:
                    _LOGGER.error(f"Error in listen loop: {e}")
                break
        _LOGGER.debug("Listen loop ended")
        asyncio.create_task(self._handle_disconnect())
        
    def _parse_response(self, packet):
        # packet should start with 0x02 0x23
        if len(packet) < 6 or packet[0] != 0x02 or packet[1] != 0x23:
            return
            
        cmd_id = packet[2]
        rsp_code = packet[3]
        data_len = packet[4]
        
        if rsp_code != RSP_SUCCESS:
            _LOGGER.warning(f"Error response for cmd {hex(cmd_id)}: {hex(rsp_code)}")
            return
            
        if len(packet) < 6 + data_len:
            return
            
        data = list(packet[5:5+data_len])
        
        if data_len == 0:
            return
            
        changed = False
        
        if cmd_id == CMD_POWER:
            new_power = (data[0] == 0x01)
            if self.power != new_power:
                self.power = new_power
                changed = True
        elif cmd_id == CMD_VOLUME:
            new_volume = data[0]
            if self.volume != new_volume:
                self.volume = new_volume
                changed = True
        elif cmd_id == CMD_MUTE:
            new_mute = (data[0] == 0x01)
            if self.mute != new_mute:
                self.mute = new_mute
                changed = True
        elif cmd_id == CMD_SOURCE:
            new_source = data[0]
            if self.source != new_source:
                self.source = new_source
                changed = True
                
        if changed:
            self._notify_callbacks()

    async def update_state(self):
        await self._send_command(CMD_POWER, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(CMD_VOLUME, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(CMD_MUTE, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(CMD_SOURCE, [0xF0])

    async def turn_on(self):
        await self._send_command(CMD_POWER, [0x01])

    async def turn_off(self):
        await self._send_command(CMD_POWER, [0x00])

    async def set_volume(self, volume):
        await self._send_command(CMD_VOLUME, [volume])

    async def volume_up(self):
        await self._send_command(CMD_IR_COMMAND, [0x01,0x0E,0xE3])
    
    async def volume_down(self):
        await self._send_command(CMD_IR_COMMAND, [0x01,0x0E,0x13])

    async def mute_volume(self, mute):
        val = 0x01 if mute else 0x00
        await self._send_command(CMD_MUTE, [val])

    async def select_source(self, source_id):
        await self._send_command(CMD_SOURCE, [source_id])
