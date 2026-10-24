from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve


def spa(request, *args, **kwargs):
    """Sert l'application React construite (frontend/dist/index.html)."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.exists():
        return HttpResponse(
            "Front-end non construit. Lancez : cd frontend && pnpm install && pnpm build",
            status=503, content_type="text/plain; charset=utf-8")
    return FileResponse(open(index, "rb"), content_type="text/html")


urlpatterns = [
    path("api/", include("segmentation.urls")),
    re_path(r"^assets/(?P<path>.*)$", serve, {"document_root": settings.FRONTEND_DIST / "assets"}),
    re_path(r"^(?P<path>favicon\.svg)$", serve, {"document_root": settings.FRONTEND_DIST}),
    re_path(r"^(?!api/|assets/).*$", spa),
]
