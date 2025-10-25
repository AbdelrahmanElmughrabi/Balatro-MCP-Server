# Balatro MCP Server (NOT COMPLETE)

An MCP (Model Context Protocol) server that allows Claude to analyze and recommend moves for the game Balatro by reading exported game state data.

## Overview

This project consists of three components:
1. **Lua Mod** (`main.lua`) - Exports Balatro game state to JSON (press F1 in-game)
2. **Python MCP Server** (`balatro_mcp_server.py`) - Reads the JSON and provides tools to Claude
3. **Claude Desktop Integration** - Allows Claude to analyze your Balatro games

## Prerequisites

- **Balatro** with [Steamodded](https://github.com/Steamopollys/Steamodded) mod loader installed
- **Python 3.11+**
- **Claude Desktop** application
- **Windows** (instructions are Windows-specific, but adaptable to other OS)

## Installation

### 1. Set Up the Lua Mod

1. Copy the `main.lua` file from this repository to:
```
%AppData%\Balatro\Mods\mcp-bridge\main.lua
```

2. Restart Balatro to load the mod

3. Verify the mod is loaded (you should see the message in console)

**What it does:** 
- Hooks into the F1 key
- Exports current game state to JSON
- Saves to: `%AppData%\Balatro\mcp-bridge\mcp_gamestate.json`

### 2. Set Up the Python MCP Server

1. **Clone or download this repository**

2. **Create a virtual environment:**
```bash
cd Balatro-MCP-Server
python -m venv .venv
```

3. **Activate the virtual environment:**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install mcp
```

5. **The `balatro_mcp_server.py` file is already in the repository** - no need to create it

**Key features of the server:**
- Automatically handles Windows encoding issues
- Provides `read_game_state` tool to fetch game data
- Provides `get_hand_analysis` tool to analyze poker hands

### 3. Configure Claude Desktop

1. **Locate your Claude Desktop config file:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

2. **Edit the config file** (create it if it doesn't exist) and add your server:

```json
{
  "mcpServers": {
    "balatro": {
      "command": "python",
      "args": [
        "-u",
        "C:\\Users\\YOUR_USERNAME\\Path\\To\\Balatro-MCP-Server\\balatro_mcp_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Important:**
- Replace `YOUR_USERNAME` and the path with your actual absolute path to `balatro_mcp_server.py`
- Use double backslashes `\\` in Windows paths
- The `-u` flag enables unbuffered Python output
- If you have other MCP servers, add this as another entry in the `mcpServers` object

3. **Restart Claude Desktop completely**
   - Quit Claude Desktop
   - Check Task Manager to ensure it's fully closed
   - Restart Claude Desktop

## Usage

1. **Launch Balatro** with the mod enabled
2. **Start a game** and navigate to any point where you have cards
3. **Press F1** to export the current game state
   - You should see a console message: `[MCP Bridge] ✓ Exported: X cards, Y jokers`
4. **Open Claude Desktop** and start a conversation
5. **Ask Claude** to read your game state:
   ```
   Can you read my current Balatro game state?
   ```

Claude will automatically use the `read_game_state` tool to fetch your game data!

## Available Tools

### `read_game_state`
Reads the exported JSON file and returns:
- 💰 Cash, hands left, discards left
- 📊 Current ante/round and blind information
- 🃏 All cards in your hand (with enhancements, editions, seals)
- 🎭 All jokers (with editions)
- 🎴 Deck size
- Raw JSON data for debugging

### `get_hand_analysis`
Analyzes your current hand and identifies possible poker hands:
- Pairs, two pairs, three of a kind, four of a kind
- Full house
- Flush
- Suit and rank distributions

## Example Interaction

```
You: Read my Balatro game state

Claude: I'll check your current Balatro game state.
[Uses read_game_state tool]

=== Balatro Game State ===

💰 Cash: $12
🎴 Hands Left: 3
🗑️ Discards Left: 2

📊 Ante: 2 | Round: 1
🎯 Chips to Beat: 450
👁️ Current Blind: Big Blind

🃏 Current Hand (8 cards):
  • King of Hearts
  • King of Diamonds
  • 7 of Spades
  • 3 of Clubs
  • Ace of Hearts (Enhancement: m_steel)
  ...

You: What's the best play here?

Claude: Looking at your hand, you have a pair of Kings which is solid...
[Claude analyzes and suggests moves]
```

## Troubleshooting

### "Game state file not found"
- Make sure you pressed **F1** in Balatro to export the state
- Check that the file exists at: `%APPDATA%\Balatro\mcp-bridge\mcp_gamestate.json`
- Verify the Lua mod is loaded in Balatro's mod menu
- Check Balatro console for `[MCP Bridge] Loaded` message

### MCP Server Won't Connect to Claude
- Ensure Python 3.11+ is installed: `python --version`
- Verify the path in `claude_desktop_config.json` is correct and absolute
- Use double backslashes `\\` in Windows paths
- Completely restart Claude Desktop (quit from Task Manager if needed)
- Check Claude's logs: **Help → Developer Tools → Console**
- Try running the server manually to test: `python balatro_mcp_server.py`

### Server Crashes on Startup
- Ensure the encoding fixes are in `balatro_mcp_server.py` (Windows-specific)
- Check that `PYTHONIOENCODING=utf-8` is in your Claude config
- Look for error messages in Claude's Developer Console

### F1 Key Not Working in Balatro
- Verify Steamodded is properly installed
- Check if another mod is conflicting with the F1 key
- Look for error messages in Balatro's console

## Project Structure

```
Balatro-MCP-Server/
├── balatro_mcp_server.py      # MCP server (main file)
├── main.lua                    # Lua mod for Balatro
├── .venv/                      # Python virtual environment (created during setup)
├── README.md                   # This file
└── .gitignore

%APPDATA%/Balatro/
├── Mods/
│   └── mcp-bridge/
│       └── main.lua            # Copy the Lua mod here
└── mcp-bridge/
    └── mcp_gamestate.json      # Auto-generated when you press F1

%APPDATA%/Claude/
└── claude_desktop_config.json  # Claude MCP configuration
```

## How It Works

1. **Game State Export**: The Lua mod hooks into Balatro's game loop and watches for F1 keypress
2. **JSON Export**: When F1 is pressed, it serializes the current game state to JSON
3. **MCP Server**: Python server monitors the JSON file and provides it to Claude via MCP protocol
4. **Claude Integration**: Claude reads the tools and can call them to analyze your game

## Development

### Testing the Server Standalone
```bash
```bash
python balatro_mcp_server.py
```
The server should start and wait for input. Press Ctrl+C to stop.

### Viewing Debug Logs
All server logs are written to stderr and appear in Claude's Developer Console:
- `[BALATRO] Starting...` - Server initializing
- `[BALATRO] list_tools called` - Claude querying available tools
- `[BALATRO] call_tool invoked: read_game_state` - Tool being executed

### Modifying the Lua Export
Edit `main.lua` to export additional game state:
- Consumables (tarot cards, planet cards, etc.)
- Shop contents
- Vouchers
- Deck modifications

## Future Enhancements

- [ ] **Scoring simulation**: Calculate exact chip values for different plays
- [ ] **Move recommendations**: Suggest optimal discards and plays based on jokers
- [ ] **Joker synergy analysis**: Identify powerful joker combinations
- [ ] **Deck state tracking**: Monitor consumables, vouchers, and shop items
- [ ] **Probability calculations**: Assess likelihood of drawing needed cards
- [ ] **Win condition analysis**: Calculate if current hand can beat the blind

## Contributing

Contributions are welcome! Some areas that need work:
- Straight detection in poker hand analysis
- Support for special Balatro hands (Flush Five, Flush House, etc.)
- Better joker effect simulation
- Real-time scoring calculations

## Technical Details

### Why MCP?
The Model Context Protocol allows Claude to access real-time data through standardized tools. This is better than:
- Pasting JSON manually (tedious)
- Screen scraping (unreliable)
- REST APIs (requires always-on server)

### Windows-Specific Fixes
The Python server includes critical Windows encoding fixes:
- UTF-8 encoding for stdin/stdout/stderr
- `PYTHONIOENCODING` environment variable
- Unbuffered output with `-u` flag

Without these, the MCP server crashes with `UnicodeDecodeError` on Windows.

## License

MIT

## Credits
- Requires [Steamodded](https://github.com/Steamopollys/Steamodded) mod loader

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all paths are correct in your config
3. Look for errors in Claude's Developer Console
4. Test the server manually with `python balatro_mcp_server.py`
5. Open an issue on GitHub with error logs

---
## Extra info
Will add more features in the future

**Happy Balatro playing! 🃏🎰**