#!/usr/bin/env python3
import sys
import argparse
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from radar.storage import JobStorage
from radar.engine import JobAggregator
from radar.models import SECTORS

console = Console()
storage = JobStorage()
aggregator = JobAggregator(storage=storage)


def cmd_fetch(args):
    console.print(Panel.fit("[bold cyan]KariyerRadar - Canlı Kurumsal Tarama Başlatılıyor...[/bold cyan]\n[dim]Resmi portallar ve kurumsal ATS beslemeleri taranıyor.[/dim]"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[yellow]Şirketler taranıyor...", total=None)
        res = aggregator.run_all()

    console.print(f"[bold green]✔ Tarama Tamamlandı![/bold green] (Süre: [bold]{res['elapsed_seconds']} sn[/bold])\n")

    # Adapter breakdown table
    table = Table(title="Kaynak Bazında Bulunan İlanlar", border_style="cyan")
    table.add_column("Kaynak / Portal", style="bold white")
    table.add_column("Bulunan İlan", justify="right", style="cyan")

    for name, count in res["adapter_breakdown"].items():
        table.add_row(name, str(count))

    console.print(table)

    console.print(f"\n[bold]Toplam Çekilen:[/bold] {res['total_fetched']}")
    console.print(f"[bold green]Yeni Keşfedilen İlanlar:[/bold green] [bold green]{res['new_jobs']}[/bold green]")
    console.print(f"[dim]Güncellenen İlanlar: {res['updated_jobs']}[/dim]")
    console.print(f"[bold blue]Veritabanındaki Toplam Aktif İlan:[/bold blue] {res['overall_stats']['total_jobs']}")
    console.print("\n[dim]İlanları listelemek için: [yellow]python3 main.py list[/yellow][/dim]")
    console.print("[dim]Web panelini açmak için: [yellow]python3 main.py web[/yellow][/dim]")


def cmd_list(args):
    jobs = storage.get_jobs(
        sector=args.sector,
        company=args.company,
        search=args.search,
        only_new=args.only_new,
        limit=args.limit
    )

    if not jobs:
        console.print("[yellow]Arama kriterlerine uygun ilan bulunamadı.[/yellow]")
        console.print("[dim]Tarama yapmak için: [cyan]python3 main.py fetch[/cyan][/dim]")
        return

    sector_title = SECTORS.get(args.sector, args.sector) if args.sector else "Tüm Sektörler"
    table = Table(title=f"KariyerRadar İlanları ({sector_title} - {len(jobs)} İlan)", border_style="blue")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Şirket", style="bold cyan")
    table.add_column("Pozisyon Başlığı", style="bold white")
    table.add_column("Sektör", style="magenta")
    table.add_column("Lokasyon", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Durum", style="bold")

    for j in jobs:
        status_str = "[bold green]YENİ[/bold green]" if j.is_new else "[dim]Kayıtlı[/dim]"
        sec_name = SECTORS.get(j.sector, j.sector).split(" ")[0]
        table.add_row(
            j.id[:12],
            j.company[:18],
            j.title[:38],
            sec_name,
            (j.location or "Türkiye")[:16],
            (j.work_model or "Tam Zamanlı")[:16],
            status_str
        )

    console.print(table)
    console.print(f"\n[dim]İlan detayını görmek için: [cyan]python3 main.py detail <ID>[/cyan][/dim]")


def cmd_search(args):
    args.sector = None
    args.company = None
    args.only_new = False
    cmd_list(args)


def cmd_detail(args):
    job = storage.get_job_by_id(args.job_id)
    if not job:
        # ID başında eşleşen var mı ara
        jobs = storage.get_jobs(search=args.job_id, limit=1)
        if jobs:
            job = jobs[0]
        else:
            console.print(f"[red]Hata: '{args.job_id}' ID'li ilan bulunamadı.[/red]")
            return

    new_badge = "[bold green]YENİ İLAN[/bold green] " if job.is_new else ""
    content = f"""
[bold cyan]Şirket:[/bold cyan] {job.company}
[bold cyan]Sektör:[/bold cyan] {SECTORS.get(job.sector, job.sector)}
[bold cyan]Lokasyon:[/bold cyan] {job.location}
[bold cyan]Çalışma Modeli:[/bold cyan] {job.work_model}
[bold cyan]Deneyim:[/bold cyan] {job.experience_level}
[bold cyan]Kaynak Portal:[/bold cyan] {job.source}
[bold cyan]Keşfedilme:[/bold cyan] {job.discovered_at}

[bold yellow]── İş Tanımı & Açıklama ──[/bold yellow]
{job.description_text or 'İş tanımı resmi portalda yayınlanmıştır.'}
"""

    if job.requirements:
        content += "\n\n[bold yellow]── Öne Çıkan Nitelikler ──[/bold yellow]\n"
        for r in job.requirements:
            content += f" • {r}\n"

    content += f"\n[bold green]── Doğrudan Başvuru Linki ──[/bold green]\n[underline blue]{job.apply_url}[/underline blue]"

    console.print(Panel(content.strip(), title=f"{new_badge}[bold white]{job.title}[/bold white]", border_style="cyan"))


def cmd_stats(args):
    stats = storage.get_stats()
    console.print(Panel.fit("[bold cyan]KariyerRadar Sistem İstatistikleri[/bold cyan]"))
    console.print(f"[bold]Toplam Aktif İlan:[/bold] {stats['total_jobs']}")
    console.print(f"[bold green]Yeni Keşfedilen İlanlar:[/bold green] {stats['new_jobs']}\n")

    table = Table(title="Sektör Dağılımı", border_style="magenta")
    table.add_column("Sektör", style="bold")
    table.add_column("İlan Sayısı", justify="right", style="cyan")

    for sec, count in stats["by_sector"].items():
        table.add_row(SECTORS.get(sec, sec), str(count))

    console.print(table)

    table_comp = Table(title="En Çok İlan Açan Kurumlar (Top 10)", border_style="green")
    table_comp.add_column("Şirket", style="bold")
    table_comp.add_column("İlan Sayısı", justify="right", style="green")

    for comp, count in stats["top_companies"].items():
        table_comp.add_row(comp, str(count))

    console.print(table_comp)


def cmd_add_company(args):
    keyword = args.keyword.strip()
    sector = args.sector or "other"
    console.print(f"[cyan]'{keyword}' radara ekleniyor ve taranıyor...[/cyan]")
    new_jobs = aggregator.scan_single_target(keyword, sector)
    console.print(f"[bold green]✔ Tamamlandı![/bold green] '{keyword}' için [bold]{len(new_jobs)}[/bold] ilan bulundu ve veritabanına kaydedildi.")


def cmd_web(args):
    console.print(Panel.fit(f"[bold cyan]KariyerRadar Web Paneli Başlatılıyor...[/bold cyan]\n[green]http://{args.host}:{args.port}[/green] adresine tarayıcınızdan erişebilirsiniz.\n[dim]Durdurmak için Ctrl+C tuşlarına basın.[/dim]"))
    import uvicorn
    uvicorn.run("radar.web.app:app", host=args.host, port=args.port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="KariyerRadar - Türkiye Prestijli Şirketler İş İlanı Radarı")
    subparsers = parser.add_subparsers(dest="command", help="Komutlar")

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Tüm resmi portalları ve şirketleri tara")
    p_fetch.set_defaults(func=cmd_fetch)

    # list
    p_list = subparsers.add_parser("list", help="İlanları listele")
    p_list.add_argument("--sector", choices=list(SECTORS.keys()), default=None, help="Sektör filtresi")
    p_list.add_argument("--company", type=str, default=None, help="Şirket adı filtresi")
    p_list.add_argument("--search", type=str, default=None, help="Arama anahtar kelimesi")
    p_list.add_argument("--only-new", action="store_true", help="Yalnızca yeni keşfedilen ilanları göster")
    p_list.add_argument("--limit", type=int, default=50, help="Listelenecek ilan limiti")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = subparsers.add_parser("search", help="Pozisyon veya şirket ara")
    p_search.add_argument("search", type=str, help="Aranacak kelime (örn: ios, müfettiş, data)")
    p_search.add_argument("--limit", type=int, default=50, help="Listelenecek ilan limiti")
    p_search.set_defaults(func=cmd_search)

    # detail
    p_detail = subparsers.add_parser("detail", help="İlan detayını görüntüle")
    p_detail.add_argument("job_id", type=str, help="İlan ID veya başlık")
    p_detail.set_defaults(func=cmd_detail)

    # stats
    p_stats = subparsers.add_parser("stats", help="İstatistikleri göster")
    p_stats.set_defaults(func=cmd_stats)

    # add-company
    p_add = subparsers.add_parser("add-company", help="Radara yeni şirket ekle ve anında tara")
    p_add.add_argument("keyword", type=str, help="Şirket adı veya arama terimi")
    p_add.add_argument("--sector", choices=list(SECTORS.keys()), default="other", help="Sektör")
    p_add.set_defaults(func=cmd_add_company)

    # web
    p_web = subparsers.add_parser("web", help="Modern Web Dashboard'unu başlat")
    p_web.add_argument("--port", type=int, default=8000, help="Web sunucu portu (varsayılan: 8000)")
    p_web.add_argument("--host", type=str, default="127.0.0.1", help="Web sunucu hostu")
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
