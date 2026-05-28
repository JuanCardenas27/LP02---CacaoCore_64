import sys, traceback
sys.path.insert(0, r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src')
from compiler.analizador_semantico import AnalizadorSemantico
from compiler.generador_codigo import GeneradorCodigo

files = [
    r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\float_insertion_sort.txt',
    r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\semalyzer_tests\correct_example.choco',
    r'c:\Users\secoe\Documents\Projects\CacaoCore\LP02---CacaoCore_64\src\examples\high_level\semalyzer_tests\dims_correct.choco',
]
for f in files:
    print('\n--- Processing', f)
    code = open(f, 'r', encoding='utf-8').read()
    try:
        sem = AnalizadorSemantico()
        sem_result = sem.parse(code, [])
        sem_errors = sem_result.get('errors', [])
        if sem_errors:
            print('Semantic errors:')
            for e in sem_errors:
                print('  ', e)
            continue
        print('Semantic: OK')
        gen = GeneradorCodigo()
        gen_errors, asm = gen.parse(code, [])
        if gen_errors:
            print('Generator (lex/parse) errors:')
            for e in gen_errors:
                print('  ', e)
        else:
            print('Generator: OK')
        print('Assembly preview (first 40 lines):')
        for i,l in enumerate(asm[:40]):
            print(f'{i+1:03}:', l)
    except Exception as ex:
        print('Exception while processing:', ex)
        traceback.print_exc()
