from __future__ import annotations
from abc import ABC, abstractmethod

class WhatsAppAdapter(ABC):
    """Transport interface. Intelligence stays inside OM AI; transport may be WhatsApp Web or an approved business gateway."""
    @abstractmethod
    def send_text(self, recipient:str, text:str) -> str: ...
    @abstractmethod
    def health(self) -> dict: ...

class DevelopmentWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self): self.outbox=[]
    def send_text(self,recipient:str,text:str)->str:
        msg_id=f'dev-{len(self.outbox)+1}'; self.outbox.append({'id':msg_id,'recipient':recipient,'text':text}); return msg_id
    def health(self): return {'ok':True,'mode':'development','queued':len(self.outbox)}
