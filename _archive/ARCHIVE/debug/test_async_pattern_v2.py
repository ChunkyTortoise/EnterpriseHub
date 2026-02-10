import pytest

@pytest.mark.unit

import asyncio
from threading import Thread
from concurrent.futures import Future

async def test_coro():
    await asyncio.sleep(0.1)
    return "SUCCESS"

def run_async(coro):
    def wrapper(future, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            loop.close()

    future = Future()
    thread = Thread(target=wrapper, args=(future, coro))
    thread.start()
    thread.join()
    return future.result()

async def main():
    print("Main loop running...")
    try:
        result = run_async(test_coro())
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
