#!/usr/bin/env python3
"""
Script unificado para iniciar o Sistema de Detecção - Visão Computacional.

Uso:
    python web/start.py              # Build frontend + inicia servidor
    python web/start.py --dev        # Modo desenvolvimento (frontend em :3000, API em :8000)
    python web/start.py --skip-build # Pula o build do frontend (usa dist/ existente)
    python web/start.py --host 0.0.0.0 --port 8080  # Customiza host/porta
"""

import argparse
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
FRONTEND_DIR = SCRIPT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
API_FILE = SCRIPT_DIR / "api.py"
SRC_DIR = PROJECT_DIR / "src"
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("start")

# ── Colors ───────────────────────────────────────────────────
IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not IS_TTY:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(t: str) -> str:
    return _c("32", t)


def yellow(t: str) -> str:
    return _c("33", t)


def red(t: str) -> str:
    return _c("31", t)


def cyan(t: str) -> str:
    return _c("36", t)


def bold(t: str) -> str:
    return _c("1", t)


def dim(t: str) -> str:
    return _c("2", t)


# ═════════════════════════════════════════════════════════════
#  Checks
# ═════════════════════════════════════════════════════════════


def check_python_deps() -> bool:
    """Verifica se as dependências Python essenciais estão instaladas."""
    required = ["fastapi", "uvicorn", "cv2", "numpy"]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        logger.error(
            red(f"Dependências Python faltando: {', '.join(missing)}")
        )
        logger.info(
            f"  Instale com: {cyan('pip install -r requirements.txt')}"
        )
        return False
    return True


def find_npm() -> str | None:
    """Localiza o executável npm."""
    return shutil.which("npm")


def find_node() -> str | None:
    """Localiza o executável node."""
    return shutil.which("node")


def check_node_installed() -> bool:
    """Verifica se Node.js e npm estão instalados."""
    node = find_node()
    npm = find_npm()

    if not node or not npm:
        logger.warning(
            yellow("Node.js/npm não encontrado. Frontend não será buildado.")
        )
        logger.info(
            f"  Instale Node.js: {cyan('https://nodejs.org/')}"
        )
        return False

    try:
        node_ver = subprocess.check_output(
            [node, "--version"], text=True, timeout=10
        ).strip()
        npm_ver = subprocess.check_output(
            [npm, "--version"], text=True, timeout=10
        ).strip()
        logger.info(f"  Node.js {green(node_ver)}  |  npm {green(npm_ver)}")
    except Exception:
        pass

    return True


def check_frontend_deps() -> bool:
    """Verifica se node_modules existe."""
    return (FRONTEND_DIR / "node_modules").exists()


def check_frontend_built() -> bool:
    """Verifica se o frontend já foi buildado."""
    return DIST_DIR.exists() and (DIST_DIR / "index.html").exists()


# ═════════════════════════════════════════════════════════════
#  Build Frontend
# ═════════════════════════════════════════════════════════════


def install_frontend_deps() -> bool:
    """Executa npm install no diretório do frontend."""
    npm = find_npm()
    if not npm:
        return False

    logger.info(f"  {cyan('npm install')} em {FRONTEND_DIR.name}/")

    try:
        result = subprocess.run(
            [npm, "install"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(red("Erro no npm install:"))
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:20]:
                    logger.error(f"    {line}")
            return False
        logger.info(f"  {green('✓')} Dependências instaladas")
        return True
    except subprocess.TimeoutExpired:
        logger.error(red("npm install excedeu o tempo limite (120s)"))
        return False
    except Exception as exc:
        logger.error(red(f"Erro ao executar npm install: {exc}"))
        return False


def build_frontend() -> bool:
    """Executa npm run build para gerar o frontend."""
    npm = find_npm()
    if not npm:
        return False

    logger.info(f"  {cyan('npm run build')} em {FRONTEND_DIR.name}/")

    try:
        result = subprocess.run(
            [npm, "run", "build"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error(red("Erro no build do frontend:"))
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:20]:
                    logger.error(f"    {line}")
            return False

        # Mostra output do Vite
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                stripped = line.strip()
                if stripped and ("dist/" in stripped or "built in" in stripped or "✓" in stripped):
                    logger.info(f"    {dim(stripped)}")

        logger.info(f"  {green('✓')} Frontend buildado com sucesso")
        return True
    except subprocess.TimeoutExpired:
        logger.error(red("Build do frontend excedeu o tempo limite (120s)"))
        return False
    except Exception as exc:
        logger.error(red(f"Erro ao buildar frontend: {exc}"))
        return False


def ensure_frontend(skip_build: bool = False) -> bool:
    """Garante que o frontend está buildado."""
    if skip_build:
        if check_frontend_built():
            logger.info(f"  {green('✓')} Frontend buildado encontrado (--skip-build)")
            return True
        else:
            logger.warning(
                yellow("--skip-build mas dist/ não existe. Tentando buildar...")
            )

    if not check_node_installed():
        if check_frontend_built():
            logger.info(
                f"  {yellow('!')} Usando build anterior do frontend"
            )
            return True
        return False

    if not check_frontend_deps():
        logger.info("  Instalando dependências do frontend...")
        if not install_frontend_deps():
            return False

    logger.info("  Buildando frontend...")
    return build_frontend()


# ═════════════════════════════════════════════════════════════
#  Start Servers
# ═════════════════════════════════════════════════════════════


def start_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Inicia o servidor FastAPI com uvicorn."""
    try:
        import uvicorn
    except ImportError:
        logger.error(red("uvicorn não está instalado."))
        logger.info(f"  Instale com: {cyan('pip install uvicorn[standard]')}")
        sys.exit(1)

    logger.info("")
    logger.info(bold("═" * 60))
    logger.info(bold("  Iniciando servidor..."))
    logger.info(bold("═" * 60))
    logger.info("")

    if check_frontend_built():
        logger.info(f"  🌐 Interface web:  {cyan(f'http://localhost:{port}')}")
    else:
        logger.info(f"  🌐 API apenas:     {cyan(f'http://localhost:{port}')}")
        logger.info(f"  ⚠  Frontend não buildado — apenas API disponível")

    logger.info(f"  📡 API base:       {cyan(f'http://localhost:{port}/api')}")
    logger.info(f"  ❤️  Health check:   {cyan(f'http://localhost:{port}/health')}")
    logger.info(f"  📂 Documentação:   {cyan(f'http://localhost:{port}/docs')}")
    logger.info("")
    logger.info(dim(f"  Pressione Ctrl+C para parar"))
    logger.info("")

    subprocess.run([
        "gunicorn",
        "-w", "4",
        "-k", "uvicorn.workers.UvicornWorker",
        "api:app",
        "--bind", f"{host}:{port}",
    ])

def start_dev_mode(host: str = "0.0.0.0", port: int = 8000):
    """Inicia em modo desenvolvimento: backend + frontend dev server."""
    npm = find_npm()
    if not npm:
        logger.error(red("npm não encontrado. Necessário para modo dev."))
        sys.exit(1)

    if not check_frontend_deps():
        logger.info("  Instalando dependências do frontend...")
        if not install_frontend_deps():
            logger.error(red("Falha ao instalar dependências do frontend"))
            sys.exit(1)

    logger.info("")
    logger.info(bold("═" * 60))
    logger.info(bold("  Modo Desenvolvimento"))
    logger.info(bold("═" * 60))
    logger.info("")
    logger.info(f"  🌐 Frontend (Vite):  {cyan('http://localhost:3000')}")
    logger.info(f"  📡 Backend (API):    {cyan(f'http://localhost:{port}')}")
    logger.info(f"  📂 API Docs:         {cyan(f'http://localhost:{port}/docs')}")
    logger.info("")
    logger.info(dim("  O Vite faz proxy das requests /api → backend automaticamente"))
    logger.info(dim("  Pressione Ctrl+C para parar ambos os servidores"))
    logger.info("")

    procs = []

    try:
        # Start backend with reload
        backend_env = os.environ.copy()
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "api:app",
            "--host", host,
            "--port", str(port),
            "--reload",
            "--reload-dir", str(SCRIPT_DIR),
            "--reload-dir", str(SRC_DIR),
            "--log-level", "info",
        ]

        logger.info(dim(f"  → Iniciando backend: uvicorn api:app --reload"))
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(SCRIPT_DIR),
            env=backend_env,
        )
        procs.append(("Backend", backend_proc))

        # Give backend a moment to start
        time.sleep(1)

        # Start frontend dev server
        logger.info(dim(f"  → Iniciando frontend: npm run dev"))
        frontend_proc = subprocess.Popen(
            [npm, "run", "dev"],
            cwd=str(FRONTEND_DIR),
        )
        procs.append(("Frontend", frontend_proc))

        # Wait for either to exit
        while True:
            for name, proc in procs:
                ret = proc.poll()
                if ret is not None:
                    logger.warning(yellow(f"{name} encerrou com código {ret}"))
                    raise KeyboardInterrupt
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("")
        logger.info(yellow("Encerrando servidores..."))
        for name, proc in procs:
            if proc.poll() is None:
                logger.info(dim(f"  Parando {name}..."))
                if platform.system() == "Windows":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)

        # Wait for graceful shutdown
        for name, proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(yellow(f"  {name} não encerrou, forçando..."))
                proc.kill()

        logger.info(green("  ✓ Servidores encerrados"))


# ═════════════════════════════════════════════════════════════
#  Main
# ═════════════════════════════════════════════════════════════


def print_banner():
    """Imprime banner do sistema."""
    print("")
    print(green("  ╔══════════════════════════════════════════════════════╗"))
    print(green("  ║") + bold("   🌿 Sistema de Detecção — Visão Computacional     ") + green("║"))
    print(green("  ║") + dim("   Detecção de mato alto e buracos v1.0.0            ") + green("║"))
    print(green("  ╚══════════════════════════════════════════════════════╝"))
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="Inicia o Sistema de Detecção - Visão Computacional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python web/start.py                    # Build + servidor produção
  python web/start.py --dev              # Modo desenvolvimento (hot reload)
  python web/start.py --skip-build       # Pula build do frontend
  python web/start.py --port 8080        # Porta customizada
  python web/start.py --host 127.0.0.1   # Apenas localhost
        """,
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Modo desenvolvimento (frontend Vite + backend com reload)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Pula o build do frontend (usa dist/ existente)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host do servidor (padrão: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta do servidor (padrão: 8000)",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Inicia apenas a API sem buildar/servir o frontend",
    )

    args = parser.parse_args()

    print_banner()

    # ── Check Python dependencies ─────────────────────────────
    logger.info(bold("Verificando dependências Python..."))
    if not check_python_deps():
        sys.exit(1)
    logger.info(f"  {green('✓')} Dependências Python OK")
    logger.info("")

    # ── Dev mode ──────────────────────────────────────────────
    if args.dev:
        logger.info(bold("Modo desenvolvimento selecionado"))
        start_dev_mode(host=args.host, port=args.port)
        return

    # ── Production mode ───────────────────────────────────────
    if not args.no_frontend:
        logger.info(bold("Preparando frontend..."))
        frontend_ok = ensure_frontend(skip_build=args.skip_build)
        if not frontend_ok:
            logger.warning(
                yellow(
                    "Frontend não disponível. O servidor iniciará apenas com a API."
                )
            )
        logger.info("")
    else:
        logger.info(dim("  Frontend desabilitado (--no-frontend)"))
        logger.info("")

    # ── Start server ──────────────────────────────────────────
    start_api_server(host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
