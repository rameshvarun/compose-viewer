from textual.app import App, ComposeResult, Binding
from textual.widgets import Log, TabbedContent, TabPane

import asyncio
import re
import argparse


class LogApp(App):
    BINDINGS = [
        Binding("ctrl+c", "quit", show=False, system=True),
    ]

    def compose(self) -> ComposeResult:
        yield TabbedContent()

    def __init__(self, project_name):
        super().__init__()
        self.project_name = project_name
        self.tabs = {}

    async def on_mount(self):
        command_args = ["docker", "compose"]
        if self.project_name:
            command_args.extend(["-p", self.project_name])
        command_args.extend(["logs", "--follow"])

        self.logs_process = await asyncio.subprocess.create_subprocess_exec(
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self.logs_task = asyncio.create_task(self.read_logs())

    async def read_logs(self):
        # Read logs until the process closes.
        while not self.logs_process.stdout.at_eof():
            line = (await self.logs_process.stdout.readline()).decode()
            match = re.match(r"([a-zA-Z0-9\-]+)\s*\|\s*(.*)", line)
            if match:
                pod_name, message = match.groups()
                if pod_name not in self.tabs:
                    tabbed_content = self.query_one(TabbedContent)
                    log = Log()
                    tabbed_content.add_pane(TabPane(pod_name, log, id=pod_name))
                    self.tabs[pod_name] = log
                self.tabs[pod_name].write_line(message)

    async def on_unmount(self):
        try:
            self.logs_process.terminate()
        except ProcessLookupError:
            pass

        await self.logs_task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project-name", help="Project name")
    args = parser.parse_args()

    app = LogApp(args.project_name)
    app.run()


if __name__ == "__main__":
    main()
