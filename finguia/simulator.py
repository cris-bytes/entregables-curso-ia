"""Cálculo determinista; ninguna tasa es un pronóstico del mercado."""
import math
import numpy as np
import pandas as pd

def simulate(initial=1000000, monthly=100000, years=10, annual_return=6, annual_fee=0.3, inflation=3):
    values = (initial, monthly, years, annual_return, annual_fee, inflation)
    if not all(math.isfinite(float(x)) for x in values):
        raise ValueError('Todos los valores deben ser finitos.')
    if not (0 <= initial <= 1e12 and 0 <= monthly <= 1e10 and 1 <= years <= 50 and float(years).is_integer()):
        raise ValueError('Capital/aporte no negativos y plazo entero entre 1 y 50 años.')
    if not (-95 <= annual_return <= 100 and 0 <= annual_fee <= 20 and -50 <= inflation <= 100):
        raise ValueError('Tasa, comisión o inflación fuera del rango del simulador.')
    gross_factor = (1+annual_return/100)**(1/12)
    net_factor = gross_factor*(1-annual_fee/100)**(1/12)
    balance, gross = float(initial), float(initial)
    rows = []
    for month in range(int(years)*12+1):
        if month:
            balance = balance*net_factor + monthly
            gross = gross*gross_factor + monthly
        rows.append(dict(month=month,year=month/12,contributed=initial+monthly*month,
            nominal=balance,real=balance/(1+inflation/100)**(month/12),without_fees=gross))
    return pd.DataFrame(rows)
