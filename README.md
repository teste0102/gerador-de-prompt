# Gerador de Prompt

Gerador universal de prompts para vídeo e imagem (Kling, Runway, Luma, Sora, Veo, Midjourney) com interface gráfica em Tkinter. Sem dependências externas.

A ideia é uma **fórmula com tokens**: você preenche os campos uma vez (personagem, câmera, luz, ambiente...) e o prompt final é recompilado inteiro a cada alteração. Trocar só o personagem, a câmera ou a iluminação muda todas as cenas de uma vez.

## Árvore do projeto

```
gerador-de-prompt/
├── gerador_de_prompt.py   # aplicativo (GUI + lógica + catálogo de opções)
├── executar.bat           # launcher do Windows (duplo clique)
├── README.md              # este arquivo
├── .gitignore             # mantém dados/usuario.json e saidas/ fora do Git
├── dados/                 # DICIONÁRIO
│   ├── gatilhos.json      # base (Git): palavra-chave -> enquadramento, lente, ação, extra
│   ├── glossario.json     # base (Git): tradução PT -> EN offline
│   └── usuario.json       # SEU (local, fora do Git): criado ao salvar na aba Dicionário
├── presets/               # seus presets .json (criada ao salvar o primeiro)
└── saidas/                # prompts exportados
```

### Dicionário: base no Git, edições locais
- `dados/gatilhos.json` e `dados/glossario.json` vêm no repositório e são atualizados com `git pull`.
- O que você adiciona na aba **Dicionario** vai para `dados/usuario.json`, que **não vai para o Git**: o `git pull` nunca sobrescreve as suas palavras.
- Palavra sua com o mesmo nome de uma da base **vence** a base. Remover a sua faz a da base voltar.
- A busca ignora acento, maiúscula e plural; a frase mais longa ganha (`copo de água` vence `copo`).
- Para compartilhar suas palavras, copie o `usuario.json` ou mescle no `gatilhos.json`/`glossario.json`.

## Árvore do `gerador_de_prompt.py` (onde editar cada coisa)

```
gerador_de_prompt.py
├── OPTIONS[...]          # listas de opções dos campos (cada opção tem a explicação do ⓘ)
│   ├── Câmera/óptica:  camera_body, lens, aperture, shot (enquadramento), angle, camera_move
│   ├── Luz/visual:     light_style, grading, atmosphere, time_of_day, weather, style_render
│   ├── Cenário/sujeito: location, subject_type, wardrobe, expression, action
│   ├── Áudio:          voice_tone, sfx, music
│   └── Técnico:        aspect, fps, negative_preset
├── NEGATIVE_BASE / NEGATIVE_PRESETS   # prompts negativos prontos
├── load_dictionaries()   # carrega dados/*.json (base + usuário) em KEYWORD_TRIGGERS e GLOSSARY
├── find_trigger()        # busca da palavra-chave (sem acento, plural, frase mais longa)
├── SECTIONS              # blocos da interface e campos de cada um (com textos de ajuda)
│   └── Hook → Setup → Build → Reveal → Proof → The Call / Outro
├── MASTER_TEMPLATE       # molde do prompt final, onde os tokens são encaixados
├── BUILTIN_PRESETS       # presets prontos (Moda Luxo, Comercial Tech, Vlog UGC...)
├── class Compiler        # monta o prompt, aplica gatilhos, traduz e formata por plataforma
├── class Tooltip         # balão ao passar o mouse
├── class InfoIcon        # ícone ⓘ (hover = balão, clique = janela com a explicação)
├── class ScrollFrame     # área rolável
├── class App             # janela principal e abas (inclui a aba Dicionário)
└── main()
```

## Como usar

1. **Roteiro por palavra-chave**: cada cena tem a palavra ("celular", "copo de água") e, na frente dela, enquadramento, ângulo, movimento, lente, ação, duração, fala e detalhe extra. A escolha vale só para aquela cena.
2. **Gatilhos automáticos**: ao digitar uma palavra cadastrada no dicionário, a cena já recebe os ajustes sugeridos (aviso ⚡ verde). Se você escolher manualmente, o automático desliga.
3. **Ícone ⓘ** em todo campo: passe o mouse para ver o resumo, clique para a explicação completa do que digitar e do efeito na imagem.
4. **Parâmetros de motor**: negative prompt, motion strength (1–10), seed com travamento, FPS/interpolação, consistency lock (rosto e roupa).
5. **Presets JSON**: salvar e carregar modelos prontos em um clique.
6. **Lucky Roll**: sorteia combinações cinematográficas compatíveis.
7. **Exportação**: Midjourney (`--ar --style --s --seed --no`), Runway, Kling, Luma, Sora/Hunyuan, Veo 3, shot list e JSON.
8. **Tradutor**: escreva em português, o prompt sai em inglês técnico. Palavras fora do glossário aparecem em um aviso. Opcional online: `pip install deep-translator`.

## Instalar (Windows)

Requer Python 3.9+ do python.org (com Tkinter, que já vem no instalador).

```
cd %USERPROFILE%\Desktop
git clone -b claude/prompt-generator-gui-ir1a57 https://github.com/teste0102/gerador-de-prompt
cd gerador-de-prompt
executar.bat
```

Ou rode direto: `python gerador_de_prompt.py`

## Cadastrar novidades sem mexer na lógica

| Quero adicionar... | Edite |
|---|---|
| Nova câmera, lente, luz, ação etc. | `OPTIONS["campo"]` |
| Nova palavra-chave com ajustes automáticos | aba **Dicionario** (ou `dados/gatilhos.json`) |
| Novos termos de tradução | aba **Dicionario** (ou `dados/glossario.json`) |
| Novo campo ou bloco na interface | `SECTIONS` |
| Mudar a estrutura do prompt final | `MASTER_TEMPLATE` |
| Novo preset pronto | `BUILTIN_PRESETS` |
