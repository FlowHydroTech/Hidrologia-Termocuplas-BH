"""
stages — Etapas del pipeline Hatch-Amplitude como módulos independientes.

Cada stage_XX.py expone una función principal decorada con @task de Prefect,
y también es ejecutable de forma independiente vía su bloque __main__.
"""
