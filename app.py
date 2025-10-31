import signal
import subprocess
import sys
import time
from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from hub import AIOZ_EXE_PATH, SERVER_URL, get_node_balance, get_node_info, update_info


class InfoCard(Static):
    def __init__(self, title: str, status: str, rewards: float, color: str = "cyan"):
        super().__init__()
        self.title = title
        self.status = status
        self.rewards = rewards
        self.color = color

    def compose(self) -> ComposeResult:
        yield Static(Text(self.title, style=f"bold {self.color}"))
        yield Static(f"[grey58]{self.status}[/grey58]", id="status")
        yield Static(f"[bold]{self.rewards:.8f}[/bold] AIOZ Rewards", id="rewards")

    def update_content(self, status: str, rewards: float):
        self.status = status
        self.rewards = rewards
        self.query_one("#status", Static).update(f"[grey58]{status}[/grey58]")
        self.query_one("#rewards", Static).update(f"[bold]{rewards:.8f}[/bold] AIOZ Rewards")


class BalanceCard(Static):
    def __init__(self, balance: float, total_rewards: float, withdrawn: float):
        super().__init__()
        self.balance = balance
        self.total_rewards = total_rewards
        self.withdrawn = withdrawn

    def compose(self) -> ComposeResult:
        yield Static(Text("Balance", style="bold white"))
        yield Static(Text(f"{self.balance:.8f} AIOZ", style="green"), id="balance")
        yield Static("")
        yield Static(Text.assemble((f"{self.total_rewards:.8f}", "yellow"), ("  Total Rewards", "white")))
        yield Static(Text.assemble((f"{self.withdrawn:.8f}", "red"), ("  Withdrawn", "white")))

    def update_balance(self, balance: float):
        self.balance = balance
        self.query_one("#balance", Static).update(f"[bold green]{balance:.8f} AIOZ[/bold green]")


class AiozDashboard(App):
    CSS = """
    Screen { background: #111111; color: white; }
    #left { width: 70%; padding: 1; }
    #right { width: 30%; padding: 1; border: round #444444; }
    InfoCard { border: round #333333; padding: 1; margin: 1; }
    BalanceCard { padding: 1; }
    Button { margin-top: 1; }
    #log_widget { border: round #666666; padding: 1; height: 10; overflow: auto; }

    #stop_node {
        background: #666666;
        color: white;
        border: round #888888;
        padding: 0 2;
        max-width: 16;
        align: center bottom;
    }

    #stop_node:hover {
        background: #888888;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.node_process = None
        self.log_text = ""

    def write_log(self, message: str):
        self.log_text = f"{time.time()} {message}\n"
        self.log_widget.update(self.log_text)

    def start_aioz_exe(self):
        wd = Path("./dist") / "node-data"
        wd.mkdir(parents=True, exist_ok=True)

        cmd = [AIOZ_EXE_PATH, "-wd", str(wd), "-dc", "15360", "-ha", SERVER_URL]
        self.write_log(f"Running: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return process, wd

    async def on_mount(self):
        # Create cardslog widget
        self.log_widget = Static(id="log_widget")

        # Create cards
        self.ai_card = InfoCard("AI", "Starting up", 0.0, color="green")
        self.transcoding_card = InfoCard("Transcoding Beta", "Standby", 0.0, color="green")
        self.storage_card = InfoCard("Storage", "Standby", 18.01109555, color="green")
        self.balance_card = BalanceCard(balance=4.94842765, total_rewards=18.61248953, withdrawn=13.66406188)

        # Layout
        self.left_panel = Vertical(self.storage_card, self.ai_card, self.transcoding_card, id="left")
        self.right_panel = Vertical(self.balance_card, Button("Pause", id="stop_node", variant="primary"), id="right")
        self.main_layout = Horizontal(self.left_panel, self.right_panel)
        self.root_layout = Vertical(self.main_layout, self.log_widget)

        await self.mount(self.root_layout)

        # Start node
        self.node_process, self.wd = self.start_aioz_exe()
        # self.write_log(f"AIOZ Node started PID={self.node_process.pid}")

        # Check Ctrl+C / terminate
        self.setup_signal_handlers()

        # Update info
        for _ in range(15):
            info = update_info()
            if info:
                break
        for _ in range(15):
            info = get_node_info()
            if info:
                break

        # Refresh
        self.set_interval(3, self.refresh_status)

    async def refresh_status(self):
        try:
            info = get_node_info()
            balance = get_node_balance()
            if not info or not balance:
                return

            status = info.get("status", "Unknown")
            total_amount = sum(v["amount"] for v in balance["earned"].values())
            rewards = total_amount / 1e18
            self.write_log(f"Blance: {rewards}")
            balance_val = float(balance.get("balance", 0))

            self.ai_card.update_content(status, rewards)
            self.balance_card.update_balance(balance_val)

        except Exception as e:
            self.write_log(f"refresh_status error: {e}")

    async def on_button_pressed(self, event):
        if event.button.id == "stop_node":
            await self.cleanup_and_exit()

    def kill_all_aioz_processes(self):
        try:
            subprocess.run(["pkill", "-9", "-f", "aiozAiNodeWrapper"], check=False)
            subprocess.run(["pkill", "-9", "-f", "aiozAiNodeExe"], check=False)
            self.write_log("Killed all aioz node processes")
        except Exception as e:
            self.write_log(f"Error killing processes: {e}")

    async def cleanup_and_exit(self):
        self.kill_all_aioz_processes()
        sys.exit(0)

    async def on_key(self, event: events.Key):
        if event.key == "q" and event.ctrl:
            event.stop()
            await self.cleanup_and_exit()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, lambda s, f: self._sig_exit())
        signal.signal(signal.SIGTERM, lambda s, f: self._sig_exit())

    def _sig_exit(self):
        self.kill_all_aioz_processes()
        sys.exit(0)


if __name__ == "__main__":
    AiozDashboard().run()
