from starlette.responses import JSONResponse

class UploadBodyLimit:
    """Acota todo el multipart antes de que el parser cree archivos temporales."""
    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].rstrip("/") != "/api/transactions/upload":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                return await JSONResponse({"detail": "La solicitud excede el tamaño permitido."}, status_code=413)(scope, receive, send)
            chunks.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(chunks)
        async def replay():
            return next(iterator, {"type": "http.request", "body": b"", "more_body": False})
        await self.app(scope, replay, send)
