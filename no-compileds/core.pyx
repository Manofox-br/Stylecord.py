import httpx
import asyncio, json, time, random, ctypes
import platform
import logging
from picows import WSListener, ws_connect, WSMsgType, WSAutoPingStrategy

from . import restapi

from ..ext.decorators.retry import async_retry

class Payloads:
    @classmethod
    def heartbeat(cls, sequencial):
        data = {
            "op": 1, 
            "d": sequencial
        }

        return data
    
    @classmethod
    def indentify(cls, token, intents):
        data = {
            "op": 2,
            "d": {
                "token": token,
                "intents": int(intents),
                "properties": {
                    "$os": platform.system().lower() or "custom_gateway",
                    "$browser": "stylecord.py",
                    "$device": platform.machine() or "custom_gateway"
                }
            }
        }

        return data

    @classmethod
    def status(cls, activities, status):
        data = {
            "op": 3,
            "d": {
                "since": int(time.time() * 1000), # timestamp
                "activities": [a.to_dict() for a in activities],
                "status": status.value,
                "afk": status.afk
            }
        }

        return data
    
    @classmethod
    def resume(cls, token, session_id, sequencial):
        data = {
            "op": 6,
            "d": {
                "token": token,
                "session_id": session_id,
                "seq": sequencial
            }
        }

        return data


class Headers:
    @classmethod
    def authorization(cls, token):
        data = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }

        return data

class Connection(WSListener):
    def __init__(self, client):
        self._client = client
        self._ws = None
        self._heartbeat_task = None
        self._stop_event = asyncio.Event()
        self._pong_future = None
        self._listener = None
        
        self._gateway = "wss://gateway.discord.gg/?v=10&encoding=json"
        self._rest_api = "https://discord.com/api/v10"
        
        self._token = None
        self._intents = 0
        self._heartbeat_interval = None
        self._session_id = None
        self._sequencial = None
        self._last_ack = 0.0
        self._last_heartbeat = None

        self.start = time.monotonic()
        self.is_closed = True
        self.latency = None

    def __repr__(self):
        return "You shouldn't be here 😕. Yes, this is an easter egg!"
        
    #===| Callbacks |===#
    def on_ws_connected(self, transport):
        self.is_closed = False
        payload = Payloads.indentify(self._token, self._intents)
        transport.send(WSMsgType.TEXT, json.dumps(payload))

    def on_ws_frame(self, transport, frame):
        if frame.msg_type.name == "TEXT":
            raw = frame.get_payload_as_utf8_text()
            event = json.loads(raw)
            asyncio.create_task(self.listener(event or {}))

        elif frame.msg_type == WSMsgType.PONG and self._pong_future and not self._pong_future.done():
            end = time.monotonic()
            latency = (end - self.start)
            self.latency = latency
            self._pong_future.set_result(latency)
            
    def on_ws_closed(self, transport): 
        code = transport.close_code
        reason = transport.close_reason  
        logging.info(f"Connection closed ({code}), reason: '{reason}'")
        
        if code in (4003, 4004, 4009, 4010, 4011, 4012, 4013, 4014):
            self.is_closed = True
            asyncio.create_task(self.reconnect(force_reindentify=True))
            return
        
        asyncio.create_task(self._close())

    def on_ws_error(self, transport, error):
        logging.error("Error in Gateway: ", error)
        asyncio.create_task(self.reconnect())
        
    #===| Functions |===#
    async def _close(self):
        try:
            if self._heartbeat_task:
                try:
                    self._heartbeat_task.cancel()
                    if not self._heartbeat_task.done():
                        await self._heartbeat_task
                    self._heartbeat_task = None
                except asyncio.CancelledError:
                    pass
            
            if self._stop_event:
                self._stop_event.set()
            
            if self._ws:
                self._ws.send_close(1000, "Connection Close.")
                await self._ws.wait_disconnected()

            if restapi.client:
                await restapi.client.close()
        
        except Exception:
            logging.error(f"Error in close websockets: ", exc_info=True)

    async def listener(self, event):
        now = time.time()
        op = event.get("op")
        t = event.get("t")
        d = event.get("d")
        if "s" in event:
            self._sequencial = event["s"]
        
        match op:
            case 0:
                match t:
                    case "READY":
                        self._session_id = d.get("_session_id")
                        await self._client.handle_ready(event)
                    
                    case "MESSAGE_CREATE":
                        restapi.client.add_message_to_cache(d["channel_id"], d)
                        await self._client.handle_message(event)

                    case "CHANNEL_CREATE":
                        restapi.client._cache_channels[d["id"]] = (d, now)

                    case "CHANNEL_UPTADE":
                        restapi.client._cache_channels[d["id"]] = (d, now)

                    case "CHANNEL_DELETE":
                        restapi.client._cache_channels.pop(d["id"], None)

                    case "GUILD_UPTADE":
                        restapi.client._cache_guilds[d["id"]] = (d, now)

                    case "GUILD_DELETE":
                        guild_id = d["id"]
                        restapi.client._cache_guilds.pop(guild_id, None)
                        for cid, (cdata, _) in list(restapi.client._cache_channels.items()):
                            if cdata.get("guild_id") == guild_id:
                                restapi.client._cache_channels.pop(cid, None)
                    
            case 10:
                self._heartbeat_interval = d["heartbeat_interval"]
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    await self._heartbeat_task
                
                self._heartbeat_task = asyncio.create_task(self.heartbeat())
    
            case 11:
                self._last_ack = time.perf_counter()
                if self._last_heartbeat:
                    self.latency = self._last_ack - self._last_heartbeat
                
                await self._client.handle_pong(self.latency)

    @async_retry(max_attempts=3, delay=(0, 30))
    async def reconnect(self, force_reindentify=False):
        if self._ws:
            try: await self._close()
            except: pass

        await self._connect()

        if self.is_closed or not self._session_id:
            payload = Payloads.indentify(self._token, self._intents)
            self._ws.send(WSMsgType.TEXT, json.dumps(payload))

        else:
            payload = Payloads.resume(self._token, self._session_id, self._sequencial)
            self._ws.send(WSMsgType.TEXT, json.dumps(payload))
            
    async def heartbeat(self):
        interval_sec = self._heartbeat_interval / 1000
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(interval_sec)

                payload = Payloads.heartbeat(self._sequencial)
                self._last_heartbeat = time.perf_counter()
                self._ws.send(WSMsgType.TEXT, json.dumps(payload))
                now = time.perf_counter()
                
                if self._last_ack and (now - self._last_ack > interval_sec * 2):
                    logging.warning("Lost heartbeat, reconnecting...")
                    await self.reconnect()
            
            except Exception as e:
                logging.error(f"Error in heartbeat: {e}", exc_info=True)

    async def _connect(self):
        if not self._ws:
            self._ws, self._listener = await ws_connect(
                ws_listener_factory=lambda: self,
                url=self._gateway,
                enable_auto_ping=True,
                enable_auto_pong=True,
                auto_ping_strategy=WSAutoPingStrategy.PING_PERIODICALLY,
                auto_ping_idle_timeout=10,
                auto_ping_reply_timeout=10,
                read_buffer_init_size=65536,
                use_aiofastnet=True,
                websocket_handshake_timeout=5
            )

        if not restapi.client:
            restapi.init_client(self._token, self._intents)
    
    async def login(self, token, intents):
        self.start = time.monotonic()
        self._token = token
        self._intents = intents

        if not self.is_closed:
            await self._close()
            
        await self._connect()
        
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            await self._close()
        finally:
            await self._close()

    async def send_ping(self, timeout:int = 60):
        loop = asyncio.get_event_loop()
        self._pong_future = loop.create_future()
        self.start = time.monotonic()

        self._ws.send_ping()

        try:
            latency = await asyncio.wait_for(self._pong_future, timeout=timeout)
            return latency
        except asyncio.TimeoutError:
            return None
        finally:
            self._pong_future = None
        
    #===| DISCORD |===#
    async def set_status(self, activities, status):
        payload = Payloads.status(activities, status)
        self._ws.send(WSMsgType.TEXT, json.dumps(payload))