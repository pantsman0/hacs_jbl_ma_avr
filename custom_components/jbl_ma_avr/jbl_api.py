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
        self.surround_mode = None
        self.display_dim = None
        self.party_mode = None
        self.party_volume = None
        self.treble_eq = None
        self.bass_eq = None
        self.room_eq = None
        self.dialog_enhance = None
        self.dolby_mode = None
        self.dolby_compression = None
        self.streaming_server = None
        self.streaming_state = None
        self.version_ip_control: str | None = None
        self.version_host: str | None = None
        self.version_dsp: str | None = None
        self.version_osd: str | None = None
        self.version_net: str | None = None
        self.model_id: int | None = None  # 0x01=MA510, 0x02=MA710, 0x03=MA7100HP, 0x04=MA9100HP

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _notify_callbacks(self):
        for callback in self.callbacks:
            callback()

    @property
    def supports_ma710_plus(self) -> bool:
        """True for MA710, MA7100HP, MA9100HP — i.e. model_id >= 0x02."""
        return self.model_id is not None and self.model_id >= 0x02

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
        packet = bytearray([0x23, cmd_id, data_len] + list(data) + [0x0D])
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
            # C1 (not recognised) and C3 (invalid at this time) are expected for
            # model-specific features not supported by this unit — log at DEBUG.
            if message.rsp_code in (ResponseCode.COMMAND_NOT_RECOGNISED, ResponseCode.COMMAND_INVALID_AT_THIS_TIME):
                _LOGGER.debug(f"Unsupported cmd {hex(cmd_id)}: {error_msg}")
            else:
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
            case Commands.SURROUND_MODE:
                val = data[0]
                if self.surround_mode != val:
                    self.surround_mode = val
                    changed = True
            case Commands.DISPLAY:
                val = data[0]
                if self.display_dim != val:
                    self.display_dim = val
                    changed = True
            case Commands.PARTY_MODE:
                val = (data[0] == 0x01)
                if self.party_mode != val:
                    self.party_mode = val
                    changed = True
            case Commands.PARTY_VOLUME:
                val = data[0]
                if self.party_volume != val:
                    self.party_volume = val
                    changed = True
            case Commands.TREBLE_EQ:
                val = self._decode_eq(data[0])
                if self.treble_eq != val:
                    self.treble_eq = val
                    changed = True
            case Commands.BASS_EQ:
                val = self._decode_eq(data[0])
                if self.bass_eq != val:
                    self.bass_eq = val
                    changed = True
            case Commands.ROOM_EQ:
                val = data[0]
                if self.room_eq != val:
                    self.room_eq = val
                    changed = True
            case Commands.DIALOG_ENHANCE_MODE:
                val = (data[0] == 0x01)
                if self.dialog_enhance != val:
                    self.dialog_enhance = val
                    changed = True
            case Commands.DOLBY_MODE:
                val = data[0]
                if self.dolby_mode != val:
                    self.dolby_mode = val
                    changed = True
            case Commands.DOLBY_COMPRESSION:
                val = (data[0] == 0x01)
                if self.dolby_compression != val:
                    self.dolby_compression = val
                    changed = True
            case Commands.STREAMING_STATE:
                if len(data) >= 2:
                    s_server = data[0]
                    s_state = data[1]
                    if self.streaming_server != s_server or self.streaming_state != s_state:
                        self.streaming_server = s_server
                        self.streaming_state = s_state
                        changed = True
            case Commands.INIT:
                # Response data[0] is the model ID reported by the AVR.
                if len(data) >= 1:
                    mid = data[0]
                    if self.model_id != mid:
                        self.model_id = mid
                        _LOGGER.debug(
                            f"AVR model_id=0x{mid:02x} "
                            f"(MA510=0x01, MA710=0x02, MA7100HP=0x03, MA9100HP=0x04)"
                        )
                        changed = True
            case Commands.VERSION:
                # data[0] = sub-type, data[1:] = ASCII version string
                if len(data) >= 2:
                    version_str = data[1:].decode("ascii", errors="replace")
                    sub = data[0]
                    if sub == 0xF0:
                        attr = "version_ip_control"
                    elif sub == 0xF1:
                        attr = "version_host"
                    elif sub == 0xF2:
                        attr = "version_dsp"
                    elif sub == 0xF3:
                        attr = "version_osd"
                    elif sub == 0xF4:
                        attr = "version_net"
                    else:
                        attr = None
                    if attr and getattr(self, attr) != version_str:
                        setattr(self, attr, version_str)
                        changed = True

        if changed:
            self._notify_callbacks()

    @staticmethod
    def _decode_eq(raw: int) -> int:
        """Convert wire byte to signed dB (-12..+12)."""
        if raw <= 0x0C:
            return raw
        # 0xFF=-1, 0xFE=-2, ..., 0xF4=-12
        return raw - 256

    @staticmethod
    def _encode_eq(db: int) -> int:
        """Convert signed dB to wire byte."""
        if db >= 0:
            return db & 0xFF
        return (db + 256) & 0xFF

    async def update_state(self):
        always_polled = [
            Commands.POWER,
            Commands.VOLUME,
            Commands.MUTE,
            Commands.SOURCE,
            Commands.SURROUND_MODE,
            Commands.DISPLAY,
            Commands.TREBLE_EQ,
            Commands.BASS_EQ,
            Commands.ROOM_EQ,
            Commands.DIALOG_ENHANCE_MODE,
            Commands.DOLBY_MODE,
            Commands.STREAMING_STATE,
        ]
        ma710_plus_only = [
            Commands.PARTY_MODE,    # 0x09 — MA710/MA7100HP/MA9100HP only
            Commands.PARTY_VOLUME,  # 0x0A — MA710/MA7100HP/MA9100HP only
            Commands.DOLBY_COMPRESSION,  # 0x10 — MA710/MA7100HP/MA9100HP only
        ]
        cmds = always_polled + (ma710_plus_only if self.supports_ma710_plus else [])
        for cmd in cmds:
            await self._send_command(cmd, [0xF0])
            await asyncio.sleep(0.05)
        # Version sub-types: 0xF0=IP control, 0xF1=Host, 0xF2=DSP, 0xF3=OSD, 0xF4=NET
        for sub in [0xF0, 0xF1, 0xF2, 0xF3, 0xF4]:
            await self._send_command(Commands.VERSION, [sub])
            await asyncio.sleep(0.05)

    async def turn_on(self):
        await self._send_command(Commands.POWER, [0x01])

    async def turn_off(self):
        await self._send_command(Commands.POWER, [0x00])

    async def set_volume(self, volume):
        await self._send_command(Commands.VOLUME, [volume])

    async def volume_up(self):
        await self._send_command(Commands.IR_COMMAND, [0x01, 0x0E, 0xE3])

    async def volume_down(self):
        await self._send_command(Commands.IR_COMMAND, [0x01, 0x0E, 0x13])

    async def mute_volume(self, mute: bool):
        val = 0x01 if mute else 0x00
        await self._send_command(Commands.MUTE, [val])

    async def select_source(self, source_id):
        await self._send_command(Commands.SOURCE, [source_id])

    async def set_surround_mode(self, mode_id: int):
        await self._send_command(Commands.SURROUND_MODE, [mode_id])

    async def set_display_dim(self, level: int):
        """0=full, 1=50%, 2=25%, 3=off."""
        await self._send_command(Commands.DISPLAY, [level])

    async def set_party_mode(self, enabled: bool):
        await self._send_command(Commands.PARTY_MODE, [0x01 if enabled else 0x00])

    async def set_party_volume(self, volume: int):
        """0–99."""
        await self._send_command(Commands.PARTY_VOLUME, [max(0, min(99, volume))])

    async def set_treble_eq(self, db: int):
        """Signed dB, -12 to +12."""
        await self._send_command(Commands.TREBLE_EQ, [self._encode_eq(db)])

    async def set_bass_eq(self, db: int):
        """Signed dB, -12 to +12."""
        await self._send_command(Commands.BASS_EQ, [self._encode_eq(db)])

    async def set_room_eq(self, mode_id: int):
        """0=disabled, 1=EZ Set EQ, 2=Dirac Live."""
        await self._send_command(Commands.ROOM_EQ, [mode_id])

    async def set_dialog_enhance(self, enabled: bool):
        await self._send_command(Commands.DIALOG_ENHANCE_MODE, [0x01 if enabled else 0x00])

    async def set_dolby_mode(self, mode_id: int):
        """0=off, 1=Music, 2=Movie, 3=Night."""
        await self._send_command(Commands.DOLBY_MODE, [mode_id])

    async def set_dolby_compression(self, enabled: bool):
        await self._send_command(Commands.DOLBY_COMPRESSION, [0x01 if enabled else 0x00])

    async def reboot(self):
        await self._send_command(Commands.REBOOT, [0xAA, 0xAA])

    async def send_ir_command(self, data: bytearray):
        await self._send_command(Commands.IR_COMMAND, data)
