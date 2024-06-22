import os
import sys
import asyncio
import socketio
from aiohttp import web
from gmx_python_sdk.scripts.v2.gmx_utils import Config, create_connection
from gmx_python_sdk.scripts.v2.get_gm_prices import GMPrices

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting the application...")

# Create a new Async Socket.IO server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')

# Create an aiohttp web application and wrap it with socketio's middleware
app = web.Application()
sio.attach(app)

price_updates = {}
fetch_in_progress = False

config = {
    'arbitrum': {
        'rpc': "https://arbitrum-mainnet.infura.io/v3/a313cf89c2134977b427d8d0c49e9480",
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

logger.info("Connecting to the Arbitrum network...")
web3_connection = create_connection(config['arbitrum']['rpc'], 'arbitrum')

if not web3_connection.is_connected():
    logger.error("Failed to connect to the Arbitrum network.")
    sys.exit(1)

logger.info("Connected to the Arbitrum network.")
gm_prices = GMPrices(chain='arbitrum')

async def fetch_prices():
    global fetch_in_progress
    if fetch_in_progress:
        return
    fetch_in_progress = True
    try:
        prices = await loop.run_in_executor(None, gm_prices.get_price_traders)
        if prices:
            price_updates.update(prices)
            logger.info(f"Prices updated: {price_updates}")
            await sio.emit('price_update', price_updates)
    except Exception as e:
        logger.error(f"An error occurred while fetching prices: {e}")
    finally:
        fetch_in_progress = False

async def send_price_updates():
    while True:
        await sio.emit('price_update', price_updates)
        logger.info(f"Prices emitted: {price_updates}")
        await asyncio.sleep(30)  # Interval for emitting updates

# Event handler for new connections
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('price_update', price_updates, room=sid) 

# Event handler for disconnections
@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

# Define the fetch prices loop
async def fetch_prices_loop():
    while True:
        await fetch_prices()
        await asyncio.sleep(30)  # Interval for fetching prices

# Run the server
async def start_server():
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting server on port {port}...")
    # Add the tasks to the event loop
    asyncio.create_task(send_price_updates())
    asyncio.create_task(fetch_prices_loop())  # Start the price fetching loop

    # Run the aiohttp web app
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Server started on http://0.0.0.0:{port}")

    # Keep the server running
    while True:
        await asyncio.sleep(3600)  # Sleep for an hour

if __name__ == '__main__':
    # Get the asyncio event loop
    loop = asyncio.get_event_loop()
    # Run the server setup and event loop
    loop.run_until_complete(start_server())
