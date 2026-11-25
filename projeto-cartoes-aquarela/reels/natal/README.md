# Reel de Natal em aquarela

## V16 · Cartões de Natal

[Baixar a V16 em MP4](./reel-cartoes-de-natal-v16.mp4?raw=1) · [Ver os quadros da V16](./quadros-v16.jpg)

A montagem de 28,6 segundos segue a referência `2.mp4`. Abre com os dois cartões sobre o xadrez, aproxima a câmera da pintura e mostra o Papai Noel saindo do envelope em stop motion. O cartão vira para revelar o verso. O detalhe do interior, a oferta das 20 unidades e a assinatura de Raynara completam a sequência.

Para reproduzir a montagem com as dependências descritas abaixo, execute `python render_v16.py`. O script usa a fonte Caveat e os seis segundos de pintura em [materiais](./materiais). A [trilha instrumental](./trilha.py) tem uma versão de duração específica para cada montagem.

## V15 · Natal feito à mão

[Baixar o Reel V15 em MP4](./reel-cartoes-de-natal-v15.mp4?raw=1) · [Ver quadros do vídeo](./quadros-v15.jpg)

São 20,4 segundos em 1080 × 1920, com trilha original e 204 poses de stop motion. Cada pose dura três quadros no vídeo de 30 fps.

| Trecho | Cena |
| --- | --- |
| 0–2,8 s | Abertura com a pintura e as letras de “Natal feito à mão”. |
| 2,8–6,5 s | O Papai Noel sai pela abertura do envelope. |
| 6,5–11,2 s | O cartão vira, mostra o verso “De / Para” e recebe a frase “o seu Natal um pouco mais único”. |
| 11,2–17,5 s | Entra a rena. Os recortes montam “20 unidades de abertura”, os preços de R$ 35 por um cartão e R$ 99 por três, e “Pedidos no direct · Envie NATAL”. |
| 17,5–20,4 s | O retrato e as letras de “Raynara” fecham o Reel. |

## Arquivo de versões

As [versões anteriores e as artes de estudo](./versoes) registram a evolução da montagem. A [V12](../../assets/reel-cartoes-de-natal-v12.mp4) e a [análise do protótipo](../../analise-prototipo-natal.md) já estavam no projeto.

## Remontar a V15

O arquivo [render_v15.py](./render_v15.py) contém a animação quadro a quadro. Ele usa as imagens, os dois clipes de pintura e a fonte Plus Jakarta Sans em [materiais](./materiais), além do [retrato da Raynara](../../assets/retrato-profissional-raynara.png).

Use Python com Pillow e NumPy, FFmpeg com libx264 e a família Bookman Old Style instalada. O render original usou Pillow 13.0.0 e NumPy 2.3.5. O script procura FFmpeg no PATH e as fontes na pasta Fonts do Windows. Para usar outra instalação, defina `FFMPEG` com o caminho do executável e `BOOKMAN_DIR` com a pasta que contém BOOKOS.TTF, BOOKOSB.TTF e BOOKOSI.TTF.

Na pasta deste README, execute:

```sh
python -m pip install Pillow numpy
python render_v15.py
```

O MP4 e a folha de quadros saem em `build/`. O render verifica a duração, o áudio, os 612 quadros e a sobreposição do bolso do envelope nas 25 poses de saída do cartão.
