#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 GERADOR DE PROMPT UNIVERSAL  -  v1.0
 Compilador cinematografico de prompts para IA de imagem e video
 (Midjourney / Runway Gen-3 / Kling / Luma / Sora / Hunyuan / Veo)
===============================================================================

 COMO FUNCIONA (a "formula"):
 ---------------------------------------------------------------------------
 1. Voce preenche UMA VEZ os blocos fixos: Personagem, Ambiente, Camera,
    Luz, Audio e Motor de IA.
 2. No RECEITA/FORMULA existe um template com tokens ({SUJEITO}, {CAMERA},
    {LUZ}, ...). O compilador apenas substitui os tokens.
    => Para mudar a cena inteira voce altera SO UM CAMPO (ex: a luz) e
       todos os prompts/cenas sao recompilados automaticamente.
 3. No ROTEIRO voce escreve palavras-chave ("celular", "copo de agua").
    Na FRENTE de cada palavra-chave existe a escolha de CAMERA + ANGULO +
    ENQUADRAMENTO (rosto e olhos / busto / meio corpo / corpo inteiro /
    pernas / barriga ...). Essa escolha define como AQUELA cena sera
    gravada. Palavras-chave conhecidas disparam sugestao automatica.
 4. SAIDA: cada plataforma recebe o prompt no formato correto, ja em
    ingles tecnico, com Negative Prompt, seed, fps e shot list.

 Requisitos: Python 3.9+ com tkinter (padrao no Windows).
 Execucao:   python gerador_de_prompt.py
 Licenca:    uso livre.
===============================================================================
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import textwrap
import datetime
from collections import namedtuple

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception as exc:  # pragma: no cover
    sys.stderr.write(
        "ERRO: tkinter nao encontrado. No Windows reinstale o Python marcando\n"
        "'tcl/tk and IDLE'. No Linux: sudo apt install python3-tk\n(%s)\n" % exc
    )
    raise

APP_NAME = "Gerador de Prompt Universal"
APP_VERSION = "1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRESET_DIR = os.path.join(BASE_DIR, "presets")
HIST_DIR = os.path.join(BASE_DIR, "historico")
OUTPUT_DIR = os.path.join(BASE_DIR, "saidas")
DATA_DIR = os.path.join(BASE_DIR, "dados")

# ----------------------------------------------------------------------------
# PALETA / TEMA
# ----------------------------------------------------------------------------
CLR = {
    "bg":        "#191b21",
    "panel":     "#21242c",
    "panel2":    "#272b34",
    "field":     "#2e3340",
    "line":      "#39404f",
    "fg":        "#e9ecf2",
    "fg_dim":    "#9aa3b2",
    "accent":    "#4da3ff",
    "accent2":   "#ffb35c",
    "ok":        "#5ddb9a",
    "warn":      "#ff6b6b",
    "tip_bg":    "#11131a",
}
FONT = ("Segoe UI", 9)
FONT_B = ("Segoe UI", 9, "bold")
FONT_H = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 9)

# ----------------------------------------------------------------------------
# CATALOGO DE OPCOES
#   Opt(label_pt, en, info)
#     label_pt -> o que aparece no combo
#     en       -> termo tecnico que entra no prompt final
#     info     -> texto do balao ⓘ
# ----------------------------------------------------------------------------
Opt = namedtuple("Opt", "label en info")


def O(label, en, info=""):
    return Opt(label, en, info)


OPTIONS: dict[str, list[Opt]] = {}

OPTIONS["camera_body"] = [
    O("ARRI Alexa Mini LF (cinema suave)", "shot on ARRI Alexa Mini LF, high dynamic range, filmic highlight rolloff",
      "Padrao de cinema de alto orcamento. Pele suave, luz com transicao macia, muita latitude em areas claras. Use em moda, luxo, drama."),
    O("RED V-Raptor 8K (nitidez extrema)", "shot on RED V-Raptor 8K, ultra sharp, micro-detail texture",
      "Nitidez agressiva e textura. Otimo para produto, tech, joias e pele com poro visivel. Evite em beauty se quiser pele limpa."),
    O("Sony FX3 / A7S III (low light)", "shot on Sony FX3, clean low-light sensor, natural color science",
      "Camera de creator profissional. Boa em cena noturna com pouca luz e ruido baixo."),
    O("Canon C70 (tom de pele quente)", "shot on Canon C70, warm skin tones, Canon color science",
      "Tom de pele quente e agradavel. Entrevista, corporativo, lifestyle."),
    O("iPhone 16 Pro Max na mao (UGC)", "shot on iPhone 16 Pro Max, handheld, casual vertical UGC look",
      "Estilo influenciador/anuncio nativo. Parece real, nao parece anuncio. Combine com luz de janela e movimento handheld."),
    O("Filme 35mm Kodak Portra 400", "35mm film, Kodak Portra 400, subtle film grain, halation",
      "Textura analogica, grao fino, cor pastel organica. Editorial, nostalgia, casamento."),
    O("Filme 16mm Kodak Vision3 500T", "16mm film, Kodak Vision3 500T, heavy grain, tungsten balance",
      "Grao forte e cru, cara de documentario antigo ou clipe musical noturno."),
    O("Polaroid / instant film", "instant polaroid film, soft focus, washed highlights, white frame",
      "Look de foto instantanea: contraste lavado, foco macio, nostalgia imediata."),
    O("Camera de seguranca / CCTV", "CCTV security camera footage, low resolution, timestamp overlay, wide angle",
      "Para suspense, 'vazamento', found footage. Resolucao baixa e grande angular."),
    O("Drone cinematografico", "aerial drone cinematography, DJI Inspire, smooth gimbal motion",
      "Plano aereo. Use com movimento 'reveal' e paisagem ampla."),
]

OPTIONS["lens"] = [
    O("14mm ultra wide (distorcao)", "14mm ultra wide angle lens, pronounced edge distortion",
      "Exagera profundidade e deforma bordas. Dramatico, skate, arquitetura, cena claustrofobica."),
    O("24mm wide (ambiente)", "24mm wide angle lens, environmental context",
      "Mostra o sujeito DENTRO do ambiente. Bom para cena com cenario importante."),
    O("35mm street/documental", "35mm lens, documentary framing, balanced subject and environment",
      "Equilibrio entre pessoa e lugar. Padrao de narrativa e vlog bem feito."),
    O("50mm standard (olho humano)", "50mm lens, natural human-eye perspective",
      "Perspectiva neutra, sem distorcao. Seguro para qualquer cena."),
    O("85mm retrato (fundo cremoso)", "85mm portrait lens, creamy bokeh, facial compression",
      "Comprime o rosto de forma elegante e derrete o fundo. Padrao de retrato e moda."),
    O("135mm telefoto (compressao)", "135mm telephoto lens, strong background compression",
      "Achata o fundo e isola o sujeito de longe. Paparazzi, esporte, isolamento."),
    O("100mm macro (textura extrema)", "100mm macro lens, extreme texture detail, shallow focus plane",
      "Gota de agua, poro, tecido, metal. Use junto com enquadramento de detalhe."),
    O("Anamorfica 2x (flares ovais)", "anamorphic 2x lens, horizontal lens flare, oval bokeh, 2.39:1",
      "Flares horizontais azuis e bokeh oval. Cara de cinema blockbuster."),
    O("Tilt-shift (foco seletivo)", "tilt-shift lens, selective plane of focus, miniature effect",
      "Faz o mundo parecer miniatura ou isola uma faixa de foco diagonal."),
    O("Lente vintage Helios swirl", "vintage Helios 44-2 lens, swirly bokeh, low contrast glow",
      "Bokeh em redemoinho e brilho suave. Romantico, sonho, retro."),
]

OPTIONS["aperture"] = [
    O("f/1.2 - f/1.8 (fundo muito desfocado)", "shot at f/1.4, razor-thin depth of field, heavy bokeh",
      "Profundidade rasissima: so o olho fica nitido. Cuidado: IA erra foco em cena com muita acao."),
    O("f/2.8 (sujeito isolado, seguro)", "shot at f/2.8, shallow depth of field, subject isolation",
      "Melhor equilibrio entre separacao do fundo e estabilidade da geracao."),
    O("f/4 - f/5.6 (sujeito + fundo proximo)", "shot at f/4, moderate depth of field",
      "Sujeito e o que esta logo atras ficam legiveis. Bom para produto na mao."),
    O("f/8 - f/11 (tudo nitido)", "shot at f/8, deep focus, everything in sharp focus",
      "Paisagem, arquitetura, cena com varios elementos importantes."),
    O("f/16 (deep focus total + estrelas de luz)", "shot at f/16, hyperfocal deep focus, starburst highlights",
      "Maxima profundidade e pontos de luz em estrela. Cena ampla e grafica."),
]

# ENQUADRAMENTO: o coracao do sistema de palavras-chave
OPTIONS["shot"] = [
    O("Rosto e olhos (extreme close-up)", "extreme close-up on the eyes, eyelashes and iris detail filling frame",
      "Maximo de emocao. Olho, iris, cilios, lagrima. Use com 100mm macro ou 85mm e f/1.4."),
    O("Rosto inteiro (close-up)", "close-up shot of the face, chin to forehead in frame",
      "Expressao facial completa. Padrao para fala, reacao e beauty."),
    O("Busto (ombros e rosto)", "bust shot, head and shoulders, chest up framing",
      "Enquadramento de entrevista e locucao. Mostra postura e colarinho."),
    O("Meio corpo (medium shot)", "medium shot, framed from the waist up",
      "Mostra maos e gesto junto do rosto. Melhor escolha para alguem segurando um objeto."),
    O("Cowboy (meio das coxas)", "cowboy shot, framed from mid-thigh up",
      "Mostra corpo e postura sem perder o rosto. Moda e atitude."),
    O("Corpo inteiro (full shot)", "full body shot, head to feet inside frame",
      "Roupa, pose e ambiente completos. Essencial para moda e dancar/andar."),
    O("Plano amplo (wide / estabelecimento)", "wide establishing shot, subject small within the environment",
      "Apresenta o lugar. Use como primeira cena do roteiro."),
    O("Busto / decote (detalhe)", "tight chest and neckline detail shot, fabric and jewelry texture",
      "Detalhe de colar, tecido, decote de roupa. Mantenha descricao de vestuario forte."),
    O("Barriga / abdomen", "midriff detail shot, waist and abdomen in frame",
      "Fitness, cintura de roupa, cinto. Combine com luz lateral dura para definicao."),
    O("Pernas", "legs detail shot, from hips to ankles",
      "Calca, saia, meia, movimento de caminhada. Angulo baixo aumenta a perna."),
    O("Pes / calcado", "feet and footwear detail shot, ground level",
      "Tenis, salto, textura do chao, passo."),
    O("Maos / detalhe de produto", "extreme close-up of hands holding the product, fingertip detail",
      "Quando a palavra-chave e um objeto pequeno (celular, perfume, copo)."),
    O("Costas / nuca", "shot from behind, back and nape of the neck in frame",
      "Misterio, reveal, caminhada de saida."),
    O("Over-the-shoulder (por tras do ombro)", "over-the-shoulder shot, shoulder in foreground framing the subject",
      "Conversa e ponto de vista de quem observa."),
    O("Olhar por cima do ombro (de costas, olhando pra tras)",
      "over-the-shoulder glance, subject seen from behind turning the head to look back at the camera over the shoulder, "
      "intense lingering gaze, shoulder and jawline in frame",
      "O personagem aparece de costas (ou 3/4) e vira o rosto para a camera POR CIMA DO OMBRO. Olhar marcante, sedutor ou "
      "misterioso. Diferente do 'Over-the-shoulder': la a camera fica atras de alguem; aqui e o proprio personagem que olha "
      "pra tras. Combine com lente 85mm, luz de contorno (rim light) e movimento lento."),
    O("POV (visao do personagem)", "first person POV shot, hands entering frame from camera position",
      "O espectador VE pelos olhos do personagem. Otimo para 'unboxing' e tutorial."),
    O("Plano detalhe do objeto (insert)", "insert shot, isolated product detail on surface",
      "Objeto sozinho, sem pessoa. Para corte rapido de produto."),
]

OPTIONS["angle"] = [
    O("Altura dos olhos (neutro)", "eye-level angle", "Neutro e honesto. Nao julga o personagem."),
    O("Contra-plonge / baixo (poder)", "low angle looking up, heroic and dominant",
      "De baixo para cima: deixa o sujeito maior, poderoso, imponente."),
    O("Plonge / alto (fragilidade)", "high angle looking down", "De cima para baixo: diminui, cria fragilidade ou visao de controle."),
    O("Holandes / inclinado (tensao)", "dutch angle, tilted horizon", "Horizonte torto = desconforto, loucura, acao."),
    O("Visao de passaro (top-down)", "bird's eye view, direct top-down", "Direto de cima. Flat lay, mesa, comida, mapa de cena."),
    O("Nivel do chao (worm's eye)", "worm's eye view from ground level", "Camera no chao. Pernas, tenis, carro, escala gigante."),
    O("Perfil 90 graus", "perfect profile side angle", "Silhueta do rosto. Grafico e elegante."),
    O("Tres quartos (3/4)", "three-quarter angle", "Angulo classico de retrato: mostra volume do rosto."),
    O("Espelho / reflexo", "reflection in mirror framing", "Conta duas coisas ao mesmo tempo: o sujeito e o que ele ve."),
    O("Atraves de objeto (foreground frame)", "shot through foreground object, natural frame, partial occlusion",
      "Filmar atraves de folhas, vidro, cortina: cria profundidade real."),
]

OPTIONS["camera_move"] = [
    O("Estatico (tripe)", "static locked-off tripod shot", "Sem movimento. Mais estavel para IA, menos distorcao."),
    O("Push in lento (aproxima)", "slow dolly push in toward the subject", "Aproxima devagar: cresce a tensao e a intimidade."),
    O("Pull out (afasta e revela)", "slow dolly pull out revealing the environment", "Afasta e revela o contexto. Bom para final de cena."),
    O("Orbita 180 graus", "smooth 180 degree orbit around the subject", "Gira em volta do sujeito. Impacto alto, risco de deformar rosto."),
    O("Pan horizontal", "horizontal pan from left to right", "Varre a cena na horizontal."),
    O("Tilt vertical", "vertical tilt from feet to face", "Sobe do pe ao rosto. Classico de reveal de look."),
    O("Handheld documental", "organic handheld camera with natural micro-shake", "Tremor natural: parece real, parece agora."),
    O("Gimbal caminhando atras", "gimbal follow shot walking behind the subject", "Segue o sujeito. Energia de 'venha comigo'."),
    O("Crane subindo", "crane shot rising upward", "Sobe e abre a cena. Final epico."),
    O("Whip pan (transicao)", "fast whip pan transition with motion blur", "Virada violenta: usada para CORTAR entre cenas."),
    O("Rack focus (troca de foco)", "rack focus from foreground to subject", "Muda o foco de um elemento para outro no mesmo plano."),
    O("Slider lateral (parallax)", "lateral slider move creating parallax", "Desliza de lado: cria profundidade com camadas."),
    O("Zoom in digital agressivo", "aggressive digital punch-in zoom", "Zoom seco para enfase (meme / viral / reacao)."),
    O("Camera presa no corpo (snorricam)", "snorricam body-mounted shot, subject fixed, world moving",
      "Sujeito travado no quadro e mundo girando. Ansiedade, caos."),
]

OPTIONS["light_style"] = [
    O("Golden hour lateral", "golden hour side lighting, warm low sun, long shadows",
      "Sol baixo e dourado do fim de tarde. Favorece pele e cria sombra longa."),
    O("Luz de janela suave (north light)", "soft diffused window light, large source, gentle falloff",
      "Luz grande e macia de janela. Natural, limpa, favoravel ao rosto."),
    O("Rembrandt (triangulo na bochecha)", "Rembrandt lighting, triangle of light on the cheek, dramatic falloff",
      "Luz a 45 graus formando triangulo de luz na bochecha. Retrato classico e dramatico."),
    O("Ring light / softbox de estudio", "studio ring light and softbox, flat frontal illumination, catchlight in eyes",
      "Frontal e sem sombra, com anel de luz no olho. Padrao de beauty, vlog e review."),
    O("Contraluz dura (rim light)", "hard backlight rim light separating subject from background",
      "Luz atras recorta o contorno do corpo. Separa do fundo e cria silhueta brilhante."),
    O("Neon cyberpunk (magenta/ciano)", "cyberpunk neon lighting, magenta and cyan practicals, wet reflections",
      "Neon colorido e reflexo molhado. Noite urbana, tech, musica."),
    O("Chiaroscuro / noir", "chiaroscuro low-key lighting, single hard source, deep black shadows",
      "Quase tudo preto e um feixe de luz. Suspense, misterio, luxo escuro."),
    O("Luz pratica dentro da cena", "motivated practical lighting from lamps inside the scene",
      "A luz vem de lampadas visiveis no quadro. Realismo total."),
    O("Luz de TV / monitor no rosto", "flickering screen light on the face, cold blue glow",
      "Brilho azul tremulo de tela. Gamer, madrugada, hacker."),
    O("Overcast difuso (nublado)", "overcast soft daylight, shadowless even illumination",
      "Dia nublado: zero sombra dura. Comercial clean e produto."),
    O("Luz dura de meio-dia", "harsh midday sun, hard shadows, high contrast",
      "Sol a pino: sombra preta e dura. Moda editorial crua, deserto."),
    O("Projecao de padrao (gobo)", "gobo pattern light projection, venetian blind shadows",
      "Sombra de persiana ou folhagem projetada no sujeito. Grafico e narrativo."),
]

OPTIONS["grading"] = [
    O("Teal & Orange (acao/cinema)", "teal and orange color grade, cinematic blockbuster contrast",
      "Pele laranja e sombra azulada. Padrao de trailer de acao."),
    O("Pastel suave baixo contraste", "pastel muted low-contrast grade, lifted blacks, soft palette",
      "Cor lavada e delicada. Skincare, bebe, clean, wellness."),
    O("Moody escuro cinematografico", "moody dark cinematic grade, crushed blacks, desaturated midtones",
      "Escuro, dessaturado, serio. Drama e luxo masculino."),
    O("Neon cyberpunk saturado", "saturated cyberpunk grade, magenta highlights, cyan shadows",
      "Cor eletrica e contraste alto. Noite e tecnologia."),
    O("Kodak quente nostalgico", "warm Kodak film emulation grade, creamy highlights, golden skin",
      "Quente e nostalgico, como filme fotografico revelado."),
    O("Bleach bypass (cru e metalico)", "bleach bypass grade, silver desaturated high contrast",
      "Dessaturado e metalico, quase prateado. Guerra, documental cru."),
    O("Preto e branco alto contraste", "high contrast black and white, deep blacks, bright specular highlights",
      "Monocromatico forte. Editorial, atemporal, grafico."),
    O("Comercial clean neutro", "neutral commercial grade, accurate white balance, clean whites",
      "Cor correta e fundo branco limpo. E-commerce e corporativo."),
]

OPTIONS["atmosphere"] = [
    O("Nevoa volumetrica (haze)", "volumetric haze with visible light beams", "Nevoa fina que deixa os raios de luz visiveis. Profundidade instantanea."),
    O("Poeira suspensa na luz", "suspended dust particles floating in light rays", "Particulas de poeira brilhando. Galpao, oficina, sol pela janela."),
    O("Chuva fina", "fine rain falling, wet surfaces, droplets on skin", "Chuva leve e superficie molhada. Drama e reflexo de luz."),
    O("Fumaca densa colorida", "thick colored smoke drifting through frame", "Fumaca de cor. Clipe, moda, show."),
    O("Faisca / brasa no ar", "floating embers and sparks in the air", "Brasas subindo. Forja, fogueira, acao."),
    O("Neve caindo", "gentle falling snow, cold breath vapor", "Neve e vapor da respiracao. Frio real."),
    O("Folhas / petalas ao vento", "petals and leaves swirling in the wind", "Petalas girando. Romance e beleza."),
    O("Bokeh de luzes ao fundo", "out of focus bokeh city lights in the background", "Pontos de luz desfocados atras. Noite urbana elegante."),
    O("Vapor de agua / banheiro", "steam and water vapor rolling through frame", "Vapor quente. Banho, cozinha, academia."),
    O("Ar limpo (sem particula)", "clean clear air, no atmospheric particles", "Nada no ar. Produto, estudio, maxima nitidez."),
]

OPTIONS["time_of_day"] = [
    O("Amanhecer (blue hour)", "pre-dawn blue hour, cold ambient light", "Luz azul fria antes do sol. Calmo e solitario."),
    O("Manha", "soft morning light", "Luz clara e otimista."),
    O("Meio-dia", "harsh midday", "Sombra dura e curta, maximo contraste."),
    O("Tarde", "warm afternoon light", "Luz quente e inclinada."),
    O("Golden hour", "golden hour just before sunset", "A melhor luz do dia: dourada e lateral."),
    O("Crepusculo (dusk)", "dusk twilight, deep blue sky with warm practicals", "Ceu azul profundo + luzes acesas. Equilibrio magico."),
    O("Noite", "night, artificial light only", "So luz artificial."),
    O("Madrugada", "late night, empty and quiet", "Vazio, silencio, solidao."),
]

OPTIONS["location"] = [
    O("Estudio fundo infinito", "seamless studio backdrop, infinite background", "Fundo liso de estudio. Foco total no sujeito/produto."),
    O("Apartamento minimalista", "minimalist modern apartment interior, neutral tones", "Interior clean e moderno."),
    O("Cozinha com luz de janela", "bright kitchen with large window light, marble counter", "Comida, rotina, lifestyle."),
    O("Banheiro com espelho", "bathroom with backlit mirror, tiles, steam", "Skincare, rotina, vapor."),
    O("Rua urbana noturna com neon", "wet night city street with neon signage", "Noite urbana molhada e colorida."),
    O("Rooftop na cidade", "city rooftop with skyline behind", "Skyline atras. Ambicao, sucesso."),
    O("Escritorio corporativo de vidro", "modern glass office interior", "Corporativo, autoridade."),
    O("Praia / costa", "coastal beach with ocean behind", "Ferias, liberdade, agua."),
    O("Floresta com raios de sol", "dense forest with god rays through canopy", "Natureza e raios de luz."),
    O("Deserto arido", "arid desert dunes, heat haze", "Isolamento, calor, escala."),
    O("Academia / galpao industrial", "industrial gym warehouse, concrete and steel", "Treino, forca, suor."),
    O("Loja / showroom", "retail showroom with product shelving", "Varejo e produto exposto."),
    O("Carro (interior)", "inside a car, dashboard reflections", "Conversa intima ou viagem."),
    O("Palco com show de luzes", "concert stage with moving lights and haze", "Musica e energia."),
]

OPTIONS["weather"] = [
    O("Ceu limpo", "clear sky", ""),
    O("Nublado", "overcast clouds", ""),
    O("Chuva", "rainy weather, wet ground", ""),
    O("Tempestade com relampago", "thunderstorm with lightning flashes", ""),
    O("Vento forte", "strong wind moving hair and fabric", ""),
    O("Neblina densa", "dense fog reducing visibility", ""),
]

OPTIONS["expression"] = [
    O("Neutro confiante", "calm confident neutral expression, steady gaze", "Base segura: nao sorri, nao tensiona. Autoridade."),
    O("Micro-sorriso sutil", "subtle micro-smile, slight lip corner lift, warm eyes", "Sorriso quase imperceptivel. Mais sofisticado que sorriso aberto."),
    O("Sorriso aberto genuino", "genuine open smile with visible teeth and eye crinkle", "Alegria real (olho fecha um pouco). Cuidado: IA erra dentes."),
    O("Olhar penetrante na lente", "intense piercing gaze directly into the lens", "Olha direto na camera. Conexao imediata com quem assiste."),
    O("Sobrancelha arqueada (duvida)", "one eyebrow raised, skeptical micro-expression", "Duvida/ironia. Otimo para hook de video."),
    O("Surpresa contida", "contained surprise, widened eyes, parted lips", "Reacao de 'nao acredito'. Gancho de retencao."),
    O("Riso espontaneo olhando pro lado", "candid laughter looking off-camera", "Parece flagrante, nao posado."),
    O("Serio melancolico", "melancholic serious expression, downcast eyes", "Drama, saudade, peso."),
    O("Concentracao focada", "focused concentration, eyes narrowed on task", "Trabalho, artesanato, esporte."),
    O("Boca pronta para falar (lip-sync)", "mouth slightly open mid-speech, lip-sync ready", "Use SEMPRE que a cena tiver locucao ou fala em sincronia."),
]

OPTIONS["action"] = [
    O("Parado(a) olhando pra lente", "standing still, looking into the lens", "Pose base. Minimo movimento = maxima estabilidade na IA."),
    O("Andando em direcao a lente", "walking toward the camera in slow confident steps", "Entrada de cena. Forte e simples."),
    O("Virando o rosto em slow motion", "turning the head toward camera in slow motion, hair follows", "Reveal de rosto. Cabelo acompanha o movimento."),
    O("Mostrando produto na palma da mao", "presenting the product on the open palm toward the lens", "Apresentacao de produto. Combine com enquadramento Maos."),
    O("Segurando e girando o produto", "holding the product and slowly rotating it to show detail", "Mostra todos os lados do objeto."),
    O("Apontando para elemento grafico na tela", "pointing at an on-screen graphic element beside them", "Para colocar texto/arte ao lado depois na edicao."),
    O("Apontando para a propria camera (CTA)", "pointing directly at the lens, direct call to action gesture", "Chamada para acao. Use no bloco The Call / Outro."),
    O("Abrindo a embalagem (unboxing)", "unboxing, hands opening the package revealing the product", "Momento de revelacao do produto."),
    O("Aplicando produto no rosto", "applying the product onto the skin with fingertips", "Skincare / maquiagem."),
    O("Bebendo / tomando um sip", "bringing the glass to the lips and taking a sip", "Bebida, refresco, satisfacao."),
    O("Digitando / usando o celular", "scrolling and tapping on the smartphone screen", "App, rede social, notificacao."),
    O("Sentando e cruzando as pernas", "sitting down and crossing the legs with composure", "Entrevista, autoridade, elegancia."),
    O("Ajustando a roupa / blazer", "adjusting the jacket cuffs and collar", "Poder, preparo, antes de entrar em cena."),
    O("Girando (fashion spin)", "spinning around so the outfit fabric flares", "Mostra o look inteiro em movimento."),
    O("Dancando no ritmo", "dancing to the beat with rhythmic body movement", "Energia alta. Use motion strength alto."),
    O("Correndo", "running at full speed, motion blur on limbs", "Acao. Exige motion strength alto e fps alto."),
    O("Rindo e cobrindo a boca", "laughing and covering the mouth with the hand", "Natural e humano."),
    O("Olhando para o horizonte", "gazing toward the horizon, contemplative", "Fim de cena, reflexao."),
    O("Escrevendo / trabalhando", "writing in a notebook, focused on the task", "Produtividade, estudo."),
    O("Cozinhando / cortando", "cooking, slicing ingredients on the board", "Comida, receita, mao na massa."),
    O("Lavando o cabelo no banho (propaganda de shampoo)",
      "washing hair in the shower, fingers massaging rich shampoo lather through wet hair, water streaming down, steam rising",
      "Cena classica de shampoo, condicionador e cuidado capilar. Mostre a espuma, a agua escorrendo e o cabelo brilhando. "
      "Combine com enquadramento busto ou rosto, luz de contorno e vapor (atmosfera). Cuidado: a IA deforma maos no cabelo; "
      "use motion baixo (3-4) e marque 'Maos naturais' em Fisica e detalhes vivos."),
]

OPTIONS["wardrobe"] = [
    O("Alfaiataria preta minimalista", "minimalist black tailored suit, sharp shoulders", "Autoridade, luxo sobrio."),
    O("Blazer bege oversized", "oversized beige blazer over white tee", "Moderno, confortavel, aspiracional."),
    O("Camiseta branca basica", "plain white cotton t-shirt", "Neutro. Deixa o foco no rosto/produto."),
    O("Vestido de seda fluido", "flowing silk slip dress catching the light", "Movimento e elegancia."),
    O("Jeans e jaqueta de couro", "denim jeans with black leather jacket", "Atitude, rua, rock."),
    O("Roupa de academia tecnica", "technical athleisure set, moisture-wicking fabric", "Fitness e performance."),
    O("Jaleco / uniforme profissional", "clean professional lab coat uniform", "Autoridade tecnica, saude."),
    O("Streetwear oversized", "oversized streetwear hoodie and cargo pants", "Jovem, urbano."),
    O("Traje de gala / vestido longo", "formal evening gown with subtle sequins", "Evento, premiacao, luxo."),
    O("Roupa de trabalho suja de oficina", "worn workshop coveralls with grease stains", "Trabalho real, textura, honestidade."),
]

OPTIONS["style_render"] = [
    O("Fotorrealista cinematografico", "photorealistic cinematic film still, natural skin texture with visible pores",
      "Padrao. Pele com poro, luz coerente, cara de frame de filme."),
    O("Editorial de moda (Vogue)", "high fashion editorial photography, Vogue aesthetic, bold styling",
      "Pose grafica, styling forte, fundo limpo."),
    O("Documental cru", "raw documentary photography, available light only, unposed",
      "Sem pose, sem luz montada. Verdade."),
    O("Comercial 4K produto", "glossy commercial product photography, controlled studio reflections",
      "Produto com reflexo controlado e fundo limpo."),
    O("3D render estilo Pixar", "stylized 3D animated render, Pixar-like character design, subsurface scattering",
      "Personagem 3D fofo e estilizado."),
    O("Anime cel-shaded", "anime cel-shaded illustration, clean line art, vibrant flats",
      "Desenho japones com linha limpa."),
    O("Pintura digital conceitual", "digital concept art painting, painterly brush texture",
      "Arte conceitual pintada, nao fotografica."),
    O("Hyperreal 8K detalhado", "hyperrealistic 8K detail, micro texture everywhere",
      "Exagero de detalhe. Pode ficar artificial: use com moderacao."),
    O("Claymation / stop-motion", "stop-motion claymation look, visible fingerprints in clay",
      "Massinha com textura de dedo. Charme artesanal."),
    O("VHS anos 90", "1990s VHS tape look, chromatic aberration, scanlines", "Fita velha, ruido, nostalgia."),
]

OPTIONS["voice_tone"] = [
    O("ASMR sussurrado intimista", "intimate ASMR whisper voiceover, close-mic breathy delivery",
      "Voz baixa e muito perto do microfone. Hipnotico, retem atencao."),
    O("Corporativa firme e confiante", "firm confident corporate voiceover, clear articulation",
      "Autoridade sem agressividade. Institucional."),
    O("Documental grave e pausada", "deep paced documentary narration, gravitas",
      "Voz grave com pausas. Peso e credibilidade."),
    O("Influenciador energico e rapido", "high-energy fast-paced influencer delivery",
      "Rapido, animado, sem pausa. Retencao em video curto."),
    O("Conversa amiga (casual)", "warm casual conversational tone, like talking to a friend",
      "Natural, com imperfeicao. Parece gente, nao anuncio."),
    O("Narrador de trailer epico", "epic movie trailer narrator voice, dramatic build",
      "Exagerado e dramatico. Lancamento."),
    O("Infantil alegre", "bright cheerful childlike narration", "Produto infantil, animacao."),
    O("Robotico / IA sintetica", "synthetic AI robotic voice, slight vocoder artifacts", "Tech, futuro, sci-fi."),
    O("Sem locucao (so ambiente)", "no voiceover, ambient sound design only", "Silencio narrativo: deixa a imagem falar."),
]

OPTIONS["sfx"] = [
    O("Whoosh / swish de transicao", "whoosh swish transition sound", "Marca o corte entre cenas."),
    O("Riser crescente", "tension riser building up", "Cria expectativa antes do reveal."),
    O("Sub-drop de impacto", "deep sub bass drop impact", "Pancada grave no corte. Impacto fisico."),
    O("Foley: clique mecanico", "mechanical click foley, tactile button press", "Tampinha, botao, trava. Realismo tatil."),
    O("Foley: toque na tela", "finger tap on glass screen foley", "Uso de celular."),
    O("Foley: tecido / roupa", "fabric movement foley, cloth rustle", "Movimento de roupa. Da presenca."),
    O("Foley: passos", "footsteps foley matched to the floor surface", "Passo no piso certo."),
    O("Agua / liquido servindo", "pouring liquid and ice clinking", "Bebida. Muito satisfatorio."),
    O("Ambiente urbano", "city ambience, distant traffic", "Cama de som de rua."),
    O("Ambiente natureza", "nature ambience, birds and wind in leaves", "Cama de som de floresta/parque."),
    O("Silencio seco (sem SFX)", "clean silence, no sound effects", "Nada. Para foco total na voz."),
]

OPTIONS["music"] = [
    O("Sem musica", "no music", ""),
    O("Lo-fi minimalista", "minimal lo-fi beat, soft vinyl texture", "Calmo, moderno, nao atrapalha a voz."),
    O("Cinematico orquestral", "cinematic orchestral score with building strings", "Emocao e escala."),
    O("Eletronica tensa (techno)", "dark tense techno pulse", "Urgencia, tech, noite."),
    O("Pop energetico", "upbeat commercial pop track", "Alegre e vendedor."),
    O("Piano emocional", "sparse emotional piano", "Vulnerabilidade, historia pessoal."),
    O("Trap / hip-hop 808", "hard trap beat with 808 bass", "Atitude, moda, jovem."),
    O("Ambient drone", "ambient atmospheric drone pad", "Textura sem melodia. Suspense."),
]

OPTIONS["aspect"] = [
    O("9:16 vertical (Reels/TikTok/Shorts)", "9:16", "Video vertical de rede social."),
    O("16:9 horizontal (YouTube/TV)", "16:9", "Padrao de tela larga."),
    O("1:1 quadrado (feed)", "1:1", "Feed de Instagram/catalogo."),
    O("4:5 retrato (feed alto)", "4:5", "Ocupa mais tela no feed que 1:1."),
    O("2.39:1 cinemascope", "2.39:1", "Faixa larga de cinema. Use com anamorfica."),
    O("4:3 retro", "4:3", "TV antiga, VHS, nostalgia."),
]

OPTIONS["fps"] = [
    O("24 fps (cinema)", "24fps cinematic motion blur", "Movimento com rastro natural de cinema."),
    O("30 fps (social media)", "30fps", "Padrao de rede social, mais 'video'."),
    O("60 fps (fluido / slow-mo)", "60fps smooth motion, slow-motion ready", "Permite camera lenta sem travar."),
    O("120 fps (super slow motion)", "120fps high speed capture for extreme slow motion", "Slow motion extremo: gota, cabelo, impacto."),
]

NEGATIVE_BASE = (
    "bad anatomy, extra limbs, extra fingers, fused fingers, deformed hands, "
    "mutated face, asymmetric eyes, crossed eyes, blurry, out of focus, low resolution, "
    "jpeg artifacts, text, watermark, logo, signature, subtitles, caption, "
    "plastic skin, waxy skin, oversaturated, overexposed, flat lighting, "
    "flicker, morphing, warping, jitter, duplicated subject, cloned face, "
    "distorted background, floating objects, broken perspective, "
    "cgi look, uncanny valley, stiff motion, ugly, amateur"
)

NEGATIVE_PRESETS = {
    "Padrao (completo)": NEGATIVE_BASE,
    "Retrato / beauty": NEGATIVE_BASE + ", heavy makeup, airbrushed skin, missing pores, dead eyes",
    "Produto": NEGATIVE_BASE + ", wrong label, misspelled packaging, dented product, dust on product",
    "Video / movimento": NEGATIVE_BASE + ", frame drop, ghosting trails, sliding feet, teleporting limbs, background morph",
    "Leve (menos restritivo)": "blurry, low resolution, text, watermark, bad anatomy, deformed hands",
}

# ----------------------------------------------------------------------------
# GATILHOS DE PALAVRA-CHAVE
#   palavra no roteiro -> sugestao de (enquadramento, lente, acao, extra)
#   Os valores sao os LABELS do catalogo (OPTIONS) para preencher o combo.
# ----------------------------------------------------------------------------
KT = namedtuple("KT", "shot lens action extra")
# Os gatilhos e o glossario ficam em dados/*.json (carregados mais abaixo).


# ----------------------------------------------------------------------------
# GLOSSARIO PT -> EN (tradutor offline do roteiro)
# Nao e um tradutor completo: e um glossario tecnico/cinematografico.
# Palavras desconhecidas sao mantidas e listadas no aviso de traducao.
# ----------------------------------------------------------------------------


# Regras aplicadas ANTES do glossario (regex)
PRE_RULES = [
    (r"\bde (\d+)\s*anos\b", r"\1 years old"),
    (r"\bcom (\d+)\s*anos\b", r"\1 years old"),
    (r"\b(\d+)\s*anos\b", r"\1 years old"),
    (r"\bmeia[- ]idade\b", "middle-aged"),
    (r"\bprimeiro\s+plano\b", "foreground"),
    (r"\bsegundo\s+plano\b", "background"),
]

# Para reordenar "substantivo + adjetivo" (PT) -> "adjetivo + substantivo" (EN)
ADJECTIVES_EN = {
    "black", "white", "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "gray", "brown", "beige", "golden", "silver", "nude", "wavy", "straight",
    "curly", "coily", "short", "long", "blonde", "slim", "strong", "tall",
    "young", "old", "light", "intense", "soft", "rough", "glossy", "matte",
    "transparent", "blurred", "sharp", "detailed", "realistic", "minimalist",
    "industrial", "rustic", "cozy", "spacious", "narrow", "deep", "shallow",
    "audible", "close", "distant", "side", "frontal", "rear", "round", "square",
    "thin", "thick", "heavy", "dirty", "clean", "wet", "dry", "warm", "cold",
    "dark", "colorful", "elegant", "simple", "expensive", "vintage", "modern",
    "natural", "artificial", "volumetric", "cinematic", "fair", "bright",
    "beautiful", "luxurious", "large", "small", "new", "empty", "full",
    "shiny", "fast", "slow", "cheerful", "calm",
    "shoulder-length", "waist-length", "middle-aged", "shirtless", "blurry",
}
NOUNS_EN = {
    "hair", "skin", "face", "eye", "eyes", "mouth", "lips", "hand", "hands",
    "leg", "legs", "foot", "feet", "arm", "arms", "shoulder", "shoulders",
    "beard", "mustache", "freckles", "wrinkles", "tattoo", "scar", "eyebrow",
    "eyelashes", "cheek", "chin", "forehead", "nose", "ear", "neck", "waist",
    "hips", "knee", "ankle", "wrist", "nail", "bun", "bangs", "braid",
    "ponytail", "makeup", "plant", "vase", "curtain", "linen", "wood", "metal",
    "glass", "concrete", "brick", "marble", "leather", "silk", "cotton", "wool",
    "fabric", "lace", "plastic", "cardboard", "rug", "shelf", "counter", "sink",
    "stove", "fridge", "picture", "countertop", "armchair", "cushion", "light",
    "shadow", "reflection", "glow", "bokeh", "background", "foreground", "wall",
    "floor", "ceiling", "door", "window", "table", "chair", "bed", "couch",
    "stairs", "dress", "shirt", "blouse", "trousers", "jeans", "skirt",
    "jacket", "blazer", "suit", "coat", "belt", "necklace", "earring", "ring",
    "jewelry", "shoe", "shoes", "sneakers", "handbag", "backpack", "wallet",
    "smartphone", "phone", "laptop", "computer", "keyboard", "screen",
    "wristwatch", "glasses", "sunglasses", "perfume", "lipstick", "cream",
    "moisturizer", "soap", "brush", "towel", "mirror", "water", "fire",
    "smoke", "steam", "rain", "snow", "wind", "sun", "moon", "sky", "cloud",
    "clouds", "ocean", "beach", "mountain", "forest", "tree", "flower", "leaf",
    "petal", "city", "street", "sidewalk", "building", "house", "apartment",
    "bedroom", "kitchen", "bathroom", "office", "store", "market", "gym",
    "car", "motorcycle", "bicycle", "food", "dish", "drink", "coffee", "cake",
    "bread", "fruit", "product", "box", "packaging", "label", "logo", "brand",
    "money", "card", "key", "book", "paper", "pen", "tool", "woman", "man",
    "girl", "boy", "person", "model", "child", "baby", "couple", "group",
    "crowd", "dog", "cat", "horse", "bird", "camera", "lens", "shot", "scene",
    "microphone", "breath", "gaze", "smile", "breathing", "condensation",
    "drop", "drops", "sweat", "pore", "pores", "tear", "foam", "spark",
    "mist", "fog", "dew", "crease", "steam", "glow",
}
NOUNS_EN |= {"rim", "key", "fill", "hour", "tone", "detail", "texture"}
# palavras que servem como substantivo E adjetivo (ex: light): a posicao decide
AMBIGUOUS_EN = ADJECTIVES_EN & NOUNS_EN

OPTIONS["subject_type"] = [
    O("Pessoa", "person", "O prompt gira em volta de um ser humano."),
    O("Produto / objeto", "product", "Nao ha pessoa principal: o heroi e o objeto."),
    O("Pessoa + produto", "person interacting with the product", "O mais vendedor: gente usando a coisa."),
    O("Animal", "animal", "Pet ou animal selvagem como sujeito."),
    O("Paisagem / ambiente", "landscape environment", "Lugar como protagonista, sem sujeito."),
    O("Grupo de pessoas", "group of people", "Varias pessoas. Cuidado: IA deforma rostos em grupo."),
    O("Personagem 3D / mascote", "3D character mascot", "Personagem estilizado, nao humano real."),
]

OPTIONS["negative_preset"] = [O(k, k, "Preenche o campo Negative Prompt com um conjunto pronto.")
                             for k in NEGATIVE_PRESETS]

# ----------------------------------------------------------------------------
# ESPECIFICACAO DOS CAMPOS (a UI e gerada a partir daqui)
# Field(id, label, kind, src, info, default)
#   kind: entry | text | combo | checks | scale | spin | check
# ----------------------------------------------------------------------------
Field = namedtuple("Field", "id label kind src info default")


def F(fid, label, kind, src=None, info="", default=""):
    return Field(fid, label, kind, src, info, default)


SECTIONS = [
    # ---------------------------------------------------------------- SUJEITO
    ("Personagem", "Identidade do sujeito", [
        F("subject_type", "Tipo de sujeito", "combo", "subject_type",
          "Define o que o prompt descreve primeiro. 'Pessoa + produto' e o formato mais usado em anuncio.",
          "Pessoa + produto"),
        F("char_id", "ID / nome do personagem", "entry", None,
          "Um apelido fixo (ex: ANA_01). O compilador repete esse ID em todas as cenas para a IA entender que e a MESMA pessoa. "
          "Troque so este campo para trocar o personagem de todo o roteiro.", "ANA_01"),
        F("char_desc", "Descricao fisica", "text", None,
          "Escreva em 1 ou 2 linhas: idade aparente, tipo de cabelo, tom de pele, formato de rosto, altura, marcas (sarda, tatuagem). "
          "Seja concreto: 'mulher 28 anos, cabelo preto ondulado na altura do ombro, pele morena, sardas leves no nariz'. "
          "Quanto mais especifico, mais consistente entre cenas.",
          "mulher de 28 anos, cabelo preto ondulado na altura do ombro, pele morena clara, sardas leves no nariz"),
        F("wardrobe", "Vestuario", "combo", "wardrobe",
          "A roupa muda a classe social e a intencao da cena inteira. Pode digitar livre tambem.",
          "Blazer bege oversized"),
        F("hair", "Cabelo / maquiagem", "entry", None,
          "Detalhe de penteado e make. Ex: 'coque baixo, make natural glow, labios nude'.",
          "ondas soltas, make natural glow"),
        F("expression", "Expressao facial (gatilho)", "combo", "expression",
          "A micro-expressao e o que separa foto viva de boneco. Se a cena tem fala, use 'Boca pronta para falar'.",
          "Micro-sorriso sutil"),
        F("action", "Acao / pose padrao", "combo", "action",
          "Acao padrao do personagem. Cada cena do roteiro pode sobrescrever esta acao.",
          "Mostrando produto na palma da mao"),
        F("props", "Objetos em cena (props)", "entry", None,
          "Objetos que aparecem junto: 'copo de agua, caderno, oculos'. Use as mesmas palavras do roteiro para a IA manter continuidade.",
          "celular, copo de agua"),
    ]),
    # ---------------------------------------------------------------- AMBIENTE
    ("Ambiente", "Cenario e atmosfera", [
        F("location", "Local", "combo", "location",
          "Onde a cena acontece. Pode digitar livre: 'oficina de moto antiga com ferramentas na parede'.",
          "Apartamento minimalista"),
        F("location_detail", "Detalhe do cenario", "entry", None,
          "2 ou 3 elementos concretos que aparecem no fundo. Ex: 'planta grande, cortina de linho, piso de madeira'. "
          "Isso impede o fundo generico e vazio.",
          "planta grande, cortina de linho, piso de madeira clara"),
        F("time_of_day", "Horario", "combo", "time_of_day",
          "Define a cor e a direcao da luz natural. 'Golden hour' e o mais favoravel para pele.",
          "Golden hour"),
        F("weather", "Clima", "combo", "weather", "Tempo/condicao do ar. Afeta reflexo e umidade da cena.", "Ceu limpo"),
        F("atmosphere", "Atmosfera de particulas", "checks", "atmosphere",
          "Particulas no ar deixam a luz VISIVEL e criam profundidade. Marque 1 ou 2 no maximo: mais que isso polui a cena.",
          "Nevoa volumetrica (haze)"),
        F("bg_detail", "Fundo / profundidade", "entry", None,
          "Como o fundo se comporta: 'fundo desfocado com luzes da cidade', 'parede lisa sem distracao', 'camadas de profundidade'.",
          "fundo desfocado com bokeh suave"),
    ]),
    # ---------------------------------------------------------------- CAMERA
    ("Camera", "Corpo, optica e movimento", [
        F("camera_body", "Tipo de camera", "combo", "camera_body",
          "A camera define a 'textura' da imagem: cinema suave, nitidez crua ou celular na mao (UGC). "
          "E o campo que mais muda a credibilidade do video.", "ARRI Alexa Mini LF (cinema suave)"),
        F("lens", "Lente / distancia focal", "combo", "lens",
          "A lente define a relacao entre o sujeito e o fundo. Regra rapida: 85mm para rosto, 35mm para narrativa, "
          "100mm macro para produto, 24mm para mostrar o lugar.", "85mm retrato (fundo cremoso)"),
        F("aperture", "Abertura / profundidade de campo", "combo", "aperture",
          "Controla o quanto o fundo desfoca. f/1.4 isola muito mas pode confundir a IA em cena com movimento; "
          "f/2.8 e o ponto de equilibrio.", "f/2.8 (sujeito isolado, seguro)"),
        F("shot", "Enquadramento padrao", "combo", "shot",
          "O corte do corpo no quadro: rosto e olhos, busto, meio corpo, corpo inteiro, pernas, barriga... "
          "Este e o valor PADRAO; no roteiro cada palavra-chave pode escolher o seu proprio.",
          "Meio corpo (medium shot)"),
        F("angle", "Angulo de camera", "combo", "angle",
          "De onde a camera olha. Angulo baixo da poder, angulo alto da fragilidade, altura do olho e neutro.",
          "Altura dos olhos (neutro)"),
        F("camera_move", "Movimento de camera", "combo", "camera_move",
          "Como a camera se move. Movimento simples = video mais estavel na IA. Orbita e zoom agressivo deformam rosto.",
          "Push in lento (aproxima)"),
        F("aspect", "Proporcao / formato", "combo", "aspect",
          "Formato final do video. 9:16 para Reels/TikTok, 16:9 para YouTube, 2.39:1 para cara de cinema.",
          "9:16 vertical (Reels/TikTok/Shorts)"),
        F("fps", "Taxa de quadros (FPS)", "combo", "fps",
          "24fps = cinema. 30fps = rede social. 60/120fps = slow motion sem travar.", "24 fps (cinema)"),
    ]),
    # ---------------------------------------------------------------- LUZ
    ("Luz & Cor", "Iluminacao, paleta e estilo", [
        F("light_style", "Estilo de luz", "combo", "light_style",
          "O desenho da luz. Trocar SO este campo muda o clima de todo o roteiro: "
          "ring light = review; Rembrandt = drama; neon = noite.", "Luz de janela suave (north light)"),
        F("light_extra", "Detalhe de luz extra", "entry", None,
          "Reforcos: 'rim light azul atras', 'rebatedor branco embaixo do rosto', 'luz pratica de abajur no fundo'.",
          "rim light suave separando do fundo"),
        F("grading", "Color grading / paleta", "combo", "grading",
          "A cor final. Teal&Orange = acao; pastel = clean; moody = luxo escuro; neutro = e-commerce.",
          "Kodak quente nostalgico"),
        F("style_render", "Estilo de renderizacao", "combo", "style_render",
          "Define se o resultado e foto real, editorial, 3D, anime ou VHS. E o campo que mais impacta o 'look' bruto.",
          "Fotorrealista cinematografico"),
    ]),
    # ---------------------------------------------------------------- AUDIO
    ("Audio & Voz", "Locucao, SFX e musica", [
        F("voice_tone", "Estilo de locucao", "combo", "voice_tone",
          "O tom da voz. ASMR retem atencao, corporativo da autoridade, influenciador acelera o ritmo. "
          "Funciona em Sora, Veo e Kling (modelos com audio).", "Conversa amiga (casual)"),
        F("vo_text", "Texto da locucao (portugues)", "text", None,
          "Escreva a fala em portugues. Se o tradutor estiver ligado, sai em ingles no prompt final e o original fica salvo no JSON. "
          "Cada cena do roteiro tambem tem a sua propria fala.", ""),
        F("sfx", "Efeitos sonoros (SFX)", "checks", "sfx",
          "Som e metade da sensacao de real. Foley (clique, tecido, passo) faz o video parecer gravado, nao gerado. "
          "Marque de 2 a 4.", "Foley: tecido / roupa"),
        F("music", "Trilha / musica", "combo", "music",
          "A trilha define o ritmo do corte. 'Sem musica' tambem e uma escolha forte quando a voz e o centro.",
          "Lo-fi minimalista"),
        F("audio_extra", "Detalhe de audio extra", "entry", None,
          "Ex: 'respiracao audivel', 'eco de sala grande', 'microfone proximo com graves'.",
          "respiracao audivel, microfone proximo"),
    ]),
    # ---------------------------------------------------------------- MOTOR
    ("Motor de IA", "Parametros tecnicos de geracao", [
        F("negative_preset", "Preset de Negative Prompt", "combo", "negative_preset",
          "Escolha um conjunto pronto de defeitos a evitar. Ao escolher, o campo abaixo e preenchido.",
          "Padrao (completo)"),
        F("negative", "Negative Prompt", "text", None,
          "Lista do que a IA NAO deve gerar: anatomia errada, mao com 6 dedos, texto/marca d'agua, pele plastica, "
          "flicker e morphing em video. Separe por virgula. Em Midjourney isso vira '--no'.", NEGATIVE_BASE),
        F("motion", "Motion Strength / Scale (1-10)", "scale", (1, 10),
          "Intensidade do movimento fisico da cena. 1-3: quase parado, maxima estabilidade. 4-6: movimento natural. "
          "7-10: acao rapida, com risco real de deformar maos e rosto.", 4),
        F("consistency", "Consistency Lock - rosto e roupa (0-100)", "scale", (0, 100),
          "Peso para manter o MESMO rosto e a MESMA roupa entre cenas diferentes. "
          "Acima de 80 a IA quase nao varia (bom para serie de videos); abaixo de 40 ela improvisa.", 85),
        F("seed", "Seed (semente deterministica)", "entry", None,
          "Numero que trava o resultado. Mesma seed + mesmo prompt = mesma imagem. "
          "Guarde a seed que funcionou para continuar o personagem nas proximas cenas. Vazio = aleatorio.", ""),
        F("seed_lock", "Travar seed em todas as cenas", "check", None,
          "Ligado: todas as cenas usam a MESMA seed (personagem consistente). "
          "Desligado: cada cena recebe seed+1, dando variacao controlada.", True),
        F("duration", "Duracao por cena (segundos)", "spin", (1, 60),
          "Duracao de cada cena gerada. Kling e Luma trabalham bem com 5 ou 10 segundos. "
          "Video longo = junte varias cenas de 5s na edicao.", 5),
        F("extra_params", "Parametros extras / flags", "entry", None,
          "Flags cruas que serao anexadas no final (ex: '--style raw --s 250 --chaos 10'). "
          "Deixe vazio se nao souber: o compilador ja escreve as flags basicas.", ""),
        F("translate", "Compilar em ingles tecnico (tradutor)", "check", None,
          "Ligado: voce escreve tudo em portugues e o prompt final sai em ingles tecnico, que e o que os modelos entendem melhor. "
          "O tradutor usa um glossario cinematografico interno; palavras que ele nao conhece ficam marcadas no aviso.", True),
    ]),
]


# ---------------------------------------------------------------------------
# CAMPOS ADICIONAIS (agencia): referencias, continuidade, texto na tela,
# movimento detalhado, marca e briefing. Todos nascem VAZIOS e marcados
# como pendentes (⚑) - voce preenche quando precisar.
# ---------------------------------------------------------------------------
OPTIONS["ref_mode"] = [
    O("Referencia de personagem (rosto/roupa)", "character reference, keep the same face and outfit as the reference image",
      "A IA copia rosto e roupa da imagem. Use a foto do personagem ja aprovado para manter a mesma pessoa em todos os videos."),
    O("Referencia de estilo / look", "style reference, match the color, lighting and texture of the reference image",
      "A IA copia o 'clima' da imagem (cor, luz, textura), nao o conteudo."),
    O("Referencia de cenario", "environment reference, match the location and set design of the reference image",
      "Mantem o mesmo lugar entre cenas e videos."),
    O("Referencia de produto", "product reference, reproduce the product exactly as in the reference image",
      "Para o produto aparecer fiel (forma, cor, rotulo). Use foto do produto em fundo limpo."),
    O("Primeiro frame (image-to-video)", "start frame image, animate from the first frame",
      "A imagem vira o primeiro quadro do video e a IA anima a partir dela. Kling, Runway, Luma e Veo aceitam."),
    O("Primeiro + ultimo frame", "start frame and end frame, interpolate motion between both",
      "Voce define onde o video comeca e termina; a IA cria o caminho. Otimo para transicoes e transformacoes controladas."),
]
OPTIONS["onscreen_pos"] = [
    O("Topo da tela", "text overlay at the top of the frame", "Titulo ou gancho escrito no alto. Cuidado com a area de interface das redes (topo e rodape)."),
    O("Centro da tela", "centered text overlay", "Texto de impacto, curto. Use poucas palavras."),
    O("Terco inferior (lower third)", "lower-third text overlay", "Nome, cargo, preco ou legenda de produto, como em TV."),
    O("Legenda estilo TikTok (palavra por palavra)", "bold word-by-word captions, centered lower, TikTok style",
      "Legenda grande que acompanha a fala, destacando a palavra falada. Padrao de retencao em video vertical."),
    O("Canto (marca d'agua / logo)", "small corner logo watermark", "Logo discreto no canto."),
]
OPTIONS["motion_speed"] = [
    O("Muito lento (slow motion)", "ultra slow motion, 120fps look", "Cada detalhe aparece: gota, tecido, cabelo. Valoriza produto e momento de emocao."),
    O("Lento e suave", "slow, smooth, deliberate motion", "Movimento calmo e elegante. Mais estavel na IA."),
    O("Natural (tempo real)", "natural real-time motion", "Velocidade normal de uma pessoa."),
    O("Rapido e energico", "fast, energetic motion", "Acao e ritmo. Maior risco de deformar maos e rosto."),
    O("Speed ramp (rapido para lento)", "speed ramp from fast to slow motion", "Comeca rapido e freia no momento importante. Efeito classico de comercial."),
    O("Timelapse", "timelapse motion", "Tempo acelerado: nuvens, luz mudando, multidao."),
]
OPTIONS["easing"] = [
    O("Ease-in-out (suave)", "ease-in-out motion curve, smooth start and stop", "Comeca e termina devagar. Parece movimento de equipamento profissional."),
    O("Ease-in (acelera)", "ease-in motion, gradually accelerating", "Comeca devagar e ganha velocidade. Tensao crescente."),
    O("Ease-out (desacelera)", "ease-out motion, decelerating to a stop", "Chega rapido e assenta. Bom para revelar o produto."),
    O("Linear (constante)", "constant linear speed motion", "Velocidade igual do inicio ao fim. Sensacao mecanica."),
    O("Snap / impacto", "sudden snap with hard stop", "Movimento seco e parada brusca. Ritmo de batida."),
]
OPTIONS["focus_pull"] = [
    O("Rack focus: fundo para sujeito", "rack focus from background to subject", "O foco 'chega' no personagem. Revela quem importa."),
    O("Rack focus: sujeito para fundo", "rack focus from subject to background", "O foco passa para o que esta atras. Mostra contexto."),
    O("Pull focus no produto", "pull focus onto the product", "O foco cai no produto no momento da revelacao."),
    O("Foco fixo (sem variacao)", "locked focus, no focus change", "Mais estavel na IA. Padrao seguro."),
    O("Dolly zoom (efeito vertigem)", "dolly zoom, vertigo effect", "Fundo se distorce enquanto o sujeito fica do mesmo tamanho. Tensao e surpresa. Use pouco."),
    O("Focus breathing (foco respirando)", "subtle focus breathing", "Leve variacao natural de foco, como lente real."),
]
OPTIONS["physics"] = [
    O("Cabelo ao vento", "hair moving naturally in the breeze", "Cabelo com movimento leve. Da vida ao retrato."),
    O("Tecido fluindo", "fabric flowing and rippling naturally", "Roupa com caimento e movimento realista."),
    O("Liquido / gotas", "realistic liquid physics, droplets and splashes", "Agua, cafe, creme com comportamento fisico crivel."),
    O("Particulas / poeira", "floating dust particles drifting in the light", "Particulas no ar que mostram a luz."),
    O("Fumaca / vapor", "wisps of steam and smoke rising", "Vapor de bebida, fumaca suave."),
    O("Reflexos mudando", "reflections shifting with the movement", "Reflexos em vidro e metal acompanhando o movimento."),
    O("Sombras se movendo", "shadows moving across the scene", "Sombras vivas, passagem de nuvem, folhas."),
    O("Maos naturais (sem deformar)", "natural hands with correct anatomy, five fingers", "Reforco anti-defeito para cenas com maos."),
]
OPTIONS["transition"] = [
    O("Corte seco (hard cut)", "hard cut", "Troca direta. A mais comum e a mais limpa."),
    O("Match cut", "match cut on shape and motion", "A proxima cena comeca com forma ou movimento parecido com o final desta. Elegante e memoravel."),
    O("Whip pan", "whip pan transition", "Giro rapido de camera que borra e leva para a proxima cena. Energia."),
    O("Dissolve / crossfade", "dissolve crossfade", "Uma cena derrete na outra. Suave, passagem de tempo."),
    O("Fade to black", "fade to black", "Escurece e encerra. Final de bloco ou de video."),
    O("Atravessar objeto (push-through)", "push-through transition passing through an object", "A camera passa por um objeto e sai na proxima cena."),
    O("Smash cut (contraste)", "smash cut for contrast", "Corte brusco entre calma e caos (ou o contrario). Surpresa."),
    O("J-cut (audio antes)", "J-cut, audio leads the next scene", "O som da proxima cena comeca antes da imagem. Fluidez de narrativa."),
    O("L-cut (audio depois)", "L-cut, audio continues over the next scene", "O som da cena anterior continua sobre a nova imagem."),
]

_N_BASE_SECTIONS = len(SECTIONS)
SECTIONS += [
    ("Camera", "Movimento detalhado (opcional)", [
        F("motion_speed", "Velocidade do movimento", "combo", "motion_speed",
          "A velocidade geral do movimento da cena (slow motion, natural, rapido, speed ramp).", ""),
        F("easing", "Curva de aceleracao (easing)", "combo", "easing",
          "Como o movimento comeca e termina. Ease-in-out parece equipamento profissional; snap da ritmo.", ""),
        F("focus_pull", "Foco (rack focus / pull)", "combo", "focus_pull",
          "Mudanca de foco durante a cena. 'Foco fixo' e o mais estavel; rack focus e visual de cinema.", ""),
        F("subject_motion", "Direcao do movimento do sujeito", "entry", None,
          "Para onde o personagem se move: 'da esquerda para a direita', 'se aproxima da camera', 'sobe a escada'. "
          "Dizer a direcao evita a IA inventar movimento aleatorio.", ""),
        F("physics", "Fisica e detalhes vivos", "checks", "physics",
          "Elementos que se movem de forma realista (cabelo, tecido, liquido, particulas). Marque 2 ou 3.", ""),
    ]),
    ("Referencias", "Imagens de referencia e frames", [
        F("ref_mode", "Tipo de referencia", "combo", "ref_mode",
          "Como a imagem de referencia sera usada: personagem, estilo, cenario, produto ou primeiro/ultimo frame. "
          "Kling, Runway, Luma e Veo aceitam imagem de entrada; Midjourney usa --cref / --sref.", ""),
        F("ref_image", "Imagem de referencia (caminho ou link)", "entry", None,
          "Caminho do arquivo ou link da imagem principal. O programa nao envia nada: ele escreve a linha de referencia no prompt "
          "e voce anexa a imagem na plataforma. Em Midjourney, use o LINK da imagem.", ""),
        F("ref_first", "Primeiro frame (imagem)", "entry", None,
          "Imagem que sera o primeiro quadro do video (image-to-video).", ""),
        F("ref_last", "Ultimo frame (imagem)", "entry", None,
          "Imagem que sera o ultimo quadro do video. Usado com o primeiro frame para controlar inicio e fim.", ""),
        F("ref_weight", "Peso da referencia (0-100)", "scale", (0, 100),
          "Quanto a IA deve obedecer a referencia. 80+ = copia bem fiel; 30-50 = so inspiracao. "
          "Em Midjourney vira --cw / --sw.", 60),
    ]),
    ("Referencias", "Texto na tela", [
        F("onscreen_text", "Texto que aparece na tela", "text", None,
          "O que fica escrito no video (gancho, preco, nome do produto). IA de video erra letras: prefira textos CURTOS "
          "e, se precisar de texto perfeito, adicione na edicao depois.", ""),
        F("onscreen_pos", "Posicao do texto", "combo", "onscreen_pos",
          "Onde o texto aparece. Evite as bordas onde as redes colocam botoes.", ""),
        F("onscreen_style", "Estilo do texto", "entry", None,
          "Fonte e cor: 'branco, sans-serif grossa, sombra suave', 'amarelo neon'. Opcional.", ""),
    ]),
    ("Referencias", "Continuidade entre cenas", [
        F("continuity", "Elementos que se repetem em todas as cenas", "text", None,
          "O que NAO pode mudar de uma cena para outra: roupa, objeto na mao, cenario, cor de unha, joia. "
          "Escreva como lista curta. Entra em todas as cenas para a IA manter a coerencia.", ""),
        F("free_notes", "Trechos livres (sem campo proprio)", "text", None,
          "Qualquer detalhe que nao cabe nos outros campos. O Importador joga aqui os trechos do prompt original que ele "
          "nao soube classificar, para nada se perder. Entra no prompt como 'NOTES'.", ""),
        F("hook_b", "Gancho alternativo (variante B)", "entry", None,
          "Palavra-chave alternativa para a cena 1. Na exportacao multi-formato o programa gera a versao A (atual) "
          "e a versao B com este gancho, para testar qual retem mais.", ""),
    ]),
    ("Marca", "Briefing da campanha", [
        F("brief_goal", "Objetivo da campanha", "entry", None,
          "Uma frase: vender, gerar lead, lancar produto, aumentar seguidores. Define o tom e a chamada final.", ""),
        F("brief_audience", "Publico", "entry", None,
          "Quem vai ver: 'mulheres 25-40, interesse em skincare, classe B'. Ajuda a escolher personagem, cenario e linguagem.", ""),
        F("brief_tone", "Tom da comunicacao", "entry", None,
          "Ex: 'divertido e direto', 'luxo discreto', 'educativo e confiavel'.", ""),
        F("cta_text", "Chamada para acao (CTA)", "entry", None,
          "A frase final: 'compre agora', 'link na bio', 'cupom OLA10'. Sem CTA o video nao converte.", ""),
    ]),
    ("Marca", "Identidade da marca", [
        F("brand_name", "Marca", "entry", None, "Nome da marca. Entra no prompt como contexto da cena.", ""),
        F("product_name", "Produto", "entry", None, "Nome e tipo do produto: 'serum facial vitamina C 30ml'.", ""),
        F("brand_colors", "Cores da marca", "entry", None,
          "Ex: 'verde sage e bege'. A IA usa essas cores no cenario, na roupa e nos objetos.", ""),
        F("logo_rule", "Regra do logo", "entry", None,
          "Ex: 'logo visivel no frasco', 'sem logo na camisa'. IA nao reproduz logo perfeito: confira no resultado.", ""),
        F("must_show", "Sempre mostrar", "text", None,
          "Itens obrigatorios no video: 'rotulo do produto voltado para a camera', 'sorriso no final'. O verificador avisa se faltar.", ""),
        F("must_avoid", "Nunca mostrar (proibido)", "text", None,
          "Itens proibidos: 'marca concorrente', 'cigarro', 'texto ilegivel'. Entram automaticamente no Negative Prompt.", ""),
    ]),
]
# campos que nascem marcados como pendentes (⚑)
DEFAULT_PENDING = [f.id for _t, _n, fl in SECTIONS[_N_BASE_SECTIONS:] for f in fl]

FIELD_BY_ID: dict[str, Field] = {f.id: f for _, _, fl in SECTIONS for f in fl}

# ----------------------------------------------------------------------------
# FORMULA / TEMPLATE MESTRE
# ----------------------------------------------------------------------------
MASTER_TEMPLATE = (
    "STYLE: {ESTILO}.\n"
    "SHOT: {ENQUADRAMENTO}, {ANGULO}.\n"
    "SUBJECT: {SUJEITO}{ROUPA}{CABELO}, {EXPRESSAO}, {ACAO}{PALAVRA_CHAVE}.\n"
    "SCENE: {AMBIENTE}, {CENARIO_DETALHE}, {HORARIO}, {CLIMA}, {ATMOSFERA}, {FUNDO}.\n"
    "CAMERA: {CAMERA}, {LENTE}, {ABERTURA}, {MOVIMENTO}.\n"
    "LIGHT: {LUZ}, {LUZ_EXTRA}, {COR}.\n"
    "TECH: {ASPECTO}, {FPS}, {MOTION}, {CONSISTENCIA}, {SEED}.\n"
    "AUDIO: {VOZ}, {FALA}, {SFX}, {MUSICA}, {AUDIO_EXTRA}."
)

TOKEN_HELP = [
    ("{ESTILO}", "style_render", "Estilo de renderizacao (foto real, editorial, 3D, anime...)"),
    ("{ENQUADRAMENTO}", "shot", "Corte do corpo no quadro - sobrescrito por cada cena do roteiro"),
    ("{ANGULO}", "angle", "Angulo da camera"),
    ("{SUJEITO}", "char_id/char_desc", "ID + descricao fisica do personagem"),
    ("{ROUPA}", "wardrobe", "Vestuario"),
    ("{CABELO}", "hair", "Cabelo e maquiagem"),
    ("{EXPRESSAO}", "expression", "Micro-expressao facial"),
    ("{ACAO}", "action", "Acao/pose - sobrescrita por cada cena do roteiro"),
    ("{PALAVRA_CHAVE}", "roteiro", "A palavra-chave daquela cena, integrada na frase"),
    ("{AMBIENTE}", "location", "Local da cena"),
    ("{CENARIO_DETALHE}", "location_detail", "Elementos concretos do cenario"),
    ("{HORARIO}", "time_of_day", "Hora do dia"),
    ("{CLIMA}", "weather", "Condicao do tempo"),
    ("{ATMOSFERA}", "atmosphere", "Particulas no ar"),
    ("{FUNDO}", "bg_detail", "Comportamento do fundo"),
    ("{CAMERA}", "camera_body", "Corpo de camera"),
    ("{LENTE}", "lens", "Lente e distancia focal"),
    ("{ABERTURA}", "aperture", "Abertura e profundidade de campo"),
    ("{MOVIMENTO}", "camera_move", "Movimento de camera - sobrescrito por cada cena"),
    ("{LUZ}", "light_style", "Estilo de iluminacao"),
    ("{LUZ_EXTRA}", "light_extra", "Reforcos de luz"),
    ("{COR}", "grading", "Color grading"),
    ("{ASPECTO}", "aspect", "Proporcao de tela"),
    ("{FPS}", "fps", "Taxa de quadros"),
    ("{MOTION}", "motion", "Motion strength 1-10"),
    ("{CONSISTENCIA}", "consistency", "Peso de consistencia de rosto e roupa"),
    ("{SEED}", "seed", "Semente deterministica"),
    ("{VOZ}", "voice_tone", "Tom da locucao"),
    ("{FALA}", "vo_text", "Texto falado - sobrescrito por cada cena"),
    ("{SFX}", "sfx", "Efeitos sonoros"),
    ("{MUSICA}", "music", "Trilha"),
    ("{AUDIO_EXTRA}", "audio_extra", "Detalhe de audio"),
]

# ----------------------------------------------------------------------------
# BLOCOS NARRATIVOS PADRAO (cada bloco explica o que escrever dentro)
# ----------------------------------------------------------------------------
BEAT_TEMPLATES = [
    ("The Hook / Abertura (0-3s)",
     "Os 3 primeiros segundos decidem se a pessoa fica. Escreva aqui a palavra-chave do elemento mais "
     "estranho, bonito ou curioso da sua historia. Enquadramento forte (rosto e olhos ou detalhe macro) "
     "e movimento rapido. NAO explique nada ainda - provoque."),
    ("Setup / Contexto (3-8s)",
     "Mostre ONDE e QUEM. Palavra-chave do ambiente ou da pessoa. Enquadramento mais aberto "
     "(meio corpo ou plano amplo) para o espectador se localizar. Uma informacao, nao tres."),
    ("Build / Desenvolvimento (8-18s)",
     "O problema ou o desejo. Palavra-chave da acao principal. Aqui entra a demonstracao do que "
     "incomoda ou do que se quer. Movimento de camera que aproxima (push in) aumenta a tensao."),
    ("Reveal / Clímax (18-25s)",
     "A virada: o produto, a solucao, a resposta. Palavra-chave do produto. Use enquadramento de "
     "detalhe (maos / insert) e a luz mais bonita do roteiro. E o frame que vira a thumbnail."),
    ("Proof / Demonstracao (25-35s)",
     "Prova concreta: o produto funcionando, o antes/depois, o numero, o depoimento. "
     "Palavra-chave do resultado. Enquadramento que mostre o efeito sem corte de edicao."),
    ("The Call / Outro (35-40s)",
     "A chamada para acao. Palavra-chave do gesto (apontar, clicar, link). Olho direto na lente, "
     "frase curta e imperativa, e um movimento de camera que afasta (pull out) ou trava. "
     "Sem CTA o video nao converte, so entretem."),
]


def new_beat(name="Nova cena", info=""):
    return {
        "name": name, "info": info, "keyword": "", "shot": "", "angle": "",
        "move": "", "action": "", "vo": "", "dur": 5, "extra": "", "auto": True,
        "transition": "", "text": "",
    }


def default_beats():
    beats = []
    seeds = [
        ("celular",      "Rosto e olhos (extreme close-up)"),
        ("janela",       "Plano amplo (wide / estabelecimento)"),
        ("copo de agua", "Meio corpo (medium shot)"),
        ("produto",      "Maos / detalhe de produto"),
        ("sorriso",      "Rosto inteiro (close-up)"),
        ("mao",          "Busto (ombros e rosto)"),
    ]
    for (name, info), (kw, shot) in zip(BEAT_TEMPLATES, seeds):
        b = new_beat(name, info)
        b["keyword"] = kw
        b["shot"] = shot
        beats.append(b)
    return beats


# ----------------------------------------------------------------------------
# PRESETS EMBUTIDOS
# ----------------------------------------------------------------------------
BUILTIN_PRESETS = {
    "Moda Luxo": {
        "subject_type": "Pessoa", "wardrobe": "Traje de gala / vestido longo",
        "camera_body": "ARRI Alexa Mini LF (cinema suave)", "lens": "85mm retrato (fundo cremoso)",
        "aperture": "f/1.2 - f/1.8 (fundo muito desfocado)", "shot": "Corpo inteiro (full shot)",
        "angle": "Tres quartos (3/4)", "camera_move": "Orbita 180 graus",
        "light_style": "Chiaroscuro / noir", "grading": "Moody escuro cinematografico",
        "style_render": "Editorial de moda (Vogue)", "location": "Estudio fundo infinito",
        "atmosphere": "Nevoa volumetrica (haze)", "voice_tone": "Sem locucao (so ambiente)",
        "music": "Ambient drone", "motion": 3, "consistency": 90, "aspect": "2.39:1 cinemascope",
        "fps": "60 fps (fluido / slow-mo)", "expression": "Neutro confiante",
        "action": "Girando (fashion spin)",
    },
    "Comercial Tech": {
        "subject_type": "Produto / objeto", "camera_body": "RED V-Raptor 8K (nitidez extrema)",
        "lens": "100mm macro (textura extrema)", "aperture": "f/4 - f/5.6 (sujeito + fundo proximo)",
        "shot": "Plano detalhe do objeto (insert)", "angle": "Altura dos olhos (neutro)",
        "camera_move": "Slider lateral (parallax)", "light_style": "Contraluz dura (rim light)",
        "grading": "Comercial clean neutro", "style_render": "Comercial 4K produto",
        "location": "Estudio fundo infinito", "atmosphere": "Ar limpo (sem particula)",
        "voice_tone": "Corporativa firme e confiante", "music": "Eletronica tensa (techno)",
        "motion": 5, "consistency": 70, "aspect": "16:9 horizontal (YouTube/TV)",
        "fps": "60 fps (fluido / slow-mo)", "action": "Segurando e girando o produto",
    },
    "Vlog UGC": {
        "subject_type": "Pessoa + produto", "wardrobe": "Camiseta branca basica",
        "camera_body": "iPhone 16 Pro Max na mao (UGC)", "lens": "24mm wide (ambiente)",
        "aperture": "f/2.8 (sujeito isolado, seguro)", "shot": "Busto (ombros e rosto)",
        "angle": "Altura dos olhos (neutro)", "camera_move": "Handheld documental",
        "light_style": "Luz de janela suave (north light)", "grading": "Pastel suave baixo contraste",
        "style_render": "Documental cru", "location": "Apartamento minimalista",
        "atmosphere": "Ar limpo (sem particula)", "voice_tone": "Influenciador energico e rapido",
        "music": "Pop energetico", "motion": 6, "consistency": 80,
        "aspect": "9:16 vertical (Reels/TikTok/Shorts)", "fps": "30 fps (social media)",
        "expression": "Boca pronta para falar (lip-sync)", "action": "Mostrando produto na palma da mao",
    },
    "Beleza / Skincare": {
        "subject_type": "Pessoa + produto", "wardrobe": "Camiseta branca basica",
        "camera_body": "ARRI Alexa Mini LF (cinema suave)", "lens": "100mm macro (textura extrema)",
        "aperture": "f/2.8 (sujeito isolado, seguro)", "shot": "Rosto inteiro (close-up)",
        "angle": "Tres quartos (3/4)", "camera_move": "Push in lento (aproxima)",
        "light_style": "Ring light / softbox de estudio", "grading": "Pastel suave baixo contraste",
        "style_render": "Fotorrealista cinematografico", "location": "Banheiro com espelho",
        "atmosphere": "Vapor de agua / banheiro", "voice_tone": "ASMR sussurrado intimista",
        "music": "Lo-fi minimalista", "motion": 2, "consistency": 92,
        "aspect": "9:16 vertical (Reels/TikTok/Shorts)", "fps": "120 fps (super slow motion)",
        "expression": "Micro-sorriso sutil", "action": "Aplicando produto no rosto",
    },
    "Food / Gastronomia": {
        "subject_type": "Produto / objeto", "camera_body": "RED V-Raptor 8K (nitidez extrema)",
        "lens": "100mm macro (textura extrema)", "aperture": "f/2.8 (sujeito isolado, seguro)",
        "shot": "Plano detalhe do objeto (insert)", "angle": "Visao de passaro (top-down)",
        "camera_move": "Rack focus (troca de foco)", "light_style": "Luz de janela suave (north light)",
        "grading": "Kodak quente nostalgico", "style_render": "Comercial 4K produto",
        "location": "Cozinha com luz de janela", "atmosphere": "Vapor de agua / banheiro",
        "voice_tone": "Sem locucao (so ambiente)", "music": "Lo-fi minimalista",
        "motion": 4, "consistency": 60, "aspect": "4:5 retrato (feed alto)",
        "fps": "120 fps (super slow motion)", "action": "Cozinhando / cortando",
    },
}

# modelo sem nada preenchido: tudo marcado com ⚑ (voce libera so o que quiser usar)
BUILTIN_PRESETS["Modelo em branco (tudo pendente)"] = {
    "_pending": [f.id for _t, _n, fl in SECTIONS for f in fl
                 if f.id not in ("translate", "seed_lock", "negative_preset", "subject_type")],
}

# combinacoes compativeis para o Lucky Roll (sorteio coerente)
LUCKY_SETS = list(BUILTIN_PRESETS.keys())

PLATFORMS = [
    ("universal", "Universal / Completo"),
    ("midjourney", "Midjourney v6/v7"),
    ("runway", "Runway Gen-3 / Gen-4"),
    ("kling", "Kling AI"),
    ("luma", "Luma Dream Machine"),
    ("sora", "Sora / Hunyuan"),
    ("veo", "Google Veo 3"),
    ("shotlist", "Shot List (roteiro cena a cena)"),
    ("json", "JSON (projeto / API)"),
]

PLATFORM_NOTES = {
    "universal": "Formato longo com todos os blocos. Use como fonte de verdade e para modelos que aceitam prompt grande.",
    "midjourney": "Midjourney ignora audio e nao tem campo negativo: os negativos viram '--no'. Mantenha uma frase densa, sem listas.",
    "runway": "Runway Gen-3/4 responde melhor a UMA frase curta comecando pelo movimento de camera. Nao tem negative prompt.",
    "kling": "Kling tem campo separado de Negative Prompt e duracao fixa de 5s ou 10s. Movimento de camera deve ser explicito.",
    "luma": "Luma gosta de prosa simples e descritiva. Evite listas tecnicas longas e parametros.",
    "sora": "Sora/Hunyuan aceitam narrativa com cenas e audio descrito. Pode enviar o roteiro inteiro com cabecalhos de cena.",
    "veo": "Veo 3 gera audio junto: descreva locucao, SFX e ambiente. Dialogo entre aspas sai como fala sincronizada.",
    "shotlist": "Uma linha de prompt pronta por cena do roteiro. Gere cada cena separada e junte na edicao.",
    "json": "Estrutura completa para reaproveitar em script/API ou para versionar o projeto no git.",
}

# ============================================================================
#  NUCLEO LOGICO  (independente da interface - pode ser importado e testado)
# ============================================================================

_ACCENTS = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
                         "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")


def deaccent(txt: str) -> str:
    return (txt or "").translate(_ACCENTS)


def opt_list(src: str) -> list[str]:
    return [o.label for o in OPTIONS.get(src, [])]


def opt_info(src: str, label: str) -> str:
    for o in OPTIONS.get(src, []):
        if o.label == label:
            return o.info
    return ""


def en_of(src: str | None, label: str) -> str:
    """Traduz o label escolhido para o termo tecnico em ingles.
    Se o usuario digitou algo fora do catalogo, o texto dele e usado como esta."""
    label = (label or "").strip()
    if not label:
        return ""
    for o in OPTIONS.get(src or "", []):
        if o.label == label:
            return o.en
    return label


# --------------------------------------------------------------------------
# DICIONARIO EXTERNO (dados/*.json)
#   dados/gatilhos.json  e dados/glossario.json -> base versionada no Git
#   dados/usuario.json   -> palavras do usuario (locais, fora do Git);
#                           vencem a base quando a palavra e a mesma.
# --------------------------------------------------------------------------
USER_DICT_FILE = os.path.join(DATA_DIR, "usuario.json")
DICT_WARNINGS: list[str] = []


def _norm_key(txt: str) -> str:
    return re.sub(r"\s+", " ", deaccent(txt or "").strip().lower())


def _read_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
    except Exception as exc:
        DICT_WARNINGS.append("%s: %s" % (os.path.basename(path), exc))
        return default


KEYWORD_TRIGGERS: dict[str, KT] = {}
GLOSSARY: dict[str, str] = {}
USER_DICT: dict = {"gatilhos": {}, "glossario": {}}


def _trigger_from(d: dict) -> KT:
    return KT(d.get("shot", ""), d.get("lens", ""), d.get("action", ""), d.get("extra", ""))


def load_dictionaries() -> None:
    """(Re)carrega base + usuario nos dicionarios globais (alteracao em-place)."""
    DICT_WARNINGS.clear()
    base_t = _read_json(os.path.join(DATA_DIR, "gatilhos.json"), {})
    base_g = _read_json(os.path.join(DATA_DIR, "glossario.json"), {})
    user = _read_json(USER_DICT_FILE, {})
    USER_DICT["gatilhos"] = dict(user.get("gatilhos", {}))
    USER_DICT["glossario"] = dict(user.get("glossario", {}))
    KEYWORD_TRIGGERS.clear()
    GLOSSARY.clear()
    for src in (base_t, USER_DICT["gatilhos"]):
        for k, v in src.items():
            KEYWORD_TRIGGERS[_norm_key(k)] = _trigger_from(v)
    for src in (base_g, USER_DICT["glossario"]):
        for k, v in src.items():
            GLOSSARY[_norm_key(k)] = v
    if not KEYWORD_TRIGGERS and not GLOSSARY:
        DICT_WARNINGS.append("pasta 'dados' vazia ou ausente: sem gatilhos e sem glossario.")
    _rebuild_gloss_index()


def save_user_dict() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USER_DICT_FILE, "w", encoding="utf-8") as fh:
        json.dump(USER_DICT, fh, ensure_ascii=False, indent=1, sort_keys=True)


def find_trigger(text: str):
    """Acha o gatilho de um trecho do roteiro. Ignora acento/maiuscula, aceita plural
    simples e a frase mais longa vence ('copo de agua' ganha de 'copo').
    Retorna (chave, KT) ou (None, None)."""
    raw = _norm_key(text)
    if not raw:
        return None, None

    def variants(w: str):
        yield w
        if w.endswith("es") and len(w) > 4:
            yield w[:-2]
        if w.endswith("s") and len(w) > 3:
            yield w[:-1]

    for cand in variants(raw):
        if cand in KEYWORD_TRIGGERS:
            return cand, KEYWORD_TRIGGERS[cand]
    for k in sorted(KEYWORD_TRIGGERS, key=len, reverse=True):
        pat = r"(?<![a-z])" + re.escape(k) + r"(?:es|s)?(?![a-z])"
        if re.search(pat, raw):
            return k, KEYWORD_TRIGGERS[k]
    return None, None


# --------------------------------------------------------------------------
# TRADUTOR PT -> EN (glossario tecnico offline)
# --------------------------------------------------------------------------
_GLOSS_KEYS: list[str] = []
_ENGLISH_SAFE: set = set()


def _rebuild_gloss_index() -> None:
    _GLOSS_KEYS[:] = sorted(GLOSSARY.keys(), key=len, reverse=True)
    _ENGLISH_SAFE.clear()
    for _v in GLOSSARY.values():
        _ENGLISH_SAFE.update(re.findall(r"[a-z]+", _v.lower()))
    for _s in (ADJECTIVES_EN, NOUNS_EN):
        _ENGLISH_SAFE.update(_s)
    _ENGLISH_SAFE.update(_ENGLISH_EXTRA)


# termos ingleses que podem aparecer digitados direto pelo usuario
_ENGLISH_EXTRA = {
    "the", "and", "with", "of", "in", "on", "at", "a", "an", "to", "from", "by",
    "shot", "lens", "light", "camera", "close", "wide", "macro", "bokeh", "grade",
    "cinematic", "photorealistic", "detail", "style", "motion", "seed", "fps",
    "slow", "fast", "soft", "hard", "handheld", "studio", "neon", "film", "grain",
    "look", "frame", "focus", "depth", "field", "angle", "view", "mid", "full",
    "body", "skin", "hair", "product", "scene", "background", "foreground",
    "very", "slightly", "while", "then", "before", "when", "everything", "each",
    "also", "only", "already", "well", "this", "that", "their", "his", "her",
    "my", "years", "old", "middle", "aged", "length", "level",
}
load_dictionaries()
_PT_HINT = re.compile(r"(ao$|oes$|aes$|inho$|inha$|mente$|cao$|ndo$|ava$|eiro$|eira$"
                      r"|^nao$|^sem$|^com$|^que$|^uma$|^dos$|^das$|^pra$|^pro$|lh|nh|ç)")


def _roles(tokens: list[str]) -> list[str]:
    """Classifica cada palavra como N (substantivo), A (adjetivo) ou O (outro).
    Palavras ambiguas (ex: 'light') sao decididas pela vizinhanca."""
    def pure(w, s, other):
        return w in s and w not in other
    roles = []
    for i, w in enumerate(tokens):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        if w in AMBIGUOUS_EN:
            if nxt and pure(nxt, ADJECTIVES_EN, NOUNS_EN):
                roles.append("N")          # 'light soft' -> light e substantivo
            elif nxt and pure(nxt, NOUNS_EN, ADJECTIVES_EN):
                roles.append("A")          # 'light freckles' -> light e adjetivo
            elif nxt is None and roles and roles[-1] == "N":
                roles.append("A")          # 'freckles light' -> light e adjetivo
            else:
                roles.append("N")
        elif w in NOUNS_EN:
            roles.append("N")
        elif w in ADJECTIVES_EN:
            roles.append("A")
        else:
            roles.append("O")
    return roles


def _reorder_adjectives(tokens: list[str]) -> list[str]:
    """PT escreve 'cabelo preto'; EN escreve 'black hair'. Move os adjetivos
    para a frente do grupo de substantivos que eles qualificam."""
    roles = _roles(tokens)
    out, i, n = [], 0, len(tokens)
    while i < n:
        if roles[i] == "N":
            j = i
            while j < n and roles[j] == "N":
                j += 1
            k = j
            while k < n and roles[k] == "A":
                k += 1
            if k > j:
                out.extend(tokens[j:k])
                out.extend(tokens[i:j])
                i = k
            else:
                out.extend(tokens[i:j])
                i = j
        else:
            out.append(tokens[i])
            i += 1
    return out


def translate_pt(text: str) -> tuple[str, list[str]]:
    """Traduz com glossario tecnico + reordenacao de adjetivos.
    Retorna (texto, palavras que ficaram sem traducao)."""
    if not text or not text.strip():
        return "", []
    out = deaccent(text).lower()
    for pattern, repl in PRE_RULES:
        out = re.sub(pattern, repl, out)
    for key in _GLOSS_KEYS:
        k = deaccent(key).lower()
        out = re.sub(r"(?<![a-z0-9-])" + re.escape(k) + r"(?![a-z0-9-])", GLOSSARY[key], out)

    # reordena adjetivos dentro de cada trecho separado por pontuacao
    pieces = re.split(r"([,;.:()\n]|\bof\b|\bwith\b|\bin\b|\bon\b|\bat\b|\band\b)", out)
    out = ""
    for idx, p in enumerate(pieces):  # indices pares = texto, impares = separador
        if idx % 2 == 0:
            m = re.match(r"^(\s*)(.*?)(\s*)$", p, re.S)
            lead, core, trail = m.group(1), m.group(2), m.group(3)
            toks = core.split()
            core = " ".join(_reorder_adjectives(toks)) if len(toks) > 1 else core
            out += lead + core + trail
        else:
            out += p
    out = re.sub(r"\s+", " ", out).strip()

    unknown = []
    for w in re.findall(r"[a-z]{3,}", out):
        if w in _ENGLISH_SAFE or w in unknown:
            continue
        unknown.append(w)
    return out, unknown


# --------------------------------------------------------------------------
# TRADUTOR ONLINE OPCIONAL
# Se o pacote 'deep-translator' estiver instalado (pip install deep-translator)
# a traducao fica completa. Sem ele, o glossario interno e usado.
# --------------------------------------------------------------------------
ONLINE = {"enabled": False, "fails": 0}


def online_available() -> bool:
    try:
        import deep_translator  # noqa: F401
        return True
    except Exception:
        return False


def translate_online(text: str) -> str:
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="pt", target="en").translate(text) or text


def maybe_translate(text: str, enabled: bool, bag: list[str]) -> str:
    if not text:
        return ""
    if not enabled:
        return text.strip()
    if ONLINE["enabled"]:
        try:
            return translate_online(text).strip()
        except Exception:
            ONLINE["fails"] += 1
            if "[tradutor online indisponivel - usando glossario]" not in bag:
                bag.append("[tradutor online indisponivel - usando glossario]")
    out, unknown = translate_pt(text)
    for u in unknown:
        if u not in bag:
            bag.append(u)
    return out.strip()


def clean_join(parts, sep=", "):
    return sep.join([p.strip().rstrip(",").strip() for p in parts if p and str(p).strip()])


def tidy(text: str) -> str:
    """Limpa tokens vazios, virgulas duplicadas e espacos."""
    text = re.sub(r"\{[A-Z_]+\}", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(,\s*){2,}", ", ", text)
    text = re.sub(r"\(\s*\)", "", text)
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        line = re.sub(r"^([A-Z]+:)\s*,\s*", r"\1 ", line)
        line = re.sub(r",\s*\.", ".", line)
        line = re.sub(r"\s+,", ",", line)
        line = re.sub(r"^,\s*", "", line)
        line = re.sub(r",\s*$", "", line)
        if line in ("", ".") or re.match(r"^[A-Z_]+:\s*[.,]?$", line):
            continue
        lines.append(line)
    return "\n".join(lines)


class Compiler:
    """Transforma o estado da UI em prompts por plataforma."""

    def __init__(self, state: dict, beats: list[dict], template: str):
        self.s = dict(state)
        self.beats = [dict(b) for b in beats]
        self.template = template or MASTER_TEMPLATE
        self.untranslated: list[str] = []
        self.tr = bool(self.s.get("translate", True))
        # campos marcados com ⚑ (preencher depois) ficam FORA do prompt
        self.pending = set(self.s.get("_pending") or [])

    # ---------------------------------------------------------------- helpers
    def g(self, fid, default=""):
        if fid in self.pending:
            return "" if not isinstance(default, (int, float)) else None
        v = self.s.get(fid, default)
        return v if v is not None else default

    def en(self, fid):
        f = FIELD_BY_ID.get(fid)
        return en_of(f.src if f else None, str(self.g(fid)))

    def en_multi(self, fid):
        f = FIELD_BY_ID.get(fid)
        vals = self.g(fid) or []
        if isinstance(vals, str):
            vals = [vals] if vals else []
        return clean_join([en_of(f.src if f else None, v) for v in vals])

    def free(self, fid):
        return maybe_translate(str(self.g(fid)), self.tr, self.untranslated)

    def seed_for(self, index: int) -> str:
        raw = str(self.g("seed", "")).strip()
        if not raw:
            return ""
        try:
            base = int(re.sub(r"\D", "", raw) or 0)
        except ValueError:
            return ""
        if self.g("seed_lock", True):
            return str(base)
        return str(base + index)

    def subject(self) -> str:
        cid = str(self.g("char_id", "")).strip()
        desc = self.free("char_desc")
        kind = self.en("subject_type")
        head = clean_join([kind, desc])
        if cid:
            head = "[%s] %s" % (cid, head)
        return head

    # ---------------------------------------------------------------- tokens
    def tokens(self, beat: dict | None, index: int = 0) -> dict:
        b = beat or {}
        shot = en_of("shot", b.get("shot") or str(self.g("shot")))
        angle = en_of("angle", b.get("angle") or str(self.g("angle")))
        move = en_of("camera_move", b.get("move") or str(self.g("camera_move")))
        action = en_of("action", b.get("action") or str(self.g("action")))
        kw = b.get("keyword", "").strip()
        kw_en = maybe_translate(kw, self.tr, self.untranslated)
        extra = b.get("extra", "").strip()
        kw_frag = ""
        if kw_en:
            kw_frag = ", focus on the %s" % kw_en
            if extra:
                kw_frag += ", %s" % extra
        vo = b.get("vo", "").strip() or str(self.g("vo_text", "")).strip()
        vo_en = maybe_translate(vo, self.tr, self.untranslated)
        seed = self.seed_for(index)
        human = str(self.g("subject_type", "")) in (
            "Pessoa", "Pessoa + produto", "Grupo de pessoas", "Personagem 3D / mascote")
        roupa = self.en("wardrobe")
        cabelo = self.free("hair")
        return {
            "{ESTILO}": self.en("style_render"),
            "{ENQUADRAMENTO}": shot,
            "{ANGULO}": angle,
            "{SUJEITO}": self.subject(),
            "{ROUPA}": (", wearing %s" % roupa) if (roupa and human) else "",
            "{CABELO}": (", %s" % cabelo) if (cabelo and human) else "",
            "{EXPRESSAO}": self.en("expression"),
            "{ACAO}": action,
            "{PALAVRA_CHAVE}": kw_frag,
            "{AMBIENTE}": self.en("location"),
            "{CENARIO_DETALHE}": self.free("location_detail"),
            "{HORARIO}": self.en("time_of_day"),
            "{CLIMA}": self.en("weather"),
            "{ATMOSFERA}": self.en_multi("atmosphere"),
            "{FUNDO}": self.free("bg_detail"),
            "{CAMERA}": self.en("camera_body"),
            "{LENTE}": en_of("lens", b.get("lens") or str(self.g("lens"))),
            "{ABERTURA}": self.en("aperture"),
            "{MOVIMENTO}": move,
            "{LUZ}": self.en("light_style"),
            "{LUZ_EXTRA}": self.free("light_extra"),
            "{COR}": self.en("grading"),
            "{ASPECTO}": ("aspect ratio %s" % self.en("aspect")) if self.en("aspect") else "",
            "{FPS}": self.en("fps"),
            "{MOTION}": ("motion strength %s/10" % self.g("motion", 4)) if self.g("motion", 4) is not None else "",
            "{CONSISTENCIA}": ("character consistency lock %s%% (same face, same outfit)" % self.g("consistency", 85))
            if self.g("consistency", 85) is not None else "",
            "{SEED}": ("seed %s" % seed) if seed else "",
            "{VOZ}": self.en("voice_tone"),
            "{FALA}": ('voiceover: "%s"' % vo_en) if vo_en else "",
            "{SFX}": self.en_multi("sfx"),
            "{MUSICA}": self.en("music"),
            "{AUDIO_EXTRA}": self.free("audio_extra"),
            # auxiliares
            "_props": self.free("props"),
            "_neg": self.negative_text(b),
            "_transition": en_of("transition", b.get("transition", "")),
            "_dur": b.get("dur", self.g("duration", 5)) or 5,
            "_name": b.get("name", ""),
            "_kw_raw": kw,
            "_vo_raw": vo,
            "_seed": seed,
            "_aspect": self.en("aspect") or "9:16",
            "_extra_params": str(self.g("extra_params", "")).strip(),
        }

    def render(self, beat=None, index=0) -> tuple[str, dict]:
        t = self.tokens(beat, index)
        out = self.template
        for k, v in t.items():
            if k.startswith("{"):
                out = out.replace(k, str(v))
        if t["_props"]:
            out += "\nPROPS: %s." % t["_props"]
        extra = self.extras_lines(beat)
        if extra:
            out += "\n" + "\n".join(extra)
        return tidy(out), t

    # ---------------------------------------------- blocos extras (agencia)
    def extras_lines(self, beat=None, compact=False) -> list[str]:
        """Linhas 'TAG: texto.' dos campos extras. compact=True descarta o que nao e visual
        (briefing e referencias), para as versoes de 1 paragrafo."""
        b = beat or {}
        L = []
        brand = clean_join([str(self.g("brand_name", "")).strip(),   # nome da marca: nunca traduzir
                            ("product: %s" % self.free("product_name")) if self.free("product_name") else "",
                            ("brand colors: %s" % self.free("brand_colors")) if self.free("brand_colors") else "",
                            ("logo: %s" % self.free("logo_rule")) if self.free("logo_rule") else ""])
        if brand:
            L.append("BRAND: %s." % brand)
        if self.free("must_show"):
            L.append("MUST SHOW: %s." % self.free("must_show"))
        motion = clean_join([self.en("motion_speed"), self.en("easing"), self.en("focus_pull"),
                             self.free("subject_motion"), self.en_multi("physics")])
        if motion:
            L.append("MOTION DETAIL: %s." % motion)
        text = (b.get("text") or "").strip() or str(self.g("onscreen_text", "")).strip()
        if text:
            L.append("ON-SCREEN TEXT: \"%s\"%s." % (
                text, (", " + clean_join([self.en("onscreen_pos"), self.free("onscreen_style")]))
                if clean_join([self.en("onscreen_pos"), self.free("onscreen_style")]) else ""))
        if self.free("continuity"):
            L.append("CONTINUITY (identical in every scene): %s." % self.free("continuity"))
        if self.free("free_notes"):
            L.append("NOTES: %s." % self.free("free_notes").rstrip(" ."))
        if not compact:
            brief = clean_join([
                ("goal: %s" % self.free("brief_goal")) if self.free("brief_goal") else "",
                ("audience: %s" % self.free("brief_audience")) if self.free("brief_audience") else "",
                ("tone: %s" % self.free("brief_tone")) if self.free("brief_tone") else "",
                ("call to action: %s" % self.free("cta_text")) if self.free("cta_text") else ""])
            if brief:
                L.append("BRIEF: %s." % brief)
            ref = self.ref_block()
            if ref:
                L.append(ref)
        return L

    def negative_text(self, beat=None) -> str:
        """Negative base + 'Nunca mostrar'. Se a cena pede texto na tela / logo, tira 'text',
        'subtitle' e 'logo' do negativo (senao um contradiz o outro)."""
        items = [x.strip() for x in str(self.g("negative", "")).split(",") if x.strip()]
        has_text = bool(((beat or {}).get("text") or "").strip() or str(self.g("onscreen_text", "")).strip())
        has_logo = bool(str(self.g("logo_rule", "")).strip())
        drop = set()
        if has_text:
            drop |= {"text", "subtitle", "subtitles", "captions", "text artifacts"}
        if has_logo:
            drop |= {"logo"}
        items = [x for x in items if x.lower() not in drop]
        return clean_join(items + [self.free("must_avoid")])

    def ref_block(self) -> str:
        parts = []
        mode = self.en("ref_mode")
        img = str(self.g("ref_image", "")).strip()
        first = str(self.g("ref_first", "")).strip()
        last = str(self.g("ref_last", "")).strip()
        w = self.g("ref_weight", 60)
        if mode and img:
            parts.append("%s: %s (weight %s%%)" % (mode, img, w if w is not None else 60))
        elif img:
            parts.append("reference image: %s" % img)
        if first:
            parts.append("start frame: %s" % first)
        if last:
            parts.append("end frame: %s" % last)
        return ("REFERENCE: %s." % "; ".join(parts)) if parts else ""

    def mj_ref_flags(self) -> list[str]:
        img = str(self.g("ref_image", "")).strip()
        if not img:
            return []
        w = self.g("ref_weight", 60)
        w = 60 if w is None else int(w)
        mode = str(self.g("ref_mode", ""))
        if "estilo" in mode or "cenario" in mode:
            return ["--sref %s" % img, "--sw %d" % w]
        return ["--cref %s" % img, "--cw %d" % w]

    # ---------------------------------------------------------- plataformas
    def one_line(self, beat=None, index=0) -> tuple[str, dict]:
        """Versao de 1 paragrafo, sem cabecalhos (para MJ / Runway / Luma)."""
        full, t = self.render(beat, index)
        drop = ("AUDIO:", "BRIEF:", "REFERENCE:")
        body = " ".join(l.split(":", 1)[-1].strip() if re.match(r"^[A-Z][A-Z \-]+:", l) else l
                        for l in full.split("\n") if not l.startswith(drop))
        body = re.sub(r"\s+", " ", body).strip()
        return body, t

    def build(self, platform: str) -> str:
        head = "# %s  |  %s  |  %s\n# %s\n\n" % (
            APP_NAME, dict(PLATFORMS).get(platform, platform),
            datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            PLATFORM_NOTES.get(platform, ""))

        if platform == "universal":
            full, t = self.render(self.beats[0] if self.beats else None, 0)
            txt = full
            if t["_neg"]:
                txt += "\n\nNEGATIVE PROMPT: %s" % t["_neg"]
            if t["_extra_params"]:
                txt += "\n\nPARAMS: %s" % t["_extra_params"]
            txt += "\n\n" + self._shotlist_block()
            return head + txt

        if platform == "midjourney":
            body, t = self.one_line(self.beats[0] if self.beats else None, 0)
            flags = ["--ar %s" % t["_aspect"], "--style raw", "--s 250"] + self.mj_ref_flags()
            if t["_seed"]:
                flags.append("--seed %s" % t["_seed"])
            if t["_neg"]:
                flags.append("--no %s" % t["_neg"].replace(",", " ").replace("  ", " "))
            if t["_extra_params"]:
                flags.append(t["_extra_params"])
            out = [head + body + " " + " ".join(flags)]
            for i, b in enumerate(self.beats):
                if not b.get("keyword"):
                    continue
                line, tt = self.one_line(b, i)
                f = ["--ar %s" % tt["_aspect"], "--style raw", "--s 250"] + self.mj_ref_flags()
                if tt["_seed"]:
                    f.append("--seed %s" % tt["_seed"])
                if tt["_neg"]:
                    f.append("--no %s" % tt["_neg"].replace(",", " "))
                out.append("\n/imagine prompt: [%d] %s %s" % (i + 1, line, " ".join(f)))
            return "\n".join(out)

        if platform == "runway":
            lines = [head]
            if self.ref_block():
                lines.append(self.ref_block() + "  (anexe a imagem no campo 'Image' do Runway)\n")
            for i, b in enumerate(self.beats or [None]):
                t = self.tokens(b, i)
                scene = clean_join([t["{ENQUADRAMENTO}"], t["{ANGULO}"], t["{SUJEITO}"],
                                    t["{ACAO}"], t["{PALAVRA_CHAVE}"].lstrip(", "),
                                    t["{AMBIENTE}"], t["{LUZ}"], t["{COR}"], t["{ESTILO}"]])
                lines.append("[%d] %s: %s. %s, %s. %s" % (
                    i + 1, t["{MOVIMENTO}"] or "static shot", scene,
                    t["{LENTE}"], t["{ABERTURA}"],
                    " ".join(self.extras_lines(b, compact=True))))
            lines.append("\n(Runway nao usa negative prompt - os defeitos foram evitados por descricao positiva.)")
            return "\n".join(lines)

        if platform == "kling":
            blocks = [head]
            if self.ref_block():
                blocks.append(self.ref_block() + "  (use 'Start frame' / 'End frame' e 'Character reference' do Kling)")
            for i, b in enumerate(self.beats or [None]):
                t = self.tokens(b, i)
                dur = 10 if int(t["_dur"] or 5) > 5 else 5
                body, _ = self.one_line(b, i)
                blocks.append(
                    "----- CENA %d  (%s) -----\n"
                    "Prompt: %s\n"
                    "Camera movement: %s\n"
                    "Negative prompt: %s\n"
                    "Duration: %ds | Mode: Professional | CFG: 0.5 | Aspect: %s"
                    % (i + 1, t["_name"] or "cena", body, t["{MOVIMENTO}"] or "static",
                       t["_neg"], dur, t["_aspect"]))
            return "\n\n".join(blocks)

        if platform == "luma":
            out = [head]
            if self.ref_block():
                out.append(self.ref_block() + "  (use Keyframes: start / end no Luma)")
            for i, b in enumerate(self.beats or [None]):
                t = self.tokens(b, i)
                prose = ("%s. The camera does a %s. %s, %s. %s, %s. %s." % (
                    clean_join([t["{ENQUADRAMENTO}"], t["{SUJEITO}"], t["{ACAO}"],
                                t["{PALAVRA_CHAVE}"].lstrip(", ")]),
                    t["{MOVIMENTO}"] or "static hold", t["{AMBIENTE}"], t["{HORARIO}"],
                    t["{LUZ}"], t["{COR}"], t["{ESTILO}"]))
                prose += " " + " ".join(self.extras_lines(b, compact=True))
                out.append("[%d] %s" % (i + 1, re.sub(r"\s+", " ", prose)))
            return "\n\n".join(out)

        if platform in ("sora", "veo"):
            out = [head]
            glob = self.tokens(self.beats[0] if self.beats else None, 0)
            out.append("GLOBAL STYLE: %s | %s | %s | %s" % (
                glob["{ESTILO}"], glob["{CAMERA}"], glob["{LUZ}"], glob["{COR}"]))
            out.append("CHARACTER (keep identical in every scene): %s%s%s. %s" % (
                glob["{SUJEITO}"], glob["{ROUPA}"], glob["{CABELO}"], glob["{CONSISTENCIA}"]))
            for ln in self.extras_lines(None, compact=False):
                if ln.startswith(("BRAND:", "BRIEF:", "REFERENCE:", "CONTINUITY", "MUST SHOW:")):
                    out.append(ln)
            out.append("")
            for i, b in enumerate(self.beats or [None]):
                t = self.tokens(b, i)
                out.append("SCENE %d - %s (%ss)" % (i + 1, t["_name"] or "cena", t["_dur"]))
                out.append("  Visual: %s" % clean_join(
                    [t["{ENQUADRAMENTO}"], t["{ANGULO}"], t["{ACAO}"],
                     t["{PALAVRA_CHAVE}"].lstrip(", "), t["{AMBIENTE}"],
                     t["{CENARIO_DETALHE}"], t["{ATMOSFERA}"]]))
                out.append("  Camera: %s, %s, %s" % (t["{MOVIMENTO}"], t["{LENTE}"], t["{ABERTURA}"]))
                audio = clean_join([t["{VOZ}"], t["{SFX}"], t["{MUSICA}"], t["{AUDIO_EXTRA}"]])
                out.append("  Audio: %s" % audio)
                if t["{FALA}"]:
                    out.append("  Dialogue: %s" % t["{FALA}"].replace("voiceover: ", ""))
                for ln in self.extras_lines(b, compact=True):
                    if ln.startswith(("MOTION DETAIL:", "ON-SCREEN")):
                        out.append("  " + ln)
                if t["_transition"] and i < len(self.beats) - 1:
                    out.append("  Transition to next scene: %s" % t["_transition"])
                out.append("")
            if platform == "veo":
                out.append("NOTE: Veo 3 generates synced audio - keep dialogue short and inside quotes.")
            else:
                out.append("NEGATIVE / AVOID: %s" % glob["_neg"])
            return "\n".join(out)

        if platform == "shotlist":
            return head + self._shotlist_block()

        if platform == "json":
            return head + json.dumps(self.project_dict(), ensure_ascii=False, indent=2)

        return head + "(plataforma desconhecida)"

    def _shotlist_block(self) -> str:
        rows = ["===================== SHOT LIST ====================="]
        for i, b in enumerate(self.beats):
            line, t = self.one_line(b, i)
            rows.append("\n--- CENA %d | %s | %ss | palavra-chave: %s ---" % (
                i + 1, t["_name"] or "cena", t["_dur"], t["_kw_raw"] or "-"))
            rows.append("ENQUADRAMENTO: %s | ANGULO: %s | CAMERA: %s" % (
                t["{ENQUADRAMENTO}"], t["{ANGULO}"], t["{MOVIMENTO}"]))
            rows.append("PROMPT: %s" % line)
            if t["{FALA}"]:
                rows.append("FALA: %s" % t["{FALA}"])
            if t["_transition"] and i < len(self.beats) - 1:
                rows.append("TRANSICAO PARA A PROXIMA: %s" % t["_transition"])
        return "\n".join(rows)

    def project_dict(self) -> dict:
        scenes = []
        for i, b in enumerate(self.beats):
            line, t = self.one_line(b, i)
            scenes.append({
                "index": i + 1, "name": b.get("name", ""), "keyword_pt": b.get("keyword", ""),
                "framing": t["{ENQUADRAMENTO}"], "angle": t["{ANGULO}"],
                "camera_move": t["{MOVIMENTO}"], "lens": t["{LENTE}"],
                "action": t["{ACAO}"], "duration_s": t["_dur"],
                "voiceover_pt": b.get("vo", ""), "voiceover_en": t["{FALA}"],
                "seed": t["_seed"], "prompt": line,
            })
        return {
            "app": APP_NAME, "version": APP_VERSION,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "template": self.template,
            "fields": self.s,
            "negative_prompt": str(self.g("negative", "")),
            "scenes": scenes,
            "untranslated_words": self.untranslated,
        }


# ----------------------------------------------------------------------------
# VERIFICADOR (checklist antes de gerar)
# ----------------------------------------------------------------------------
# Limites APROXIMADOS de caracteres por cena em cada plataforma. Mudam com as versoes dos
# modelos: se a plataforma atualizar, ajuste aqui.
PLATFORM_LIMITS = {"midjourney": 6000, "runway": 1000, "kling": 2500, "luma": 3000}


def preflight(comp: "Compiler", platform: str) -> list[tuple[str, str]]:
    """Retorna [(nivel, mensagem)] com nivel 'erro' | 'aviso' | 'ok'."""
    out: list[tuple[str, str]] = []
    st, pend = comp.s, comp.pending

    def filled(fid):
        v = st.get(fid)
        return fid not in pend and bool(v if not isinstance(v, (int, float)) else True) and v != ""

    if not comp.beats:
        out.append(("erro", "O roteiro esta vazio: adicione pelo menos uma cena."))
    if not (filled("char_id") or filled("char_desc")):
        out.append(("aviso", "Personagem sem ID e sem descricao fisica (a IA vai inventar uma pessoa diferente a cada cena)."))
    if not (filled("camera_body") or filled("lens")):
        out.append(("aviso", "Sem camera e sem lente definidas: o 'look' ficara aleatorio."))
    if not filled("light_style"):
        out.append(("aviso", "Sem estilo de luz definido."))
    if platform not in ("runway", "shotlist", "json") and not str(comp.negative_text()).strip():
        out.append(("aviso", "Negative Prompt vazio (anatomia errada, texto e marca d'agua podem aparecer)."))
    for i, b in enumerate(comp.beats):
        if not (b.get("keyword") or "").strip():
            out.append(("aviso", "Cena %d (%s) sem palavra-chave." % (i + 1, b.get("name", ""))))
    # campo marcado ⚑ mas com conteudo digitado (sera ignorado)
    ign = [FIELD_BY_ID[f].label for f in pend
           if f in FIELD_BY_ID and f not in DEFAULT_PENDING
           and st.get(f) not in ("", None, [], False) and FIELD_BY_ID[f].kind in ("entry", "text", "combo", "checks")]
    if ign:
        out.append(("aviso", "Campos com conteudo mas marcados ⚑ (ficam FORA do prompt): " + ", ".join(ign[:8])
                    + (" ..." if len(ign) > 8 else "")))
    seed = str(st.get("seed", "")).strip()
    if "seed" not in pend and seed and not re.fullmatch(r"\d+", seed):
        out.append(("erro", "Seed deve ser um numero inteiro (esta: '%s')." % seed))
    if str(st.get("ref_image", "")).strip() and not str(st.get("ref_mode", "")).strip():
        out.append(("aviso", "Imagem de referencia sem 'Tipo de referencia' (personagem, estilo, produto...)."))
    if platform == "midjourney" and (str(st.get("ref_first", "")).strip() or str(st.get("ref_last", "")).strip()):
        out.append(("aviso", "Midjourney gera imagem: primeiro/ultimo frame nao tem efeito la."))
    ost = str(st.get("onscreen_text", "")).strip()
    if ost and len(ost) > 40:
        out.append(("aviso", "Texto na tela com %d caracteres: IA de video erra letras, prefira ate ~40." % len(ost)))
    if comp.untranslated:
        out.append(("aviso", "Palavras fora do glossario (saem sem traducao): " + ", ".join(comp.untranslated[:10])))
    # item proibido aparecendo no prompt positivo
    try:
        full = comp.build(platform)
    except Exception:
        full = ""
    positive = re.split(r"NEGATIVE|--no ", full)[0].lower()
    for item in [x.strip() for x in comp.free("must_avoid").split(",") if x.strip()]:
        if len(item) > 3 and item.lower() in positive:
            out.append(("erro", "Item proibido '%s' aparece no prompt." % item))
    # limite de caracteres por cena (mede o texto que realmente vai para a plataforma)
    lim = PLATFORM_LIMITS.get(platform)
    if lim:
        pat = {"midjourney": r"^(?:/imagine prompt: \[\d+\] )?(.+?)\s--ar", "runway": r"^\[\d+\] (.+)$",
               "luma": r"^\[\d+\] (.+)$", "kling": r"^Prompt: (.+)$"}.get(platform)
        sizes = [len(m) for m in re.findall(pat, full, re.M)] if pat else []
        over = [(i + 1, n) for i, n in enumerate(sizes) if n > lim]
        if over:
            out.append(("aviso", "%d cena(s) acima do limite aproximado de %s (%d caracteres); maior: cena %d com %d. "
                                 "Encurte ou marque campos como ⚑." % (len(over), platform, lim, *max(over, key=lambda x: x[1]))))
    if not any(l in ("erro", "aviso") for l, _ in out):
        out.append(("ok", "Tudo certo: nenhum problema encontrado."))
    return out


# ----------------------------------------------------------------------------
# IMPORTADOR DE PROMPT PRONTO
#   Recebe um prompt escrito por voce (ou por outra IA), em PT ou EN, e distribui
#   o texto nos campos. O que nao for reconhecido NAO e perdido: vai para os campos
#   de texto livre ou fica listado no relatorio para voce encaixar na mao.
# ----------------------------------------------------------------------------
# frase (EN ou PT, sem acento) -> (campo, inicio do label da opcao)
IMPORT_ALIASES = [
    (r"extreme close[- ]?up", "shot", "Rosto e olhos"), (r"close[- ]?up", "shot", "Rosto inteiro"),
    (r"medium close[- ]?up|chest[- ]up|bust shot|busto", "shot", "Busto (ombros"),
    (r"medium shot|mid shot|waist[- ]up|plano medio|meio corpo", "shot", "Meio corpo"),
    (r"cowboy shot|medium full", "shot", "Cowboy"), (r"full[- ]body|full shot|corpo inteiro", "shot", "Corpo inteiro"),
    (r"wide shot|establishing shot|plano aberto|plano amplo", "shot", "Plano amplo"),
    (r"(glance|glancing|looking|look|looks|turning)\b.{0,30}over (her|his|their|the) shoulder|por cima do ombro",
     "shot", "Olhar por cima do ombro"),
    (r"washing (?:her |his |their |the |my )?hair|hair wash|lavando o cabelo|lavar o cabelo", "action", "Lavando o cabelo"),
    (r"over[- ]the[- ]shoulder", "shot", "Over-the-shoulder"), (r"\bpov\b|point of view", "shot", "POV"),
    (r"eye[- ]level|altura dos olhos", "angle", "Altura dos olhos"),
    (r"low[- ]angle|contra[- ]?plong", "angle", "Contra-plonge"), (r"high[- ]angle|\bplong", "angle", "Plonge"),
    (r"dutch angle|tilted", "angle", "Holandes"), (r"top[- ]down|bird'?s[- ]eye|overhead shot", "angle", "Visao de passaro"),
    (r"three[- ]quarter|3/4 view", "angle", "Tres quartos"), (r"profile view|side profile", "angle", "Perfil"),
    (r"locked[- ]off|static shot|tripod|camera estatica", "camera_move", "Estatico"),
    (r"slow push[- ]in|push[- ]in|dolly in", "camera_move", "Push in"), (r"pull[- ]out|dolly out", "camera_move", "Pull out"),
    (r"orbit|arc shot", "camera_move", "Orbita"), (r"\bpan(ning)?\b", "camera_move", "Pan horizontal"),
    (r"handheld|camera na mao", "camera_move", "Handheld"), (r"gimbal|steadicam|tracking shot", "camera_move", "Gimbal"),
    (r"crane", "camera_move", "Crane"), (r"whip pan", "camera_move", "Whip pan"),
    (r"golden hour|hora dourada", "time_of_day", "Golden hour"), (r"blue hour|dawn|sunrise|amanhecer", "time_of_day", "Amanhecer"),
    (r"dusk|twilight|crepusculo", "time_of_day", "Crepusculo"), (r"\bnight\b|noite|nighttime", "time_of_day", "Noite"),
    (r"midday|noon|meio[- ]dia", "time_of_day", "Meio-dia"),
    (r"rembrandt", "light_style", "Rembrandt"), (r"ring light|softbox", "light_style", "Ring light"),
    (r"rim light|backlight|contraluz", "light_style", "Contraluz"), (r"neon", "light_style", "Neon"),
    (r"chiaroscuro|film noir", "light_style", "Chiaroscuro"),
    (r"window light|soft natural daylight|natural daylight from (large )?windows|luz de janela", "light_style", "Luz de janela"),
    (r"overcast", "light_style", "Overcast"),
    (r"teal (and|&) orange", "grading", "Teal"), (r"pastel|muted low[- ]contrast", "grading", "Pastel"),
    (r"moody|dark cinematic", "grading", "Moody"), (r"black and white|monochrome|preto e branco", "grading", "Preto e branco"),
    (r"photorealistic|photo[- ]?realistic|fotorrealista|cinematic realism", "style_render", "Fotorrealista"),
    (r"editorial|vogue", "style_render", "Editorial"), (r"documentary|documental", "style_render", "Documental"),
    (r"\b8k\b|hyper[- ]?real", "style_render", "Hyperreal"), (r"pixar|3d render", "style_render", "3D render"),
    (r"anime", "style_render", "Anime"), (r"\bvhs\b", "style_render", "VHS"),
]
PERSON_WORDS = r"woman|man|girl|boy|person|model|child|people|couple|mulher|homem|menina|menino|pessoa|crianca|casal|influencer|creator"
PLACE_WORDS = (r"loft|apartment|room|kitchen|street|studio|office|house|cafe|park|beach|city|bedroom|bathroom|gym|store|shop|"
               r"ceiling|wall|sofa|couch|window|garden|forest|desert|rooftop|car|stage|apartamento|sala|cozinha|rua|escritorio|"
               r"casa|praia|cidade|quarto|banheiro|academia|loja|parede|teto|sofa|janela|jardim")
LIGHT_WORDS = r"light|lighting|spotlight|daylight|shadow|glow|luz|sombra|iluminacao|brilho"
_IMPORT_STOP = set("with from that this shot camera lens light lighting look style very high low wide angle and the for into "
                   "over under strong soft natural subtle mode scene frame real time".split())


def split_prompts(text: str) -> list[str]:
    """Separa varios prompts colados juntos. Separadores: linhas de ---- / ==== / ####,
    rotulos de idioma sozinhos na linha ('portugues', 'english') e titulos numerados
    curtos ('1. Para Geracao de Video'), que NAO viram prompt."""
    sep = re.compile(r"(?im)^\s*(?:[-=_#*]{5,}|(?:portugu[eê]s|english|ingl[eê]s|translation|tradu[cç][aã]o)\s*:?"
                     r"|\d+[.)]\s+[^\n.]{3,90})\s*$")
    blocks = [p.strip() for p in sep.split(text) if p and len(p.strip()) > 25]
    return blocks or ([text.strip()] if text.strip() else [])


def detect_lang(text: str) -> str:
    low = " " + deaccent(text.lower()) + " "
    pt = sum(low.count(w) for w in (" de ", " com ", " uma ", " um ", " em ", " para ", " que ", " na ", " no ", " ao ", " dos ", " muito "))
    en = sum(low.count(w) for w in (" the ", " with ", " and ", " in a ", " of ", " on ", " to ", " from ", " shot ", " a "))
    return "pt" if pt > en else "en"


_OPT_INDEX: dict = {}


def _opt_index():
    """Para cada opcao do catalogo: palavras 'raras' do termo EN e do label PT, com peso (IDF simples)."""
    if _OPT_INDEX:
        return _OPT_INDEX
    fields = [f for f in FIELD_BY_ID.values()
              if f.kind in ("combo", "checks") and f.src in OPTIONS
              and f.id not in ("negative_preset", "subject_type", "ref_mode", "transition")]
    df: dict[str, int] = {}
    toks = {}
    for f in fields:
        for o in OPTIONS[f.src]:
            words = {w for w in re.findall(r"[a-z0-9]+", deaccent((o.en + " " + re.sub(r"\(.*?\)", "", o.label)).lower()))
                     if len(w) >= 4 and w not in _IMPORT_STOP}
            toks[(f.id, o.label)] = words
            for w in words:
                df[w] = df.get(w, 0) + 1
    for (fid, label), words in toks.items():
        _OPT_INDEX[(fid, label)] = {w: (1.0 if df[w] == 1 else 0.6 if df[w] <= 3 else 0.25) for w in words}
    return _OPT_INDEX


def parse_prompt(text: str) -> dict:
    """Analisa UM prompt e devolve {'fields': {...}, 'recognized': [(label, valor, origem)],
    'leftover': [trechos], 'lang': 'pt'|'en'}."""
    lang = detect_lang(text)
    work = text.strip()
    low = deaccent(work.lower())
    fields: dict = {}
    rec: list[tuple[str, str, str]] = []
    used: list[str] = []          # trechos reconhecidos (para descontar do 'sobrou')

    def put(fid, val, how):
        if isinstance(val, str):
            val = val.strip(" .!?;")
            if FIELD_BY_ID[fid].kind in ("entry", "text") and len(val) > 2 and val[0].isupper() and (
                    val[1].islower() or re.match(r"(?i)(a|an|the|um|uma)\s", val)):
                val = val[0].lower() + val[1:]
        if val in ("", None) or fid in fields:
            return
        fields[fid] = val
        rec.append((FIELD_BY_ID[fid].label, str(val) if not isinstance(val, list) else ", ".join(val), how))

    # --- 1) numeros e flags (alta precisao)
    m = re.search(r"--ar\s+(\d+:\d+)|\b(\d{1,2}:\d{1,2})\b(?!\d)", low)
    if m:
        ratio = m.group(1) or m.group(2)
        for o in OPTIONS["aspect"]:
            if o.en == ratio:
                put("aspect", o.label, "proporcao")
                used.append(m.group(0))
    elif re.search(r"\bvertical\b", low):
        put("aspect", OPTIONS["aspect"][0].label, "'vertical'")
    m = re.search(r"(\d{2,3})\s*-?\s*fps", low)
    if m:
        for o in OPTIONS["fps"]:
            if o.label.startswith(m.group(1)):
                put("fps", o.label, "fps")
                used.append(m.group(0))
    m = re.search(r"(\d{2,3})\s*mm\b", low)
    if m:
        for o in OPTIONS["lens"]:
            if re.match(r"%s\s*mm" % m.group(1), deaccent(o.label.lower())):
                put("lens", o.label, "lente")
                used.append(m.group(0))
    if "anamorphic" in low or "anamorfic" in low:
        for o in OPTIONS["lens"]:
            if "anamorf" in deaccent(o.label.lower()):
                put("lens", o.label, "lente anamorfica")
    m = re.search(r"\bf\s*/\s*(\d+(?:\.\d+)?)", low)
    if m:
        v = float(m.group(1))
        pick = None
        for o in OPTIONS["aperture"]:
            nums = [float(x) for x in re.findall(r"f/(\d+(?:\.\d+)?)", o.label)]
            if nums and (min(nums) - 0.01 <= v <= max(nums) + 0.01):
                pick = o.label
        if pick is None:
            pick = min(OPTIONS["aperture"], key=lambda o: abs(float(re.search(r"f/(\d+(?:\.\d+)?)", o.label).group(1)) - v)).label
        put("aperture", pick, "abertura")
        used.append(m.group(0))
    m = re.search(r"--seed\s+(\d+)|\bseed\s*[:=]?\s*(\d{3,})", low)
    if m:
        put("seed", m.group(1) or m.group(2), "seed")
        used.append(m.group(0))
    m = re.search(r"--no\s+([^-]+?)(?=\s--|$)", work, re.I) or re.search(r"negative prompt\s*:\s*(.+)", work, re.I)
    if m:
        put("negative", clean_join([x.strip() for x in re.split(r"[,;]", m.group(1)) if x.strip()]), "negative")
        used.append(m.group(0))
    flags = list(dict.fromkeys(re.findall(r"--(?!ar\b|seed\b|no\b)\w+(?:\s+[\w.]+)?", work)))
    if flags:
        put("extra_params", " ".join(flags), "flags")
        used.extend(flags)
    m = re.search(r"(\d{2})[- ]?(?:year[- ]old|anos)", low)
    age = m.group(0) if m else ""

    # --- 2) aliases (frases comuns de cinema)
    for pat, fid, prefix in IMPORT_ALIASES:
        mm = re.search(pat, low)
        if not mm or fid in fields:
            continue
        for o in OPTIONS.get(FIELD_BY_ID[fid].src, []):
            if o.label.startswith(prefix):
                put(fid, o.label, "'%s'" % mm.group(0))
                used.append(mm.group(0))
                break

    # --- 3) casamento por palavras raras do catalogo (EN do termo + label PT)
    words = set(re.findall(r"[a-z0-9]+", low))
    en_words = set(words)
    if lang == "pt":
        try:
            tr, _unk = translate_pt(work)
            en_words |= set(re.findall(r"[a-z0-9]+", tr.lower()))
        except Exception:
            pass
    best: dict[str, tuple[float, str, list[str]]] = {}
    multi: dict[str, list[tuple[float, str]]] = {}
    for (fid, label), wts in _opt_index().items():
        hit = [w for w in wts if w in en_words]
        if not hit:
            continue
        score = sum(wts[w] for w in hit)
        ratio = score / max(sum(wts.values()), 0.01)
        strict = fid in ("location", "wardrobe", "expression", "action")
        if score < (2.0 if strict else 1.2) or ratio < (0.6 if strict else 0.34):
            continue
        val = score * (0.5 + ratio)
        if FIELD_BY_ID[fid].kind == "checks":
            multi.setdefault(fid, []).append((val, label))
        elif fid not in best or val > best[fid][0]:
            best[fid] = (val, label, hit)
        used.extend(hit)
    for fid, (_v, label, hit) in best.items():
        put(fid, label, "~aproximado, por palavras: " + ", ".join(hit[:3]))
    for fid, lst in multi.items():
        lst.sort(reverse=True)
        put(fid, [l for _v, l in lst[:4]], "palavras do catalogo")

    # --- 4) tipo de sujeito
    has_person = re.search(r"\b(%s)\b" % PERSON_WORDS, low)
    if has_person:
        put("subject_type", "Pessoa", "palavra de pessoa")

    # --- 5) frases: o que sobrou vai para texto livre
    clean = re.sub(r"--\w+(?:\s+[\w.:]+)?|\bf\s*/\s*\d+(?:\.\d+)?|\b\d{2,3}\s*mm\b(?:\s+(?:lens|lente))?|"
                   r"\b\d{2,3}\s*-?\s*fps\b|\b8k\b|\(?\b\d{1,2}:\d{1,2}\b\)?", " ", work, flags=re.I)
    clean = re.sub(r"\s{2,}", " ", re.sub(r"\s+([,.])", r"\1", clean))
    clauses = [c.strip() for c in re.split(r"(?<=[.!?])\s+|\n+", clean) if c.strip()]
    used_low = [deaccent(u.lower()) for u in used if len(u) > 2]
    leftover: list[str] = []
    for cl in clauses:
        cl_l = deaccent(cl.lower())
        if re.fullmatch(r"[\d\s:.\-]*", cl_l):
            continue
        parts = [p.strip() for p in re.split(r",(?![^()]*\))", cl) if p.strip()]
        keep = []
        for p in parts:
            pl = deaccent(p.lower())
            tokens = [w for w in re.findall(r"[a-z0-9]+", pl) if len(w) >= 4 and w not in _IMPORT_STOP]
            matched = [w for w in tokens if w in used_low or any(w in u for u in used_low)]
            if tokens and len(matched) / len(tokens) >= 0.6:
                continue                      # trecho ja coberto por um campo reconhecido
            keep.append(p)
        if not keep:
            continue
        rest = ", ".join(keep).strip(" ,")
        if re.search(r"\b(%s)\b" % PERSON_WORDS, deaccent(rest.lower())) and "char_desc" not in fields:
            rest = rest.rstrip(" .!?")
            # cenario: ultimo ' in a ... <lugar>' da frase
            cuts = [m_ for m_ in re.finditer(r"\s(?:in|at|inside|em|no|na)\s+(?:a|an|the|um|uma)\s+", rest, re.I)]
            for m_ in reversed(cuts):
                tail = rest[m_.end():]
                if re.search(r"\b(%s)\b" % PLACE_WORDS, deaccent(tail.lower())) and not re.search(
                        r"\b(%s)\b" % PERSON_WORDS, deaccent(tail.lower())):
                    put("location_detail", tail.strip(), "frase do cenario")
                    rest = rest[:m_.start()].strip(" ,")
                    break
            # roupa
            wm = re.search(r"(?:wearing|dressed in|vestindo|veste|usando)\s+((?:[\w-]+\s+){0,5}?[\w-]+?)"
                           r"(?=,|$|\s(?:talking|standing|sitting|walking|holding|looking|smiling|falando|em pe|sentad\w+)\b)", rest, re.I)
            if not wm:
                wm = re.search(r"\b(?:in|em)\s+(?:an?\s+|um\s+|uma\s+)?((?:[\w-]+\s+){0,4}(?:romper|bodysuit|dress|shirt|t-shirt|jacket|blazer|suit|"
                               r"hoodie|jeans|coat|macacao|vestido|camiseta|jaqueta|terno|body|top|skirt|saia)\b)", rest, re.I)
            if wm:
                put("wardrobe", wm.group(1).strip(), "roupa na frase")
                rest = (rest[:wm.start()] + rest[wm.end():]).strip(" ,")
            rest = re.sub(r"^(?:an?\s+)?(?:realistic\s+|photorealistic\s+)?(?:vertical\s+|horizontal\s+)?(?:photo|video|image|picture|shot|foto|video|imagem)\s+"
                          r"(?:of|de|em formato vertical de)\s+(?:an?\s+|uma?\s+)?", "", rest, flags=re.I)
            put("char_desc", re.sub(r"\s{2,}", " ", re.sub(r"\s+,", ",", rest)).strip(" ,"), "frase da pessoa")
        elif re.search(r"\b(%s)\b" % LIGHT_WORDS, deaccent(rest.lower())) and "light_extra" not in fields:
            put("light_extra", rest, "frase de luz")
        elif re.search(r"\b(%s)\b" % PLACE_WORDS, deaccent(rest.lower())):
            old = fields.get("location_detail", "")
            fields["location_detail"] = clean_join([old, rest.rstrip(" .")])
            if old:
                rec[:] = [r for r in rec if r[0] != FIELD_BY_ID["location_detail"].label]
            rec.append((FIELD_BY_ID["location_detail"].label, fields["location_detail"], "frase do cenario"))
        else:
            leftover.append(rest)
    if age and "char_desc" in fields and age not in fields["char_desc"].lower():
        fields["char_desc"] = clean_join([age.replace("-", " "), fields["char_desc"]])
    return {"fields": fields, "recognized": rec, "leftover": leftover, "lang": lang}


# ----------------------------------------------------------------------------
# APLICAR MUDANCAS NO PROMPT PRONTO
#   Compara o projeto "como foi gerado" com o projeto "como esta agora" e troca, no texto da
#   saida, cada trecho antigo pelo novo - em TODAS as cenas. Preserva edicoes manuais.
# ----------------------------------------------------------------------------
# campos que, ao mudar, arrastam outro campo junto
APPLY_DEPENDS = {"negative_preset": ["negative"]}


def _norm_snip(t) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip(" ,.")


def snippet_pairs(old: "Compiler", new: "Compiler") -> tuple[list[dict], list]:
    """Para cada cena: {trecho_antigo: trecho_novo}. E a lista de trechos novos sem lugar para entrar."""
    per_scene: list[dict] = []
    inserts: list[str] = []
    obeats = old.beats or [None]
    nbeats = new.beats or [None]
    for i, (ob, nb) in enumerate(zip(obeats, nbeats)):
        pairs: dict[str, str] = {}

        def add(o, n):
            o, n = _norm_snip(o), _norm_snip(n)
            if o == n:
                return
            if not o:
                if n and n not in inserts:
                    inserts.append(n)
                return
            pairs.setdefault(o, n)

        ot, nt = old.tokens(ob, i), new.tokens(nb, i)
        for k in ot:
            if k.startswith("{") or k in ("_kw_raw", "_props", "_transition"):
                add(ot[k], nt.get(k, ""))
        add(old.negative_text(ob), new.negative_text(nb))
        oe = {l.split(":", 1)[0]: l.split(":", 1)[1] for l in old.extras_lines(ob) if ":" in l}
        ne = {l.split(":", 1)[0]: l.split(":", 1)[1] for l in new.extras_lines(nb) if ":" in l}
        for tag in set(oe) | set(ne):
            add(oe.get(tag, ""), ne.get(tag, ""))
        per_scene.append(pairs)
    return per_scene, inserts


_SCENE_MARK = re.compile(r"(?m)^(?:/imagine prompt: )?\[(\d+)\] |^-{3,5} CENA (\d+)\b|^SCENE (\d+) - ")
_EMPTY_TAGS = re.compile(r"^[ \t]*(?:BRAND|MUST SHOW|MOTION DETAIL|ON-SCREEN TEXT|CONTINUITY \(identical in every scene\)|NOTES"
                         r"|BRIEF|REFERENCE|PROPS):[ \t]*[.,]?[ \t]*$")


def _tidy_changed_line(line: str) -> str:
    line = re.sub(r"(,\s*){2,}", ", ", line)
    line = re.sub(r",\s*\.", ".", line)
    line = re.sub(r"[ \t]+,", ",", line)
    return re.sub(r"^([ \t]*[A-Z]+:)\s*,\s*", r"\1 ", line)


def _patch_block(block: str, pairs: dict, counts: dict) -> str:
    if not pairs:
        return block
    olds = sorted(pairs, key=len, reverse=True)
    pat = re.compile("|".join(r"(?<![\w])%s(?![\w])" % re.escape(o) for o in olds), re.I)
    lower = {o.lower(): o for o in olds}

    def sub(m):
        key = lower.get(m.group(0).lower())
        if key is None:
            return m.group(0)
        counts[key] = counts.get(key, 0) + 1
        return pairs[key]

    out = []
    for line in block.split("\n"):
        new = pat.sub(sub, line)
        if new != line:
            new = _tidy_changed_line(new)
            if _EMPTY_TAGS.match(new):
                continue
        out.append(new)
    return "\n".join(out)


def patch_text(text: str, per_scene: list[dict]) -> tuple[str, dict, list]:
    """Aplica as trocas de cada cena SO dentro do bloco daquela cena (as demais ficam intactas).
    Antes do primeiro marcador de cena vale a cena 1. Sem marcadores, usa todas as trocas no texto todo.
    Retorna (texto, {trecho: vezes}, [trechos que nao foram achados])."""
    counts: dict[str, int] = {}
    marks = list(_SCENE_MARK.finditer(text))
    if not marks:
        merged: dict = {}
        for p in per_scene:
            for k, v in p.items():
                merged.setdefault(k, v)
        return _patch_block(text, merged, counts), counts, [o for o in merged if o not in counts]
    cuts = [(0, marks[0].start(), 0)]
    for j, m in enumerate(marks):
        idx = int(next(g for g in m.groups() if g)) - 1
        end = marks[j + 1].start() if j + 1 < len(marks) else len(text)
        cuts.append((m.start(), end, idx))
    out = []
    for start, end, idx in cuts:
        pairs = per_scene[idx] if 0 <= idx < len(per_scene) else {}
        out.append(_patch_block(text[start:end], pairs, counts))
    wanted = {o for p in per_scene for o in p}
    return "".join(out), counts, sorted(o for o in wanted if o not in counts)


# ============================================================================
#  WIDGETS DE INTERFACE
# ============================================================================

class Tooltip:
    """Balao de ajuda ao passar o mouse."""

    def __init__(self, widget, text_fn, delay=350, width=440):
        self.widget = widget
        self.text_fn = text_fn if callable(text_fn) else (lambda: text_fn)
        self.delay = delay
        self.width = width
        self.tip = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _=None):
        self._cancel()
        self.after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self.after_id:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _show(self):
        txt = (self.text_fn() or "").strip()
        if not txt or self.tip:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry("+%d+%d" % (x, y))
        self.tip.configure(bg=CLR["accent"])
        lbl = tk.Label(self.tip, text=txt, justify="left", wraplength=self.width,
                       bg=CLR["tip_bg"], fg=CLR["fg"], font=FONT,
                       padx=10, pady=8, bd=0)
        lbl.pack(padx=1, pady=1)

    def _hide(self, _=None):
        self._cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


class InfoIcon(tk.Canvas):
    """Icone 'i' dentro de um circulo. Hover = balao, clique = janela completa."""

    def __init__(self, parent, title, text, size=16):
        super().__init__(parent, width=size, height=size, bg=parent["bg"] if "bg" in parent.keys() else CLR["panel"],
                         highlightthickness=0, bd=0, cursor="hand2")
        self.title_txt = title
        self.text = text or "Sem descricao."
        pad = 1
        self.circle = self.create_oval(pad, pad, size - pad, size - pad,
                                       outline=CLR["accent"], width=1, fill=CLR["panel2"])
        self.letter = self.create_text(size / 2, size / 2 + 0.5, text="i",
                                       fill=CLR["accent"], font=("Georgia", int(size * 0.62), "bold italic"))
        Tooltip(self, lambda: "%s\n\n%s" % (self.title_txt, self.text))
        self.bind("<Button-1>", self.popup)
        self.bind("<Enter>", lambda e: self.itemconfig(self.circle, fill=CLR["accent"]), add="+")
        self.bind("<Enter>", lambda e: self.itemconfig(self.letter, fill="#101218"), add="+")
        self.bind("<Leave>", lambda e: self.itemconfig(self.circle, fill=CLR["panel2"]), add="+")
        self.bind("<Leave>", lambda e: self.itemconfig(self.letter, fill=CLR["accent"]), add="+")

    def popup(self, _=None):
        win = tk.Toplevel(self)
        win.title("Ajuda - %s" % self.title_txt)
        win.configure(bg=CLR["panel"])
        win.geometry("560x320")
        win.transient(self.winfo_toplevel())
        tk.Label(win, text=self.title_txt, bg=CLR["panel"], fg=CLR["accent"],
                 font=FONT_H, anchor="w").pack(fill="x", padx=16, pady=(14, 6))
        frm = tk.Frame(win, bg=CLR["panel"])
        frm.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        txt = tk.Text(frm, wrap="word", bg=CLR["field"], fg=CLR["fg"], bd=0,
                      font=FONT, padx=12, pady=10, relief="flat",
                      insertbackground=CLR["fg"])
        sb = ttk.Scrollbar(frm, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        txt.insert("1.0", self.text)
        txt.configure(state="disabled")
        ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=(0, 14))


class ScrollFrame(tk.Frame):
    """Area rolavel com roda do mouse (Windows e Linux)."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CLR["panel"], **kw)
        self.canvas = tk.Canvas(self, bg=CLR["panel"], highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=CLR["panel"])
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_conf)
        self.canvas.bind("<Configure>", self._on_canvas)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, self._wheel, add="+")

    def _on_conf(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self.win, width=e.width)

    def _wheel(self, e):
        try:
            if not str(self.canvas.winfo_containing(e.x_root, e.y_root)).startswith(str(self.canvas)):
                pass
        except Exception:
            pass
        if getattr(e, "num", None) == 4:
            delta = -1
        elif getattr(e, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if e.delta > 0 else 1
        try:
            self.canvas.yview_scroll(delta, "units")
        except Exception:
            pass


def style_app(root):
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure(".", background=CLR["panel"], foreground=CLR["fg"], font=FONT,
                 fieldbackground=CLR["field"], bordercolor=CLR["line"])
    st.configure("TFrame", background=CLR["panel"])
    st.configure("TLabel", background=CLR["panel"], foreground=CLR["fg"])
    st.configure("Dim.TLabel", background=CLR["panel"], foreground=CLR["fg_dim"])
    st.configure("Head.TLabel", background=CLR["panel"], foreground=CLR["accent"], font=FONT_H)
    st.configure("TButton", background=CLR["panel2"], foreground=CLR["fg"],
                 borderwidth=1, focusthickness=0, padding=(10, 5))
    st.map("TButton", background=[("active", CLR["accent"]), ("pressed", CLR["accent"])],
           foreground=[("active", "#0e1016"), ("pressed", "#0e1016")])
    st.configure("Accent.TButton", background=CLR["accent"], foreground="#0e1016", font=FONT_B)
    st.map("Accent.TButton", background=[("active", "#7bbcff")])
    st.configure("Treeview", background=CLR["field"], fieldbackground=CLR["field"],
                 foreground=CLR["fg"], rowheight=22, borderwidth=0, font=FONT)
    st.configure("Treeview.Heading", background=CLR["panel2"], foreground=CLR["accent"],
                 font=FONT_B, relief="flat")
    st.map("Treeview", background=[("selected", CLR["accent"])],
           foreground=[("selected", "#0e1016")])
    st.map("Treeview.Heading", background=[("active", CLR["line"])])
    st.configure("TNotebook", background=CLR["bg"], borderwidth=0)
    st.configure("TNotebook.Tab", background=CLR["panel2"], foreground=CLR["fg_dim"],
                 padding=(14, 7), borderwidth=0)
    st.map("TNotebook.Tab", background=[("selected", CLR["panel"])],
           foreground=[("selected", CLR["accent"])])
    st.configure("TCombobox", fieldbackground=CLR["field"], background=CLR["panel2"],
                 foreground=CLR["fg"], arrowcolor=CLR["accent"], selectbackground=CLR["field"],
                 selectforeground=CLR["fg"], padding=4)
    st.map("TCombobox", fieldbackground=[("readonly", CLR["field"])])
    st.configure("TEntry", fieldbackground=CLR["field"], foreground=CLR["fg"],
                 insertcolor=CLR["fg"], padding=4)
    st.configure("TSpinbox", fieldbackground=CLR["field"], foreground=CLR["fg"],
                 arrowcolor=CLR["accent"], padding=3)
    st.configure("TCheckbutton", background=CLR["panel"], foreground=CLR["fg"])
    st.map("TCheckbutton", background=[("active", CLR["panel"])])
    st.configure("TScale", background=CLR["panel"], troughcolor=CLR["field"])
    st.configure("Vertical.TScrollbar", background=CLR["panel2"], troughcolor=CLR["bg"],
                 arrowcolor=CLR["fg_dim"], bordercolor=CLR["bg"], darkcolor=CLR["panel2"],
                 lightcolor=CLR["panel2"])
    st.configure("Horizontal.TScrollbar", background=CLR["panel2"], troughcolor=CLR["bg"],
                 arrowcolor=CLR["fg_dim"])
    st.configure("TLabelframe", background=CLR["panel"], foreground=CLR["accent"],
                 bordercolor=CLR["line"])
    st.configure("TLabelframe.Label", background=CLR["panel"], foreground=CLR["accent"], font=FONT_B)
    root.option_add("*TCombobox*Listbox.background", CLR["field"])
    root.option_add("*TCombobox*Listbox.foreground", CLR["fg"])
    root.option_add("*TCombobox*Listbox.selectBackground", CLR["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#0e1016")
    root.option_add("*TCombobox*Listbox.font", FONT)
    return st


def make_text(parent, height=3, mono=False):
    t = tk.Text(parent, height=height, wrap="word", bg=CLR["field"], fg=CLR["fg"],
                insertbackground=CLR["accent"], relief="flat", bd=0,
                font=FONT_MONO if mono else FONT, padx=8, pady=6,
                selectbackground=CLR["accent"], selectforeground="#0e1016")
    return t

# ============================================================================
#  APLICACAO
# ============================================================================

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("%s  v%s" % (APP_NAME, APP_VERSION))
        self.geometry("1320x880")
        self.minsize(1060, 680)
        self.configure(bg=CLR["bg"])
        style_app(self)

        self.vars: dict[str, tk.Variable] = {}
        self.texts: dict[str, tk.Text] = {}
        self.checks: dict[str, dict[str, tk.BooleanVar]] = {}
        self.beats: list[dict] = default_beats()
        self.beat_vars: list[dict] = []
        self.out_cache: dict[str, str] = {}
        self.hint_updaters: list = []
        self.pending: dict[str, tk.BooleanVar] = {}
        self.snap = None            # projeto 'como foi gerado' (base das trocas)
        self.out_dirty = False      # o texto da saida foi editado a mao?
        self._prog = False
        self.apply_btns: dict[str, ttk.Button] = {}
        self.field_labels: dict[str, tk.Label] = {}
        self.field_tab: dict[str, str] = {}

        os.makedirs(PRESET_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self._build_menu()
        self._build_toolbar()

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(6, 4))

        for tabname in ["Personagem", "Ambiente", "Camera", "Luz & Cor", "Audio & Voz", "Motor de IA",
                        "Referencias", "Marca"]:
            self._build_field_tab(tabname)
        self._build_script_tab()
        self._build_dict_tab()
        self._build_import_tab()
        self._build_formula_tab()
        self._build_output_tab()

        self.status = tk.Label(self, text="Pronto.", anchor="w", bg=CLR["panel2"],
                               fg=CLR["fg_dim"], font=FONT, padx=12, pady=5)
        self.status.pack(fill="x", side="bottom")

        self.apply_preset("Vlog UGC", silent=True)
        self.set_pending(DEFAULT_PENDING)
        self.render_beats()
        self.after(900, self._poll_changes)
        self.say("Preset inicial 'Vlog UGC' carregado. Altere um campo e clique em GERAR PROMPT.")

    # ------------------------------------------------------------------ util
    def say(self, msg, color=None):
        self.status.configure(text=msg, fg=color or CLR["fg_dim"])

    # ------------------------------------------------------------------ menu
    def _build_menu(self):
        m = tk.Menu(self, bg=CLR["panel"], fg=CLR["fg"], activebackground=CLR["accent"],
                    activeforeground="#0e1016", bd=0)

        arq = tk.Menu(m, tearoff=0, bg=CLR["panel"], fg=CLR["fg"],
                      activebackground=CLR["accent"], activeforeground="#0e1016")
        arq.add_command(label="Novo projeto (limpar)", command=self.new_project)
        arq.add_command(label="Abrir projeto/preset .json...", command=self.load_preset_file)
        arq.add_command(label="Salvar projeto/preset .json...", command=self.save_preset_file)
        arq.add_command(label="Historico de versoes geradas...", command=self.show_history)
        arq.add_separator()
        arq.add_command(label="Exportar prompt .txt...", command=self.export_txt)
        arq.add_command(label="Exportar todos os formatos (9:16, 1:1, 16:9) + versao B...", command=self.export_multi)
        arq.add_command(label="Exportar projeto completo .json...", command=self.export_json)
        arq.add_separator()
        arq.add_command(label="Sair", command=self.destroy)
        m.add_cascade(label="Arquivo", menu=arq)

        pre = tk.Menu(m, tearoff=0, bg=CLR["panel"], fg=CLR["fg"],
                      activebackground=CLR["accent"], activeforeground="#0e1016")
        for name in BUILTIN_PRESETS:
            pre.add_command(label=name, command=lambda n=name: self.apply_preset(n))
        m.add_cascade(label="Presets", menu=pre)

        fer = tk.Menu(m, tearoff=0, bg=CLR["panel"], fg=CLR["fg"],
                      activebackground=CLR["accent"], activeforeground="#0e1016")
        fer.add_command(label="Lucky Roll (sorteio cinematografico)", command=self.lucky_roll)
        fer.add_command(label="Gerar nova seed aleatoria", command=self.random_seed)
        fer.add_command(label="↻ Aplicar todas as mudancas no prompt pronto", command=self.apply_changes)
        fer.add_command(label="Verificar antes de gerar (checklist)", command=lambda: (self.nb.select(self.nb.index("end") - 1), self.generate(switch=False)))
        fer.add_command(label="⚑ Ver campos pendentes...", command=self.show_pending)
        fer.add_command(label="⚑ Marcar TODOS os campos como pendentes (modelo em branco)", command=self.mark_all_pending)
        fer.add_command(label="⚑ Remover todas as marcacoes", command=self.clear_all_pending)
        fer.add_separator()
        fer.add_command(label="Restaurar blocos narrativos padrao", command=self.reset_beats)
        fer.add_command(label="Restaurar template da formula", command=self.reset_template)
        m.add_cascade(label="Ferramentas", menu=fer)

        aju = tk.Menu(m, tearoff=0, bg=CLR["panel"], fg=CLR["fg"],
                      activebackground=CLR["accent"], activeforeground="#0e1016")
        aju.add_command(label="Guia rapido", command=self.show_guide)
        aju.add_command(label="Sobre", command=lambda: messagebox.showinfo(
            "Sobre", "%s v%s\nCompilador de prompts cinematograficos.\nPython + tkinter, sem dependencias externas."
            % (APP_NAME, APP_VERSION)))
        m.add_cascade(label="Ajuda", menu=aju)
        self.configure(menu=m)

    # --------------------------------------------------------------- toolbar
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=CLR["bg"])
        bar.pack(fill="x", padx=10, pady=(10, 0))

        tk.Label(bar, text="GERADOR DE PROMPT UNIVERSAL", bg=CLR["bg"], fg=CLR["fg"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        ttk.Button(bar, text="⚡ GERAR PROMPT", style="Accent.TButton",
                   command=lambda: self.generate(save=True)).pack(side="right", padx=(8, 0))
        ttk.Button(bar, text="🎲 Lucky Roll", command=self.lucky_roll).pack(side="right", padx=4)
        ttk.Button(bar, text="↻ Aplicar", command=self.apply_changes).pack(side="right", padx=4)
        self.change_lbl = tk.Label(bar, text="", bg=CLR["bg"], fg=CLR["accent2"], font=FONT_B)
        self.change_lbl.pack(side="right", padx=4)
        self.pend_btn = ttk.Button(bar, text="⚑ Pendentes: 0", command=self.show_pending)
        self.pend_btn.pack(side="right", padx=4)

        self.preset_var = tk.StringVar(value="Vlog UGC")
        cb = ttk.Combobox(bar, textvariable=self.preset_var, width=20, state="readonly",
                          values=list(BUILTIN_PRESETS.keys()))
        cb.pack(side="right", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.apply_preset(self.preset_var.get()))
        tk.Label(bar, text="Preset:", bg=CLR["bg"], fg=CLR["fg_dim"], font=FONT).pack(side="right")

    # ----------------------------------------------------------- abas campos
    def _build_field_tab(self, tabname):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text=tabname)
        for tname, section_title, fields in SECTIONS:
            if tname != tabname:
                continue
            box = ttk.Labelframe(sf.inner, text="  %s  " % section_title)
            box.pack(fill="x", expand=False, padx=12, pady=(12, 4))
            grid = tk.Frame(box, bg=CLR["panel"])
            grid.pack(fill="x", padx=6, pady=8)
            grid.columnconfigure(1, weight=1)
            for r, f in enumerate(fields):
                self.field_tab[f.id] = tabname
                self._build_field_row(grid, f, r)

    def _build_field_row(self, grid, f: Field, r: int):
        left = tk.Frame(grid, bg=CLR["panel"])
        left.grid(row=r * 2, column=0, sticky="nw", padx=(6, 12), pady=(8, 0))
        lab = tk.Label(left, text=f.label, bg=CLR["panel"], fg=CLR["fg"], font=FONT_B,
                       anchor="w", justify="left", wraplength=230)
        lab.pack(side="left")
        InfoIcon(left, f.label, f.info).pack(side="left", padx=(6, 0))
        self.field_labels[f.id] = lab
        ap = ttk.Button(grid, text="Aplicar", width=9, command=lambda _id=f.id: self.apply_changes(only={_id}))
        ap.grid(row=r * 2, column=2, sticky="ne", padx=(0, 8), pady=(7, 0))
        self.apply_btns[f.id] = ap
        Tooltip(ap, "Aplicar SO esta mudanca no prompt pronto: troca o texto antigo pelo novo em todas as cenas, "
                    "sem refazer o resto nem perder o que voce editou a mao na aba Saida.")
        pv = tk.BooleanVar(value=(f.id in DEFAULT_PENDING))
        self.pending[f.id] = pv
        pk = tk.Checkbutton(left, text="⚑", variable=pv, bg=CLR["panel"], fg=CLR["accent2"],
                            activebackground=CLR["panel"], activeforeground=CLR["accent2"],
                            selectcolor=CLR["field"], bd=0, highlightthickness=0, cursor="hand2",
                            font=FONT_B, command=lambda _id=f.id: self._pending_changed(_id))
        pk.pack(side="left", padx=(8, 0))
        Tooltip(pk, "⚑ Preencher depois\nMarcado: o campo fica FORA do prompt e entra na lista de pendencias.\n"
                    "Desmarque quando quiser usar. Ao digitar no campo, a marca sai sozinha.")
        self._pending_changed(f.id)

        cell = tk.Frame(grid, bg=CLR["panel"])
        cell.grid(row=r * 2, column=1, sticky="ew", padx=(0, 10), pady=(8, 0))
        cell.columnconfigure(0, weight=1)

        hint = tk.Label(grid, text="", bg=CLR["panel"], fg=CLR["fg_dim"], font=("Segoe UI", 8),
                        anchor="w", justify="left", wraplength=820)
        hint.grid(row=r * 2 + 1, column=1, sticky="ew", padx=(2, 10), pady=(1, 6))

        kind = f.kind
        if kind == "combo":
            var = tk.StringVar(value=str(f.default))
            cb = ttk.Combobox(cell, textvariable=var, values=opt_list(f.src))
            cb.grid(row=0, column=0, sticky="ew")
            self.vars[f.id] = var

            def upd(*_a, _f=f, _v=var, _h=hint):
                info = opt_info(_f.src, _v.get())
                _h.configure(text=("↳ " + info) if info else "↳ valor personalizado (sera usado como esta no prompt)")
                if _f.id == "negative_preset":
                    self.set_text("negative", NEGATIVE_PRESETS.get(_v.get(), NEGATIVE_BASE))
            cb.bind("<<ComboboxSelected>>", upd)
            cb.bind("<KeyRelease>", upd)
            cb.bind("<<ComboboxSelected>>", lambda e, _id=f.id: self._touch(_id), add="+")
            cb.bind("<KeyRelease>", lambda e, _id=f.id: self._touch(_id), add="+")
            self.hint_updaters.append(upd)
            upd()

        elif kind == "entry":
            var = tk.StringVar(value=str(f.default))
            ent = ttk.Entry(cell, textvariable=var)
            ent.grid(row=0, column=0, sticky="ew")
            ent.bind("<KeyRelease>", lambda e, _id=f.id: self._touch(_id), add="+")
            self.vars[f.id] = var
            hint.grid_remove()

        elif kind == "text":
            t = make_text(cell, height=4 if f.id in ("negative", "char_desc") else 3)
            t.grid(row=0, column=0, sticky="ew")
            t.insert("1.0", str(f.default))
            t.bind("<KeyRelease>", lambda e, _id=f.id: self._touch(_id), add="+")
            self.texts[f.id] = t
            hint.grid_remove()

        elif kind == "checks":
            holder = tk.Frame(cell, bg=CLR["panel"])
            holder.grid(row=0, column=0, sticky="ew")
            self.checks[f.id] = {}
            opts = OPTIONS.get(f.src, [])
            cols = 2
            for i, o in enumerate(opts):
                bv = tk.BooleanVar(value=(o.label == f.default))
                self.checks[f.id][o.label] = bv
                cell_f = tk.Frame(holder, bg=CLR["panel"])
                cell_f.grid(row=i // cols, column=i % cols, sticky="w", padx=(0, 14), pady=1)
                ttk.Checkbutton(cell_f, text=o.label, variable=bv,
                                command=lambda _id=f.id: self._touch(_id)).pack(side="left")
                InfoIcon(cell_f, o.label, o.info, size=13).pack(side="left", padx=(4, 0))
            hint.configure(text="↳ marque as opcoes que devem entrar no prompt")

        elif kind == "scale":
            lo, hi = f.src
            var = tk.IntVar(value=int(f.default))
            row = tk.Frame(cell, bg=CLR["panel"])
            row.grid(row=0, column=0, sticky="ew")
            row.columnconfigure(0, weight=1)
            val = tk.Label(row, text=str(f.default), bg=CLR["panel"], fg=CLR["accent"],
                           font=FONT_B, width=5)
            sc = ttk.Scale(row, from_=lo, to=hi, orient="horizontal",
                           command=lambda v, _v=var, _l=val, _id=f.id: (
                               _v.set(int(float(v))), _l.configure(text=str(int(float(v)))), self._touch(_id)))
            sc.set(int(f.default))
            sc.grid(row=0, column=0, sticky="ew")
            val.grid(row=0, column=1, padx=(8, 0))
            self.vars[f.id] = var
            hint.grid_remove()

        elif kind == "spin":
            lo, hi = f.src
            var = tk.IntVar(value=int(f.default))
            ttk.Spinbox(cell, from_=lo, to=hi, textvariable=var, width=8).grid(row=0, column=0, sticky="w")
            self.vars[f.id] = var
            hint.grid_remove()

        elif kind == "check":
            var = tk.BooleanVar(value=bool(f.default))
            ttk.Checkbutton(cell, text="ativado", variable=var).grid(row=0, column=0, sticky="w")
            self.vars[f.id] = var
            hint.grid_remove()

    # ------------------------------------------------------------ pendencias ⚑
    def _pending_changed(self, fid):
        lab = self.field_labels.get(fid)
        on = bool(self.pending[fid].get()) if fid in self.pending else False
        if lab is not None:
            lab.configure(fg=CLR["accent2"] if on else CLR["fg"])
        self._update_pending_count()

    def _touch(self, fid):
        """O usuario mexeu no campo: tira a marca ⚑ sozinha (senao o valor seria ignorado)."""
        pv = self.pending.get(fid)
        if pv is not None and pv.get():
            pv.set(False)
            self._pending_changed(fid)

    def _update_pending_count(self):
        n = sum(1 for v in self.pending.values() if v.get())
        if hasattr(self, "pend_btn"):
            self.pend_btn.configure(text="⚑ Pendentes: %d" % n)

    def set_pending(self, ids):
        ids = set(ids)
        for fid, pv in self.pending.items():
            pv.set(fid in ids)
            self._pending_changed(fid)

    def mark_all_pending(self):
        keep = {"translate", "seed_lock", "negative_preset", "subject_type"}
        self.set_pending([fid for fid in FIELD_BY_ID if fid not in keep])
        self.say("Todos os campos marcados como ⚑ pendentes. Desmarque so os que quiser usar.", CLR["accent2"])

    def clear_all_pending(self):
        self.set_pending([])
        self.say("Marcacoes ⚑ removidas: todos os campos preenchidos entram no prompt.", CLR["ok"])

    def show_pending(self):
        win = tk.Toplevel(self)
        win.title("Campos pendentes (⚑)")
        win.geometry("560x520")
        win.configure(bg=CLR["panel"])
        tk.Label(win, text="Campos marcados para preencher depois (ficam fora do prompt).\n"
                           "Duplo clique: ir ate o campo.", bg=CLR["panel"], fg=CLR["fg_dim"],
                 font=FONT, justify="left").pack(anchor="w", padx=14, pady=(12, 6))
        lb = tk.Listbox(win, bg=CLR["field"], fg=CLR["fg"], font=FONT, selectbackground=CLR["accent"],
                        selectforeground="#0e1016", bd=0, highlightthickness=0, activestyle="none")
        lb.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        items = [(self.field_tab.get(fid, "?"), FIELD_BY_ID[fid].label, fid)
                 for fid, pv in self.pending.items() if pv.get()]
        for tab, label, _fid in items:
            lb.insert("end", "%-22s  %s" % (tab, label))
        if not items:
            lb.insert("end", "(nenhum campo pendente)")

        def go(_e=None):
            sel = lb.curselection()
            if not sel or not items:
                return
            tab = items[sel[0]][0]
            for i in range(self.nb.index("end")):
                if self.nb.tab(i, "text") == tab:
                    self.nb.select(i)
                    break
        lb.bind("<Double-Button-1>", go)

    # ------------------------------------------------------------ estado
    def set_text(self, fid, value):
        t = self.texts.get(fid)
        if t is not None:
            t.delete("1.0", "end")
            t.insert("1.0", value)

    def get_state(self) -> dict:
        st = {}
        for fid, f in FIELD_BY_ID.items():
            if f.kind == "text":
                st[fid] = self.texts[fid].get("1.0", "end-1c").strip() if fid in self.texts else ""
            elif f.kind == "checks":
                st[fid] = [lbl for lbl, v in self.checks.get(fid, {}).items() if v.get()]
            elif fid in self.vars:
                st[fid] = self.vars[fid].get()
            else:
                st[fid] = f.default
        st["_pending"] = [fid for fid, pv in self.pending.items() if pv.get()]
        return st

    def set_state(self, data: dict):
        if data and "_pending" in data:
            self.set_pending(data["_pending"] or [])
        for fid, val in (data or {}).items():
            f = FIELD_BY_ID.get(fid)
            if not f:
                continue
            if f.kind == "text":
                self.set_text(fid, str(val))
            elif f.kind == "checks":
                for lbl, v in self.checks.get(fid, {}).items():
                    v.set(lbl in (val if isinstance(val, (list, tuple)) else [val]))
            elif fid in self.vars:
                try:
                    self.vars[fid].set(val)
                except Exception:
                    pass
        self.refresh_hints()

    def refresh_hints(self):
        """Reaplica as explicacoes dos combos (apos troca de preset/sorteio)."""
        for fn in self.hint_updaters:
            try:
                fn()
            except Exception:
                pass

    # =================================================================== ROTEIRO
    def _build_script_tab(self):
        wrap = tk.Frame(self.nb, bg=CLR["panel"])
        self.nb.add(wrap, text="Roteiro ⚡")

        top = tk.Frame(wrap, bg=CLR["panel2"])
        top.pack(fill="x")
        inner = tk.Frame(top, bg=CLR["panel2"])
        inner.pack(fill="x", padx=12, pady=8)
        tk.Label(inner, text="ROTEIRO POR PALAVRA-CHAVE", bg=CLR["panel2"], fg=CLR["accent"],
                 font=FONT_H).pack(side="left")
        InfoIcon(inner, "Como funciona o roteiro",
                 "Cada bloco abaixo e uma CENA. Voce escreve a palavra-chave ou frase "
                 "(ex: 'celular', 'copo de agua') e na FRENTE dela escolhe a camera: enquadramento "
                 "(rosto e olhos, busto, meio corpo, corpo inteiro, pernas, barriga...), angulo, "
                 "movimento, lente e acao.\n\n"
                 "Essa escolha define como AQUELA cena sera gravada - e e ela que entra no prompt final "
                 "daquela cena, sobrescrevendo o padrao da aba Camera.\n\n"
                 "Palavras-chave ja cadastradas no programa (celular, copo de agua, perfume, batom, tenis, "
                 "notebook, carro, cabelo, olhos, barriga, pernas, busto, produto, comida...) disparam a "
                 "sugestao automatica de camera. Enquanto 'auto' estiver marcado a sugestao e aplicada; "
                 "ao escolher manualmente um enquadramento o 'auto' desliga e a sua escolha manda.").pack(side="left", padx=8)

        ttk.Button(inner, text="↻ Aplicar mudanças no prompt", command=self.apply_changes).pack(side="right", padx=4)
        ttk.Button(inner, text="+ Adicionar cena", command=self.add_beat).pack(side="right", padx=4)
        ttk.Button(inner, text="Blocos padrao", command=self.reset_beats).pack(side="right", padx=4)
        ttk.Button(inner, text="Limpar roteiro", command=self.clear_beats).pack(side="right", padx=4)

        tk.Label(wrap, text="Palavras-chave cadastradas: " + ", ".join(sorted(KEYWORD_TRIGGERS)[:28]) + " ... (veja e edite todas na aba Dicionario)",
                 bg=CLR["panel"], fg=CLR["fg_dim"], font=("Segoe UI", 8), anchor="w",
                 wraplength=1250, justify="left").pack(fill="x", padx=14, pady=(6, 0))

        self.script_sf = ScrollFrame(wrap)
        self.script_sf.pack(fill="both", expand=True, padx=4, pady=6)

    # ------------------------------------------------------------ importar
    def _build_import_tab(self):
        wrap = tk.Frame(self.nb, bg=CLR["panel"])
        self.nb.add(wrap, text="Importar")
        top = tk.Frame(wrap, bg=CLR["panel2"])
        top.pack(fill="x")
        inner = tk.Frame(top, bg=CLR["panel2"])
        inner.pack(fill="x", padx=12, pady=8)
        tk.Label(inner, text="IMPORTAR PROMPT PRONTO", bg=CLR["panel2"], fg=CLR["accent"], font=FONT_H).pack(side="left")
        InfoIcon(inner, "Importar um prompt existente",
                 "Cole (ou abra de um .txt) um prompt que voce ja tem, em portugues ou ingles. O programa le o texto "
                 "e distribui nos campos: enquadramento, angulo, lente, abertura, luz, cor, estilo, proporcao, fps, "
                 "seed, negative, personagem, roupa, cenario...\n\n"
                 "Se o arquivo tiver varios prompts (separados por ----, por 'portugues'/'english' ou por titulos "
                 "numerados), escolha qual importar.\n\n"
                 "O que for reconhecido preenche o campo certo. O que nao for vai para 'Trechos livres', entao nada se perde. "
                 "Os campos NAO reconhecidos podem ficar marcados com ⚑ para voce preencher depois.\n\n"
                 "Depois de importar, mude so o que quiser (personagem, camera, luz...) e o prompt se refaz inteiro.\n\n"
                 "Resultados marcados '~aproximado' foram deduzidos por palavras: confira.").pack(side="left", padx=8)

        bar = tk.Frame(wrap, bg=CLR["panel"])
        bar.pack(fill="x", padx=12, pady=(8, 2))
        ttk.Button(bar, text="Colar da area de transferencia", command=self.import_paste).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Abrir .txt...", command=self.import_open).pack(side="left", padx=6)
        ttk.Button(bar, text="Limpar", command=lambda: self.imp_text.delete("1.0", "end")).pack(side="left", padx=6)
        tk.Label(bar, text="Prompt a importar:", bg=CLR["panel"], fg=CLR["fg"], font=FONT).pack(side="left", padx=(16, 4))
        self.imp_pick = tk.StringVar()
        self.imp_combo = ttk.Combobox(bar, textvariable=self.imp_pick, state="readonly", width=60, values=[])
        self.imp_combo.pack(side="left", fill="x", expand=True)

        h = tk.Frame(wrap, bg=CLR["panel"])
        h.pack(fill="both", expand=True, padx=12, pady=6)
        h.columnconfigure(0, weight=1)
        h.columnconfigure(1, weight=1)
        h.rowconfigure(1, weight=1)
        tk.Label(h, text="Seu prompt (pode editar aqui)", bg=CLR["panel"], fg=CLR["fg_dim"], font=FONT).grid(row=0, column=0, sticky="w")
        tk.Label(h, text="O que o programa entendeu", bg=CLR["panel"], fg=CLR["fg_dim"], font=FONT).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.imp_text = make_text(h, height=14)
        self.imp_text.grid(row=1, column=0, sticky="nsew")
        self.imp_report = make_text(h, height=14, mono=True)
        self.imp_report.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        self.imp_report.configure(state="disabled")

        opt = tk.Frame(wrap, bg=CLR["panel"])
        opt.pack(fill="x", padx=12, pady=(0, 4))
        self.imp_clear = tk.BooleanVar(value=True)
        self.imp_mark = tk.BooleanVar(value=True)
        self.imp_beats = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt, text="Esvaziar os campos que nao foram reconhecidos", variable=self.imp_clear).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(opt, text="Marcar esses campos como ⚑ pendentes", variable=self.imp_mark).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(opt, text="Trocar o roteiro por 1 cena so (sem gatilhos)", variable=self.imp_beats).pack(side="left")
        act = tk.Frame(wrap, bg=CLR["panel"])
        act.pack(fill="x", padx=12, pady=(2, 12))
        ttk.Button(act, text="Analisar e preencher campos", style="Accent.TButton", command=self.import_apply).pack(side="left")
        ttk.Button(act, text="Enviar texto para a Saida (editar livre)", command=self.import_to_output).pack(side="left", padx=10)
        self._imp_blocks = []
        self.imp_combo.bind("<<ComboboxSelected>>", self.import_choose)

    def import_paste(self):
        try:
            txt = self.clipboard_get()
        except Exception:
            messagebox.showinfo("Importar", "A area de transferencia esta vazia.")
            return
        self.imp_text.delete("1.0", "end")
        self.imp_text.insert("1.0", txt)
        self.import_detect()

    def import_open(self):
        path = filedialog.askopenfilename(filetypes=[("Texto", "*.txt *.md"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8-sig") as fh:
                txt = fh.read()
        except Exception as exc:
            messagebox.showerror("Importar", "Nao foi possivel ler o arquivo:\n%s" % exc)
            return
        self.imp_text.delete("1.0", "end")
        self.imp_text.insert("1.0", txt)
        self.import_detect()

    def import_detect(self):
        """Separa varios prompts do texto e preenche a lista de escolha."""
        self._imp_blocks = split_prompts(self.imp_text.get("1.0", "end-1c"))
        labels = ["%d - [%s] %s" % (i + 1, detect_lang(b).upper(), re.sub(r"\s+", " ", b)[:70] + "...")
                  for i, b in enumerate(self._imp_blocks)]
        self.imp_combo.configure(values=labels)
        if labels:
            self.imp_combo.current(0)
        self.say("%d prompt(s) encontrado(s) no texto." % len(labels), CLR["ok"] if labels else CLR["warn"])

    def import_choose(self, _e=None):
        pass

    def _imp_selected(self) -> str:
        if not self._imp_blocks:
            self.import_detect()
        idx = self.imp_combo.current()
        if idx < 0 or idx >= len(self._imp_blocks):
            return ""
        return self._imp_blocks[idx]

    def import_apply(self):
        # se o usuario editou o texto depois da deteccao, redetecta
        if "\n".join(self._imp_blocks) != "\n".join(split_prompts(self.imp_text.get("1.0", "end-1c"))):
            self.import_detect()
        block = self._imp_selected()
        if not block.strip():
            messagebox.showinfo("Importar", "Cole ou abra um prompt primeiro.")
            return
        res = parse_prompt(block)
        found = dict(res["fields"])
        notes = " | ".join(res["leftover"])
        if notes:
            found["free_notes"] = notes
        # 1) esvazia o que nao foi reconhecido
        keep = {"translate", "seed_lock", "negative_preset", "subject_type", "motion", "consistency", "duration",
                "ref_weight"}
        if self.imp_clear.get():
            blank = {}
            for fid, f in FIELD_BY_ID.items():
                if fid in found or fid in keep:
                    continue
                blank[fid] = [] if f.kind == "checks" else ("" if f.kind in ("entry", "text", "combo") else f.default)
            self.set_state(blank)
        # 2) preenche
        fill = dict(found)
        fill["translate"] = (res["lang"] == "pt")
        self.set_state(fill)
        if self.imp_beats.get():
            self.beats = [new_beat("Cena 1 (importada)", "Cena criada pelo Importador: usa so os campos preenchidos.")]
            self.render_beats()
        # 3) pendencias
        if self.imp_mark.get():
            self.set_pending([fid for fid in FIELD_BY_ID if fid not in found and fid not in keep])
        else:
            for fid in found:
                if fid in self.pending:
                    self.pending[fid].set(False)
                    self._pending_changed(fid)
        # 4) relatorio
        lines = ["Idioma detectado: %s%s" % (res["lang"].upper(),
                 "  (tradutor ligado)" if res["lang"] == "pt" else "  (tradutor desligado: o texto ja esta em ingles)"),
                 "", "RECONHECIDO (%d campos):" % len(res["recognized"])]
        for label, val, how in res["recognized"]:
            lines.append("  ✓ %s\n      = %s\n      (%s)" % (label, val if len(val) < 140 else val[:137] + "...", how))
        lines += ["", "SEM CAMPO PROPRIO -> 'Trechos livres':"] + (["  • " + x for x in res["leftover"]] or ["  (nada)"])
        lines += ["", "Confira a lista acima: itens '~aproximado' foram deduzidos por palavras."]
        self.imp_report.configure(state="normal")
        self.imp_report.delete("1.0", "end")
        self.imp_report.insert("1.0", "\n".join(lines))
        self.imp_report.configure(state="disabled")
        self.say("Importado: %d campos preenchidos, %d trecho(s) em 'Trechos livres'. Edite o que quiser e gere."
                 % (len(res["recognized"]), len(res["leftover"])), CLR["ok"])

    def import_to_output(self):
        block = self._imp_selected() or self.imp_text.get("1.0", "end-1c")
        self.snap = None
        self.set_out(block)
        self.nb.select(self.nb.index("end") - 1)
        self.say("Texto enviado para a Saida: edite livremente e use Copiar / Salvar .txt.", CLR["ok"])

    # ------------------------------------------------------------ dicionario
    def _build_dict_tab(self):
        wrap = tk.Frame(self.nb, bg=CLR["panel"])
        self.nb.add(wrap, text="Dicionario")
        top = tk.Frame(wrap, bg=CLR["panel2"])
        top.pack(fill="x")
        inner = tk.Frame(top, bg=CLR["panel2"])
        inner.pack(fill="x", padx=12, pady=8)
        tk.Label(inner, text="DICIONARIO", bg=CLR["panel2"], fg=CLR["accent"], font=FONT_H).pack(side="left")
        InfoIcon(inner, "Dicionario de palavras",
                 "GATILHOS: palavra do roteiro -> enquadramento, lente, acao e detalhe extra aplicados "
                 "automaticamente na cena.\n\nGLOSSARIO: traducao PT -> EN usada pelo tradutor offline.\n\n"
                 "A base fica em dados/gatilhos.json e dados/glossario.json (versionada no Git). "
                 "As palavras que voce adiciona aqui ficam em dados/usuario.json (so no seu computador) "
                 "e sempre vencem a base. Remover uma palavra sua faz a da base voltar a valer.\n\n"
                 "A busca ignora acento, maiuscula e plural; a frase mais longa ganha "
                 "('copo de agua' vence 'copo').").pack(side="left", padx=8)
        ttk.Button(inner, text="Recarregar arquivos", command=self.dict_reload).pack(side="right", padx=4)

        bar = tk.Frame(wrap, bg=CLR["panel"])
        bar.pack(fill="x", padx=12, pady=(8, 2))
        self.dict_kind = tk.StringVar(value="gatilhos")
        for txt, val in (("Gatilhos (camera)", "gatilhos"), ("Glossario (traducao)", "glossario")):
            ttk.Radiobutton(bar, text=txt, value=val, variable=self.dict_kind,
                            command=self.dict_fill).pack(side="left", padx=(0, 10))
        tk.Label(bar, text="Buscar:", bg=CLR["panel"], fg=CLR["fg"], font=FONT).pack(side="left", padx=(12, 4))
        self.dict_q = tk.StringVar()
        self.dict_q.trace_add("write", lambda *_: self.dict_fill())
        ttk.Entry(bar, textvariable=self.dict_q, width=28).pack(side="left")
        self.dict_count = tk.Label(bar, text="", bg=CLR["panel"], fg=CLR["fg_dim"], font=FONT)
        self.dict_count.pack(side="right")

        cols = ("palavra", "campo1", "campo2", "campo3", "campo4", "origem")
        self.dict_tree = ttk.Treeview(wrap, columns=cols, show="headings", height=14)
        self.dict_tree.pack(fill="both", expand=True, padx=12, pady=6)
        self.dict_tree.bind("<<TreeviewSelect>>", self.dict_pick)

        ed = tk.Frame(wrap, bg=CLR["panel"])
        ed.pack(fill="x", padx=12, pady=(0, 10))
        self.dv = {k: tk.StringVar() for k in ("word", "f1", "f2", "f3", "f4")}
        self.dict_lbls = []
        self.dict_widgets = []
        tk.Label(ed, text="Palavra", bg=CLR["panel"], fg=CLR["fg"], font=FONT).grid(row=0, column=0, sticky="w")
        ttk.Entry(ed, textvariable=self.dv["word"]).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        for i in range(1, 5):
            lb = tk.Label(ed, text="", bg=CLR["panel"], fg=CLR["fg"], font=FONT)
            lb.grid(row=0, column=i, sticky="w")
            self.dict_lbls.append(lb)
            cb = ttk.Combobox(ed, textvariable=self.dv["f%d" % i])
            cb.grid(row=1, column=i, sticky="ew", padx=(0, 8))
            self.dict_widgets.append(cb)
            ed.columnconfigure(i, weight=1)
        ed.columnconfigure(0, weight=1)
        btns = tk.Frame(ed, bg=CLR["panel"])
        btns.grid(row=2, column=0, columnspan=5, sticky="w", pady=(8, 0))
        ttk.Button(btns, text="Salvar / adicionar", command=self.dict_save).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Remover (so as minhas)", command=self.dict_delete).pack(side="left", padx=6)
        ttk.Button(btns, text="Limpar campos", command=self.dict_clear).pack(side="left", padx=6)
        self.dict_fill()

    def dict_fill(self):
        kind = self.dict_kind.get()
        tree = self.dict_tree
        tree.delete(*tree.get_children())
        if kind == "gatilhos":
            heads = ("Palavra", "Enquadramento", "Lente", "Acao", "Detalhe extra (EN)", "Origem")
            lists = (opt_list("shot"), opt_list("lens"), opt_list("action"), [])
        else:
            heads = ("Palavra (PT)", "Traducao (EN)", "", "", "", "Origem")
            lists = ([], [], [], [])
        for col, h in zip(tree["columns"], heads):
            tree.heading(col, text=h)
            tree.column(col, width=60 if col == "origem" else 170, stretch=True)
        for i, lb in enumerate(self.dict_lbls):
            lb.configure(text=heads[i + 1] if heads[i + 1] else "")
            self.dict_widgets[i].configure(values=lists[i])
        q = _norm_key(self.dict_q.get())
        n = 0
        data = KEYWORD_TRIGGERS if kind == "gatilhos" else GLOSSARY
        mine = {_norm_key(k) for k in USER_DICT[kind]}
        for k in sorted(data):
            if q and q not in k:
                continue
            val = data[k]
            row = (k, val.shot, val.lens, val.action, val.extra) if kind == "gatilhos" else (k, val, "", "", "")
            tree.insert("", "end", values=row + ("meu" if k in mine else "base",))
            n += 1
        self.dict_count.configure(text="%d palavras" % n)

    def dict_pick(self, _e=None):
        sel = self.dict_tree.selection()
        if not sel:
            return
        vals = self.dict_tree.item(sel[0], "values")
        self.dv["word"].set(vals[0])
        for i in range(1, 5):
            self.dv["f%d" % i].set(vals[i])

    def dict_clear(self):
        for var in self.dv.values():
            var.set("")

    def dict_save(self):
        kind = self.dict_kind.get()
        word = _norm_key(self.dv["word"].get())
        if not word:
            messagebox.showwarning("Dicionario", "Digite a palavra.")
            return
        if kind == "gatilhos":
            shot, lens, action = (self.dv[k].get().strip() for k in ("f1", "f2", "f3"))
            if not (shot and lens and action):
                messagebox.showwarning("Dicionario", "Escolha enquadramento, lente e acao.")
                return
            USER_DICT["gatilhos"][word] = {"shot": shot, "lens": lens, "action": action,
                                           "extra": self.dv["f4"].get().strip()}
        else:
            en = self.dv["f1"].get().strip()
            if not en:
                messagebox.showwarning("Dicionario", "Digite a traducao em ingles.")
                return
            USER_DICT["glossario"][word] = en
        save_user_dict()
        load_dictionaries()
        self.dict_fill()
        self.status.configure(text="Dicionario: '%s' salvo em dados/usuario.json" % word)

    def dict_delete(self):
        kind = self.dict_kind.get()
        word = _norm_key(self.dv["word"].get())
        mine = {_norm_key(k): k for k in USER_DICT[kind]}
        if word not in mine:
            messagebox.showinfo("Dicionario", "Essa palavra nao e sua (e da base) - nada a remover.")
            return
        del USER_DICT[kind][mine[word]]
        save_user_dict()
        load_dictionaries()
        self.dict_fill()
        self.dict_clear()

    def dict_reload(self):
        load_dictionaries()
        self.dict_fill()
        msg = "Dicionarios recarregados."
        if DICT_WARNINGS:
            msg += "\nAvisos:\n" + "\n".join(DICT_WARNINGS)
        messagebox.showinfo("Dicionario", msg)

    def _lab(self, parent, text, info, row, col):
        f = tk.Frame(parent, bg=CLR["panel"])
        f.grid(row=row, column=col, sticky="w", padx=(6, 8), pady=4)
        tk.Label(f, text=text, bg=CLR["panel"], fg=CLR["fg"], font=FONT).pack(side="left")
        if info:
            InfoIcon(f, text, info, size=13).pack(side="left", padx=(4, 0))
        return f

    def render_beats(self):
        for w in self.script_sf.inner.winfo_children():
            w.destroy()
        self.beat_vars = []
        for i, b in enumerate(self.beats):
            self._beat_card(i, b)
        self.script_sf._on_conf()

    def _beat_card(self, i, b):
        card = ttk.Labelframe(self.script_sf.inner, text="  CENA %d  " % (i + 1))
        card.pack(fill="x", padx=12, pady=6)
        g = tk.Frame(card, bg=CLR["panel"])
        g.pack(fill="x", padx=6, pady=6)
        g.columnconfigure(1, weight=1)
        g.columnconfigure(3, weight=1)

        v = {
            "name": tk.StringVar(value=b.get("name", "")),
            "keyword": tk.StringVar(value=b.get("keyword", "")),
            "shot": tk.StringVar(value=b.get("shot", "")),
            "angle": tk.StringVar(value=b.get("angle", "")),
            "move": tk.StringVar(value=b.get("move", "")),
            "lens": tk.StringVar(value=b.get("lens", "")),
            "action": tk.StringVar(value=b.get("action", "")),
            "vo": tk.StringVar(value=b.get("vo", "")),
            "extra": tk.StringVar(value=b.get("extra", "")),
            "dur": tk.IntVar(value=int(b.get("dur", 5) or 5)),
            "auto": tk.BooleanVar(value=bool(b.get("auto", True))),
            "transition": tk.StringVar(value=b.get("transition", "")),
            "text": tk.StringVar(value=b.get("text", "")),
        }
        self.beat_vars.append(v)

        # linha 0: nome do bloco + navegacao
        self._lab(g, "Bloco narrativo", b.get("info", "") or "Nome livre desta cena.", 0, 0)
        ttk.Entry(g, textvariable=v["name"]).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        nav = tk.Frame(g, bg=CLR["panel"])
        nav.grid(row=0, column=2, columnspan=2, sticky="e")
        ttk.Button(nav, text="▲", width=3, command=lambda idx=i: self.move_beat(idx, -1)).pack(side="left", padx=2)
        ttk.Button(nav, text="▼", width=3, command=lambda idx=i: self.move_beat(idx, 1)).pack(side="left", padx=2)
        ttk.Button(nav, text="✕", width=3, command=lambda idx=i: self.del_beat(idx)).pack(side="left", padx=2)

        # linha 1: palavra-chave + gatilho
        self._lab(g, "Palavra-chave / frase",
                  "A palavra ou frase do seu roteiro que esta cena mostra. Ex: 'celular', 'copo de agua', "
                  "'batom', 'tenis novo'. Ela entra no prompt como foco da cena e, se estiver cadastrada, "
                  "dispara automaticamente a escolha de camera.", 1, 0)
        kw = ttk.Entry(g, textvariable=v["keyword"])
        kw.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        hint = tk.Label(g, text="", bg=CLR["panel"], fg=CLR["fg_dim"], font=("Segoe UI", 8),
                        anchor="w", justify="left", wraplength=430)
        hint.grid(row=1, column=2, columnspan=2, sticky="ew")

        def on_kw(*_a):
            found, trig = find_trigger(v["keyword"].get())
            if trig:
                hint.configure(text="⚡ gatilho '%s' → %s | %s | %s" % (found, trig.shot, trig.lens, trig.action),
                               fg=CLR["ok"])
                if v["auto"].get():
                    v["shot"].set(trig.shot)
                    v["lens"].set(trig.lens)
                    v["action"].set(trig.action)
                    if trig.extra and not v["extra"].get():
                        v["extra"].set(trig.extra)
            else:
                hint.configure(text="sem gatilho cadastrado - escolha a camera manualmente ao lado",
                               fg=CLR["fg_dim"])
        kw.bind("<KeyRelease>", on_kw)
        kw.bind("<FocusOut>", on_kw)

        # linha 2: enquadramento + angulo
        self._lab(g, "Enquadramento (camera)",
                  "Como o corpo e cortado no quadro nesta cena: rosto e olhos, rosto, busto, meio corpo, "
                  "cowboy, corpo inteiro, barriga, pernas, pes, maos/produto, costas, POV ou insert de objeto. "
                  "Esta escolha sobrescreve o enquadramento padrao da aba Camera.", 2, 0)
        cb_shot = ttk.Combobox(g, textvariable=v["shot"], values=opt_list("shot"))
        cb_shot.grid(row=2, column=1, sticky="ew", padx=(0, 8))
        self._lab(g, "Angulo", "De onde a camera olha nesta cena.", 2, 2)
        ttk.Combobox(g, textvariable=v["angle"], values=opt_list("angle")).grid(row=2, column=3, sticky="ew", padx=(0, 8))

        def manual(*_a):
            v["auto"].set(False)
        cb_shot.bind("<<ComboboxSelected>>", manual)

        # linha 3: movimento + lente
        self._lab(g, "Movimento de camera", "Como a camera se move nesta cena. Vazio = usa o padrao da aba Camera.", 3, 0)
        ttk.Combobox(g, textvariable=v["move"], values=opt_list("camera_move")).grid(row=3, column=1, sticky="ew", padx=(0, 8))
        self._lab(g, "Lente (opcional)", "Trocar a lente so nesta cena. Vazio = usa a lente padrao.", 3, 2)
        ttk.Combobox(g, textvariable=v["lens"], values=opt_list("lens")).grid(row=3, column=3, sticky="ew", padx=(0, 8))

        # linha 4: acao + duracao + auto
        self._lab(g, "Acao / pose", "O que o personagem faz nesta cena. Vazio = usa a acao padrao.", 4, 0)
        ttk.Combobox(g, textvariable=v["action"], values=opt_list("action")).grid(row=4, column=1, sticky="ew", padx=(0, 8))
        right = tk.Frame(g, bg=CLR["panel"])
        right.grid(row=4, column=2, columnspan=2, sticky="w")
        tk.Label(right, text="Duracao (s)", bg=CLR["panel"], fg=CLR["fg"], font=FONT).pack(side="left", padx=(6, 6))
        ttk.Spinbox(right, from_=1, to=60, textvariable=v["dur"], width=6).pack(side="left")
        ttk.Checkbutton(right, text="auto-camera pelo gatilho", variable=v["auto"]).pack(side="left", padx=(14, 0))
        InfoIcon(right, "auto-camera",
                 "Marcado: a palavra-chave escolhe o enquadramento, a lente e a acao automaticamente. "
                 "Ao escolher um enquadramento na mao isto desliga sozinho e a sua escolha passa a mandar.",
                 size=13).pack(side="left", padx=(4, 0))

        # linha 5: fala
        self._lab(g, "Fala / locucao (PT)",
                  "O que e falado nesta cena, em portugues. Sai traduzido no prompt (se o tradutor estiver ligado) "
                  "e tambem fica salvo no JSON em portugues. Frases curtas funcionam melhor em lip-sync.", 5, 0)
        ttk.Entry(g, textvariable=v["vo"]).grid(row=5, column=1, columnspan=3, sticky="ew", padx=(0, 8))

        # linha 6: detalhe extra
        self._lab(g, "Detalhe visual extra",
                  "Um detalhe exclusivo desta cena: 'gotas de condensacao escorrendo no vidro', "
                  "'brilho da tela refletindo nos dedos'. E o que da realismo ao plano.", 6, 0)
        ttk.Entry(g, textvariable=v["extra"]).grid(row=6, column=1, columnspan=3, sticky="ew", padx=(0, 8))

        # linha 7: transicao + texto na tela (opcionais)
        self._lab(g, "Transicao p/ proxima cena",
                  "Como esta cena passa para a seguinte (corte seco, match cut, whip pan, dissolve...). "
                  "Opcional: vazio = corte seco. Aparece na Shot List e em Sora/Veo.", 7, 0)
        ttk.Combobox(g, textvariable=v["transition"], values=opt_list("transition")).grid(
            row=7, column=1, sticky="ew", padx=(0, 8))
        self._lab(g, "Texto na tela (cena)",
                  "Texto escrito na tela so nesta cena. Vazio = usa o texto global da aba 'Referencias'. "
                  "Prefira poucas palavras.", 7, 2)
        ttk.Entry(g, textvariable=v["text"]).grid(row=7, column=3, sticky="ew", padx=(0, 8))

        if b.get("info"):
            tk.Label(g, text="O que escrever aqui: " + b["info"], bg=CLR["panel"], fg=CLR["fg_dim"],
                     font=("Segoe UI", 8), anchor="w", justify="left", wraplength=1150
                     ).grid(row=8, column=0, columnspan=4, sticky="ew", padx=6, pady=(6, 2))
        on_kw()

    def read_beats(self):
        for b, v in zip(self.beats, self.beat_vars):
            b["name"] = v["name"].get()
            b["keyword"] = v["keyword"].get()
            b["shot"] = v["shot"].get()
            b["angle"] = v["angle"].get()
            b["move"] = v["move"].get()
            b["lens"] = v["lens"].get()
            b["action"] = v["action"].get()
            b["vo"] = v["vo"].get()
            b["extra"] = v["extra"].get()
            try:
                b["dur"] = int(v["dur"].get() or 5)
            except Exception:
                b["dur"] = 5
            b["auto"] = bool(v["auto"].get())
            b["transition"] = v["transition"].get()
            b["text"] = v["text"].get()

    def add_beat(self):
        self.read_beats()
        self.beats.append(new_beat("Cena %d" % (len(self.beats) + 1),
                                   "Cena livre: escreva a palavra-chave e escolha a camera."))
        self.render_beats()
        self.say("Cena adicionada.")

    def del_beat(self, idx):
        self.read_beats()
        if len(self.beats) <= 1:
            self.say("E preciso manter pelo menos uma cena.", CLR["warn"])
            return
        self.beats.pop(idx)
        self.render_beats()
        self.say("Cena removida.")

    def move_beat(self, idx, delta):
        self.read_beats()
        j = idx + delta
        if 0 <= j < len(self.beats):
            self.beats[idx], self.beats[j] = self.beats[j], self.beats[idx]
            self.render_beats()

    def reset_beats(self):
        self.beats = default_beats()
        self.render_beats()
        self.say("Blocos narrativos padrao restaurados (Hook → Setup → Build → Reveal → Proof → The Call/Outro).")

    def clear_beats(self):
        self.beats = [new_beat("Cena 1", "Escreva a palavra-chave e escolha a camera.")]
        self.render_beats()
        self.say("Roteiro limpo.")

    # =================================================================== FORMULA
    def _build_formula_tab(self):
        wrap = tk.Frame(self.nb, bg=CLR["panel"])
        self.nb.add(wrap, text="Formula")

        head = tk.Frame(wrap, bg=CLR["panel2"])
        head.pack(fill="x")
        hin = tk.Frame(head, bg=CLR["panel2"])
        hin.pack(fill="x", padx=12, pady=8)
        tk.Label(hin, text="FORMULA / TEMPLATE MESTRE", bg=CLR["panel2"], fg=CLR["accent"],
                 font=FONT_H).pack(side="left")
        InfoIcon(hin, "Formula mestre",
                 "Este e o molde do prompt. Tudo entre chaves e um TOKEN que o compilador troca pelo "
                 "valor dos seus campos.\n\n"
                 "E por isso que voce altera UM campo (a luz, por exemplo) e todas as cenas mudam juntas: "
                 "a formula nao muda, so o valor do token.\n\n"
                 "Voce pode reescrever a ordem das frases, apagar blocos que seu modelo nao usa "
                 "(ex: tirar AUDIO para Midjourney) ou criar a sua propria estrutura. "
                 "De duplo clique num token da lista ao lado para inserir no cursor.").pack(side="left", padx=8)
        ttk.Button(hin, text="Restaurar padrao", command=self.reset_template).pack(side="right")

        body = tk.Frame(wrap, bg=CLR["panel"])
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        tk.Label(body, text="Template (edite livremente):", bg=CLR["panel"], fg=CLR["fg"],
                 font=FONT_B, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.template_text = make_text(body, height=14, mono=True)
        self.template_text.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.template_text.insert("1.0", MASTER_TEMPLATE)

        tk.Label(body, text="Tokens disponiveis (duplo clique insere):", bg=CLR["panel"],
                 fg=CLR["fg"], font=FONT_B, anchor="w").grid(row=0, column=1, sticky="w", pady=(0, 4))
        tok_wrap = ScrollFrame(body)
        tok_wrap.grid(row=1, column=1, sticky="nsew")
        for tok, src, desc in TOKEN_HELP:
            row = tk.Frame(tok_wrap.inner, bg=CLR["panel"])
            row.pack(fill="x", padx=6, pady=1)
            lb = tk.Label(row, text=tok, bg=CLR["panel"], fg=CLR["accent2"], font=FONT_MONO,
                          cursor="hand2", anchor="w", width=20)
            lb.pack(side="left")
            lb.bind("<Double-Button-1>", lambda e, t=tok: self.template_text.insert("insert", t))
            tk.Label(row, text=desc, bg=CLR["panel"], fg=CLR["fg_dim"], font=("Segoe UI", 8),
                     anchor="w", justify="left", wraplength=300).pack(side="left", fill="x", expand=True)
            InfoIcon(row, tok, "Campo de origem: %s\n\n%s" % (src, desc), size=13).pack(side="left", padx=4)

    def reset_template(self):
        self.template_text.delete("1.0", "end")
        self.template_text.insert("1.0", MASTER_TEMPLATE)
        self.say("Template restaurado.")

    # ==================================================================== SAIDA
    def _build_output_tab(self):
        wrap = tk.Frame(self.nb, bg=CLR["panel"])
        self.nb.add(wrap, text="Saida")

        bar = tk.Frame(wrap, bg=CLR["panel2"])
        bar.pack(fill="x")
        b = tk.Frame(bar, bg=CLR["panel2"])
        b.pack(fill="x", padx=12, pady=8)

        tk.Label(b, text="Plataforma:", bg=CLR["panel2"], fg=CLR["fg"], font=FONT_B).pack(side="left")
        self.plat_map = {label: key for key, label in PLATFORMS}
        self.plat_var = tk.StringVar(value=PLATFORMS[0][1])
        cb = ttk.Combobox(b, textvariable=self.plat_var, state="readonly", width=30,
                          values=[lbl for _, lbl in PLATFORMS])
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self.generate())
        InfoIcon(b, "Plataformas",
                 "Cada motor de IA le prompt de um jeito diferente. O compilador reescreve o MESMO projeto "
                 "no formato de cada um:\n\n" +
                 "\n\n".join("%s: %s" % (lbl, PLATFORM_NOTES[k]) for k, lbl in PLATFORMS)).pack(side="left")

        ttk.Button(b, text="⚡ Gerar / Atualizar", style="Accent.TButton",
                   command=lambda: self.generate(save=True)).pack(side="left", padx=(14, 4))
        ttk.Button(b, text="↻ Aplicar mudanças", command=self.apply_changes).pack(side="left", padx=4)
        ttk.Button(b, text="Copiar", command=self.copy_out).pack(side="left", padx=4)
        ttk.Button(b, text="Salvar .txt", command=self.export_txt).pack(side="left", padx=4)
        ttk.Button(b, text="Salvar .json", command=self.export_json).pack(side="left", padx=4)
        ttk.Button(b, text="Todos os formatos...", command=self.export_multi).pack(side="left", padx=4)

        self.online_var = tk.BooleanVar(value=False)
        has_online = online_available()
        chk = ttk.Checkbutton(b, text="tradutor online", variable=self.online_var,
                              state=("normal" if has_online else "disabled"))
        chk.pack(side="right", padx=(4, 0))
        InfoIcon(b, "Tradutor online (opcional)",
                 ("Ligado: a traducao do roteiro e feita por servico online (completa, qualquer frase).\n"
                  "Desligado: usa o glossario cinematografico interno, que funciona offline mas so conhece "
                  "o vocabulario cadastrado.\n\n"
                  + ("Pacote 'deep-translator' detectado: a opcao esta disponivel."
                     if has_online else
                     "Para habilitar, instale no terminal:\n\n    pip install deep-translator\n\n"
                     "e reabra o programa. Sem ele, o glossario interno continua funcionando."))
                 ).pack(side="right", padx=(8, 2))

        self.plat_note = tk.Label(wrap, text="", bg=CLR["panel"], fg=CLR["accent2"], font=("Segoe UI", 8),
                                  anchor="w", justify="left", wraplength=1250)
        self.plat_note.pack(fill="x", padx=14, pady=(6, 2))

        holder = tk.Frame(wrap, bg=CLR["panel"])
        holder.pack(fill="both", expand=True, padx=12, pady=(2, 8))
        self.out_text = make_text(holder, height=10, mono=True)
        self.out_text.bind("<<Modified>>", self._out_modified)
        sb = ttk.Scrollbar(holder, command=self.out_text.yview)
        self.out_text.configure(yscrollcommand=sb.set)
        self.out_text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.warn = tk.Label(wrap, text="", bg=CLR["panel"], fg=CLR["warn"], font=("Segoe UI", 8),
                             anchor="w", justify="left", wraplength=1250)
        self.warn.pack(fill="x", padx=14, pady=(0, 2))
        self.check_lbl = tk.Label(wrap, text="", bg=CLR["panel"], fg=CLR["ok"], font=("Segoe UI", 9),
                                  anchor="w", justify="left", wraplength=1250)
        self.check_lbl.pack(fill="x", padx=14, pady=(0, 10))

    # ================================================================== ACOES
    def compiler(self) -> Compiler:
        self.read_beats()
        return Compiler(self.get_state(), self.beats,
                        self.template_text.get("1.0", "end-1c"))

    def generate(self, switch=True, save=False):
        ONLINE["enabled"] = bool(getattr(self, "online_var", None) and self.online_var.get())
        comp = self.compiler()
        key = self.plat_map.get(self.plat_var.get(), "universal")
        try:
            txt = comp.build(key)
        except Exception as exc:
            messagebox.showerror("Erro ao compilar", "%s: %s" % (type(exc).__name__, exc))
            return
        self.set_out(txt)
        self._take_snapshot(key, txt)
        self.plat_note.configure(text="ⓘ " + PLATFORM_NOTES.get(key, ""))
        self.show_checklist(comp, key)
        if save:
            self.save_history(comp, key, txt)
        if comp.untranslated:
            self.warn.configure(
                text="Tradutor - revisar: o glossario nao reconheceu estas palavras e elas sairam como estao -> "
                     + ", ".join(comp.untranslated[:30])
                     + "   (se alguma estiver em portugues, troque por um sinonimo simples ou escreva direto em ingles)")
        else:
            self.warn.configure(text="")
        if switch:
            self.nb.select(self.nb.index("end") - 1)
        self.say("Prompt gerado para %s - %d cena(s)." % (self.plat_var.get(), len(self.beats)), CLR["ok"])


    # ------------------------------------------- aplicar mudancas no prompt pronto
    def set_out(self, text: str, dirty: bool = False):
        """Escreve na saida sem contar como 'edicao manual' (a menos que dirty=True)."""
        self._prog = True
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", text)
        self.out_text.edit_modified(False)
        self._prog = False
        self.out_dirty = dirty

    def _out_modified(self, _e=None):
        if self._prog:
            return
        if self.out_text.edit_modified():
            self.out_dirty = True
            self.out_text.edit_modified(False)

    def _take_snapshot(self, key, txt):
        self.read_beats()
        self.snap = {"state": self.get_state(), "beats": json.loads(json.dumps(self.beats)),
                     "template": self.template_text.get("1.0", "end-1c"), "platform": key, "text": txt}
        self._refresh_changes()

    def changed_fields(self) -> list[str]:
        if not self.snap:
            return []
        cur, sn = self.get_state(), self.snap["state"]
        cp, sp = set(cur.get("_pending", [])), set(sn.get("_pending", []))
        out = []
        for fid in FIELD_BY_ID:
            if fid in cp and fid in sp:
                continue                      # ⚑ nos dois: nao afeta o prompt
            if cur.get(fid) != sn.get(fid) or ((fid in cp) != (fid in sp)):
                out.append(fid)
        return out

    def _beats_changed(self) -> bool:
        if not self.snap:
            return False
        self.read_beats()
        return json.dumps(self.beats, sort_keys=True) != json.dumps(self.snap["beats"], sort_keys=True)

    def _refresh_changes(self):
        try:
            ch = set(self.changed_fields())
            for dep_src, deps in APPLY_DEPENDS.items():
                if any(d in ch for d in deps):
                    ch.add(dep_src)
            for fid, btn in self.apply_btns.items():
                want = "▶ Aplicar" if fid in ch else "Aplicar"
                if btn.cget("text") != want:
                    btn.configure(text=want, style="Accent.TButton" if fid in ch else "TButton")
            n = len(ch) + (1 if self._beats_changed() else 0)
            self.change_lbl.configure(text=("● %d por aplicar" % n) if (n and self.snap) else "")
        except Exception:
            pass

    def _poll_changes(self):
        self._refresh_changes()
        self.after(900, self._poll_changes)

    def apply_changes(self, only=None):
        """Aplica no prompt pronto as mudancas feitas nos campos/cenas desde a ultima geracao.
        only = {ids de campo} aplica so aqueles; None aplica tudo."""
        self.read_beats()
        key = self.plat_map.get(self.plat_var.get(), "universal")
        out = self.out_text.get("1.0", "end-1c")
        snap = self.snap
        if snap is None or not out.strip():
            if out.strip() and not messagebox.askyesno(
                    "Aplicar", "O texto da Saida nao foi gerado pelos campos (veio de fora).\n"
                               "Gerar agora a partir dos campos e substituir o texto?"):
                return
            self.generate(switch=False)
            return
        cur = self.get_state()
        tmpl = self.template_text.get("1.0", "end-1c")
        if only is None:
            mix_state, mix_beats = dict(cur), json.loads(json.dumps(self.beats))
        else:
            ids = set(only)
            for src, deps in APPLY_DEPENDS.items():
                if src in ids:
                    ids |= set(deps)
            mix_state = dict(snap["state"])
            pend = set(snap["state"].get("_pending", []))
            cp = set(cur.get("_pending", []))
            for fid in ids:
                if fid in cur:
                    mix_state[fid] = cur[fid]
                (pend.add if fid in cp else pend.discard)(fid)
            mix_state["_pending"] = sorted(pend)
            mix_beats = json.loads(json.dumps(snap["beats"]))
        structural = (key != snap["platform"] or tmpl != snap["template"]
                      or len(mix_beats) != len(snap["beats"]))
        same = (not structural and json.dumps(mix_state, sort_keys=True, default=str)
                == json.dumps(snap["state"], sort_keys=True, default=str)
                and json.dumps(mix_beats, sort_keys=True) == json.dumps(snap["beats"], sort_keys=True))
        if same:
            self.say("Nenhuma mudanca para aplicar: o prompt ja esta igual aos campos.", CLR["fg_dim"])
            return
        new_comp = Compiler(mix_state, mix_beats, tmpl)

        def commit(text, dirty):
            self.set_out(text, dirty)
            self.snap = {"state": mix_state, "beats": mix_beats, "template": tmpl, "platform": key,
                         "text": text if not dirty else snap["text"]}
            self.show_checklist(new_comp, key)
            self._refresh_changes()

        # texto intacto (ou mudanca estrutural): refaz exato, com so as mudancas escolhidas
        if structural or not self.out_dirty:
            if structural and self.out_dirty and not messagebox.askyesno(
                    "Aplicar", "Mudou a plataforma, o numero de cenas ou a formula. Isso exige refazer o texto\n"
                               "e as suas edicoes manuais na Saida serao perdidas. Continuar?"):
                return
            commit(new_comp.build(key), False)
            self.say("Mudancas aplicadas (prompt refeito sem edicoes manuais a preservar).", CLR["ok"])
            return

        # texto editado a mao: troca so os trechos antigos pelos novos, em todas as cenas
        old_comp = Compiler(snap["state"], snap["beats"], snap["template"])
        pairs, inserts = snippet_pairs(old_comp, new_comp)
        new_text, counts, missed = patch_text(out, pairs)
        was = snap["text"].lower()
        missed = [m for m in missed if m.lower() in was]      # so conta se estava no texto gerado
        commit(new_text, True)
        n = sum(counts.values())
        msg = "Aplicado: %d troca(s) em %d trecho(s), suas edicoes foram preservadas." % (n, len(counts))
        if not n and not inserts and not missed:
            msg = "Nada para trocar no texto atual."
        problems = []
        if missed:
            problems.append("Nao achei no texto (voce editou esse trecho?): " +
                            "; ".join("'%s'" % (m if len(m) < 50 else m[:47] + "...") for m in missed[:5]))
        if inserts:
            problems.append("Campos que estavam vazios e agora tem conteudo nao tem onde entrar sem refazer o texto: " +
                            "; ".join("'%s'" % (t if len(t) < 50 else t[:47] + "...") for t in inserts[:5]))
        self.say(msg + ("  ▲ " + " | ".join(problems) if problems else ""),
                 CLR["accent2"] if problems else CLR["ok"])
        if inserts and messagebox.askyesno(
                "Aplicar", "Alguns campos novos so entram refazendo o texto.\n\nRefazer o prompt do zero agora "
                           "(as suas edicoes manuais na Saida serao perdidas)?"):
            commit(new_comp.build(key), False)
            self.say("Prompt refeito com todas as mudancas.", CLR["ok"])

    # ------------------------------------------------------------ checklist
    def show_checklist(self, comp=None, key=None):
        comp = comp or self.compiler()
        key = key or self.plat_map.get(self.plat_var.get(), "universal")
        res = preflight(comp, key)
        icon = {"erro": "✖", "aviso": "▲", "ok": "✓"}
        self.check_lbl.configure(
            text="Verificador:  " + "\n".join("%s %s" % (icon[l], m) for l, m in res),
            fg=CLR["warn"] if any(l == "erro" for l, _ in res)
            else CLR["accent2"] if any(l == "aviso" for l, _ in res) else CLR["ok"])

    # ------------------------------------------------------------ historico
    def save_history(self, comp, key, txt):
        try:
            os.makedirs(HIST_DIR, exist_ok=True)
            self.read_beats()
            data = {"_type": "gerador-de-prompt-historico",
                    "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
                    "platform": key, "fields": self.get_state(), "beats": self.beats,
                    "template": self.template_text.get("1.0", "end-1c"), "prompt": txt}
            sig = hash(json.dumps([data["fields"], data["beats"], data["template"], key], sort_keys=True, default=str))
            if sig == getattr(self, "_hist_sig", None):
                return
            self._hist_sig = sig
            name = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".json"
            with open(os.path.join(HIST_DIR, name), "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=1)
            files = sorted(f for f in os.listdir(HIST_DIR) if f.endswith(".json"))
            for old in files[:-100]:
                os.remove(os.path.join(HIST_DIR, old))
        except Exception as exc:
            self.say("Historico nao salvo: %s" % exc, CLR["warn"])

    def show_history(self):
        files = sorted((f for f in (os.listdir(HIST_DIR) if os.path.isdir(HIST_DIR) else []) if f.endswith(".json")),
                       reverse=True)
        win = tk.Toplevel(self)
        win.title("Historico de versoes geradas")
        win.geometry("700x520")
        win.configure(bg=CLR["panel"])
        tk.Label(win, text="Cada vez que voce clica em GERAR PROMPT a versao e guardada (ultimas 100).\n"
                           "Duplo clique ou 'Restaurar': volta todos os campos e o roteiro daquela versao.",
                 bg=CLR["panel"], fg=CLR["fg_dim"], font=FONT, justify="left").pack(anchor="w", padx=14, pady=(12, 6))
        lb = tk.Listbox(win, bg=CLR["field"], fg=CLR["fg"], font=FONT, selectbackground=CLR["accent"],
                        selectforeground="#0e1016", bd=0, highlightthickness=0, activestyle="none")
        lb.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        rows = []
        for f in files:
            try:
                with open(os.path.join(HIST_DIR, f), encoding="utf-8") as fh:
                    d = json.load(fh)
            except Exception:
                continue
            kws = ", ".join(b.get("keyword", "") for b in d.get("beats", []) if b.get("keyword"))[:60]
            lb.insert("end", "%s   %-11s  %s" % (d.get("saved_at", f).replace("T", " "), d.get("platform", ""), kws))
            rows.append(d)
        if not rows:
            lb.insert("end", "(historico vazio - gere um prompt primeiro)")

        def restore(_e=None):
            sel = lb.curselection()
            if not sel or not rows:
                return
            d = rows[sel[0]]
            self.set_state(d.get("fields", {}))
            if d.get("beats"):
                self.beats = [dict(new_beat(), **b) for b in d["beats"]]
                self.render_beats()
            if d.get("template"):
                self.template_text.delete("1.0", "end")
                self.template_text.insert("1.0", d["template"])
            self.snap = None
            self.set_out(d.get("prompt", ""))
            self.say("Versao de %s restaurada." % d.get("saved_at", ""), CLR["ok"])
            win.destroy()
        lb.bind("<Double-Button-1>", restore)
        ttk.Button(win, text="Restaurar versao selecionada", command=restore).pack(pady=(0, 14))

    # ------------------------------------------------- todos os formatos / A-B
    def export_multi(self):
        win = tk.Toplevel(self)
        win.title("Exportar todos os formatos")
        win.geometry("520x330")
        win.configure(bg=CLR["panel"])
        tk.Label(win, text="Gera o MESMO roteiro em varios formatos de tela (e a versao B do gancho)\n"
                           "para a plataforma escolhida na aba Saida.", bg=CLR["panel"], fg=CLR["fg_dim"],
                 font=FONT, justify="left").pack(anchor="w", padx=14, pady=(14, 8))
        ratios = [("9:16", "9:16 vertical (Reels/TikTok/Shorts)"), ("1:1", "1:1 quadrado (feed)"),
                  ("16:9", "16:9 horizontal (YouTube/TV)"), ("4:5", "4:5 retrato (feed alto)")]
        vars_ = {}
        for key, label in ratios:
            bv = tk.BooleanVar(value=key in ("9:16", "1:1", "16:9"))
            vars_[label] = bv
            ttk.Checkbutton(win, text=label, variable=bv).pack(anchor="w", padx=24, pady=2)
        hook_b = str(self.get_state().get("hook_b", "")).strip()
        ab = tk.BooleanVar(value=bool(hook_b))
        ttk.Checkbutton(win, text="Incluir versao B do gancho" + ("" if hook_b else "  (preencha 'Gancho alternativo' na aba Referencias & Texto)"),
                        variable=ab, state=("normal" if hook_b else "disabled")).pack(anchor="w", padx=24, pady=(10, 2))

        def go():
            chosen = [lbl for lbl, bv in vars_.items() if bv.get()]
            if not chosen:
                messagebox.showinfo("Formatos", "Marque pelo menos um formato.")
                return
            self.read_beats()
            plat = self.plat_map.get(self.plat_var.get(), "universal")
            variants = [("A", None)] + ([("B", hook_b)] if ab.get() and hook_b else [])
            parts = []
            for label in chosen:
                for vname, hook in variants:
                    st = self.get_state()
                    st["aspect"] = label
                    st["_pending"] = [p for p in st.get("_pending", []) if p != "aspect"]
                    beats = [dict(b) for b in self.beats]
                    if hook and beats:
                        beats[0]["keyword"] = hook
                        found, trig = find_trigger(hook)
                        if trig and beats[0].get("auto"):
                            beats[0].update(shot=trig.shot, lens=trig.lens, action=trig.action)
                    comp = Compiler(st, beats, self.template_text.get("1.0", "end-1c"))
                    parts.append("#" * 78 + "\n#  FORMATO %s  |  VERSAO %s\n" % (label.split(" ")[0], vname)
                                 + "#" * 78 + "\n" + comp.build(plat))
            txt = "\n\n".join(parts)
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            path = os.path.join(OUTPUT_DIR, "multi_%s_%s.txt" % (plat, datetime.datetime.now().strftime("%Y%m%d_%H%M")))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(txt)
            self.snap = None
            self.set_out(txt)
            self.say("%d versoes geradas e salvas em %s" % (len(parts), path), CLR["ok"])
            win.destroy()
        ttk.Button(win, text="Gerar e salvar", style="Accent.TButton", command=go).pack(pady=18)

    def copy_out(self):
        txt = self.out_text.get("1.0", "end-1c")
        if not txt.strip():
            self.generate()
            txt = self.out_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(txt)
        self.update_idletasks()
        self.say("Prompt copiado para a area de transferencia.", CLR["ok"])

    def export_txt(self):
        txt = self.out_text.get("1.0", "end-1c")
        if not txt.strip():
            self.generate()
            txt = self.out_text.get("1.0", "end-1c")
        name = "prompt_%s_%s.txt" % (self.plat_map.get(self.plat_var.get(), "out"),
                                     datetime.datetime.now().strftime("%Y%m%d_%H%M"))
        path = filedialog.asksaveasfilename(initialdir=OUTPUT_DIR, initialfile=name,
                                            defaultextension=".txt",
                                            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(txt)
        self.say("Salvo em %s" % path, CLR["ok"])

    def export_json(self):
        comp = self.compiler()
        data = comp.project_dict()
        data["beats"] = self.beats
        name = "projeto_%s.json" % datetime.datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(initialdir=OUTPUT_DIR, initialfile=name,
                                            defaultextension=".json",
                                            filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        self.say("Projeto salvo em %s" % path, CLR["ok"])

    def save_preset_file(self):
        self.read_beats()
        data = {"_type": "gerador-de-prompt-preset", "version": APP_VERSION,
                "fields": self.get_state(), "beats": self.beats,
                "template": self.template_text.get("1.0", "end-1c")}
        path = filedialog.asksaveasfilename(initialdir=PRESET_DIR, defaultextension=".json",
                                            initialfile="meu_preset.json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        self.say("Preset salvo em %s" % path, CLR["ok"])

    def load_preset_file(self):
        path = filedialog.askopenfilename(initialdir=PRESET_DIR, filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            messagebox.showerror("Erro", "Nao foi possivel ler o arquivo:\n%s" % exc)
            return
        self.set_state(data.get("fields", data))
        if data.get("beats"):
            self.beats = [dict(new_beat(), **b) for b in data["beats"]]
            self.render_beats()
        if data.get("template"):
            self.template_text.delete("1.0", "end")
            self.template_text.insert("1.0", data["template"])
        self.say("Preset carregado de %s" % os.path.basename(path), CLR["ok"])

    def apply_preset(self, name, silent=False):
        data = BUILTIN_PRESETS.get(name)
        if not data:
            return
        self.set_state(data)
        if not silent:
            self.preset_var.set(name)
            self.say("Preset '%s' aplicado. As cenas do roteiro foram mantidas." % name, CLR["ok"])

    def lucky_roll(self):
        base = random.choice(LUCKY_SETS)
        self.set_state(BUILTIN_PRESETS[base])
        roll = {
            "camera_move": random.choice(opt_list("camera_move")),
            "expression": random.choice(opt_list("expression")),
            "action": random.choice(opt_list("action")),
            "time_of_day": random.choice(opt_list("time_of_day")),
            "light_style": random.choice(opt_list("light_style")),
            "grading": random.choice(opt_list("grading")),
            "lens": random.choice(opt_list("lens")),
            "atmosphere": [random.choice(opt_list("atmosphere"))],
        }
        self.set_state(roll)
        self.random_seed()
        self.say("🎲 Lucky Roll sobre '%s': %s + %s + %s" % (
            base, roll["lens"], roll["light_style"], roll["grading"]), CLR["accent2"])

    def random_seed(self):
        if "seed" in self.vars:
            self.vars["seed"].set(str(random.randint(100000, 999999999)))

    def new_project(self):
        if not messagebox.askyesno("Novo projeto", "Limpar todos os campos e voltar ao padrao?"):
            return
        self.set_state({fid: f.default for fid, f in FIELD_BY_ID.items()})
        self.set_pending(DEFAULT_PENDING)
        self.beats = default_beats()
        self.render_beats()
        self.reset_template()
        self.snap = None
        self.set_out("")
        self.say("Projeto novo.")

    def show_guide(self):
        win = tk.Toplevel(self)
        win.title("Guia rapido")
        win.geometry("760x560")
        win.configure(bg=CLR["panel"])
        t = make_text(win, height=10)
        sb = ttk.Scrollbar(win, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        t.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=14)
        sb.pack(side="right", fill="y", pady=14, padx=(0, 14))
        t.insert("1.0", GUIDE_TEXT)
        t.configure(state="disabled")


GUIDE_TEXT = """GUIA RAPIDO - GERADOR DE PROMPT UNIVERSAL

1) A FORMULA
   O programa nao escreve prompt "do zero" a cada vez. Existe UM template (aba Formula)
   com tokens entre chaves: {SUJEITO}, {CAMERA}, {LUZ}, {ENQUADRAMENTO}...
   Os campos das abas preenchem esses tokens.
   Consequencia pratica: para mudar a cena inteira voce altera UM campo.
   Trocou "Luz de janela" por "Neon cyberpunk"? Todas as cenas mudam de clima juntas.
   Trocou o ID do personagem e a descricao fisica? O roteiro inteiro troca de ator.

2) ORDEM DE TRABALHO RECOMENDADA
   Preset (barra de cima)  ->  Personagem  ->  Ambiente  ->  Camera  ->  Luz & Cor
   ->  Audio  ->  Motor de IA  ->  Roteiro  ->  Saida / Exportar.

3) O ROTEIRO POR PALAVRA-CHAVE
   Cada cena tem uma palavra-chave ("celular", "copo de agua", "batom") e, na frente dela,
   a escolha de camera: enquadramento (rosto e olhos / busto / meio corpo / corpo inteiro /
   barriga / pernas / maos...), angulo, movimento, lente e acao.
   Palavras ja cadastradas disparam a sugestao automatica (indicador ⚡ verde).
   Ao escolher o enquadramento na mao, o "auto" desliga e a sua escolha manda.

4) CONSISTENCIA DE PERSONAGEM (o que mais quebra video de IA)
   - Use sempre o mesmo ID (ex: ANA_01) no campo "ID / nome do personagem".
   - Mantenha "Consistency Lock" alto (80-95).
   - Trave a seed: gere uma seed, veja qual funcionou e deixe "Travar seed" ligado.
   - Nao mude a descricao fisica entre cenas. Mude so enquadramento e acao.

5) MOTION STRENGTH
   1-3 = quase parado (mais estavel, menos defeito de mao e rosto)
   4-6 = movimento natural
   7-10 = acao rapida (deforma mais; use com fps 60/120)

6) NEGATIVE PROMPT
   Lista do que a IA deve evitar. Em Midjourney vira "--no ...".
   Runway e Luma nao tem campo negativo: nesses casos o compilador descreve
   o resultado de forma positiva e ignora a lista.

7) TRADUTOR
   Escreva em portugues; o compilador exporta em ingles tecnico.
   O glossario e cinematografico, nao e um tradutor completo: palavras desconhecidas
   aparecem no aviso vermelho na aba Saida para voce trocar por um sinonimo simples.

8) EXPORTACAO
   - Universal: tudo, com shot list no fim.
   - Midjourney: 1 paragrafo + flags (--ar, --style, --s, --seed, --no).
   - Runway: 1 frase por cena comecando pelo movimento de camera.
   - Kling: prompt + negative prompt + duracao 5s/10s por cena.
   - Luma: prosa simples.
   - Sora / Hunyuan e Veo 3: roteiro com cenas e audio descrito (Veo gera voz sincronizada).
   - Shot List: uma linha pronta por cena.
   - JSON: o projeto inteiro para versionar no git ou usar via API.

9) PRESETS
   Moda Luxo, Comercial Tech, Vlog UGC, Beleza/Skincare e Food ja vem configurados.
   Salve os seus em Arquivo > Salvar projeto/preset .json (pasta "presets").

10) LUCKY ROLL
   Sorteia uma combinacao coerente (preset + lente + luz + grading + seed nova).
   Use quando travar na escolha visual.
"""


def main():
    app = App()
    if DICT_WARNINGS:
        app.status.configure(text="Aviso no dicionario: " + " | ".join(DICT_WARNINGS))
    app.mainloop()


if __name__ == "__main__":
    main()
