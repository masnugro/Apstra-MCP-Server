# Apstra-MCP-Server

This is to connect Apstra with Claude & MCP (FASTMCP/Claude Desktop) in order to interact with natural language.

I was inspired by Nitin Vig to try this one, please visit his Github for more detail on how to create the MCP Server/Client connectivity: https://github.com/vignitin/apstra-mcp-server  

# Connection Detail

<img width="905" height="174" alt="image" src="https://github.com/user-attachments/assets/c72bbdc5-f1ba-4a01-8997-bd33eb953aa1" />

# Nota Bene

```
There is a small difference on the FastMCP command as follow:
1/Before version 2.10.3: fastmcp install <MCP Server Path>
2/After version 2.10.3: fastmcp install claude-desktop <MCP Server Path>

masnugro@mbp% fastmcp version
	FastMCP version:2.10.5
	MCP version:1.11.0
	Python version:3.13.3
	Platform: macOS-14.4-arm64-arm-64bit-Mach-O

full available command:

fastmcp --help
Usage: fastmcp COMMAND

FastMCP 2.0 - The fast, Pythonic way to build MCP servers and clients.                                                                                                                             
```

## Tool List

```
1/ get blueprint
2/ get racks
3/ create virtual networks
4/ get difference status
5/ post (commit a new changes)
6/ get all blueprints
7/ get device OS
8/ get chassis profiles
9/ get Apstra version
10/ get running devices in blueprint
11/ create security zone
12/ get blueprint metric
13/ get remote gateway
14/ get property set
15/ get SRX configlet
16/ create a new blueprint
17/ delete virtual networks

```

## Sample Output

<img width="1497" height="878" alt="image" src="https://github.com/user-attachments/assets/245a7ef2-cb76-4b3d-a632-7199dc553090" />

<img width="747" height="719" alt="image" src="https://github.com/user-attachments/assets/850d04c7-b695-492b-a101-32aa565e1e6a" />

<img width="747" height="366" alt="image" src="https://github.com/user-attachments/assets/bb084ff9-5042-4423-b207-ee364a36c0a4" />


# Disclaimer
```
The functions available tools (apstra_mcp.py) is a living documentation, I will try to add the capabilities along the time and it is not perfect. :) 
```
