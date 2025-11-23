"""
Sistema de Identificação de Colorimetria Pessoal
Utiliza heurísticas clássicas: Lab/HSV, Harmonia Sazonal e Proporções
Análise de imagens para identificação de coloração pessoal (entrada via bytes ou base64)
"""

import numpy as np
import cv2
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum
from sklearn.cluster import KMeans
import base64


class Estacao(Enum):
    """Classificação sazonal"""
    PRIMAVERA = "Primavera"
    VERAO = "Verão"
    OUTONO = "Outono"
    INVERNO = "Inverno"


@dataclass
class AnaliseCor:
    """Resultado da análise de uma cor"""
    rgb: Tuple[int, int, int]
    hex: str
    hsv: Tuple[float, float, float]
    lab: Tuple[float, float, float]
    temperatura: str  # "quente" ou "fria"
    saturacao: str    # "baixa", "media", "alta"
    luminosidade: str # "escura", "media", "clara"
    estacao: Estacao
    confianca: float


@dataclass
class AnalisePaleta:
    """Resultado da análise de paleta extraída de imagem"""
    cores_principais: List[AnaliseCor]
    estacao_dominante: Estacao
    proporcao_quente_fria: Tuple[int, int]
    proporcao_saturacao: Dict[str, int]
    proporcao_luminosidade: Dict[str, int]
    confianca_geral: float
    imagem_processada: Optional[np.ndarray] = None


class ProcessadorImagem:
    """Processa imagens para extrair paletas de cores relevantes para a análise"""

    @staticmethod
    def carregar_imagem_bytes(imagem_bytes: bytes) -> np.ndarray:
        """Carrega uma imagem a partir de bytes e converte para RGB"""
        nparr = np.frombuffer(imagem_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Não foi possível decodificar a imagem. Verifique o formato.")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb

    @staticmethod
    def redimensionar_imagem(imagem: np.ndarray, max_dimensao: int = 800) -> np.ndarray:
        """Redimensiona a imagem para acelerar processamento"""
        altura, largura = imagem.shape[:2]
        if max(altura, largura) > max_dimensao:
            escala = max_dimensao / max(altura, largura)
            nova_altura = int(altura * escala)
            nova_largura = int(largura * escala)
            imagem = cv2.resize(imagem, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)
        return imagem

    @staticmethod
    def remover_background(imagem: np.ndarray, sensibilidade: float = 0.3) -> np.ndarray:
        """
        Remove background muito claro ou muito escuro (simplificação via canal L do LAB)
        sensibilidade: 0-1, quanto maior, mais agressivo
        """
        img_lab = cv2.cvtColor(imagem, cv2.COLOR_RGB2LAB)
        l_channel = img_lab[:, :, 0]
        limiar_inferior = int(255 * sensibilidade * 0.2)
        limiar_superior = int(255 * (1 - sensibilidade * 0.2))
        mascara = (l_channel > limiar_inferior) & (l_channel < limiar_superior)
        imagem_filtrada = imagem.copy()
        imagem_filtrada[~mascara] = [255, 255, 255]  # Fundo branco
        return imagem_filtrada

    @staticmethod
    def extrair_cores_dominantes(imagem: np.ndarray, n_cores: int = 5, remover_bg: bool = True) -> List[Tuple[int, int, int]]:
        """
        Extrai as cores dominantes da imagem usando K-means clustering
        Retorna lista de cores RGB em ordem de frequência
        """
        img_processada = imagem.copy()
        if remover_bg:
            img_processada = ProcessadorImagem.remover_background(img_processada)

        # Remove pixels muito claros (tende a ser fundo)
        mascara_background = (img_processada.sum(axis=2) < 750)
        pixels_validos = img_processada[mascara_background]
        if len(pixels_validos) < 100:
            pixels_validos = img_processada.reshape(-1, 3)

        unique_colors = len(np.unique(pixels_validos, axis=0))
        k = max(1, min(n_cores, unique_colors))

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(pixels_validos)

        labels = kmeans.labels_
        frequencias = np.bincount(labels)
        indices_ordenados = np.argsort(-frequencias)

        cores = []
        for idx in indices_ordenados:
            cor = tuple(int(x) for x in kmeans.cluster_centers_[idx])
            cores.append(cor)

        return cores


class ColorimetriaAnalyzer:
    """Analisador de colorimetria pessoal (somente rotas usadas por analisar_imagem_bytes)"""

    def __init__(self):
        self.paleta_estacoes = self._definir_paleta_estacoes()

    def _definir_paleta_estacoes(self) -> Dict[Estacao, List[Tuple[int, int, int]]]:
        """Define cores características de cada estação"""
        return {
            Estacao.PRIMAVERA: [
                (255, 182, 193), (144, 238, 144), (255, 218, 185), (173, 255, 47), (255, 240, 245)
            ],
            Estacao.VERAO: [
                (0, 191, 255), (0, 255, 255), (255, 255, 0), (144, 238, 144), (255, 105, 180)
            ],
            Estacao.OUTONO: [
                (184, 92, 23), (255, 140, 0), (210, 105, 30), (189, 183, 107), (205, 92, 92)
            ],
            Estacao.INVERNO: [
                (0, 0, 0), (255, 0, 0), (0, 0, 255), (255, 255, 255), (192, 192, 192)
            ]
        }

    @staticmethod
    def hex_para_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Converte cor hexadecimal para RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_para_hex(rgb: Tuple[int, int, int]) -> str:
        """Converte RGB para hexadecimal"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @staticmethod
    def rgb_para_hsv(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Converte RGB para HSV (H em 0-360, S/V em 0-100)"""
        r, g, b = [x / 255.0 for x in rgb]
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        delta = max_val - min_val

        if delta == 0:
            h = 0
        elif max_val == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_val == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

        s = 0 if max_val == 0 else (delta / max_val) * 100
        v = max_val * 100
        return (h, s, v)

    @staticmethod
    def rgb_para_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Converte RGB para Lab (D65)"""
        r, g, b = [x / 255.0 for x in rgb]

        def srgb_to_linear(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)

        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505

        x /= 0.95047
        y /= 1.00000
        z /= 1.08883

        def f(t):
            delta = 6 / 29
            return t ** (1/3) if t > delta ** 3 else t / (3 * delta ** 2) + 4 / 29

        fx, fy, fz = f(x), f(y), f(z)
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b_val = 200 * (fy - fz)
        return (L, a, b_val)

    def classificar_temperatura(self, h: float, a: float) -> str:
        """Classifica a cor como quente ou fria a partir de H (HSV) e a (Lab)"""
        h = h % 360
        if (0 <= h <= 60) or (330 <= h <= 360):
            return "quente"
        elif 120 <= h <= 240:
            return "fria"
        else:
            return "quente" if a > 0 else "fria"

    @staticmethod
    def classificar_saturacao(s: float) -> str:
        if s < 30:
            return "baixa"
        elif s < 70:
            return "media"
        else:
            return "alta"

    @staticmethod
    def classificar_luminosidade(l: float, v: float) -> str:
        if v < 35:
            return "escura"
        elif v < 65:
            return "media"
        else:
            return "clara"

    @staticmethod
    def calcular_distancia_lab(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
        return np.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

    def classificar_estacao(self, rgb: Tuple[int, int, int], lab: Tuple[float, float, float]) -> Tuple[Estacao, float]:
        """Classifica a cor em uma estação e retorna (estacao, confiança)"""
        distancias = {}
        for estacao, paleta in self.paleta_estacoes.items():
            dist_paleta = [
                self.calcular_distancia_lab(lab, self.rgb_para_lab(cor))
                for cor in paleta
            ]
            distancias[estacao] = min(dist_paleta)

        estacao_minima = min(distancias, key=distancias.get)
        dist_minima = distancias[estacao_minima]
        confianca = max(0, 1 - (dist_minima / 100))
        return estacao_minima, confianca

    def analisar_cor(self, cor_hex: str) -> AnaliseCor:
        """Análise completa de uma cor em hexadecimal '#RRGGBB'"""
        if not isinstance(cor_hex, str) or not cor_hex.startswith('#'):
            raise ValueError("Formato inválido. Use '#RRGGBB'")
        rgb = self.hex_para_rgb(cor_hex)
        hsv = self.rgb_para_hsv(rgb)
        lab = self.rgb_para_lab(rgb)
        temperatura = self.classificar_temperatura(hsv[0], lab[1])
        saturacao = self.classificar_saturacao(hsv[1])
        luminosidade = self.classificar_luminosidade(lab[0], hsv[2])
        estacao, confianca = self.classificar_estacao(rgb, lab)

        return AnaliseCor(
            rgb=rgb,
            hex=cor_hex,
            hsv=hsv,
            lab=lab,
            temperatura=temperatura,
            saturacao=saturacao,
            luminosidade=luminosidade,
            estacao=estacao,
            confianca=confianca
        )

    def analisar_imagem_bytes(self, imagem_bytes: bytes, n_cores: int = 5, remover_background: bool = True) -> AnalisePaleta:
        """
        Análise de imagem a partir de bytes (requisição HTTP)
        Retorna AnalisePaleta com cores principais e estatísticas
        """
        img = ProcessadorImagem.carregar_imagem_bytes(imagem_bytes)
        img_redimensionada = ProcessadorImagem.redimensionar_imagem(img)

        cores_rgb = ProcessadorImagem.extrair_cores_dominantes(
            img_redimensionada,
            n_cores=n_cores,
            remover_bg=remover_background
        )

        cores_hex = [self.rgb_para_hex(cor) for cor in cores_rgb]
        analises = [self.analisar_cor(hex_cor) for hex_cor in cores_hex]

        contagem_estacoes: Dict[Estacao, int] = {}
        contagem_temperatura = {"quente": 0, "fria": 0}
        contagem_saturacao = {"baixa": 0, "media": 0, "alta": 0}
        contagem_luminosidade = {"escura": 0, "media": 0, "clara": 0}
        confiancas = []

        for analise in analises:
            est = analise.estacao
            contagem_estacoes[est] = contagem_estacoes.get(est, 0) + 1
            contagem_temperatura[analise.temperatura] += 1
            contagem_saturacao[analise.saturacao] += 1
            contagem_luminosidade[analise.luminosidade] += 1
            confiancas.append(analise.confianca)

        estacao_dominante = max(contagem_estacoes, key=contagem_estacoes.get)
        confianca_geral = float(np.mean(confiancas)) if confiancas else 0.0

        return AnalisePaleta(
            cores_principais=analises,
            estacao_dominante=estacao_dominante,
            proporcao_quente_fria=(contagem_temperatura["quente"], contagem_temperatura["fria"]),
            proporcao_saturacao=contagem_saturacao,
            proporcao_luminosidade=contagem_luminosidade,
            confianca_geral=confianca_geral,
            imagem_processada=img_redimensionada
        )
    
def analisar_imagem(imagem_dados, n_cores=5, remover_background=True):
    """
    Analisa uma imagem fornecida como bytes, base64 ou arquivo e retorna informações de colorimetria.

    Args:
        imagem_dados: Pode ser:
            - bytes: dados brutos da imagem
            - str (base64): string codificada em base64
            - str (caminho): caminho para o arquivo de imagem
        n_cores (int): Número de cores a extrair (padrão: 5).
        remover_background (bool): Indica se o background deve ser removido (padrão: True).

    Returns:
        dict: Informações de colorimetria da imagem.
    """
    try:
        # Converter para bytes se necessário
        imagem_bytes = _converter_para_bytes(imagem_dados)
        
        # Criar analisador e processar
        analyzer = ColorimetriaAnalyzer()
        analise = analyzer.analisar_imagem_bytes(imagem_bytes, n_cores=n_cores, 
                                                remover_background=remover_background)

        # Formatar resposta
        return {
            "estacao_dominante": analise.estacao_dominante.value,
            "confianca_geral": float(analise.confianca_geral),
            "proporcao_temperatura": {
                "quentes": analise.proporcao_quente_fria[0],
                "frias": analise.proporcao_quente_fria[1]
            },
            "proporcao_saturacao": analise.proporcao_saturacao,
            "proporcao_luminosidade": analise.proporcao_luminosidade,
            "cores_principais": [
                {
                    "hex": cor.hex,
                    "rgb": list(cor.rgb),
                    "hsv": {
                        "hue": round(cor.hsv[0], 2),
                        "saturation": round(cor.hsv[1], 2),
                        "value": round(cor.hsv[2], 2)
                    },
                    "lab": {
                        "L": round(cor.lab[0], 2),
                        "a": round(cor.lab[1], 2),
                        "b": round(cor.lab[2], 2)
                    },
                    "temperatura": cor.temperatura,
                    "saturacao": cor.saturacao,
                    "luminosidade": cor.luminosidade,
                    "estacao": cor.estacao.value,
                    "confianca": round(cor.confianca, 3)
                }
                for cor in analise.cores_principais
            ]
        }

    except ValueError as e:
        raise ValueError(f"Erro de valor: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao processar: {str(e)}")

def _converter_para_bytes(imagem_dados):
    """
    Converte dados de imagem em diferentes formatos para bytes.
    
    Args:
        imagem_dados: bytes, base64 string, ou caminho de arquivo
        
    Returns:
        bytes: Dados da imagem em formato bytes
    """
    # Se for bytes, retornar diretamente
    if isinstance(imagem_dados, bytes):
        return imagem_dados
    
    # Se for string
    if isinstance(imagem_dados, str):
        # Tentar abrir como arquivo primeiro
        try:
            with open(imagem_dados, 'rb') as file:
                return file.read()
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            pass
        
        # Tentar decodificar como base64
        try:
            return base64.b64decode(imagem_dados)
        except Exception:
            raise ValueError(f"Não foi possível interpretar a entrada como caminho de arquivo ou base64")
    
    # Verificar se é um objeto FileInfo (do Azure)
    if hasattr(imagem_dados, 'id') and hasattr(imagem_dados, 'filename'):
        raise ValueError("Objeto FileInfo recebido. Use a API do Azure para baixar o arquivo antes.")
    
    raise ValueError(f"Tipo de dados não suportado: {type(imagem_dados)}. Use bytes, string (base64) ou caminho de arquivo.")

def analisar_imagem_arquivo(imagem_dados, n_cores=5, remover_background=True):
    """
    Analisa uma imagem fornecida como bytes, base64 ou arquivo e retorna informações de colorimetria.
    
    Wrapper da função analisar_imagem() com tratamento de erros específico.

    Args:
        imagem_dados: Pode ser:
            - bytes: dados brutos da imagem
            - str (base64): string codificada em base64
            - str (caminho): caminho para o arquivo de imagem
        n_cores (int): Número de cores a extrair (padrão: 5).
        remover_background (bool): Indica se o background deve ser removido (padrão: True).

    Returns:
        dict: Informações de colorimetria da imagem ou erro estruturado.
    """
    try:
        return analisar_imagem(imagem_dados, n_cores=n_cores, remover_background=remover_background)
    except Exception as e:
        return {
            "erro": str(e),
            "tipo_erro": type(e).__name__
        }
