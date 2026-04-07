from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.services.dongwon import (
    convert_pipeline,
)
from app.services.convert_dongwon import (
    extract_gauce_headers,
    extract_grid_schema,
)
from app.services.event_converter import convert_script_events

from app.services.donwon_properties import (
    extract_table_controls_text,
)

from app.services.dongwon_oz import convert_oz

router = APIRouter()


class ConvertFunctionRequest(BaseModel):
    code: str
    type: str


object_attr_keys = ["objType", "mandatory", "validExp"]

# <param> name에서 가져올 키 (필요한 것만!)
param_keys = ["DataID", "Format", "UpperFlag", "ReadOnly"]

# <input>에서 가져올 키(옵션)
input_attr_keys = ["objType", "mandatory", "validExp", "maxlength"]


@router.post("/convert_function_raw")
async def convert_function_raw(request: ConvertFunctionRequest):
    _type = request.type
    if _type == "function":
        converted_code = convert_pipeline(request.code)
    elif _type == "header":
        converted_code = extract_gauce_headers(request.code)
    elif _type == "grid":
        converted_code = extract_grid_schema(request.code)
    elif _type == "script":
        converted_code = convert_script_events(request.code)
    elif _type == "properties":
        converted_code = extract_table_controls_text(
            request.code, object_attr_keys, param_keys, input_attr_keys
        )
    elif _type == "oz":
        converted_code = convert_oz(request.code)

    return {"converted_code": converted_code}


class AnalyzeSchemaRequest(BaseModel):
    code: str


@router.post("/analyze-schema")
async def analyze_schema(code: str = Body(..., media_type="text/plain")):
    datacollection = extract_gauce_headers(code)

    return datacollection
