from __future__ import annotations
import httpx
from urllib.parse import urljoin
from .plugin import IntegrationPlugin, ActionSpec

class RESTIntegration(IntegrationPlugin):
    """Generic credentialed REST connector. Restricts requests to one configured base URL."""
    def __init__(self,base_url:str,headers:dict|None=None,timeout:float=30.0,allow_writes:bool=False):
        self.base_url=base_url.rstrip('/')+'/' ; self.headers=headers or {}; self.timeout=timeout; self.allow_writes=allow_writes
    def health(self):
        try:
            r=httpx.get(self.base_url,headers=self.headers,timeout=self.timeout,follow_redirects=True);return {"ok":r.status_code<500,"status":r.status_code}
        except Exception as e:return {"ok":False,"error":str(e)}
    def actions(self):
        return [ActionSpec("request","Call an endpoint under the configured integration base URL",{"method":"GET|POST|PUT|PATCH|DELETE","path":"relative path","json":"optional object"},write=True)]
    def execute(self,action,arguments):
        if action!="request": raise KeyError(action)
        method=str(arguments.get("method","GET")).upper()
        if method not in {"GET","HEAD","OPTIONS"} and not self.allow_writes: raise PermissionError("write requests are disabled for this connector")
        path=str(arguments.get("path","")); url=urljoin(self.base_url,path.lstrip('/'))
        if not url.startswith(self.base_url): raise PermissionError("endpoint escaped configured base URL")
        r=httpx.request(method,url,headers=self.headers,json=arguments.get("json"),params=arguments.get("params"),timeout=self.timeout);r.raise_for_status()
        ct=r.headers.get("content-type",""); return r.json() if "json" in ct else r.text
