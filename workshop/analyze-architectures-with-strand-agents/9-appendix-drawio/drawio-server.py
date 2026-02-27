# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import base64
import binascii
import html
import io
import json
import logging
import urllib.parse
import warnings
import zlib
from typing import Dict

# Only for type hints and XML construction
from xml.etree.ElementTree import (  # nosec B405
    Element,
)

import defusedxml.ElementTree as ET
from defusedxml import defuse_stdlib
from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging
from PIL import Image

# Suppress defusedxml deprecation warning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="defusedxml")

# Defuse stdlib to prevent XML vulnerabilities
defuse_stdlib()

# Security limits for XML parsing
MAX_XML_SIZE = 50 * 1024 * 1024  # 50MB
MAX_DECOMPRESSED_SIZE = 100 * 1024 * 1024  # 100MB
MAX_DIAGRAM_COUNT = 100

# PlantUML size limits
MAX_PLANTUML_OBJECTS = 50
MAX_PLANTUML_JSON_SIZE = 1024 * 1024  # 1MB limit per PlantUML object
MAX_DECODED_JSON_SIZE = 512 * 1024  # 512KB limit for decoded JSON
MAX_PLANTUML_SOURCE_SIZE = 256 * 1024  # 256KB limit per PlantUML source


# Reconfigure FastMCP logging with custom time format
configure_logging(
    level="INFO",
    log_time_format="%Y-%m-%dT%H:%M:%S",
)
mcp = FastMCP("DrawIO Server")

# Use from your Strands agents with this code:
#
# Example 1: Basic MCP client setup
# from mcp import StdioServerParameters, stdio_client
# from strands.tools.mcp import MCPClient
#
# drawio_mcp_client = MCPClient(
#     lambda: stdio_client(
#         StdioServerParameters(command="uv", args=["run", "drawio-server.py"])
#     )
# )
#
# Example 2: Using the client in an agent
# with drawio_mcp_client:
#     tools = drawio_mcp_client.list_tools_sync()
#     # Process tools for diagram analysis

def parse_styles(mxCell):  # pylint: disable=invalid-name
    styles = {}
    style_attr = mxCell.get("style")
    if style_attr:
        style_parts = style_attr.split(";")
        for kv in style_parts:
            if "=" in kv:
                key, value = kv.split("=", 1)
                if key:
                    styles[key] = value
    return styles


def find_legacy_aws_shapes(mxfile: Element) -> Dict:
    legacy_aws_shapes = {}
    cells = mxfile.findall(".//mxCell")
    for cell in cells:
        cell_id = cell.get("id")
        label = cell.get("value")
        styles = parse_styles(cell)
        shape = styles.get("shape", "")
        pr_icon = styles.get("prIcon", "")
        # amazonq-ignore-next-line
        res_icon = styles.get("resIcon", "")  # pylint: disable=unused-variable

        if "mxgraph.aws3." in shape or "mxgraph.aws4.productIcon" in shape:
            legacy_aws_shapes[cell_id] = {
                "label": label,
                "shape": shape,
                "pr_icon": pr_icon,
            }

    return legacy_aws_shapes


def parse_drawio_xml(drawio: str) -> Element:
    # Check input size limit
    if len(drawio.encode("utf-8")) > MAX_XML_SIZE:
        raise ValueError(f"XML input too large: {len(drawio)} bytes > {MAX_XML_SIZE}")

    # Parse with defusedxml for security
    try:
        mxfile = ET.fromstring(drawio)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {str(e)}") from e

    if mxfile.tag != "mxfile":
        return None

    diagram_count = 0
    for child in mxfile:
        diagram_count += 1
        if diagram_count > MAX_DIAGRAM_COUNT:
            raise ValueError(
                f"Too many diagrams: {diagram_count} > {MAX_DIAGRAM_COUNT}"
            )

        if child.text and child.text.strip():
            try:
                # Decode and check size before decompression
                encoded_data = child.text
                if len(encoded_data) > MAX_XML_SIZE // 2:  # Conservative estimate
                    raise ValueError("Encoded diagram data too large")

                decoded_data = base64.b64decode(encoded_data)
                decompressed = zlib.decompress(decoded_data, -15)

                # Check decompressed size
                if len(decompressed) > MAX_DECOMPRESSED_SIZE:
                    raise ValueError(
                        f"Decompressed data too large: {len(decompressed)} > {MAX_DECOMPRESSED_SIZE}"
                    )

                uri_decoded = urllib.parse.unquote(decompressed.decode("utf-8"))
                mxGraphModel = ET.fromstring(uri_decoded)  # pylint: disable=invalid-name

                # Replace child.text with mxGraphModel content, preserving attributes
                child.text = None
                # Clear only the text content, not the attributes
                for elem in list(child):
                    child.remove(elem)
                child.append(mxGraphModel)

            except (
                binascii.Error,
                zlib.error,
                ET.ParseError,
                ValueError,
                UnicodeDecodeError,
            ) as e:
                raise ValueError(f"Failed to parse diagram data: {str(e)}")

    return mxfile


@mcp.tool
def validate_drawio(drawio_xml_string: str) -> Dict:
    """
    Validate draw.io XML string representation and return validated XML, version and list of embedded diagram ids.
    This detects when XML <diagram> content is compressed and expands into normalized XML.

    Args:
        drawio_xml_string: draw.io XML string representation which is the full contexts of a .drawio file

    Returns:
        Dict containing status and response content in the format:
        {
            "status": "success|error",
            "content": "<drawio_xml_string>",
            "version": "<drawio_version>",
            "diagram_ids": ["<diagram_id>"]
        }

        Success case: Returns the validation result with appropriate formatting
        Error case: Returns message about what went wrong during validation
    """
    try:
        mxfile = parse_drawio_xml(drawio_xml_string)
        if mxfile is None:
            return {"status": "error", "message": "Invalid DrawIO XML format"}
    except ValueError as e:
        return {"status": "error", "message": f"Security validation failed: {str(e)}"}

    #  If encoding is "unicode", a string is returned. Otherwise a bytestring is returned.
    content = ET.tostring(mxfile, encoding="unicode")
    diagram_ids = [
        diagram.get("id")
        for diagram in mxfile.findall("./diagram")
        if diagram.get("id")
    ]

    return {
        "status": "success",
        "content": content,
        "version": mxfile.get("version", ""),
        "diagram_ids": diagram_ids,
    }


@mcp.tool
def extract_plantuml_from_drawio(drawio_xml_string: str) -> Dict:
    """
    Extracts embedded PlantUML source from a draw.io XML string representation and return validated XML, version and list of embedded diagram ids.

    Args:
        drawio_xml_string: draw.io XML string representation which is the full contexts of a .drawio file

    Returns:
        Dict containing status and response content in the format:
        {
            "status": "success|error",
            "content": [{"<plantuml_object_id>": "<plantuml_object_source"}]
        }

        Success case: Returns the extraction result of any PlantUML objects with their id and source
        Error case: Returns message about what went wrong during extraction
    """
    try:
        mxfile = parse_drawio_xml(drawio_xml_string)
    except ValueError as e:
        return {"status": "error", "message": f"Security validation failed: {str(e)}"}

    if mxfile is None:
        return {"status": "error", "message": "Invalid DrawIO XML format"}

    logging.info(
        "Extracting PlantUML from draw.io XML: %s", mxfile.get("version", "unknown")
    )

    plantuml_data = []
    plantuml_count = 0
    for user_object in mxfile.findall(".//UserObject[@plantUmlData]"):
        plantuml_count += 1
        if plantuml_count > MAX_PLANTUML_OBJECTS:
            logging.warning("Limiting PlantUML objects to %s", MAX_PLANTUML_OBJECTS)
            break

        plant_uml_json = user_object.get("plantUmlData")
        if plant_uml_json and len(plant_uml_json) < MAX_PLANTUML_JSON_SIZE:
            try:
                # Decode HTML entities
                decoded_json = html.unescape(plant_uml_json)
                # Parse JSON with size limit
                if len(decoded_json) > MAX_DECODED_JSON_SIZE:
                    continue
                json_data = json.loads(decoded_json)
                # Extract PlantUML source from data field
                plantuml_source = json_data.get("data", "")
                if len(plantuml_source) < MAX_PLANTUML_SOURCE_SIZE:
                    plantuml_data.append(
                        {
                            "id": user_object.get("id"),
                            "plantuml_source": plantuml_source,
                        }
                    )
            except (json.JSONDecodeError, KeyError):
                continue

    return {"status": "success", "content": plantuml_data}


@mcp.tool
def extract_drawio_xml_from_image(image_data: str) -> Dict:
    """
    Extract draw.io XML string representation from a PNG image with the .drawio.png extension.

    Args:
        image_data: Base64-encoded PNG image data which is the full contexts of a .png file

    Returns:
        Dict containing status and response content in the format:
        {
            "status": "success|error",
            "content": "<drawio_xml_string>"
        }

        Success case: Returns the extraction result with appropriate formatting
        Error case: Returns message about what went wrong during extraction
    """
    try:
        decoded_data = base64.b64decode(image_data)
        with Image.open(io.BytesIO(decoded_data)) as image:
            image.load()  # needed for .png zTXt / tEXt data
            if "mxfile" not in image.info:
                return {
                    "status": "error",
                    "message": "Image does not contain DrawIO metadata",
                }
            drawio_xml_string = urllib.parse.unquote(image.info["mxfile"])
            # Validate extracted XML size
            if len(drawio_xml_string.encode("utf-8")) > MAX_XML_SIZE:
                return {"status": "error", "message": "Extracted XML too large"}
            mxfile = parse_drawio_xml(drawio_xml_string)
            # ET.indent(mxfile)
            content = ET.tostring(mxfile, encoding="unicode")
    except (
        binascii.Error,
        Image.UnidentifiedImageError,
        ET.ParseError,
        UnicodeDecodeError,
    ) as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "content": content}


@mcp.prompt
def ask_about_shape_icons(drawio_file: str) -> str:
    """Generates a user message asking for the shape icons found in a .drawio file"""
    return f"list the shape icons found in {drawio_file} - first use the validate_drawio tool with the full contents of a .drawio file"


if __name__ == "__main__":
    mcp.run(show_banner=False)
