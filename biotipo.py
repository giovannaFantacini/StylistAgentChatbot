"""
Sistema de Classificação de Biotipo Corporal
Classifica o tipo de corpo baseado em medidas de ombro, cintura e quadril
"""

from typing import Dict


def classificar_biotipo(ombro: float, cintura: float, quadril: float, tolerancia: float = 2.0) -> Dict[str, str]:
    """
    Classifica o biotipo corporal baseado em medidas de ombro, cintura e quadril.
    
    Args:
        ombro (float): Medida do ombro em cm
        cintura (float): Medida da cintura em cm
        quadril (float): Medida do quadril em cm
        tolerancia (float): Margem de tolerância em cm para considerar medidas iguais (padrão: 2.0)
    
    Returns:
        dict: Dicionário com:
            - "biotipo": Nome do tipo corporal
    """
    
    # Validar entrada
    if ombro <= 0 or cintura <= 0 or quadril <= 0:
        return {
            "erro": "Todas as medidas devem ser maiores que zero",
            "biotipo": None
        }
    
    # Calcular diferenças
    diff_ombro_quadril = ombro - quadril
    diff_quadril_ombro = quadril - ombro

    # Função auxiliar para verificar se dois valores são aproximadamente iguais
    def sao_iguais(valor1: float, valor2: float, tol: float = tolerancia) -> bool:
        return abs(valor1 - valor2) <= tol
    
    # Classificação
    biotipo = None

    
    # 1. Triângulo Invertido: Ombros > Quadris
    if diff_ombro_quadril > tolerancia:
        biotipo = "Triângulo Invertido"

    
    # 2. Triângulo: Quadris > Ombros com Cintura Fina
    elif diff_quadril_ombro > tolerancia and cintura < ombro and cintura < quadril:
        biotipo = "Triângulo"

    
    # 3. Ampulheta: Ombros = Quadris com Cintura Fina
    elif sao_iguais(ombro, quadril) and cintura < ombro and cintura < quadril:
        biotipo = "Ampulheta"

    
    # 4. Oval: Cintura > Ombros e Cintura > Quadrils
    elif cintura > ombro and cintura > quadril:
        biotipo = "Oval"

    # 5. Retângulo: Todas as medidas aproximadamente iguais
    elif sao_iguais(ombro, cintura) and sao_iguais(cintura, quadril):
        biotipo = "Retângulo"

    
    else:
        # Se quadril > ombro mas cintura não é tão fina
        if diff_quadril_ombro > tolerancia:
            biotipo = "Triângulo"

        # Se ombro > quadril
        elif diff_ombro_quadril > tolerancia:
            biotipo = "Triângulo Invertido"

        # Se cintura > ombro e quadril
        elif cintura > ombro and cintura > quadril:
            biotipo = "Oval"

        else:
            biotipo = "Retângulo"
    
    return biotipo


