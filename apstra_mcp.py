from fastmcp import FastMCP
import httpx
import sys
from typing import Optional, Dict, List, Union

# Create an MCP server
mcp = FastMCP("Apstra MCP server")

# IP of Cloudlabs AOS Server
aos_server = 'Your Apstra Instance ID'
username = 'XXX'
password = 'YYY'

# Token cache to avoid repeated auth calls
_token_cache: Optional[Dict[str, str]] = None

def auth(aos_server: str, username: str, password: str) -> Optional[Dict[str, str]]:
    """
    Authenticate with the AOS server and return headers with AuthToken.
    Uses cached token if available.
    """
    global _token_cache
    if _token_cache:
        return _token_cache

    try:
        url_login = f'https://{aos_server}/api/user/login'
        headers_init = {'Content-Type': "application/json", 'Cache-Control': "no-cache"}
        data = {"username": username, "password": password}
        response = httpx.post(url_login, json=data, headers=headers_init, verify=False)
        if response.status_code != 201:
            print(f"Authentication failed: {response.status_code} - {response.text}", file=sys.stderr)
            return None
        auth_token = response.json().get('token')
        if not auth_token:
            print("No token found in authentication response", file=sys.stderr)
            return None
        headers = {
            'AuthToken': auth_token,
            'Content-Type': "application/json",
            'Cache-Control': "no-cache"
        }
        _token_cache = headers
        return headers
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_bp() -> Optional[List[dict]]:
    """Gets blueprint information"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_bp: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_racks(blueprint_id: str) -> Optional[List[dict]]:
    """Gets rack information for a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/racks'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_racks: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_rz(blueprint_id: str) -> Optional[dict]:
    """Gets routing zone information for a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/security-zones'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An unexpected error occurred in get_rz: {e}", file=sys.stderr)
        return None

@mcp.tool()
def create_vn(blueprint_id: str, security_zone_id: str, vn_name: str) -> Optional[dict]:
    """Creates a virtual network in a given blueprint and routing zone"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/virtual-networks'
        data = {
            "label": vn_name,
            "vn_type": "vxlan",
            "security_zone_id": security_zone_id
        }
        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An unexpected error occurred in create_vn: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_diff_status(blueprint_id: str) -> Optional[dict]:
    """Gets the diff status for a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/diff-status'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An unexpected error occurred in get_diff_status: {e}", file=sys.stderr)
        return None

@mcp.tool()
def deploy(blueprint_id: str, description: str, staging_version: int) -> Optional[dict]:
    """Deploys the config for a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/deploy'
        data = {
            "version": staging_version,
            "description": description
        }
        response = httpx.put(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An unexpected error occurred in deploy: {e}", file=sys.stderr)
        return None

@mcp.tool()
def delete_bp(blueprint_id: str) -> Optional[dict]:
    """Delete the blueprint from Apstra Instance"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}'
        response = httpx.delete(url, headers=headers, verify=False)
        response.raise_for_status()
        return {"message": "Blueprint deleted succesfully"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        print(f"An unexpected error occurred in delete_bp: {e}", file=sys.stderr)
        return None

@mcp.tool()
def create_blueprint_from_template(label: str, init_type: str = "template_reference") -> Optional[dict]:
    """
    Creates a new blueprint using the 'Rack Based' template, initialized appropriately so it appears in Apstra UI.
    """
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None

        # 1. Get available templates
        templates_url = f"https://{aos_server}/api/blueprints/templates"
        templates_resp = httpx.get(templates_url, headers=headers, verify=False)
        templates_resp.raise_for_status()
        templates = templates_resp.json().get("items", [])

        # 2. Find the 'Rack Based' template
        rack_template = next((t for t in templates if t.get("name") == "Rack Based"), None)
        if not rack_template:
            print("Rack Based blueprint template not found.", file=sys.stderr)
            return {"error": "Rack Based blueprint template not found"}

        # 3. Create blueprint with correct init_type
        create_url = f"https://{aos_server}/api/blueprints"
        data = {
            "label": label,
            "template_id": rack_template["id"],
            "init_type": init_type
        }
        create_resp = httpx.post(create_url, json=data, headers=headers, verify=False)
        create_resp.raise_for_status()
        return create_resp.json()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error in create_blueprint_from_template: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return {"error": f"{e.response.status_code} - {e.response.text}"}
    except Exception as e:
        print(f"Unexpected error in create_blueprint_from_template: {e}", file=sys.stderr)
        return None


@mcp.tool()
def list_virtual_networks(blueprint_id: str) -> Optional[List[dict]]:
    """List all virtual networks in a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/experience/web/virtual-networks'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get("items", [])
    except Exception as e:
        print(f"An unexpected error occurred in list_virtual_networks: {e}", file=sys.stderr)
        return None

@mcp.tool()
def delete_vn(blueprint_id: str, security_zone_id: str, vn_name: str) -> Optional[dict]:
    """delete a virtual network in a given blueprint and routing zone"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/delete-virtual-networks'
        data = {
            "label": vn_name,
            "vn_type": "vxlan",
            "security_zone_id": security_zone_id
        }
        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        resp_data = response.json()
        print("Delete VN API response:", resp_data, file=sys.stderr)
        return resp_data
    except Exception as e:
        print(f"An unexpected error occurred in delete_vn: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_devices_os(blueprint_id: str) -> Optional[List[dict]]:
    """Gets devices OS from a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/device-os/platforms'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_devices_os: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_chassis_profiles(blueprint_id: str) -> Optional[List[dict]]:
    """Gets chassis profile from a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/chassis-profiles'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_chassis_profiles: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_apstra_version() -> Optional[dict]:
    """Get Apstra version"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/versions/server'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An unexpected error occurred in get_apstra_version: {e}", file=sys.stderr)
        return None

def get_alert() -> Optional[dict]:
    """Gets blueprint alert information"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/alert-events'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        print("License API response:", data)
        return data
    except Exception as e:
        print(f"An unexpected error occurred in get_alert: {e}", file=sys.stderr)
        return None

def get_license() -> Optional[List[dict]]:
    """Gets blueprint license information"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/cluster/licenses'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json().get('items')
        print("License API response:", data)
        return data
    except Exception as e:
        print(f"An unexpected error occurred in get_license: {e}", file=sys.stderr)
        return None

def get_vni_pools() -> Optional[List[dict]]:
    """Gets vni pools from blueprint information"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/resources/vni-pools'
        response = httpx.get(url, headers=headers, verify=False)
        print("Status code:", response.status_code)
        print ("Response body:", response.text)
        response.raise_for_status()
        data = response.json()
        vni_data = data.get("items",[])
        print("Full JSON:", data)

        if vni_data is None:
            print("No 'items' found, returning raw data", file=sys.stderr)
        return vni_data
    except Exception as e:
        print(f"An unexpected error occurred in get_vni_pools: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_systems(blueprint_id: str) -> Optional[List[dict]]:
    """Gets Switches information from a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/systems'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_devices_os: {e}", file=sys.stderr)
        return None

@mcp.tool() # new
def create_security_zone(
    blueprint_id: str,
    label: str,
    vlan_id: int,
    route_target: str = None,
    vni: int = None,
    vrf_name: str = None
) -> Optional[dict]:
    """
    Creates a security zone in a given blueprint with VLAN ID, Route Target, sz_type and VNI.
    """
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return {"error": "Authentication failed"}

        url = f"https://{aos_server}/api/blueprints/{blueprint_id}/security-zones"

        if vrf_name is None:
            vrf_name = label

        data = {
            "label": label,
            "vlan_id": vlan_id,
            "sz_type": "evpn",
            "vrf_name": vrf_name,
            "junos_evpn_irb_mode": "asymmetric"
        }

        if route_target:
            data["route_target"] = route_target
        if vni:
            data["vni_id"] = vni

        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}", "detail": e.response.text}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_blueprint_metrics(blueprint_id: str) -> Optional[dict]:
    """
    Retrieves operational metrics for a given blueprint.
    This may include resource utilization, system status, or traffic stats (depending on Apstra version).
    """
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None

        url = f"https://{aos_server}/api/metricdb/metric"
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()

        metrics = response.json()

        # Optionally log or filter here
        return metrics

    except httpx.HTTPStatusError as e:
        print(f"HTTP error in get_blueprint_metrics: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return {"error": f"{e.response.status_code} - {e.response.text}"}
    except Exception as e:
        print(f"Unexpected error in get_blueprint_metrics: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_remote_gw (blueprint_id: str) -> Optional[dict]:
    """
    get remote_gw information in blueprint
    """
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None

        url = f"https://{aos_server}/api/blueprints/{blueprint_id}/remote_gateways"
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()

        metrics = response.json()

        # Optionally log or filter here
        return metrics

    except httpx.HTTPStatusError as e:
        print(f"HTTP error in get_blueprint_metrics: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        return {"error": f"{e.response.status_code} - {e.response.text}"}
    except Exception as e:
        print(f"Unexpected error in get_blueprint_metrics: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_property_set (blueprint_id: str) -> Optional[List[dict]]:
    """Gets property set information from blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/property-sets'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_devices_os: {e}", file=sys.stderr)
        return None

@mcp.tool()
def get_srx_configlet (blueprint_id: str) -> Optional[List[dict]]:
    """Gets SRX property set information from blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return None
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/configlets'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('items')
    except Exception as e:
        print(f"An unexpected error occurred in get_devices_os: {e}", file=sys.stderr)
        return None
