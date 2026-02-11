from mcp.server.fastmcp import FastMCP
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("NowCerts Server")

TOKEN_URL = "https://test-null-ref-express.nowcerts.com/api/token/exchange-api-key"
ODATA_URL = "https://test-null-ref-express.nowcerts.com/api/odata/InsuredDetailList"
INSERT_INSURED_URL = "https://test-null-ref-express.nowcerts.com/api/Insured/Insert"
API_KEY = "amp_ai_mLz0esF0pqsVAZgGWF2Y2oMAwqebSt1qudYB48pqo7RC7ZrH0ON80CJo5O5UngG6J1x0LFxhr5WYvwM67w"

# Simple in-memory cache to ensure we can return quickly if the external API is slow.
CACHED_SUMMARY = None
CACHE_TS = 0
CACHE_TTL = 300  # seconds


def get_access_token(timeout: int = 4):
    response = requests.post(
        TOKEN_URL,
        params={"apiKey": API_KEY},
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("accessToken")


@mcp.tool()
def get_insured_list(top: int = 30, skip: int = 0) -> str:
    logging.info("get_insured_list called with top=%s, skip=%s", top, skip)
    # Return cached result immediately if fresh
    import time

    global CACHED_SUMMARY, CACHE_TS
    if CACHED_SUMMARY and (time.time() - CACHE_TS) < CACHE_TTL:
        logging.info("get_insured_list returning cached result")
        return CACHED_SUMMARY
    try:
        access_token = get_access_token(timeout=4)
        logging.info("get_insured_list obtained access token: %s", "<redacted>" if access_token else "None")

        params = {
            "$count": "true",
            "$orderby": "changeDate DESC",
            "$skip": skip,
            "$top": top
        }

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        # Keep the request short so the ADK MCP client (5s default) doesn't time out.
        response = requests.get(ODATA_URL, headers=headers, params=params, timeout=4)
        response.raise_for_status()

        data = response.json()

        # Return only first few names to avoid huge JSON
        items = data.get("value", [])
        if not items:
            logging.info("get_insured_list: no items returned from API")
            return "No insured records found."

        summary = []
        for item in items[:5]:
            summary.append(str(item))

        logging.info("get_insured_list returning %s items", len(summary))
        result = "\n\n".join(summary)
        # update cache
        CACHED_SUMMARY = result
        CACHE_TS = time.time()
        return result

    except Exception as e:
        logging.exception("Error in get_insured_list")
        # If we have a cached result, return it as a fallback
        if CACHED_SUMMARY:
            logging.info("get_insured_list returning stale cached result due to error")
            return CACHED_SUMMARY
        return f"Error: {str(e)}"


@mcp.tool()
def insert_insured(
    database_id: str,
    first_name: str,
    last_name: str,
    middle_name: str = "",
    insured_type: int = 0,
    address_line1: str = "",
    address_line2: str = "",
    city: str = "",
    state: str = "",
    zip_code: str = "",
    cell_phone: str = "",
    email: str = "",
    fein: str = "",
    description: str = "",
    active: bool = True,
    custom_id: str = "",
    insured_id: str = "",
) -> str:
    """Insert a new insured record into NowCerts system."""
    logging.info("insert_insured called with first_name=%s, last_name=%s", first_name, last_name)
    
    try:
        access_token = get_access_token(timeout=4)
        logging.info("insert_insured obtained access token: <redacted>")
        
        # Build payload
        payload = {
            "databaseId": database_id,
            "firstName": first_name,
            "lastName": last_name,
            "middleName": middle_name,
            "type": insured_type,
            "addressLine1": address_line1,
            "addressLine2": address_line2,
            "city": city,
            "state": state,
            "zipCode": zip_code,
            "cellPhone": cell_phone,
            "email": email,
            "fein": fein,
            "description": description,
            "active": active,
            "customerId": custom_id,
            "insuredId": insured_id,
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(
            INSERT_INSURED_URL,
            json=payload,
            headers=headers,
            timeout=4
        )
        response.raise_for_status()
        
        result = response.json()
        logging.info("insert_insured succeeded for %s %s", first_name, last_name)
        return f"Successfully inserted insured: {first_name} {last_name}. Response: {result}"
        
    except Exception as e:
        logging.exception("Error in insert_insured")
        return f"Error inserting insured: {str(e)}"


if __name__ == "__main__":
    print("Starting NowCerts MCP server (stdio transport). Waiting for connection...")
    try:
      mcp.run(transport="stdio")
      
    except Exception as e:
        print("MCP server exited with error:", repr(e))