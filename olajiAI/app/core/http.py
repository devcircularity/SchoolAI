# app/core/http.py
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from app.core.config import settings
from app.core.logging import log

class CoreHTTP:
    def __init__(self):
        # httpx requires all four timeout parts (or a single default)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.HTTP_CONNECT_TIMEOUT,
                read=settings.HTTP_READ_TIMEOUT,
                write=settings.HTTP_READ_TIMEOUT,
                pool=settings.HTTP_CONNECT_TIMEOUT,
            )
        )

    async def close(self):
        await self._client.aclose()

    def headers(self, bearer: str | None, school_id: str | None, idem_key: str | None):
        h = {}
        if bearer:
            h["Authorization"] = bearer if bearer.lower().startswith("bearer ") else f"Bearer {bearer}"
        if school_id:
            h["X-School-ID"] = school_id
        if settings.SERVICE_TOKEN:
            h["X-Service-Auth"] = settings.SERVICE_TOKEN
        if idem_key:
            h["Idempotency-Key"] = idem_key
        
        # Debug: Log what headers we're creating
        log.info(
            "core_http_headers",
            bearer_provided=bool(bearer),
            bearer_starts_with_bearer=bearer.lower().startswith("bearer ") if bearer else False,
            school_id_provided=bool(school_id),
            service_token_provided=bool(settings.SERVICE_TOKEN),
            final_auth_header=h.get("Authorization", "NOT_SET")[:20] + "..." if h.get("Authorization") else "NOT_SET",
            final_school_header=h.get("X-School-ID", "NOT_SET"),
        )
        
        return h

    @retry(stop=stop_after_attempt(settings.RETRY_ATTEMPTS), wait=wait_fixed(0.4),
           retry=retry_if_exception_type(httpx.HTTPError))
    async def get(self, path: str, bearer: str | None, school_id: str | None):
        url = settings.CORE_API_BASE + path
        headers = self.headers(bearer, school_id, None)
        
        # Debug: Log the actual request being made
        log.info(
            "core_http_request",
            method="GET",
            url=url,
            path=path,
            headers_count=len(headers),
            has_auth=bool(headers.get("Authorization")),
            has_school=bool(headers.get("X-School-ID")),
        )
        
        try:
            response = await self._client.get(url, headers=headers)
            
            # Debug: Log the response
            log.info(
                "core_http_response",
                status_code=response.status_code,
                url=url,
                response_content_preview=str(response.content)[:200] if response.content else None,
            )
            
            return response
        except Exception as e:
            log.error(
                "core_http_error",
                error=str(e),
                error_type=type(e).__name__,
                url=url,
            )
            raise

    async def post(self, path: str, bearer: str | None, school_id: str | None, data: dict, idem_key: str | None):
        url = settings.CORE_API_BASE + path
        return await self._client.post(url, json=data, headers=self.headers(bearer, school_id, idem_key))

    async def patch(self, path: str, bearer: str | None, school_id: str | None, data: dict, idem_key: str | None):
        url = settings.CORE_API_BASE + path
        return await self._client.patch(url, json=data, headers=self.headers(bearer, school_id, idem_key))