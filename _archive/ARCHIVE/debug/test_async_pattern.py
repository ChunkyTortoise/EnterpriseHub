
import asyncio

async def test_coro():
    await asyncio.sleep(0.1)
    return "SUCCESS"

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def main():
    print("Main loop running...")
    # This simulates calling it from a running loop
    try:
        result = run_async(test_coro())
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
