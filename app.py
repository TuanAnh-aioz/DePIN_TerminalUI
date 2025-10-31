import os
import signal
import subprocess
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button
from rich.text import Text
import psutil
from hub import get_node_info, get_node_balance, update_info
from textual import events
import sys

from hub import get_node_info, get_node_balance, update_info

AIOZ_EXE_PATH = "./dist/aiozAiNodeWrapper"


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
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_content = ""
        self.node_process = None

    def write_log(self, msg: str):
        self.log_content += msg + "\n"
        if hasattr(self, "log_widget"):
            self.log_widget.update(self.log_content)

    def start_aioz_exe(self):
        wd = Path("./dist") / "node-data"
        wd.mkdir(parents=True, exist_ok=True)

        cmd = [AIOZ_EXE_PATH, "-wd", str(wd), "-dc", "15360", "-ha", "http://10.0.0.238:8083"]
        self.write_log(f"Running: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return process, wd

    async def on_mount(self):
        # Tạo log widget
        self.log_widget = Static(id="log_widget")

        # Tạo các card
        self.ai_card = InfoCard("AI", "Starting up", 0.0, color="green")
        self.transcoding_card = InfoCard("Transcoding Beta", "Standby", 0.0, color="green")
        self.storage_card = InfoCard("Storage", "Standby", 18.01109555, color="green")
        self.balance_card = BalanceCard(balance=4.94842765, total_rewards=18.61248953, withdrawn=13.66406188)

        # Container layout
        self.left_panel = Vertical(self.storage_card, self.ai_card, self.transcoding_card, id="left")
        self.right_panel = Vertical(self.balance_card,  Button("Stop Node", id="stop_node", variant="error"), id="right")
        self.main_layout = Horizontal(self.left_panel, self.right_panel)
        self.root_layout = Vertical(self.main_layout, self.log_widget)

        await self.mount(self.root_layout)

        # Start AIOZ Node
        self.node_process, self.wd = self.start_aioz_exe()
        self.write_log(f"AIOZ Node started with PID: {self.node_process.pid}")

        # Bắt Ctrl+C / terminate
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
        
        # Refresh status mỗi 3 giây
        self.set_interval(3, self.refresh_status)

    async def refresh_status(self):
        try:
            info = get_node_info()
            status = info.get("status", "Unknown")

            balance = get_node_balance()
            if not info or not balance:
                return

            total_amount = sum(v["amount"] for v in balance["earned"].values())
            total_aios = total_amount / 1e18
            rewards = float(total_aios)

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
        except Exception as e:
            print(f"Error killing aiozAiNodeWrapper: {e}")

        try:
            subprocess.run(["pkill", "-9", "-f", "aiozAiNodeExe"], check=False)
        except Exception as e:
            print(f"Error killing aiozAiNodeWrapper: {e}")
            
    async def cleanup_and_exit(self):
        self.kill_all_aioz_processes()
        self.exit()

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
