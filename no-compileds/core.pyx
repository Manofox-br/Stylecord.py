import httpx
import asyncio, json, time, random, ctypes
import platform
import logging
import wsutils
from picows import WSListener, ws_connect, WSMsgType

class Connection(WSListener):
    def __init__(self, client):
        self._client = client
        self._ws = None
        self._heartbeat_task = None
        self._stop_event = asyncio.Event()
        self._listener = None
        self._gateway = "wss://gateway.discord.gg/?v=10&encoding=json"
        self._token = None
        self._intents = 0
        self._heartbeat_interval = None
        self._session_id = None
        self._sequencial = None
        self._last_ack = 0.0
        self._last_heartbeat = None
        self.latency = None

    #===| Callbacks |===#
    def on_ws_connected(self, transport):
        payload = {
            "op": 2,
            "d": {
                "token": self._token,
                "intents": int(self._intents),
                "properties": {
                    "$os": platform.system().lower() or "custom_gateway",
                    "$browser": "stylecord.py",
                    "$device": platform.machine() or "custom_gateway"
                }
            }
        }
        transport.send(WSMsgType.TEXT, json.dumps(payload))

    def on_ws_frame(self, transport, frame):
        if frame.msg_type.name == "TEXT":
            raw = wsutils.frame_to_bytes(frame.payload_ptr, frame.payload_size)
            text = raw.decode("utf-8")
            event = json.loads(text)
            asyncio.create_task(self.listener(event or {}))

    def on_ws_closed(self, transport):
        code = transport.close_code
        reason = transport.close_reason
        logging.info(f"Connection closed ({code}), reason: '{reason}'")
        if code in (4003, 4004, 4009, 4010, 4011, 4012, 4013, 4014):
            payload = {
                "op": 2,
                "d": {
                    "token": self._token,
                    "intents": int(self._intents),
                    "properties": {
                        "$os": platform.system().lower() or "custom_gateway",
                        "$browser": "stylecord.py",
                        "$device": platform.machine() or "custom_gateway"
                    }
                }
            }
            transport.send(WSMsgType.TEXT, json.dumps(payload))
            return
        asyncio.create_task(self.close)

    def on_ws_error(self, transport, error):
        logging.error("Error in Gateway: ", error)
        payload = {
            "op": 6,
            "d": {
                "token": self._token,
                "session_id": self._session_id,
                "seq": self._sequencial
            }
        }
        transport.send(WSMsgType.TEXT, json.dumps(payload))

    #===| Functions |===#
    async def close(self):
        try:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                if not self._heartbeat_task.done:
                    await self._heartbeat_task
                self._heartbeat_task = None
            if self._stop_event:
                self._stop_event.set()
            if self._ws:
                await self._ws.close(code=1000, reason="Connection Close.")
        except Exception:
            logging.error(f"Error in close websockets: ", exc_info=True)

    async def listener(self, msg):
        event = json.loads(msg)
        op = event.get("op")
        t = event.get("t")
        if "s" in event:
            self._sequencial = event["s"]
        match op:
            case 0:
                match t:
                    case "READY":
                        await self._client.handle_ready(event)
                    case "MESSAGE_CREATE":
                        await self._client.handle_message(event)
            case 10:
                heartbeat_interval = event["d"]["heartbeat_interval"]
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    await self._heartbeat_task
                self._heartbeat_task = asyncio.create_task(self.heartbeat())
            case 11:
                self._last_ack = time.perf_counter()
                if self._last_heartbeat:
                    self.latency = self._last_ack - self._last_heartbeat
                await self._client.handle_pong(self.latency)

    async def reconnect_with_retry(self, max_attempts=5):
        delay = 1
        for attempt in range(max_attempts):
            try:
                if self._ws:
                    try:
                        self._ws.disconnect()
                    except Exception:
                        pass
                await self.connect()
                return
            except Exception as e:
                logging.error(f"Error in attempt {attempt+1}: {e}")
                await asyncio.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, 60)
        raise RuntimeError("We were unable to reconnect after several attempts.")

    async def heartbeat(self):
        interval_sec = self._heartbeat_interval / 1000
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(interval_sec)
                self._last_heartbeat = time.perf_counter()
                data = {"op": 1, "d": self._sequencial}
                self._ws.send(WSMsgType.TEXT, json.dumps(data))
                now = time.perf_counter()
                if self._last_ack and (now - self._last_ack > interval_sec * 2):
                    logging.warning("Lost heartbeat, reconnecting...")
                    await self.reconnect_with_retry(3)
            except Exception as e:
                logging.error(f"Error in heartbeat: {e}", exc_info=True)

    async def login(self, token, intents):
        self._token = token
        self._intents = intents
        if not self._ws:
            self._ws, self._listener = await ws_connect(lambda: self, self._gateway)