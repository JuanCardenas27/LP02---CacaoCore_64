"""
semantic_ast_annotator.py
=========================
Pasada semántica del AST para CacaoScript.

Este módulo separa la recursión de anotación del analizador semántico
principal para mantener `analizador_semantico.py` centrado en scopes,
validación y símbolos.
"""

from __future__ import annotations

from .ast_nodos import (
    Nodo,
    NodoAccesoArreglo,
    NodoAccesoMiembro,
    NodoBinario,
    NodoBloque,
    NodoBooleano,
    NodoCadena,
    NodoDeclaracion,
    NodoEntregar,
    NodoEntero,
    NodoFlotante,
    NodoFuncion,
    NodoID,
    NodoListaValores,
    NodoLlamada,
    NodoMold,
    NodoNada,
    NodoOhmy,
    NodoOops,
    NodoParametro,
    NodoPrograma,
    NodoReasignacion,
    NodoSi,
    NodoMostrar,
    NodoSummon,
    NodoTerminal,
    NodoUnario,
    NodoMientras,
    NodoPara,
)


class ASTSemanticAnnotator:
    """Anotador recursivo del AST con metadatos semánticos."""

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def annotate(self, node, _visited=None):
        """Recorrido semántico del AST."""
        if _visited is None:
            _visited = set()

        def default_info(type_name='unknown', dims=0, symbol=None, scope_id=None, value=None):
            return self.analyzer._make_semantic_info(
                type_name,
                dims,
                symbol=symbol,
                scope_id=scope_id,
                value=value,
            )

        if node is None:
            return default_info('void', 0)

        if isinstance(node, (list, tuple)):
            last_info = default_info('void', 0)
            for item in node:
                last_info = self.annotate(item, _visited)
            return last_info

        if not isinstance(node, Nodo):
            return default_info('unknown', 0)

        node_id = id(node)
        if node_id in _visited:
            return getattr(node, 'semantic_info', default_info(
                getattr(node, 'tipo', 'unknown') if not isinstance(node, NodoTerminal) else 'unknown',
                getattr(node, 'dims', 0) if not isinstance(node, NodoTerminal) else 0,
                scope_id=getattr(node, 'scope_id', None) if not isinstance(node, NodoTerminal) else None,
            ))
        _visited.add(node_id)

        child_infos = {}
        for child_name, child in self.analyzer._semantic_children(node):
            if isinstance(child, (list, tuple)):
                child_infos[child_name] = [self.annotate(item, _visited) for item in child]
            else:
                child_infos[child_name] = self.annotate(child, _visited)

        def info_from_child(name, fallback=None):
            value = child_infos.get(name)
            if value is None:
                return fallback if fallback is not None else default_info()
            if isinstance(value, list):
                if not value:
                    return fallback if fallback is not None else default_info()
                return value[-1]
            return value

        if isinstance(node, NodoDeclaracion):
            declared_type = self.analyzer._extract_type(node.tipo)
            declared_dims = int(getattr(node, 'dim1', None) is not None) + int(getattr(node, 'dim2', None) is not None)
            sym = self.analyzer._find_symbol_for_name(self.analyzer._node_name(node), self.analyzer._node_line(node))
            node.tipo_decl = declared_type
            return self.analyzer._set_node_semantics(
                node,
                type_name=declared_type,
                dims=declared_dims,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoParametro):
            declared_type = self.analyzer._extract_type(node.tipo)
            sym = self.analyzer._find_symbol_for_name(self.analyzer._node_name(node), self.analyzer._node_line(node))
            node.tipo_decl = declared_type
            return self.analyzer._set_node_semantics(
                node,
                type_name=declared_type,
                dims=0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoID):
            sym = self.analyzer._find_symbol_for_name(node.nombre, self.analyzer._node_line(node))
            return self.analyzer._set_node_semantics(
                node,
                type_name=sym.get('type', 'unknown') if sym else 'unknown',
                dims=sym.get('dims', 0) if sym else 0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
                value=sym.get('value') if sym else None,
            )

        if isinstance(node, NodoEntero):
            return self.analyzer._set_node_semantics(node, type_name='int', dims=0, value=node.valor)
        if isinstance(node, NodoFlotante):
            return self.analyzer._set_node_semantics(node, type_name='float', dims=0, value=node.valor)
        if isinstance(node, NodoCadena):
            return self.analyzer._set_node_semantics(node, type_name='text', dims=0, value=node.valor)
        if isinstance(node, NodoBooleano):
            return self.analyzer._set_node_semantics(node, type_name='bool', dims=0, value=node.valor)
        if isinstance(node, NodoNada):
            return self.analyzer._set_node_semantics(node, type_name='void', dims=0)
        if isinstance(node, NodoTerminal):
            return default_info('unknown', 0)

        if isinstance(node, NodoPrograma):
            return self.analyzer._set_node_semantics(
                node,
                type_name='void',
                dims=0,
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoBloque):
            return self.analyzer._set_node_semantics(
                node,
                type_name='void',
                dims=0,
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoListaValores):
            items_info = child_infos.get('items', [])
            first_info = default_info('unknown', 1)
            if isinstance(items_info, list):
                for item_info in items_info:
                    if item_info.get('type') not in (None, 'unknown'):
                        first_info = item_info
                        break
                if items_info and first_info.get('type') == 'unknown':
                    first_info = items_info[0]
            return self.analyzer._set_node_semantics(
                node,
                type_name=first_info.get('type', 'unknown'),
                dims=1,
                symbol=None,
                scope_id=first_info.get('scope_id'),
            )

        if isinstance(node, NodoAccesoArreglo):
            target_info = info_from_child('arreglo', default_info('unknown', 0))
            index_count = sum(
                1
                for element in getattr(node, 'brackets_indices', [])
                if isinstance(element, Nodo) and not isinstance(element, NodoTerminal)
            )
            return self.analyzer._set_node_semantics(
                node,
                type_name=target_info.get('type', 'unknown'),
                dims=max(target_info.get('dims', 0) - index_count, 0),
                symbol=None,
                scope_id=target_info.get('scope_id'),
            )

        if isinstance(node, NodoAccesoMiembro):
            target_info = info_from_child('obj', default_info('unknown', 0))
            member_name = self.analyzer._node_name(node.miembro)
            mold_name = target_info.get('type', 'unknown')
            field_info = self.analyzer._resolve_field_from_mold(mold_name, member_name) if member_name else None
            if field_info is not None:
                return self.analyzer._set_node_semantics(
                    node,
                    type_name=field_info.get('type', 'unknown'),
                    dims=field_info.get('dims', 0),
                    symbol=field_info,
                    scope_id=field_info.get('scope_id', target_info.get('scope_id')),
                )
            method_info = self.analyzer._resolve_method_from_mold(mold_name, member_name) if member_name else None
            if method_info is not None:
                return self.analyzer._set_node_semantics(
                    node,
                    type_name=method_info.get('return_type', 'void'),
                    dims=method_info.get('dims', 0),
                    symbol=method_info,
                    scope_id=method_info.get('scope_id', target_info.get('scope_id')),
                )
            return self.analyzer._set_node_semantics(
                node,
                type_name='unknown',
                dims=0,
                symbol=None,
                scope_id=target_info.get('scope_id'),
            )

        if isinstance(node, NodoSummon):
            class_name = self.analyzer._node_name(node.clase)
            sym = self.analyzer._resolve_symbol(class_name) if class_name else None
            if sym is None and class_name:
                sym = self.analyzer._find_symbol_for_name(class_name, self.analyzer._node_line(node))
            return self.analyzer._set_node_semantics(
                node,
                type_name=class_name or 'unknown',
                dims=0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoOhmy):
            sym = self.analyzer._resolve_symbol(self.analyzer.current_method_mold) if self.analyzer.current_method_mold else None
            if sym is None and self.analyzer.current_method_mold:
                sym = self.analyzer._find_symbol_for_name(self.analyzer.current_method_mold, self.analyzer._node_line(node))
            return self.analyzer._set_node_semantics(
                node,
                type_name=self.analyzer.current_method_mold or 'unknown',
                dims=0,
                symbol=None,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoLlamada):
            if isinstance(node.func, NodoAccesoMiembro):
                object_info = self.annotate(node.func.obj, _visited)
                member_name = self.analyzer._node_name(node.func.miembro)
                method_info = self.analyzer._resolve_method_from_mold(object_info.get('type', 'unknown'), member_name) if member_name else None
                if method_info is not None:
                    return self.analyzer._set_node_semantics(
                        node,
                        type_name=method_info.get('return_type', 'void'),
                        dims=method_info.get('dims', 0),
                        symbol=method_info,
                        scope_id=method_info.get('scope_id', object_info.get('scope_id')),
                    )
                return self.analyzer._set_node_semantics(
                    node,
                    type_name='unknown',
                    dims=0,
                    symbol=None,
                    scope_id=object_info.get('scope_id'),
                )

            func_name = self.analyzer._node_name(node.func)
            sym = self.analyzer._resolve_symbol(func_name) if func_name else None
            if sym is None and func_name:
                sym = self.analyzer._find_symbol_for_name(func_name, self.analyzer._node_line(node))
            return self.analyzer._set_node_semantics(
                node,
                type_name=sym.get('return_type', sym.get('type', 'unknown')) if sym else 'unknown',
                dims=sym.get('dims', 0) if sym else 0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoBinario):
            left_info = info_from_child('izq', default_info('unknown', 0))
            right_info = info_from_child('der', default_info('unknown', 0))
            op = self.analyzer._node_name(node.op)
            if op in {'+', '-', '*', '/', '%'}:
                return self.analyzer._set_node_semantics(
                    node,
                    type_name=self.analyzer._promote_numeric_types(left_info.get('type'), right_info.get('type')),
                    dims=max(left_info.get('dims', 0), right_info.get('dims', 0)),
                    symbol=None,
                    scope_id=None,
                )
            if op in {'==', '!=', '<', '>', '<=', '>='}:
                return self.analyzer._set_node_semantics(
                    node,
                    type_name='bool',
                    dims=0,
                    symbol=None,
                    scope_id=None,
                )
            if op in {'and', 'or', 'xor'}:
                return self.analyzer._set_node_semantics(
                    node,
                    type_name='bool',
                    dims=0,
                    symbol=None,
                    scope_id=None,
                )
            return self.analyzer._set_node_semantics(
                node,
                type_name='unknown',
                dims=max(left_info.get('dims', 0), right_info.get('dims', 0)),
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoUnario):
            expr_info = info_from_child('expr', default_info('unknown', 0))
            op = self.analyzer._node_name(node.op)
            if op == '-':
                return self.analyzer._set_node_semantics(
                    node,
                    type_name=expr_info.get('type', 'unknown'),
                    dims=expr_info.get('dims', 0),
                    symbol=None,
                    scope_id=None,
                )
            if op == 'not':
                return self.analyzer._set_node_semantics(
                    node,
                    type_name='bool',
                    dims=0,
                    symbol=None,
                    scope_id=None,
                )
            return self.analyzer._set_node_semantics(
                node,
                type_name=expr_info.get('type', 'unknown'),
                dims=expr_info.get('dims', 0),
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoReasignacion):
            expr_info = info_from_child('expr', default_info('unknown', 0))
            lvalue_info = self.analyzer._resolve_lvalue_type(node.lvalue, self.analyzer._node_line(node)) or {}
            return self.analyzer._set_node_semantics(
                node,
                type_name=lvalue_info.get('type', expr_info.get('type', 'unknown')),
                dims=lvalue_info.get('dims', expr_info.get('dims', 0)),
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoEntregar):
            expr_info = info_from_child('expr', default_info('void', 0))
            return self.analyzer._set_node_semantics(
                node,
                type_name=expr_info.get('type', 'void'),
                dims=expr_info.get('dims', 0),
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, (NodoMostrar, NodoOops)):
            expr_info = info_from_child('expr', default_info('unknown', 0))
            return self.analyzer._set_node_semantics(
                node,
                type_name='void',
                dims=0,
                symbol=None,
                scope_id=None,
            )

        if isinstance(node, NodoFuncion):
            name = self.analyzer._node_name(node)
            sym = self.analyzer._find_symbol_for_name(name, self.analyzer._node_line(node)) if name else None
            return_type = sym.get('return_type', 'void') if sym else 'void'
            node.set_return_type(return_type)
            return self.analyzer._set_node_semantics(
                node,
                type_name='function',
                dims=0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, NodoMold):
            name = self.analyzer._node_name(node)
            sym = self.analyzer._find_symbol_for_name(name, self.analyzer._node_line(node)) if name else None
            return self.analyzer._set_node_semantics(
                node,
                type_name='mold',
                dims=0,
                symbol=sym,
                scope_id=sym.get('scope_id') if sym else None,
            )

        if isinstance(node, (NodoMientras, NodoPara, NodoSi)):
            return self.analyzer._set_node_semantics(
                node,
                type_name='void',
                dims=0,
                symbol=None,
                scope_id=None,
            )

        last_info = default_info('unknown', 0)
        for child_info in child_infos.values():
            if isinstance(child_info, list) and child_info:
                last_info = child_info[-1]
            elif isinstance(child_info, dict):
                last_info = child_info

        return self.analyzer._set_node_semantics(
            node,
            type_name=last_info.get('type', 'unknown'),
            dims=last_info.get('dims', 0),
            symbol=None,
            scope_id=last_info.get('scope_id'),
        )
