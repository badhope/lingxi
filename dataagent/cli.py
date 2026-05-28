"""
DATA-Agent CLI - 命令行界面
基于 CrewAI 的智能数据助手
"""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from config import settings
from agents.base_agent import get_llm
from crews.data_analysis import run_data_analysis
from crews.knowledge_team import run_knowledge_query

console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = Panel(
        f"[bold blue]DATA-Agent {settings.app_version}[/bold blue]\n"
        "基于 CrewAI 的智能数据助手",
        border_style="blue"
    )
    console.print(banner)


def analyze_data():
    """数据分析功能"""
    console.print("\n[cyan]📊 数据分析[/cyan]")
    query = Prompt.ask("请输入您要分析的问题")
    
    if not query:
        console.print("[yellow]问题不能为空[/yellow]")
        return
    
    console.print("\n[yellow]⏳ 正在分析...[/yellow]\n")
    
    try:
        result = run_data_analysis(query)
        console.print(Panel(
            result,
            title="[bold green]分析结果[/bold green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]分析失败: {str(e)}[/red]")


def query_knowledge():
    """知识库查询功能"""
    console.print("\n[cyan]📚 知识库查询[/cyan]")
    question = Prompt.ask("请输入您的问题")
    
    if not question:
        console.print("[yellow]问题不能为空[/yellow]")
        return
    
    console.print("\n[yellow]⏳ 正在查询...[/yellow]\n")
    
    try:
        result = run_knowledge_query(question)
        console.print(Panel(
            result,
            title="[bold green]查询结果[/bold green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]查询失败: {str(e)}[/red]")


def show_menu():
    """显示菜单"""
    console.print("\n[bold]请选择操作:[/bold]")
    console.print("  [1] 数据分析")
    console.print("  [2] 知识库查询")
    console.print("  [q] 退出")


def main():
    """主程序入口"""
    print_banner()
    
    while True:
        show_menu()
        choice = Prompt.ask("\n[bold cyan]请选择[/bold cyan]", 
                           choices=["1", "2", "q"],
                           default="q")
        
        if choice == "1":
            analyze_data()
        elif choice == "2":
            query_knowledge()
        elif choice == "q":
            console.print("\n[yellow]👋 再见![/yellow]")
            break
        
        if not Confirm.ask("\n[bold]继续操作?[/bold]"):
            console.print("\n[yellow]👋 再见![/yellow]")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]已取消[/yellow]")
        sys.exit(0)
