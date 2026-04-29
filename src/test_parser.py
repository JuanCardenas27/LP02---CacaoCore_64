"""
test_parser.py
==============
Suite de pruebas para el Analizador Sintáctico de CacaoScript.
Ejecutar con: uv run python test_parser.py
"""
from compiler.analizador_sintactico import AnalizadorSintactico


def run_tests():
    p = AnalizadorSintactico()
    tests = []

    # ── TEST 1: Algoritmo de Euclides ─────────────────────────────────────
    tests.append(("Euclides (gcd)", """
let a: int = 756
let b: int = 924
asLongAs a != b {
    if a > b { set a = a - b }
    otherwise { set b = b - a }
}
show a
"""))

    # ── TEST 2: Arreglos y matrices ───────────────────────────────────────
    tests.append(("Arreglos y Matrices 2D", """
let rows: int = 3
let cols: int = 2
let mat: int[rows][cols] = 1,2,3,4,5,6
let vec: float[3] = 1.1, 2.2, 3.3
for (let i:int = 0, i < rows, set i += 1) {
    for (let j:int = 0, j < cols, set j += 1) {
        set mat[i][j] = mat[i][j] * 2
    }
}
show mat[0][0]
"""))

    # ── TEST 3: Funciones recursivas ──────────────────────────────────────
    tests.append(("Funciones y recursion", """
func factorial(n: int) {
    if n <= 1 { deliver 1 }
    deliver n * factorial(n - 1)
}
func esPar(n: int) {
    deliver n % 2 == 0
}
show factorial(5)
show esPar(4)
"""))

    # ── TEST 4: Mold / TDA ────────────────────────────────────────────────
    tests.append(("Mold / TDA (clase)", """
mold Vector2D {
    let x: float
    let y: float
    func escalar(factor: float) {
        set ohmy.x = ohmy.x * factor
        set ohmy.y = ohmy.y * factor
    }
    func magnitud() {
        deliver ohmy.x * ohmy.x + ohmy.y * ohmy.y
    }
}
let v: Vector2D = summon Vector2D()
v.escalar(2.0)
show v.magnitud()
"""))

    # ── TEST 5: Flotantes IEEE 754 + operadores logicos ───────────────────
    tests.append(("Flotantes IEEE 754 + logica", """
let pi: float = 3.14159
let radio: float = 5.0
let area: float = pi * radio * radio
let activo: bool = indeed
let nombre: text = "CacaoScript"
if area > 70.0 and activo {
    show "Area grande"
} otherwise {
    oops "Area inesperada"
}
asLongAs radio > 1.0 {
    set radio = radio - 0.5
}
show radio
"""))

    # ── TEST 6: Busqueda del maximo ───────────────────────────────────────
    tests.append(("Busqueda del maximo", """
let n: int = 5
let a: int[n] = 10, 3, 7, 1, 9
let i: int = 0
let maxVal: int = a[0]
for (i, i < n, set i += 1) {
    if maxVal < a[i] {
        set maxVal = a[i]
    }
}
show maxVal
"""))

    # ── TEST 7: Error sintactico detectado y recuperacion ─────────────────
    tests.append(("Deteccion de error sintatctico", """
let x: int = 42
let y: int = }}}
let z: int = x + 1
show z
"""))

    # ── Ejecutar ──────────────────────────────────────────────────────────
    sep = "=" * 62
    print(sep)
    print("  SUITE DE PRUEBAS — Analizador Sintáctico CacaoScript")
    print(sep)

    ok  = 0
    err = 0

    for nombre, codigo in tests:
        errs, ast = p.parse(codigo)

        # Test 7 es especial: esperamos que haya errores
        if nombre.startswith("Deteccion"):
            esperamos_error = True
        else:
            esperamos_error = False

        if esperamos_error:
            paso = bool(errs)          # paso si hay errores (los detectó)
            estado = "OK (error detectado)" if paso else "FALLO (no detectó el error)"
        else:
            paso  = (ast is not None and not errs)
            estado = "OK" if paso else "FALLO"

        if paso:
            ok += 1
        else:
            err += 1

        print(f"\n[{estado}]  {nombre}")

        if errs:
            for e in errs:
                print(f"         >> {e}")
        if ast is not None and not esperamos_error:
            lineas = ast.pprint().splitlines()
            for l in lineas[:6]:
                print(f"         {l}")
            if len(lineas) > 6:
                print(f"         ... ({len(lineas) - 6} líneas más en el AST)")

    print()
    print(sep)
    print(f"  RESULTADO FINAL: {ok}/{len(tests)} pruebas pasaron  |  {err} fallaron")
    print(sep)


if __name__ == "__main__":
    run_tests()
