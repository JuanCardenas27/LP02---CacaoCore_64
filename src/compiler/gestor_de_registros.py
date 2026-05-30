class GestorRegistros:
    def __init__(self):
        # Usamos R0-R15, reservando R9 para convenios internos y R13 para SP.
        self.registros = {f"R{i}": False for i in range(16) if i not in (9,)}
        self.acumulador = "R15"
        self.allow_r13 = True
        # Instrumentation: append-only log of allocation/free events for debugging.
        try:
            self._log_fh = open('reg_ops.log', 'a', encoding='utf-8')
        except Exception:
            self._log_fh = None

    def ocupar(self):
        for reg, ocupado in self.registros.items():
            if reg == 'R13' and not self.allow_r13:
                continue
            if not ocupado:
                self.registros[reg] = True
                try:
                    if self._log_fh:
                        import traceback, time
                        self._log_fh.write(f"OCCUPY {reg} @ {time.time()}\n")
                        self._log_fh.writelines(traceback.format_stack()[-6:])
                        self._log_fh.flush()
                except Exception:
                    pass
                return reg
        # No free registers: print a diagnostic stack to help trace where
        # registers were consumed (temporary debugging aid), then raise.
        try:
            import traceback
            stack = traceback.format_stack()
            with open('reg_trace.txt', 'w', encoding='utf-8') as fh:
                fh.write('--- Register allocation failure stack trace ---\n')
                fh.writelines(stack)
                fh.write('\n--- Registros state ---\n')
                fh.write(repr(self.registros) + '\n')
        except Exception:
            pass
        raise RuntimeError('No free registers available')

    def liberar(self, reg):
        if reg in self.registros:
            self.registros[reg] = False
            try:
                if self._log_fh:
                    import traceback, time
                    self._log_fh.write(f"FREE   {reg} @ {time.time()}\n")
                    self._log_fh.writelines(traceback.format_stack()[-6:])
                    self._log_fh.flush()
            except Exception:
                pass

    def liberar_todo(self):
        for reg in self.registros:
            self.registros[reg] = False
        try:
            if self._log_fh:
                self._log_fh.write('LIBERAR_TODO\n')
                self._log_fh.flush()
        except Exception:
            pass
