# Apstra-MCP-Server

This is to connect Apstra with A2A (Agent-to-Agent) using Claude & MCP.

I was inspired by Nitin Vig to try this one, please visit his Github for more detail on how to create the MCP Server/Client connectivity: https://github.com/vignitin/apstra-mcp-server  

# Connection Detail

<img width="905" height="174" alt="image" src="https://github.com/user-attachments/assets/c72bbdc5-f1ba-4a01-8997-bd33eb953aa1" />

# Nota Bene

There is a small difference on the FastMCP command as follow:
Before version 2.10.3: fastmcp install <MCP Server Path>
After version 2.10.3: fastmcp install claude-desktop <MCP Server Path>

masnugro@mbp% fastmcp version
	FastMCP version:2.10.5
	MCP version:1.11.0
	Python version:3.13.3
	Platform: macOS-14.4-arm64-arm-64bit-Mach-O

full available command:

fastmcp --help
Usage: fastmcp COMMAND

FastMCP 2.0 - The fast, Pythonic way to build MCP servers and clients.

Commands 
dev        Run an MCP server with the MCP Inspector for development.                                                                                                                             inspect    Inspect an MCP server and generate a JSON report.                                                                                                                                     install    Install MCP servers in various clients and formats.                                                                                                                                   run        Run an MCP server or connect to a remote one.                                                                                                                                          version    Display version information and platform details.                                                                                                                                       --help -h  Display this message and exit.                                                                                                                                                          --version  Display application version.                                                                                                                                                          

#disclaimer

The functions available tools (apstra_mcp.py) is a living documentation, I will try to add the capabilities along the time and it is not perfect. :) 
