"""TiTiler-Image FastAPI application."""
import warnings

from rasterio.errors import NotGeoreferencedWarning, RasterioIOError

from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import CacheControlMiddleware
from titiler.image import __version__ as titiler_image_version
from titiler.image.factory import (
    DeepZoomFactory,
    IIIFFactory,
    MetadataFactory,
    TilerFactory,
)
from titiler.image.settings import api_settings

from fastapi import FastAPI

from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware

app = FastAPI(title=api_settings.name, version=titiler_image_version)

warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

DEFAULT_STATUS_CODES.update(
    {
        RasterioIOError: status.HTTP_404_NOT_FOUND,
    }
)

add_exception_handlers(app, DEFAULT_STATUS_CODES)

# Set all CORS enabled origins
if api_settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=api_settings.cachecontrol,
    exclude_path={r"/healthz"},
)

meta = MetadataFactory()
app.include_router(meta.router, tags=["Metadata"])

tiles = TilerFactory(router_prefix="/tiles")
app.include_router(tiles.router, tags=["Tiles"], prefix="/tiles")

iiif = IIIFFactory(router_prefix="/iiif")
app.include_router(iiif.router, tags=["IIIF"], prefix="/iiif")

deepzoom = DeepZoomFactory(router_prefix="/deepzoom")
app.include_router(deepzoom.router, tags=["Deepzoom"], prefix="/deepzoom")


###############################################################################
# Health Check Endpoint
@app.get(
    "/healthz",
    description="Health Check.",
    summary="Health Check.",
    operation_id="healthCheck",
    tags=["Health Check"],
)
def ping():
    """Health check."""
    return {"ping": "pong!"}