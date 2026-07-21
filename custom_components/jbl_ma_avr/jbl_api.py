from enum import IntEnum
import asyncio
import logging
import json
import os

_LOGGER = logging.getLogger(__name__)

try:
    with open(os.path.join(os.path.dirname(__file__), "translations", "en.json")) as f:
        _TRANSLATIONS = json.load(f)
        _ERRORS = _TRANSLATIONS.get("api_errors", {})
except Exception:
    _ERRORS = {}

class Commands(IntEnum):
    POWER = 0x00
    DISPLAY = 0x01
    VERSION = 0x02
    IR_COMMAND = 0x04
    SOURCE = 0x05
    VOLUME = 0x06
    MUTE = 0x07
    SURROUND_MODE = 0x08
    PARTY_MODE = 0x09
    PARTY_VOLUME = 0x0A
    TREBLE_EQ = 0x0B
    BASS_EQ = 0x0C
    ROOM_EQ = 0x0D
    DIALOG_ENHANCE_MODE = 0x0E
    DOLBY_MODE = 0x0F
    DOLBY_COMPRESSION = 0x10
    STREAMING_STATE = 0x11
    INIT = 0x50
    HEARTBEAT = 0x51
    REBOOT = 0x52
    #FACTORY_RESET = 0x53

class ResponseCode(IntEnum):
    SUCCESS = 0x00
    COMMAND_NOT_RECOGNISED = 0xC1
    PARAMETER_NOT_RECOGNISED = 0xC2
    COMMAND_INVALID_AT_THIS_TIME = 0xC3
    INVALID_DATA_LENGTH = 0xC4


class JblServerMessage:
    def __init__(self, cmd_id, rsp_code, data):
        self.cmd_id = cmd_id
        self.rsp_code = rsp_code
        self.data = data

    def __str__(self):
        return f"JblServerMessage(cmd_id=0x{self.cmd_id:x}, rsp_code=0x{self.rsp_code:x}, data={self.data.hex()})"

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
            _LOGGER.debug(f"Connecting to {self.host}:{self.port}")
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.is_connected = True
            _LOGGER.debug(f"Connected to {self.host}:{self.port}")
            
            # Send init request
            try:
                await self._send_command(Commands.INIT, [0xF0])
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

    async def _send_command(self, cmd_id: Commands, data: bytearray):
        if not self.writer:
            _LOGGER.warning("Not connected")
            if not self._reconnect_task:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())
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
                # Find start sequence 0x02 0x23
                head = (0,0)
                while head != (0x02,0x23):
                    head = (head[1], (await self.reader.readexactly(1))[0])
                            
                # Read CmdID, RspCode, DataLen
                header = await self.reader.readexactly(3)
                cmd_id = header[0]
                rsp_code = header[1]
                data_len = header[2]
                
                # Read Data
                data_payload = b''
                if data_len > 0:
                    data_payload = await self.reader.readexactly(data_len)
                    
                # Read End
                end_byte = await self.reader.readexactly(1)
                if end_byte[0] != 0x0D:
                    raise ValueError(f"Corrupted packet: expected termination byte (0x0D), got {hex(end_byte[0])}")
                    
                message = JblServerMessage(cmd_id, rsp_code, data_payload)
                _LOGGER.debug(f"Received: {message}")
                self._handle_message(message)
                
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                if self.is_connected:
                    _LOGGER.error(f"Error in listen loop: {e}")
                break
        _LOGGER.debug("Listen loop ended")
        asyncio.create_task(self._handle_disconnect())
        
    def _handle_message(self, message: JblServerMessage):
        cmd_id = message.cmd_id
        data = message.data
        
        if message.rsp_code != ResponseCode.SUCCESS:
            error_msg = _ERRORS.get(f"{message.rsp_code:x}", f"Unknown error code {hex(message.rsp_code)}")
            _LOGGER.warning(f"Error response for cmd {hex(cmd_id)}: {error_msg}")
            return
        
        if len(data) == 0:
            _LOGGER.debug(f"No data for command {hex(cmd_id)}")
            return
            
        changed = False
        
        match message.cmd_id:
            case Commands.POWER:
                new_power = (data[0] == 0x01)
                if self.power != new_power:
                    self.power = new_power
                    changed = True
            case Commands.VOLUME:
                new_volume = data[0]
                if self.volume != new_volume:
                    self.volume = new_volume
                    changed = True
            case Commands.MUTE:
                new_mute = (data[0] == 0x01)
                if self.mute != new_mute:
                    self.mute = new_mute
                    changed = True
            case Commands.SOURCE:
                new_source = data[0]
                if self.source != new_source:
                    self.source = new_source
                    changed = True
                    
        if changed:
            self._notify_callbacks()

    async def update_state(self):
        await self._send_command(Commands.POWER, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(Commands.VOLUME, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(Commands.MUTE, [0xF0])
        await asyncio.sleep(0.1)
        await self._send_command(Commands.SOURCE, [0xF0])

    async def turn_on(self):
        await self._send_command(Commands.POWER, [0x01])

    async def turn_off(self):
        await self._send_command(Commands.POWER, [0x00])

    async def set_volume(self, volume):
        await self._send_command(Commands.VOLUME, [volume])

    async def volume_up(self):
        await self._send_command(Commands.IR_COMMAND, [0x01,0x0E,0xE3])
    
    async def volume_down(self):
        await self._send_command(Commands.IR_COMMAND, [0x01,0x0E,0x13])

    async def mute_volume(self, mute: bool):
        val = 0x01 if mute else 0x00
        await self._send_command(Commands.MUTE, [val])

    async def select_source(self, source_id):
        await self._send_command(Commands.SOURCE, [source_id])
