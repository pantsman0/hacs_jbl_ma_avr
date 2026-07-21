import asyncio
import logging
import sys

from custom_components.jbl_ma_avr.jbl_api import JblApi

logging.basicConfig(level=logging.DEBUG)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <IP_ADDRESS>")
        sys.exit(1)

    host = sys.argv[1]
    print(f"Connecting to {host}...")
    
    api = JblApi(host)
    
    def on_update():
        print(f"--- Update ---")
        print(f"Power: {api.power}")
        print(f"Volume: {api.volume}")
        print(f"Mute: {api.mute}")
        print(f"Source ID: {api.source}")
        print(f"--------------")
        
    api.register_callback(on_update)
    
    await api.connect()
    print("Connected. Waiting for state updates... (Press Ctrl+C to exit)")
    
    try:
        # Keep the script running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Disconnecting...")
        await api.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
