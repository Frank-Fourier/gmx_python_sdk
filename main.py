import sys
import asyncio
import socketio
from gmx_python_sdk.scripts.v2.gmx_utils import Config, create_connection
from gmx_python_sdk.scripts.v2.get_gm_prices import GMPrices

# Set up socket.io server
sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio)

# Global variable to store price updates
price_updates = {}

# Configuration setup
config = {
    'arbitrum': {
        'rpc': "https://arbitrum-mainnet.infura.io/v3/cd67bf30b3a64391805989ba259cec10",
        'chain_id': 42161
    },
    'avalanche': {
        'rpc': None,
        'chain_id': None
    },
    'private_key': None,
    'user_wallet_address': None
}

config_obj = Config()
config_obj.set_config(config)

web3_connection = create_connection(config['arbitrum']['rpc'], 'arbitrum')

if not web3_connection.is_connected():
    print("Failed to connect to the Arbitrum network.", file=sys.stderr)
    sys.exit(1)

gm_prices = GMPrices(chain='arbitrum')

async def fetch_prices():
    try:
        prices = gm_prices.get_price_traders()  # Assume synchronous
        return prices
    except Exception as e:
        print(f"An error occurred while fetching prices: {e}", file=sys.stderr)
        return None

async def send_price_updates():
    while True:
        prices = await fetch_prices()
        if prices:
            price_updates.update(prices)
            await sio.emit('price_update', price_updates)
            print(f"Prices updated and emitted: {price_updates}")
        await asyncio.sleep(60)

@sio.event
async def connect(sid, environ):
    print(f"New client connected: {sid}")
    await sio.emit('price_update', price_updates)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

if __name__ == "__main__":
    import uvicorn
    # Start the send_price_updates task before running the Uvicorn server
    asyncio.run(send_price_updates())
    uvicorn.run(app, host="0.0.0.0", port=8000)
