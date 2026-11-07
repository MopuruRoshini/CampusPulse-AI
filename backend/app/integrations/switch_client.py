"""Minimal Switch agent-protocol client based on the official protocol docs.
Registration and WebSocket connectivity require a Switch server and credentials.
"""
import asyncio, json, uuid
from urllib.parse import urlencode, urlparse
import httpx, websockets
from ..config import settings

class SwitchClient:
    def configured(self):
        return bool(settings.switch_base_url and settings.switch_agent_id and settings.switch_agent_api_key)

    async def health(self):
        if not settings.switch_base_url: return {"connected":False,"reason":"SWITCH_BASE_URL is not configured"}
        try:
            async with httpx.AsyncClient(timeout=4) as client:
                r=await client.get(settings.switch_base_url.rstrip("/")+"/health")
                return {"connected":r.is_success,"status_code":r.status_code,"detail":r.text[:300]}
        except Exception as e: return {"connected":False,"reason":str(e)}

    async def register(self, name: str, description: str):
        if not settings.switch_base_url or not settings.switch_registration_key:
            raise RuntimeError("Set SWITCH_BASE_URL and SWITCH_REGISTRATION_KEY first")
        profile={"connection_model":"always_on","message_exchange":True,"pre_invocation_mediation":[],"post_invocation_mediation":[],"event_reporting":[]}
        payload={"name":name,"description":description,"connector_type":"campuspulse-python","integration_profile":profile,"display_name":name.title()}
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post(settings.switch_base_url.rstrip("/")+"/agents",headers={"Authorization":f"Bearer {settings.switch_registration_key}"},json=payload)
            r.raise_for_status(); return r.json()

    async def post_message(self, room_id: str, content: str):
        if not self.configured(): raise RuntimeError("Switch agent credentials are not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            r=await client.post(f"{settings.switch_base_url.rstrip('/')}/agents/{settings.switch_agent_id}/message",headers={"Authorization":f"Bearer {settings.switch_agent_api_key}"},json={"room_id":room_id,"content":content})
            r.raise_for_status(); return r.json()

    async def listen(self, room_id: str, on_message):
        if not self.configured(): raise RuntimeError("Switch agent credentials are not configured")
        base=urlparse(settings.switch_base_url)
        scheme="wss" if base.scheme=="https" else "ws"
        connection_id=str(uuid.uuid4()); cursor="head"; generation=None
        while True:
            query={"connection_id":connection_id,"rooms":room_id,"start_from":cursor,"scope":"single","filter":"all"}
            if generation is not None: query["expected_generation"]=str(generation)
            uri=f"{scheme}://{base.netloc}/agents/{settings.switch_agent_id}/connection/ws?{urlencode(query)}"
            try:
                async with websockets.connect(uri,additional_headers={"Authorization":f"Bearer {settings.switch_agent_api_key}"},ping_interval=None) as ws:
                    async for raw in ws:
                        frame=json.loads(raw); kind=frame.get("type") or frame.get("event")
                        if kind=="connection_state":
                            generation=frame.get("generation"); cursor=str(frame.get("cursor",0))
                        elif kind=="ping":
                            await ws.send(json.dumps({"type":"pong","cursor":int(cursor) if cursor.isdigit() else 0}))
                        elif kind=="message":
                            data=frame.get("data",frame); cursor=str(data.get("sequence",frame.get("id",cursor)))
                            payload=data.get("payload",{})
                            if payload.get("addressed"):
                                await on_message(data)
                        elif kind in ("evicted","refused"):
                            if frame.get("data",{}).get("code")=="taken_over": return
            except Exception:
                await asyncio.sleep(4)
