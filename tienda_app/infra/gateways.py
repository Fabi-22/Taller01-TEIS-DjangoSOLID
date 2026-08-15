from datetime import datetime
from pathlib import Path

from ..domain.interfaces import ProcesadorPago


class BancoNacionalProcesador(ProcesadorPago):
    """Procesador de pagos local que deja trazabilidad en un archivo."""

    def pagar(self, monto: float) -> bool:
        archivo_log = Path(__file__).resolve().parents[2] / "pagos_locales_fabiola_valencia.log"
        with archivo_log.open("a", encoding="utf-8") as archivo:
            archivo.write(
                f"[{datetime.now().isoformat(timespec='seconds')}] Transaccion por: ${monto}\n"
            )
        return True