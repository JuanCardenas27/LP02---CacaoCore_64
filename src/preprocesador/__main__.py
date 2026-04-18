import sys

from .errors import PreprocesadorError
from .high_level import Preprocesador


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocesador CACAO_Core-64 (alto nivel)"
    )
    parser.add_argument("input", help="Archivo fuente a preprocesar")
    args = parser.parse_args()

    try:
        pre = Preprocesador()
        result = pre.preprocess_archivo(args.input)
        # Escribir con codificación UTF-8 para soportar caracteres especiales
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(result.text.encode('utf-8'))
        else:
            sys.stdout.write(result.text)
    except PreprocesadorError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
