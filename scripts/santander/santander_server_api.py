import argparse
from santander_server_core import ROOT, Store, BankError, months, update


def main():
    parser = argparse.ArgumentParser(description="Consulta Santander de solo lectura")
    parser.add_argument("--desde")
    parser.add_argument("--hasta")
    parser.add_argument("--cuenta", "--account-number")
    parser.add_argument(
        "--base", "--database", default=str(ROOT / "data/history.sqlite")
    )
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    try:
        requested = months(args.desde, args.hasta)
        update(
            Store(args.base),
            requested,
            interactive=args.interactive,
            account=args.cuenta,
            progress=print,
        )
    except BankError as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
