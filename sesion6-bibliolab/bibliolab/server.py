"""Dos servicios de solo consulta. Ejecutar con -m bibliolab.server normas|circulacion."""
import argparse
from typing import Literal
from mcp.server.fastmcp import FastMCP
from bibliolab.core import search_rules,search_catalog,due_date

def make_server(kind,port=9080):
    server=FastMCP('BiblioLab-'+kind,host='127.0.0.1',port=port,log_level='ERROR')
    if kind=='normas':
        @server.tool()
        def buscar_normas(consulta:str)->dict:
            """Busca reglas de la biblioteca ficticia: plazos, cupos, salas, portátiles, privacidad y alcance. Devuelve fragmentos con IDs citables [N01-S1]. No consulta inventario."""
            return search_rules(consulta)
    else:
        @server.tool()
        def buscar_catalogo(consulta:str)->dict:
            """Busca un título, tema o código de libro y devuelve disponibilidad al corte 2026-10-16. Usa solo el título/tema como consulta. Cita [CAT-Bxxx]. No crea reservas ni identifica lectores."""
            return search_catalog(consulta)

        @server.tool()
        def calcular_devolucion(perfil:Literal['estudiante','docente','egresado'],fecha_retiro:str)->dict:
            """Calcula el vencimiento de un LIBRO en días hábiles, excluyendo fines de semana y cierres. Requiere perfil explícito y fecha AAAA-MM-DD; no inventes datos faltantes. Solo calendario 2026-10-01 a 2026-12-31. Devuelve fechas contadas y referencias."""
            return due_date(perfil,fecha_retiro)
    return server

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['normas','circulacion']);parser.add_argument('--http',action='store_true');parser.add_argument('--port',type=int,default=9080)
    args=parser.parse_args();make_server(args.kind,args.port).run(transport='streamable-http' if args.http else 'stdio')
