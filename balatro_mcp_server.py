import json
import asyncio
from pathlib import Path
import os
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

# Path to the JSON file
APPDATA = os.getenv('APPDATA')
JSON_PATH = Path(APPDATA) / "Balatro" / "mcp-bridge" / "mcp_gamestate.json"

# Create the MCP server
server = Server("balatro-agent")
print("MCP server created")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="read_game_state",
            description="Read the current Balatro game state from the exported JSON file. Returns information about current hand, jokers, chips needed, cash, hands/discards remaining, and more.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_hand_analysis",
            description="Analyze what poker hands can be made from the current cards in hand. Returns all possible poker hands (pairs, flush, straight, etc.) that can be formed.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
        name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution."""

    if name == "read_game_state":
        try:
            if not JSON_PATH.exists():
                return [types.TextContent(
                    type="text",
                    text="Error: Game state file not found. Make sure Balatro is running and you've pressed F1 to export the game state."
                )]

            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                game_state = json.load(f)

            # Format the game state nicely
            output = "=== Balatro Game State ===\n\n"

            # Player info
            if 'player_data' in game_state:
                pd = game_state['player_data']
                output += f"💰 Cash: ${pd.get('cash', 0)}\n"
                output += f"🎴 Hands Left: {pd.get('hands_left', 0)}\n"
                output += f"🗑️ Discards Left: {pd.get('discards_left', 0)}\n\n"

            # Run info
            if 'run_info' in game_state:
                ri = game_state['run_info']
                output += f"📊 Ante: {ri.get('ante', 0)} | Round: {ri.get('round', 0)}\n"
                output += f"🎯 Chips to Beat: {ri.get('chips_to_beat', '0')}\n"
                output += f"👁️ Current Blind: {ri.get('current_blind_name', 'None')}\n\n"

            # Current hand
            if 'current_hand' in game_state and game_state['current_hand']:
                output += f"🃏 Current Hand ({len(game_state['current_hand'])} cards):\n"
                for card in game_state['current_hand']:
                    rank = card.get('rank', '?')
                    suit = card.get('suit', '?')
                    enhancement = card.get('enhancement', 'none')
                    edition = card.get('edition', 'none')
                    seal = card.get('seal', 'none')

                    extras = []
                    if enhancement != 'none': extras.append(f"Enhancement: {enhancement}")
                    if edition != 'none': extras.append(f"Edition: {edition}")
                    if seal != 'none': extras.append(f"Seal: {seal}")

                    extra_str = f" ({', '.join(extras)})" if extras else ""
                    output += f"  • {rank} of {suit}{extra_str}\n"
                output += "\n"

            # Jokers
            if 'jokers' in game_state and game_state['jokers']:
                output += f"🃏 Jokers ({len(game_state['jokers'])}):\n"
                for joker in game_state['jokers']:
                    name = joker.get('name', 'Unknown')
                    key = joker.get('key', '?')
                    edition = joker.get('edition', 'none')
                    edition_str = f" [{edition}]" if edition != 'none' else ""
                    output += f"  • {name}{edition_str} ({key})\n"
                output += "\n"

            # Add raw JSON for reference
            output += "\n=== Raw Game State JSON ===\n"
            output += json.dumps(game_state, indent=2)

            return [types.TextContent(type="text", text=output)]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error reading game state: {str(e)}"
            )]

    elif name == "get_hand_analysis":
        try:
            if not JSON_PATH.exists():
                return [types.TextContent(
                    type="text",
                    text="Error: Game state file not found."
                )]

            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                game_state = json.load(f)

            if 'current_hand' not in game_state or not game_state['current_hand']:
                return [types.TextContent(
                    type="text",
                    text="No cards in hand currently."
                )]

            cards = game_state['current_hand']

            # Simple poker hand detection
            output = "=== Possible Poker Hands ===\n\n"

            # Count ranks and suits
            ranks = {}
            suits = {}
            for card in cards:
                rank = card['rank']
                suit = card['suit']
                ranks[rank] = ranks.get(rank, 0) + 1
                suits[suit] = suits.get(suit, 0) + 1

            # Check for pairs, trips, etc.
            pairs = [r for r, count in ranks.items() if count == 2]
            trips = [r for r, count in ranks.items() if count == 3]
            quads = [r for r, count in ranks.items() if count == 4]

            if quads:
                output += f"✅ Four of a Kind: {quads[0]}\n"
            if trips:
                output += f"✅ Three of a Kind: {trips[0]}\n"
                if pairs:
                    output += f"✅ Full House: {trips[0]}s full of {pairs[0]}s\n"
            if len(pairs) >= 2:
                output += f"✅ Two Pair: {pairs[0]}s and {pairs[1]}s\n"
            elif len(pairs) == 1:
                output += f"✅ Pair: {pairs[0]}s\n"

            # Check for flush
            flush_suits = [s for s, count in suits.items() if count >= 5]
            if flush_suits:
                output += f"✅ Flush: {flush_suits[0]}\n"

            output += f"\n💡 You have {len(cards)} cards to work with\n"
            output += f"Suits: {dict(suits)}\n"
            output += f"Ranks: {dict(ranks)}\n"

            return [types.TextContent(type="text", text=output)]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing hand: {str(e)}"
            )]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="balatro-agent",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())