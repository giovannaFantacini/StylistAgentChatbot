# 🎨 Sistema de Análise de Colorimetria Pessoal

Um sistema completo e inteligente para identificar colorimetria pessoal a partir de imagens, utilizando heurísticas clássicas de análise de cor.

## 📋 Recursos

✅ **Processamento de Imagens**
- Extração automática de cores dominantes usando K-means clustering
- Suporte para múltiplos formatos (JPG, PNG, BMP, GIF)

✅ **Análise Completa de Cores**
- Conversão entre espaços de cor (RGB → HSV → Lab)
- Análise perceptual usando espaço CIE L*a*b*
- Classificação automática por características

✅ **Harmonia Sazonal**
- Classificação em 4 estações (Primavera, Verão, Outono, Inverno)
- Score de confiança para cada classificação
- Paletas características por estação

✅ **Proporções de Cor**
- **Temperatura**: Cores Quentes vs Frias
- **Saturação**: Baixa, Média, Alta
- **Luminosidade**: Escura, Média, Clara

## 🚀 Quick Start

### 1. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 2. Análise Simples de uma Imagem

```python
from colorimetria import ColorimetriaAnalyzer

analyzer = ColorimetriaAnalyzer()

# Analisar imagem
analise = analyzer.analisar_imagem("sua_imagem.jpg", n_cores=5)

# Exibir relatório
print(analyzer.gerar_relatorio_imagem(analise))

# Salvar análise em JSON
analyzer.salvar_analise_json(analise, "analise.json")
```

## 📖 Documentação

### Classe ColorimetriaAnalyzer

#### Métodos Principais

**`analisar_cor(cor: str) → AnaliseCor`**
- Analisa uma cor individual (formato: "#RRGGBB")
- Retorna: AnaliseCor com todas as características

**`analisar_imagem(caminho_imagem: str, n_cores: int = 5) → AnalisePaleta`**
- Analisa uma imagem completa
- Extrai `n_cores` cores dominantes
- Retorna: AnalisePaleta com estatísticas completas

**`gerar_relatorio_imagem(analise_paleta: AnalisePaleta) → str`**
- Gera relatório completo da análise de imagem

**`salvar_analise_json(analise_paleta: AnalisePaleta, caminho_saida: Path) → None`**
- Salva análise em formato JSON

## 📊 Interpretação de Resultados

### Estações Identificadas

| Estação | Características |
|---------|-----------------|
| **Primavera** | Tons suaves, pastéis, claros e frescos |
| **Verão** | Cores vibrantes, luminosas e saturadas |
| **Outono** | Tons quentes, terrosos, dourados, marrom |
| **Inverno** | Cores puras, contrastadas, preto/branco/neon |

### Espaço de Cores

#### HSV (Hue, Saturation, Value)
- **Hue (Matiz)**: 0-360° (cor pura)
- **Saturation**: 0-100% (intensidade da cor)
- **Value**: 0-100% (luminosidade)

#### Lab (Espaço Perceptual CIE L*a*b*)
- **L (Luminosidade)**: 0-100
- **a (Eixo verde-magenta)**: -128 a 127
- **b (Eixo azul-amarelo)**: -128 a 127

### Temperatura das Cores

```
QUENTE: 0-60° e 300-360° (Vermelho, Laranja, Amarelo)
FRIA:   120-240° (Verde, Ciano, Azul)
```

### Saturação

- **Baixa** (<30%): Cores acinzentadas, suaves
- **Média** (30-70%): Cores naturais, equilibradas
- **Alta** (>70%): Cores vibrantes, intensas

### Luminosidade

- **Escura** (<35%): Cores muito escuras
- **Média** (35-65%): Cores neutras
- **Clara** (>65%): Cores muito brilhantes

## ⚙️ Formato JSON de Saída

```json
{
  "estacao_dominante": "Verão",
  "confianca_geral": 0.95,
  "proporcao_temperatura": {
    "quentes": 3,
    "frias": 2
  },
  "proporcao_saturacao": {
    "baixa": 1,
    "media": 2,
    "alta": 2
  },
  "proporcao_luminosidade": {
    "escura": 0,
    "media": 0,
    "clara": 5
  },
  "cores_principais": [
    {
      "hex": "#00BFFF",
      "rgb": [0, 191, 255],
      "hsv": {
        "hue": 195.06,
        "saturation": 100.0,
        "value": 100.0
      },
      "lab": {
        "L": 72.55,
        "a": -17.65,
        "b": -42.55
      },
      "temperatura": "fria",
      "saturacao": "alta",
      "luminosidade": "clara",
      "estacao": "Verão",
      "confianca": 1.0
    }
  ]
}
```

## 💡 Dicas e Boas Práticas

1. **Use imagens com boa iluminação**: Resultados mais precisos com luz natural
2. **Analise múltiplas fotos**: Combine resultados para melhor caracterização
3. **Ajuste n_cores**: Teste diferentes números para sua aplicação

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
- Verifique o caminho correto da imagem
- Use caminhos absolutos ou relativos bem definidos

### Erro: "Formato de imagem não suportado"
- Formatos aceitos: JPG, PNG, BMP, GIF
- Converta sua imagem para um desses formatos

### Resultado impreciso
- Melhore a iluminação da imagem
- Aumente `n_cores` para análise mais detalhada

## 📝 Licença e Créditos

Desenvolvido com base em heurísticas clássicas de colorimetria pessoal e análise de cores.

Todas as informações sobre colorimetria foram retiradas da seguinte referência:  https://portalidea.com.br/apostila-arquivo/bsico-em-colorimetria-pessoal-apostila02.pdf

---

**Enjoy your color analysis! 🎨✨**
