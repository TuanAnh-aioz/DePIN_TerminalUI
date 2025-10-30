from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, ProgressBar
from rich.text import Text


class InfoCard(Static):
    """Widget show 1 module như Storage / Delivery / AI / Transcoding"""

    def __init__(self, title: str, status: str, rewards: float, progress: float | None = None, color: str = "cyan"):
        super().__init__()
        self.title = title
        self.status = status
        self.rewards = rewards
        self.progress = progress
        self.color = color

    def compose(self) -> ComposeResult:
        title = Text(self.title, style=f"bold {self.color}")
        yield Static(title)

        if self.progress is not None:
            bar = ProgressBar(total=100, show_eta=False, show_percentage=False)
            bar.progress = self.progress
            yield bar

        yield Static(f"[grey58]{self.status}[/grey58]")
        yield Static(f"[bold]{self.rewards:.8f}[/bold] AIOZ Rewards")


class BalanceCard(Static):
    """Widget show Balance, Total Rewards, Withdrawn"""

    def __init__(self, balance: float, total_rewards: float, withdrawn: float):
        super().__init__()
        self.balance = balance
        self.total_rewards = total_rewards
        self.withdrawn = withdrawn

    def compose(self) -> ComposeResult:
        yield Static(Text("Balance", style="bold white"))
        yield Static(Text(f"{self.balance:.8f} AIOZ", style="green"))
        yield Static("")
        yield Static(Text(f"{self.total_rewards:.8f}", style="yellow") + Text("  Total Rewards"))
        yield Static(Text(f"{self.withdrawn:.8f}", style="red") + Text("  Withdrawn"))
        yield Static("")
        yield Static("[bold reverse] Withdraw [/bold reverse]")


class AiozTerminalUI(App):
    CSS = """
    Screen {
        background: #111111;
        color: white;
    }

    #left {
        width: 70%;
        padding: 1;
    }

    #right {
        width: 30%;
        padding: 1;
        border: round #444444;
    }

    InfoCard {
        border: round #333333;
        padding: 1;
        margin: 1;
    }

    BalanceCard {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        left_panel = Vertical(
            InfoCard("Storage", "77.47 of 200 GB", 0.00125907, progress=38, color="magenta"),
            InfoCard("Delivery", "Standby", 18.01109555, color="blue"),
            InfoCard("AI", "Standby", 0.60013491, color="green"),
            InfoCard("Transcoding (Beta)", "Standby", 0.0, color="yellow"),
            id="left",
        )

        right_panel = BalanceCard(balance=4.94842765, total_rewards=18.61248953, withdrawn=13.66406188)
        right_container = Vertical(right_panel, id="right")

        yield Horizontal(left_panel, right_container)


if __name__ == "__main__":
    AiozTerminalUI().run()
