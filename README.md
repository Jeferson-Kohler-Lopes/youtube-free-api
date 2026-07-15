# YouTube Strategy Lab — edição sem API

Sistema gratuito para analisar canais do YouTube **sem YouTube Data API, sem chave do Google e sem cartão**.

O projeto usa:

- **yt-dlp** para ler metadados públicos;
- **Python** para calcular os padrões do canal;
- **Pillow** para métricas visuais básicas das thumbnails;
- **GitHub Actions** para executar análises manualmente na nuvem;
- **GitHub Pages** para publicar o painel.

## O que esta versão entrega

- coleta de até 2.000 vídeos por execução, ou de toda a aba com `--all-videos`;
- títulos, descrições, tags e métricas quando disponíveis;
- visualizações por dia;
- engajamento público aproximado;
- comparação separada de Shorts e vídeos longos;
- vídeos fora da curva;
- nicho e temas dominantes;
- frequência de publicação;
- pesquisas automáticas em inglês;
- canais e vídeos internacionais relacionados;
- brilho, contraste, saturação, cores e densidade das thumbnails;
- insights estratégicos;
- até 30 ideias de vídeos;
- painel publicado gratuitamente;
- exportação do relatório em JSON.

## Limitação principal

Sem a API oficial, não existe confirmação confiável de que um canal é dos Estados Unidos. O sistema encontra **referências em inglês** e usa sinais de idioma e similaridade. A localização deve ser tratada como estimativa.

A coleta depende da estrutura pública do YouTube. Quando o site mudar, pode ser necessário atualizar o `yt-dlp`.

## Uso mais fácil no Windows

1. Instale o Python 3.11 ou superior.
2. Dê dois cliques em `analisar-canal.bat`.
3. Cole a URL ou o `@handle` do canal.
4. Aguarde a criação de `reports/latest.json`.
5. Dê dois cliques em `abrir-painel.bat`.
6. Abra `http://localhost:8080` caso o navegador não abra automaticamente.

O primeiro uso cria um ambiente virtual e instala as dependências.

## Uso pelo terminal

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No macOS ou Linux:

```bash
source .venv/bin/activate
```

Instale:

```bash
pip install -r requirements.txt
```

Analise um canal:

```bash
python -m collector.collect "https://youtube.com/@nomedocanal" \
  --max-videos 200 \
  --max-competitors 3 \
  --output reports/latest.json
```

Para coletar toda a aba pública de vídeos no computador:

```bash
python -m collector.collect "@nomedocanal" --all-videos
```

Em canais muito grandes, mantenha o modo padrão primeiro para validar a coleta.

Para abrir cada vídeo e tentar obter tags, descrições, curtidas e comentários completos:

```bash
python -m collector.collect "@nomedocanal" --deep-all
```

Esse modo faz mais acessos às páginas. Dados ocultos ou indisponíveis continuarão vazios.

Para não pesquisar referências:

```bash
python -m collector.collect "@nomedocanal" --skip-competitors
```

Para indicar manualmente canais internacionais:

```bash
python -m collector.collect "@canalbrasileiro" \
  --competitor-url "https://youtube.com/@canal1" \
  --competitor-url "https://youtube.com/@canal2"
```

## Abrir o painel

Na raiz do projeto:

```bash
python -m http.server 8080
```

Acesse:

```text
http://localhost:8080
```

O painel permite:

- carregar `reports/latest.json` automaticamente;
- abrir qualquer relatório JSON;
- baixar novamente o relatório;
- visualizar uma demonstração.

## Executar no GitHub sem instalar no computador

1. Coloque os arquivos em um repositório do GitHub.
2. Abra a aba **Actions**.
3. Selecione **Analisar canal sem API**.
4. Clique em **Run workflow**.
5. Informe a URL do canal e as quantidades.
6. O workflow atualizará `reports/latest.json`.

A execução seguinte do workflow de Pages publicará o novo relatório.

### Permissão necessária

Em:

```text
Settings → Actions → General → Workflow permissions
```

marque:

```text
Read and write permissions
```

Isso permite que o workflow salve o relatório no próprio repositório.

## Publicar o painel no GitHub Pages

1. Entre em `Settings → Pages`.
2. Em **Source**, selecione **GitHub Actions**.
3. Faça um push na branch `main` ou execute **Publicar painel no GitHub Pages**.
4. O endereço aparecerá no resumo da execução.

## Testes

```bash
python -m unittest discover -s tests -v
```

## Atualizar o coletor

Quando a coleta parar por mudança no YouTube:

```bash
pip install -U yt-dlp
```

## Estrutura

```text
assets/                         Interface do painel
collector/                      Coleta e análise em Python
reports/sample.json             Demonstração
reports/latest.json             Gerado após uma análise
tests/                          Testes do motor
.github/workflows/pages.yml     Publicação do painel
.github/workflows/analyze-channel.yml
analisar-canal.bat              Atalho para Windows
abrir-painel.bat                Servidor local no Windows
```

Leia também `docs/COMO-FUNCIONA.md` e `docs/ROADMAP.md`.
