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
def delete_bp(blueprint_id: str) -> dict:
    """Delete the blueprint from Apstra Instance"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return {"error": "Authentication failed"}
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}'
        response = httpx.delete(url, headers=headers, verify=False)
        response.raise_for_status()

        # Handle empty response
        if not response.text or response.text == '':
            return {"status": "success", "message": f"Blueprint {blueprint_id} deleted successfully"}

        return response.json()

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(f"HTTP error in delete_bp: {error_msg}", file=sys.stderr)
        return {"error": error_msg, "status": "failed"}
    except Exception as e:
        error_msg = f"Unexpected error in delete_bp: {e}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg, "status": "failed"}

@mcp.tool()
def create_blueprint_from_template(
    label: str,
    template_name: str = "connectorops_2spine4leaf",  # Changed default
    init_type: str = "template_reference"
) -> dict:
    """
    Creates a new blueprint using a specified template.
    """
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return {"error": "Authentication failed"}

        # 1. Get available templates
        templates_url = f"https://{aos_server}/api/design/templates"
        templates_resp = httpx.get(templates_url, headers=headers, verify=False)
        templates_resp.raise_for_status()

        templates_data = templates_resp.json()

        # Handle both dict and list responses
        if isinstance(templates_data, dict):
            templates = templates_data.get("items", {})
            if isinstance(templates, list):
                templates = {t.get("id", idx): t for idx, t in enumerate(templates)}
        elif isinstance(templates_data, list):
            templates = {t.get("id", idx): t for idx, t in enumerate(templates_data)}
        else:
            templates = {}

        # 2. Find the specified template
        target_template = None
        for template_id, template_data in templates.items():
            t_name = template_data.get("display_name") or template_data.get("label") or template_data.get("name")
            if t_name == template_name:
                target_template = template_data
                target_template["id"] = template_id
                break

        if not target_template:
            available = [t.get("display_name") or t.get("label") or t.get("name") for t in templates.values()]
            return {"error": f"Template '{template_name}' not found", "available_templates": available}

        # 3. Create blueprint
        create_url = f"https://{aos_server}/api/blueprints"
        data = {
            "label": label,
            "template_id": target_template["id"],
            "design": "two_stage_l3clos",
            "init_type": init_type
        }

        print(f"Creating blueprint with data: {data}", file=sys.stderr)
        create_resp = httpx.post(create_url, json=data, headers=headers, verify=False)
        create_resp.raise_for_status()

        if not create_resp.text or create_resp.text == '':
            return {"status": "success", "message": f"Blueprint '{label}' created successfully"}

        return create_resp.json()

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(f"HTTP error: {error_msg}", file=sys.stderr)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}

@mcp.tool()
def list_virtual_networks(blueprint_id: str) -> dict:
    """List all virtual networks in a blueprint"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return {"error": "Authentication failed"}

        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/experience/web/virtual-networks'
        response = httpx.get(url, headers=headers, verify=False)
        response.raise_for_status()

        data = response.json()
        virtual_networks = data.get("virtual_networks", {})

        return {
            "virtual_networks": virtual_networks,
            "count": len(virtual_networks),
            "version": data.get("version")
        }

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred in list_virtual_networks: {e}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}

@mcp.tool()
def delete_vn(blueprint_id: str, security_zone_id: str, vn_name: str) -> dict:
    """delete a virtual network in a given blueprint and routing zone"""
    try:
        headers = auth(aos_server, username, password)
        if not headers:
            return {"error": "Authentication failed"}

        # First, get the virtual network ID by listing all VNs
        list_url = f'https://{aos_server}/api/blueprints/{blueprint_id}/virtual-networks'
        list_response = httpx.get(list_url, headers=headers, verify=False)
        list_response.raise_for_status()

        vn_id = None
        vns = list_response.json()

        # Find the VN ID by matching name and security zone
        if 'virtual_networks' in vns:
            for vn in vns['virtual_networks'].values():
                if vn.get('label') == vn_name and vn.get('security_zone_id') == security_zone_id:
                    vn_id = vn.get('id')
                    break

        if not vn_id:
            return {"error": f"Virtual network '{vn_name}' not found in security zone {security_zone_id}"}

        # Now delete using the VN ID
        url = f'https://{aos_server}/api/blueprints/{blueprint_id}/delete-virtual-networks'
        data = {
            "virtual_network_ids": [vn_id]  # API expects a list of IDs
        }
        response = httpx.post(url, json=data, headers=headers, verify=False)
        response.raise_for_status()

        # Handle empty response
        if not response.text or response.text == '':
            return {"status": "success", "message": f"Virtual network '{vn_name}' (ID: {vn_id}) deleted successfully"}

        resp_data = response.json()
        print("Delete VN API response:", resp_data, file=sys.stderr)
        return resp_data

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred in delete_vn: {e}"
        print(error_msg, file=sys.stderr)
        return {"error": error_msg}

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
