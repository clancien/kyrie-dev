from santander_login import login
from santander_server_core import BankError

if __name__ == "__main__":
    try:
        login()
        print("Sesión privada validada")
    except BankError as error:
        raise SystemExit(str(error))
