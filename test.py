from config import *

from lib.request import Request as Request

import asyncio

async def main():

    r = Request.create({
        "category": "",
        "channel_topic": "default-workflow",
        "user_message": "3x4 steps30 cfg8 > close portrait of an attractive female -bad anatomy, disfigured, malformed, ugly"
    })

    print("options_json:")
    print(r.get_options_json())
    print()

    print("workflow_json:")
    print(r.get_workflow_json())
    print()

    print("images:")

    img_data = await r.get_images()

    print(img_data)
    print()

# Test
if __name__ == "__main__":
    # main()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
