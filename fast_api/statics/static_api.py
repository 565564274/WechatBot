from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html

static_app = FastAPI(docs_url=None, redoc_url=None)


@static_app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=static_app.openapi_url,
        title=static_app.title + " - Swagger UI",
        oauth2_redirect_url=static_app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@static_app.get(static_app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@static_app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=static_app.openapi_url,
        title=static_app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
