#!/usr/bin/env python3
import asyncio
import pathlib
import sys
import os

import yapapi
from yapapi.log import enable_default_logger, log_summary, log_event_repr  # noqa
from yapapi.runner import Engine, Task, vm
from yapapi.runner.ctx import WorkContext
from datetime import timedelta
import numpy as np

# For importing `utils.py`:
script_dir = pathlib.Path(__file__).resolve().parent
parent_directory = script_dir.parent
sys.stderr.write(f"Adding {parent_directory} to sys.path.\n")
sys.path.append(str(parent_directory))
import utils  # noqa


async def main(subnet_tag: str):
    package = await vm.repo(
        image_hash = "83b5ebab52f39e676173de32f56cf2648c136050b8fa1f31a791c467",
        min_mem_gib = 0.5,
        min_storage_gib = 2.0,
    )

    async def worker(ctx: WorkContext, tasks):
        ctx.send_file(
            "./lens.py",
            "/golem/work/lens.py",
        )           
        async for task in tasks:
            feed = task.data            
            ctx.send_json(
                "/golem/work/params.json",
                feed,
            )
            commands = (
                "python3 /golem/work/lens.py >> /golem/output/task-log 2>&1;"
            )
            ctx.run("/bin/sh",
                "-c",
                commands
            )
            frame_start = feed["start_frame"]
            frame_end = feed["start_frame"] + len(feed["points"])
            frames = range(frame_start, frame_end)
            ctx.log(f"Downloading frames {frame_start}-{frame_end}...")
            for frame in frames:
                ctx.download_file(f"/golem/output/{frame}.png", f"out/{frame + 100}.png")
            output = f"task-log"
            ctx.download_file(f"/golem/output/task-log", f"out/{output}")
            yield ctx.commit()
            # TODO: Check if job results are valid
            # and reject by: task.reject_task(reason = 'invalid file')
            task.accept_task(result=output)

        ctx.log("no more frames to render")

    points = np.arange(0.001, 1.0, 0.005)
    feeds = []
    for i in range(len(points) // 10):
        feed = {
            "start_frame": 10 * i,
            "points": [points[i] for i in range(10 * i, 10 * (i + 1))]
        }
        feeds.append(feed)

    # By passing `event_consumer=log_summary()` we enable summary logging.
    # See the documentation of the `yapapi.log` module on how to set
    # the level of detail and format of the logged information.
    async with Engine(
        package=package,
        max_workers=8,
        budget=100.0,
        timeout=timedelta(minutes=3) + timedelta(minutes=10),
        subnet_tag=subnet_tag,
        event_emitter=log_summary(log_event_repr),
    ) as engine:

        async for task in engine.map(worker, [Task(data=feed) for feed in feeds]):
            print(
                f"{utils.TEXT_COLOR_CYAN}"
                f"Task computed: {task}, result: {task.output}"
                f"{utils.TEXT_COLOR_DEFAULT}"
            )


if __name__ == "__main__":
    parser = utils.build_parser("Simulate a strong gravitational lensing")
    parser.set_defaults()
    args = parser.parse_args()

    enable_default_logger(log_file=args.log_file)
    loop = asyncio.get_event_loop()
    subnet = args.subnet_tag
    sys.stderr.write(
        f"yapapi version: {utils.TEXT_COLOR_YELLOW}{yapapi.__version__}{utils.TEXT_COLOR_DEFAULT}\n"
    )
    sys.stderr.write(f"Using subnet: {utils.TEXT_COLOR_YELLOW}{subnet}{utils.TEXT_COLOR_DEFAULT}\n")
    task = loop.create_task(main(subnet_tag=args.subnet_tag))
    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(task)
