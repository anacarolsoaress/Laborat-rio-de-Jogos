"""Apocalipse Runaways - versão 2 organizada.

Estrutura:
  1. CONFIGURAÇÕES   - constantes do jogo
  2. UTILIDADES      - funções auxiliares (imagens, sons)
  3. ASSETS          - carregamento de imagens, fontes e sons (uma vez só)
  4. ENTIDADES       - Entidade, Arvore, Zumbi, Item, Bala, Sobrevivente, Jogador
  5. MUNDO           - chão, chunks (árvores, zumbis, itens) gerados sob demanda
  6. JOGO            - estados (MENU, ESPERA, JOGO, CONFIG, MORTE) e desenho
"""
import math
import random
import time

import pygame
from PPlay.window import Window
from PPlay.keyboard import Keyboard
from PPlay.mouse import Mouse
from menu import Menu

# =============================================================================
# 1. CONFIGURAÇÕES
# =============================================================================
LARGURA_TELA, ALTURA_TELA = 800, 600
MAPA_LARGURA, MAPA_ALTURA = 5600, 4200
CHUNK_SIZE = 400
TAMANHO_CHAO = 600

JOGADOR_INICIO = (400, 3600)
CAMERA_OFFSET = (350, 250)

T_PLAYER = 100
T_ZUMBI = 125
T_SOBRI = 82
T_ARVORE = 200
BASE_LARGURA, BASE_ALTURA = 540, 360

VELOCIDADE_JOGADOR = 500
VELOCIDADE_ZUMBI = 100
VELOCIDADE_BALA = 800
INTERVALO_ANIM_JOGADOR = 10 / 100   # segundos por frame
INTERVALO_ANIM_ZUMBI = 10 / 70

# Sobrevivente (companheiro)
SOBRI_VIDA = 4
SOBRI_DIST_SEGUIR = 90
SOBRI_MULT_VELOCIDADE = 0.88
SOBRI_INTERVALO_DANO = 2.2
SOBRI_DURACAO_PISCAR = 1.2
SOBRI_OFFSET_INICIO = 100          # nasce ao lado do jogador
INTERVALO_ANIM_SOBRI = 10 / 110
SOBRI_DIST_MIN_ENTRE_ELES = 62

# Zumbis e cerco do acampamento
DIST_PERSEGUICAO = 800
DIST_ATAQUE_ZUMBI = 70
DIST_MIN_SPAWN_ZUMBI = 800
DIST_MIN_SPAWN_ACAMPAMENTO = 220
INTERVALO_DANO_ZUMBI = 3
DANO_ZUMBI = 1
FORCA_EMPURRAO = 50
HITBOX_ZUMBI = (45, 75)
CERCO_QTD_ZUMBIS = 10
CERCO_RAIO = 360
CERCO_ATRASO_PERSEGUICAO = 1.0

# Árvores
DIST_MIN_ARVORES = 210

# Efeitos de dano
DURACAO_VERMELHO = 0.2
DURACAO_BRANCO = 0.4
PISCADAS_DANO = 20
INTERVALO_PISCADA = 0.1

# Ciclo de dia e noite
DURACAO_PERIODO = 40         # segundos de dia ou de noite
DURACAO_TRANSICAO = 30         # segundos de entardecer/amanhecer no fim de cada período
ALPHA_NOITE = 190              # opacidade do filtro com a noite fechada
COR_NOITE = (0, 0, 20)
COR_CREPUSCULO = (110, 45, 25) # tom alaranjado no começo do entardecer / fim do amanhecer
FADE_MUSICA_MS = 3000          # troca suave de música no ciclo automático
FADE_MUSICA_BARRACA_MS = 800
TEMPO_LIMITE_SEM_DORMIR = DURACAO_PERIODO * 2  # 1 dia inteiro (dia + noite completos)
MULT_VELOCIDADE_CANSADO = 0.80                 # 20% mais lentos

# Diagnóstico do som de zumbi: imprime o estado no terminal 1x por segundo (use False para desligar)
DEBUG_SOM = False

# Munição
BALAS_INICIAIS = 10
BALAS_POR_PACOTE = 10

# Itens espalhados pelo mapa (prob = chance de aparecer em cada chunk)
ITENS_CFG = {
    "municao": {"arquivo": "balas", "tam": (34, 34), "respawn": 10, "prob": 0.75, "realocar": True},
    "medkit": {"arquivo": "medkit", "tam": (50, 50), "respawn": 15, "prob": 0.125, "realocar": False},
    "laranja": {"arquivo": "laranja", "tam": (40, 40), "respawn": 10, "prob": 0.375, "realocar": False},
}

# Direções: tecla -> (dx, dy, direção)
TECLAS_MOVIMENTO = {
    "LEFT": (-1, 0, "esquerda"),
    "A": (-1, 0, "esquerda"),
    "RIGHT": (1, 0, "direita"),
    "D": (1, 0, "direita"),
    "UP": (0, -1, "tras"),
    "W": (0, -1, "tras"),
    "DOWN": (0, 1, "frente"),
    "S": (0, 1, "frente"),
}
LETRA_DIRECAO = {"direita": "D", "esquerda": "E", "frente": "F", "tras": "T"}
TAMANHO_JOGADOR_DIRECAO = {
    "direita": (100, 100), "esquerda": (95, 100),
    "frente": (100, 105), "tras": (100, 105),
}


# =============================================================================
# 2. UTILIDADES
# =============================================================================
def carregar_som(nome, volume=None):
    for ext in (".mp3", ".wav", ".ogg", ""):
        try:
            som = pygame.mixer.Sound(nome + ext)
            if volume is not None:
                som.set_volume(volume)
            return som
        except Exception:
            continue
    return None


def carregar_imagem(caminho, tamanho):
    """Carrega, converte e redimensiona; se falhar, devolve um quadrado magenta."""
    for sufixo in ("", ".png"):
        try:
            img = pygame.image.load(caminho + sufixo).convert_alpha()
            return pygame.transform.scale(img, tamanho)
        except Exception:
            continue
    surf = pygame.Surface(tamanho, pygame.SRCALPHA)
    surf.fill((255, 0, 255, 80))
    return surf


def tocar(som, **kwargs):
    if som:
        som.play(**kwargs)


def nivel_barra(vida):
    """Converte vida em índice (0 a 4) da imagem da barra."""
    return max(0, min(4, int(vida)))


# =============================================================================
# 3. ASSETS
# =============================================================================
class Assets:
    def __init__(self):
        img = carregar_imagem

        # Cenário
        self.chao = [img(n, (TAMANHO_CHAO, TAMANHO_CHAO)) for n in ("chao", "chao2", "chao3")]
        self.arvore = img("arvore", (T_ARVORE, T_ARVORE))
        self.arvore_seca = img("arvore_seca", (T_ARVORE, T_ARVORE))
        self.arbusto = img("arbusto", (65, 65))
        self.base = img("base", (BASE_LARGURA, BASE_ALTURA))
        self.vitoria = img("vitoria", (900, 600))
        self.som_vitoria = carregar_som("vitoria")
        self.barraca = carregar_imagem("barraca.png", (230, 140))
        self.barraca_botao = carregar_imagem("barraca_botao.png", (600, 401))
        self.salvar = img("salvar", (1568, 880))

        # Personagens
        self.anim_jogador = self._animacao("boneco", TAMANHO_JOGADOR_DIRECAO)
        self.anim_sobri = self._animacao("sobri", {d: (T_SOBRI, T_SOBRI) for d in LETRA_DIRECAO})
        tamanhos_resgataveis = {
            d: (int(largura * 0.65), int(altura * 0.72))
            for d, (largura, altura) in TAMANHO_JOGADOR_DIRECAO.items()
        }
        self.anim_resgataveis = {
            i: self._animacao(f"S{i}", tamanhos_resgataveis) for i in range(1, 4)
        }
        self.anim_zumbi = self._animacao_zumbi()
        self.zumbi_parado = img("zumbiF1", (T_ZUMBI, T_ZUMBI))
        self.morte = [img("normal", (100, 100))]
        self.morte += [img(f"trans{i}", (100, 100)) for i in range(1, 10)]
        self.morte.append(img("morte", (100, 100)))

        # Itens, tiros e mochila
        self.itens = {tipo: img(c["arquivo"], c["tam"]) for tipo, c in ITENS_CFG.items()}
        self.tiro = img("tiro", (30, 15))
        self.icone_mochila = img("icone_mochila", (90, 90))
        self.tela_mochila = img("mochila", (600, 600))
        self.laranja_mochila = img("laranja", (100, 100))
        self.medkit_mochila = img("medkit", (100, 100))

        # Barras de vida
        self.barra_jogador = {i: img(f"barra_vida_{i}", (200, 70)) for i in range(5)}
        self.barra_zumbi = {i: img(f"barra_zumbi_{i}", (100, 20)) for i in range(5)}
        self.barra_sobri = {i: img(f"barra_vida_{i}", (90, 22)) for i in range(5)}

        # Fontes e textos que não mudam (renderizados uma única vez)
        try:
            fonte_morte = pygame.font.Font("Creepster.ttf", 90)
        except Exception:
            fonte_morte = pygame.font.Font(None, 90)
        try:
            self.fonte_vitoria_sub = pygame.font.Font("Creepster.ttf", 34)
        except Exception:
            self.fonte_vitoria_sub = pygame.font.Font(None, 36)
        self.fonte = pygame.font.Font(None, 30)
        self.fonte_cansado = pygame.font.Font(None, 26)
        self.texto_morte = fonte_morte.render("VOCÊ É UM DE NÓS...", True, (255, 0, 0))
        self.texto_recomecar = self.fonte.render("clique ESC para recomeçar", True, (255, 255, 255))
        self.texto_abrir_mochila = self.fonte.render("E para abrir", True, (255, 255, 255))
        self.texto_cansado = self.fonte_cansado.render("cansado", True, (255, 0, 0))

        # Sons
        self.som_ambiente = carregar_som("ambiente", 0.1)
        self.musica_noite = pygame.mixer.Sound("noite.mp3")
        self.musica_noite.set_volume(0.4)
        self.som_barraca = carregar_som("som_barraca", 0.5)
        self.som_coleta = carregar_som("coleta", 0.2)
        self.som_morte = carregar_som("morte", 0.2)
        self.som_empurrao = carregar_som("empurrao")
        self.som_zumbi = carregar_som("som_zumbi", 0)
        self.som_tiro = carregar_som("som_tiro", 0.09)
        self.som_recupera_vida = carregar_som("recupera_vida", 0.5)

    @staticmethod
    def _animacao(prefixo, tamanhos):
        """{'idle': {dir: img}, 'walk': {dir: [img, img]}} - serve para jogador e sobrevivente."""
        anim = {"idle": {}, "walk": {}}
        for direcao, letra in LETRA_DIRECAO.items():
            tam = tamanhos[direcao]
            anim["idle"][direcao] = carregar_imagem(f"{prefixo}{letra}1", tam)
            anim["walk"][direcao] = [
                carregar_imagem(f"{prefixo}{letra}2", tam),
                carregar_imagem(f"{prefixo}{letra}3", tam),
            ]
        return anim

    @staticmethod
    def _animacao_zumbi():
        """{dir: [img, img]}"""
        tam = (T_ZUMBI, T_ZUMBI)
        return {
            d: [carregar_imagem(f"zumbi{l}2", tam), carregar_imagem(f"zumbi{l}3", tam)]
            for d, l in LETRA_DIRECAO.items()
        }


# =============================================================================
# 4. ENTIDADES
# =============================================================================
class Entidade:
    """Objeto do mundo: posição (x, y) em coordenadas do mapa."""

    def __init__(self, imagem, x=0, y=0, w=None, h=None):
        self.image = imagem
        self.x, self.y = x, y
        self.w = w if w is not None else imagem.get_width()
        self.h = h if h is not None else imagem.get_height()

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    @property
    def hitbox(self):
        return pygame.Rect(self.x + 95, self.y + 93, 19, 64)

    @property
    def ordem_y(self):
        """Ordena o desenho: quem está mais abaixo aparece na frente."""
        return self.y + self.h

    def visivel(self, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        return sx + self.w > 0 and sx < LARGURA_TELA and sy + self.h > 0 and sy < ALTURA_TELA

    def desenhar(self, tela, cam_x, cam_y):
        tela.blit(self.image, (self.x - cam_x, self.y - cam_y))


class Base(Entidade):
    def __init__(self, assets):
        largura = BASE_LARGURA
        altura = BASE_ALTURA

        x = MAPA_LARGURA - largura
        y = 50

        super().__init__(assets.base, x, y, largura, altura)

    @property
    def hitbox(self):
        return pygame.Rect(self.x + 60, self.y + 60, self.w - 120, self.h - 75)


class Arvore(Entidade):
    @property
    def hitbox_tronco(self):
        """Área colidível apenas do tronco (base central da árvore)."""
        tronco_w = max(20, int(self.w * 0.18))
        tronco_h = max(24, int(self.h * 0.22))
        tronco_x = self.x + (self.w - tronco_w) / 2
        tronco_y = self.y + self.h - tronco_h - int(self.h * 0.04)
        return pygame.Rect(tronco_x, tronco_y, tronco_w, tronco_h)

    @property
    def ordem_y(self):
        return self.y + self.h - 30


class Arbusto(Entidade):
    pass


class Zumbi(Entidade):
    def __init__(
        self,
        assets,
        x,
        y,
        lista,
        dist_perseguicao=DIST_PERSEGUICAO,
        atraso_perseguicao=0.0,
    ):
        super().__init__(assets.zumbi_parado, x, y, T_ZUMBI, T_ZUMBI)
        self.anim = assets.anim_zumbi
        self.lista = lista              # lista do chunk onde ele nasceu
        self.dist_perseguicao = dist_perseguicao
        self.atraso_perseguicao = atraso_perseguicao
        self.vida_maxima = 4
        self.vida = 4
        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0.0

    def perseguir(self, jx, jy, dt, mundo):
        if self.atraso_perseguicao > 0:
            self.atraso_perseguicao = max(0.0, self.atraso_perseguicao - dt)
            return

        dx, dy = jx - self.x, jy - self.y
        dist = math.hypot(dx, dy)

        if dist > self.dist_perseguicao:
            return

        if dist != 0:
            passo_x = (dx / dist) * VELOCIDADE_ZUMBI * dt
            passo_y = (dy / dist) * VELOCIDADE_ZUMBI * dt

            novo_x = max(0, min(self.x + passo_x, MAPA_LARGURA - self.w))
            rect_x = pygame.Rect(novo_x + 22, self.y + 30, self.w - 44, self.h - 36)
            if not mundo.colide_tronco(rect_x) and not mundo.colide_acampamento(rect_x):
                self.x = novo_x

            novo_y = max(0, min(self.y + passo_y, MAPA_ALTURA - self.h))
            rect_y = pygame.Rect(self.x + 22, novo_y + 30, self.w - 44, self.h - 36)
            if not mundo.colide_tronco(rect_y) and not mundo.colide_acampamento(rect_y):
                self.y = novo_y

        if abs(dx) > abs(dy):
            self.direcao = "direita" if dx > 0 else "esquerda"
        else:
            self.direcao = "frente" if dy > 0 else "tras"

        self.timer_anim += dt

        if self.timer_anim >= INTERVALO_ANIM_ZUMBI:
            self.timer_anim = 0
            self.frame = (self.frame + 1) % 2

        self.image = self.anim[self.direcao][self.frame]

    def acertado_por(self, px, py):
        """A bala está dentro da hitbox (menor que o sprite) do zumbi?"""
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        return (abs(px - cx) < HITBOX_ZUMBI[0] / 2) and (abs(py - cy) < HITBOX_ZUMBI[1] / 2)


class Item(Entidade):
    """Munição, medkit ou laranja, com respawn depois de coletado."""

    def __init__(self, tipo, imagem, x, y, origem_chunk):
        super().__init__(imagem, x, y)
        self.tipo = tipo
        self.origem_chunk = origem_chunk
        self.coletado = False
        self.tempo_respawn = 0.0

    def atualizar(self, dt):
        if not self.coletado:
            return
        cfg = ITENS_CFG[self.tipo]
        self.tempo_respawn += dt
        if self.tempo_respawn >= cfg["respawn"]:
            self.coletado = False
            self.tempo_respawn = 0
            if cfg["realocar"]:
                ox, oy = self.origem_chunk
                self.x = ox + random.randint(0, CHUNK_SIZE - self.w)
                self.y = oy + random.randint(0, CHUNK_SIZE - self.h)


class Bala(Entidade):
    """x, y = centro da bala (coordenadas do mapa)."""

    def __init__(self, imagem, x, y, dir_x, dir_y):
        super().__init__(imagem, x, y)
        self.dir_x, self.dir_y = dir_x, dir_y

    def atualizar(self, dt):
        self.x += self.dir_x * VELOCIDADE_BALA * dt
        self.y += self.dir_y * VELOCIDADE_BALA * dt

    def fora_do_mapa(self):
        return not (0 <= self.x <= MAPA_LARGURA and 0 <= self.y <= MAPA_ALTURA)

    def desenhar(self, tela, cam_x, cam_y):
        tela.blit(self.image, (self.x - cam_x - self.w / 2, self.y - cam_y - self.h / 2))


class Sobrevivente(Entidade):
    """Companheiro que segue um alvo e tem vida própria."""

    def __init__(self, assets, x, y, anim=None, dist_seguir=SOBRI_DIST_SEGUIR):
        anim_escolhida = anim if anim is not None else assets.anim_sobri
        imagem_inicial = anim_escolhida["idle"]["frente"]
        super().__init__(
            imagem_inicial,
            x,
            y,
            imagem_inicial.get_width(),
            imagem_inicial.get_height(),
        )
        self.anim = anim_escolhida
        self.dist_seguir = dist_seguir
        self.vida_maxima = SOBRI_VIDA
        self.restaurar(x, y)

    @property
    def ordem_y(self):
        """Mantém os sobreviventes sempre na frente das árvores próximas."""
        return self.y + self.h + 45

    def restaurar(self, x, y):
        """Devolve a vida e reposiciona (usado ao começar uma partida nova)."""
        self.x, self.y = x, y
        self.vida = self.vida_maxima
        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0.0
        self.ultimo_dano = -SOBRI_INTERVALO_DANO
        self.tempo_piscar = 0.0
        self.image = self.anim["idle"]["frente"]

    @property
    def vivo(self):
        return self.vida > 0

    @property
    def oculto_piscando(self):
        """Verdadeiro nos instantes em que o sprite some após levar dano."""
        return self.tempo_piscar > 0 and int(self.tempo_piscar * 10) % 2 == 0

    def _hitbox_corpo(self, px, py):
        return pygame.Rect(px + 16, py + 24, self.w - 32, self.h - 28)

    def _colide_com_outros(self, px, py, outros_personagens):
        meu_rect = self._hitbox_corpo(px, py)
        meu_centro = (px + self.w / 2, py + self.h / 2)
        for outro in outros_personagens:
            if outro is self:
                continue
            if hasattr(outro, "vivo") and not outro.vivo:
                continue
            outro_rect = pygame.Rect(
                outro.x + 16,
                outro.y + 24,
                max(20, outro.w - 32),
                max(20, outro.h - 28),
            )
            if meu_rect.colliderect(outro_rect):
                return True
            outro_centro = (outro.x + outro.w / 2, outro.y + outro.h / 2)
            if math.hypot(meu_centro[0] - outro_centro[0], meu_centro[1] - outro_centro[1]) < SOBRI_DIST_MIN_ENTRE_ELES:
                return True
        return False

    def atualizar(self, dt, alvo_x, alvo_y, velocidade_jogador, mundo, outros_personagens=None):
        """Segue o alvo e atualiza animação, separação/colisão entre personagens e efeito de dano."""
        if not self.vivo:
            return

        outros = outros_personagens or []
        dx, dy = alvo_x - self.x, alvo_y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.dist_seguir:
            dx, dy = dx / dist, dy / dist
            velocidade = velocidade_jogador * SOBRI_MULT_VELOCIDADE

            novo_x = max(0, min(self.x + dx * velocidade * dt, MAPA_LARGURA - self.w))
            if not mundo.colide_tronco(self._hitbox_corpo(novo_x, self.y)) and not self._colide_com_outros(novo_x, self.y, outros):
                self.x = novo_x

            novo_y = max(0, min(self.y + dy * velocidade * dt, MAPA_ALTURA - self.h))
            if not mundo.colide_tronco(self._hitbox_corpo(self.x, novo_y)) and not self._colide_com_outros(self.x, novo_y, outros):
                self.y = novo_y

            if abs(dx) > abs(dy):
                self.direcao = "direita" if dx > 0 else "esquerda"
            else:
                self.direcao = "frente" if dy > 0 else "tras"

            self.timer_anim += dt

            if self.timer_anim >= INTERVALO_ANIM_SOBRI:
                self.timer_anim = 0
                self.frame = (self.frame + 1) % 2

            self.image = self.anim["walk"][self.direcao][self.frame]

        else:
            self.frame = 0
            self.image = self.anim["idle"][self.direcao]

        # Empurrão suave caso fiquem próximos demais ao cercar ou parar
        meu_cx = self.x + self.w / 2
        meu_cy = self.y + self.h / 2
        for outro in outros:
            if outro is self:
                continue
            if hasattr(outro, "vivo") and not outro.vivo:
                continue
            ocx = outro.x + outro.w / 2
            ocy = outro.y + outro.h / 2
            sep_x = meu_cx - ocx
            sep_y = meu_cy - ocy
            sep_dist = math.hypot(sep_x, sep_y)
            if 0 < sep_dist < SOBRI_DIST_MIN_ENTRE_ELES:
                forca = (SOBRI_DIST_MIN_ENTRE_ELES - sep_dist) * 4.5 * dt
                emp_x = max(0, min(self.x + (sep_x / sep_dist) * forca, MAPA_LARGURA - self.w))
                emp_y = max(0, min(self.y + (sep_y / sep_dist) * forca, MAPA_ALTURA - self.h))
                if not mundo.colide_tronco(self._hitbox_corpo(emp_x, self.y)):
                    self.x = emp_x
                if not mundo.colide_tronco(self._hitbox_corpo(self.x, emp_y)):
                    self.y = emp_y

        self.x = max(0, min(self.x, MAPA_LARGURA - self.w))
        self.y = max(0, min(self.y, MAPA_ALTURA - self.h))

        if self.tempo_piscar > 0:
            self.tempo_piscar -= dt

    def receber_dano(self, agora=None):
        """Tira vida respeitando o intervalo. Retorna True se o dano foi aplicado."""
        if not self.vivo:
            return False
        if agora is None:
            agora = time.time()
        if agora - self.ultimo_dano < SOBRI_INTERVALO_DANO:
            return False
        self.vida = max(0, self.vida - 2)
        self.ultimo_dano = agora
        self.tempo_piscar = SOBRI_DURACAO_PISCAR
        return True


class SobreviventeResgatavel(Entidade):
    def __init__(self, identificacao, anim, x, y):
        imagem_inicial = anim["idle"]["frente"]
        super().__init__(
            imagem_inicial,
            x,
            y,
            imagem_inicial.get_width(),
            imagem_inicial.get_height(),
        )

        self.identificacao = identificacao
        self.anim = anim
        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0

    @property
    def ordem_y(self):
        """Mantém os sobreviventes resgatáveis sempre na frente das árvores próximas."""
        return self.y + self.h + 45


def escolher_alvo(jogador, aliados, zumbi):
    """O zumbi persegue quem estiver mais perto: jogador ou qualquer aliado vivo."""
    melhor_alvo = jogador
    menor_dist = math.hypot(jogador.x - zumbi.x, jogador.y - zumbi.y)

    for aliado in aliados:
        if not aliado.vivo:
            continue
        dist = math.hypot(aliado.x - zumbi.x, aliado.y - zumbi.y)
        if dist < menor_dist:
            menor_dist = dist
            melhor_alvo = aliado

    return melhor_alvo


class Jogador(Entidade):
    def __init__(self, assets, jogo):
        super().__init__(assets.anim_jogador["idle"]["direita"], *JOGADOR_INICIO, T_PLAYER, T_PLAYER)
        self.assets = assets
        self.jogo = jogo
        self.anim = assets.anim_jogador
        self._cache_branco = {}
        self.resetar()

    def resetar(self):
        self.x, self.y = JOGADOR_INICIO
        self.direcao = "direita"
        self.frame = 0
        self.timer_anim = 0.0
        self.image = self.anim["idle"]["direita"]

        self.vida_max = 4
        self.vida = 4
        self.balas = BALAS_INICIAIS
        self.laranjas = 0
        self.medkits = 0
        self.ordem_itens = []

        self.ultimo_dano = -INTERVALO_DANO_ZUMBI
        self.tempo_vermelho = 0.0
        self.tempo_branco = 0.0
        self.branco = False
        self.piscadas = 0
        self.efeito_dano = False

        self.fase_morte = 0
        self.frame_morte = 0
        self.tempo_morte = 0.0

    # --------------------------------------------------------------- movimento

    def mover(self, teclado, dt, mundo, mult_velocidade=1.0):
        andando = False
        velocidade_atual = VELOCIDADE_JOGADOR * mult_velocidade

        for tecla, (dx, dy, direcao) in TECLAS_MOVIMENTO.items():
            if teclado.key_pressed(tecla):
                deslocamento_x = dx * velocidade_atual * dt
                novo_x = max(0, min(self.x + deslocamento_x, MAPA_LARGURA - self.w))
                rect_x = pygame.Rect(novo_x + 22, self.y + 30, self.w - 44, self.h - 36)
                if not mundo.colide_tronco(rect_x):
                    self.x = novo_x

                deslocamento_y = dy * velocidade_atual * dt
                novo_y = max(0, min(self.y + deslocamento_y, MAPA_ALTURA - self.h))
                rect_y = pygame.Rect(self.x + 22, novo_y + 30, self.w - 44, self.h - 36)
                if not mundo.colide_tronco(rect_y):
                    self.y = novo_y

                self.direcao = direcao
                andando = True

        if andando:
            self.timer_anim += dt

            if self.timer_anim >= INTERVALO_ANIM_JOGADOR:
                self.timer_anim = 0
                self.frame = (self.frame + 1) % 2
                self.image = self.anim["walk"][self.direcao][self.frame]

        else:
            self.frame = 0
            self.timer_anim = 0
            self.image = self.anim["idle"][self.direcao]

    def limitar_ao_mapa(self):
        self.x = max(0, min(self.x, MAPA_LARGURA - T_PLAYER))
        self.y = max(0, min(self.y, MAPA_ALTURA - T_PLAYER))

    # -------------------------------------------------------------------- dano
    def levar_dano(self, zumbi, agora):
        self.vida = max(0, self.vida - DANO_ZUMBI)
        self.ultimo_dano = agora
        self.tempo_vermelho = DURACAO_VERMELHO
        self.tempo_branco = DURACAO_BRANCO
        self.piscadas = 0
        self.branco = True
        self.efeito_dano = True

        dx, dy = self.x - zumbi.x, self.y - zumbi.y
        d = math.hypot(dx, dy)
        if d != 0:
            self.x += dx / d * FORCA_EMPURRAO
            self.y += dy / d * FORCA_EMPURRAO

        if self.vida <= 0:
            self.branco = False
            self.efeito_dano = False
            self.tempo_branco = 0

    def atualizar_efeito_dano(self, dt):
        if not self.efeito_dano:
            return
        if self.tempo_branco > 0:
            self.tempo_branco -= dt
            return
        self.piscadas += 1
        if self.piscadas < PISCADAS_DANO:
            self.branco = not self.branco
            self.tempo_branco = INTERVALO_PISCADA
        else:
            self.branco = False
            self.efeito_dano = False

    @property
    def morto(self):
        return self.vida <= 0

    # ------------------------------------------------------------------- morte
    def atualizar_morte(self, dt):
        if self.fase_morte != 1:
            return
        self.tempo_morte += dt
        if self.tempo_morte >= 0.1:
            self.tempo_morte = 0
            self.frame_morte += 1
            if self.frame_morte >= len(self.assets.morte):
                self.frame_morte = len(self.assets.morte) - 1
                self.fase_morte = 2
        self.image = self.assets.morte[self.frame_morte]

    # ---------------------------------------------------------------- desenho
    def _imagem_branca(self):
        """Silhueta branca do sprite atual (guardada em cache)."""
        chave = id(self.image)
        if chave not in self._cache_branco:
            mascara = pygame.mask.from_surface(self.image)
            self._cache_branco[chave] = mascara.to_surface(
                setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)
            )
        return self._cache_branco[chave]

    def desenhar(self, tela, cam_x, cam_y):
        img = self._imagem_branca() if self.branco else self.image
        tela.blit(img, (self.x - cam_x, self.y - cam_y))


# =============================================================================
# 5. MUNDO
# =============================================================================
class Mundo:
    """Chão + chunks. Só os chunks perto do jogador são criados e processados."""

    def __init__(self, assets, jogo):
        self.assets = assets
        self.jogo = jogo
        colunas = (MAPA_LARGURA + TAMANHO_CHAO - 1) // TAMANHO_CHAO
        linhas = (MAPA_ALTURA + TAMANHO_CHAO - 1) // TAMANHO_CHAO
        self.tiles = [
            [random.choices((0, 1, 2), weights=(25, 56, 19))[0] for _ in range(linhas)]
            for _ in range(colunas)
        ]
        self.chunks = {}
        self.chunk_atual = None
        self.arvores, self.arbustos, self.zumbis, self.itens = [], [], [], []

    def resetar(self):
        self.chunks.clear()
        self.chunk_atual = None
        self.arvores, self.arbustos, self.zumbis, self.itens = [], [], [], []

    def area_acampamento_rect(self):
        """Retorna a área de colisão do acampamento/base."""
        area = pygame.Rect(
            MAPA_LARGURA - BASE_LARGURA,
            50,
            BASE_LARGURA,
            BASE_ALTURA,
        )
        if self.jogo.acampamento == "barraca":
            j = self.jogo.jogador
            barraca_rect = pygame.Rect(j.x + j.w + 10, j.y - 40, 230, 140)
            return area.union(barraca_rect)
        return area

    def muito_perto_acampamento(self, x, y, w=T_ZUMBI, h=T_ZUMBI):
        """Evita que zumbis nasçam em cima ou muito perto do acampamento."""
        area = self.area_acampamento_rect()
        centro_z = (x + w / 2, y + h / 2)
        centro_a = area.center
        if area.inflate(DIST_MIN_SPAWN_ACAMPAMENTO, DIST_MIN_SPAWN_ACAMPAMENTO).collidepoint(centro_z):
            return True
        return math.hypot(centro_z[0] - centro_a[0], centro_z[1] - centro_a[1]) < DIST_MIN_SPAWN_ACAMPAMENTO

    # -------------------------------------------------------------- geração
    def _gerar_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            return
        rnd = random.Random(int(cx * 73856093 ^ cy * 19349663) % (2 ** 32))
        base_x, base_y = cx * CHUNK_SIZE, cy * CHUNK_SIZE
        area_base = pygame.Rect(
            MAPA_LARGURA - BASE_LARGURA,
            50,
            BASE_LARGURA,
            BASE_ALTURA,
        )

        # Árvores (quantidade reduzida e mais espaçadas)
        arvores = []
        for _ in range(rnd.randint(6, 10)):
            for _ in range(100):
                x = base_x + rnd.randint(0, CHUNK_SIZE - T_ARVORE)
                y = base_y + rnd.randint(0, CHUNK_SIZE - T_ARVORE)
                arvore_rect = pygame.Rect(x, y, T_ARVORE, T_ARVORE)
                if (
                    not arvore_rect.colliderect(area_base)
                    and all(math.hypot(x - a.x, y - a.y) >= DIST_MIN_ARVORES for a in arvores)
                ):
                    if rnd.random() < 0.2:
                        imagem = self.assets.arvore_seca
                    else:
                        imagem = self.assets.arvore

                    arvores.append(Arvore(imagem, x, y, T_ARVORE, T_ARVORE))
                    break

        # Zumbis (longe do ponto onde o jogador nasce e longe do acampamento)
        zumbis = []
        if self.jogo.eh_noite:
            quantidade_zumbis = rnd.choice([0, 1, 1, 2, 2])
        else:
            quantidade_zumbis = rnd.choice([0, 0, 0, 1])

        for _ in range(quantidade_zumbis):
            for _ in range(20):
                x = base_x + rnd.randint(0, CHUNK_SIZE - T_ZUMBI)
                y = base_y + rnd.randint(0, CHUNK_SIZE - T_ZUMBI)
                if (
                    math.hypot(x - JOGADOR_INICIO[0], y - JOGADOR_INICIO[1]) >= DIST_MIN_SPAWN_ZUMBI
                    and not self.muito_perto_acampamento(x, y, T_ZUMBI, T_ZUMBI)
                ):
                    zumbis.append(Zumbi(self.assets, x, y, zumbis))
                    break

        # Arbustos espalhados pelo mapa
        arbustos = []

        for _ in range(rnd.randint(4, 7)):
            for _ in range(30):
                x = base_x + rnd.randint(0, CHUNK_SIZE - 55)
                y = base_y + rnd.randint(0, CHUNK_SIZE - 55)
                arbusto_rect = pygame.Rect(x, y, 55, 55)

                if (
                    not arbusto_rect.colliderect(area_base)
                    and not any(arbusto_rect.colliderect(a.rect) for a in arvores)
                    and not any(arbusto_rect.colliderect(a.rect) for a in arbustos)
                ):
                    arbustos.append(Arbusto(self.assets.arbusto, x, y, 55, 55))
                    break

        # Itens
        itens = []
        for tipo, cfg in ITENS_CFG.items():
            if rnd.random() < cfg["prob"]:
                w, h = cfg["tam"]
                itens.append(
                    Item(
                        tipo,
                        self.assets.itens[tipo],
                        base_x + rnd.randint(0, CHUNK_SIZE - w),
                        base_y + rnd.randint(0, CHUNK_SIZE - h),
                        (base_x, base_y),
                    )
                )

        self.chunks[(cx, cy)] = {
            "arvores": arvores,
            "arbustos": arbustos,
            "zumbis": zumbis,
            "itens": itens,
        }

    def atualizar(self, jx, jy, forcar=False):
        """Cria chunks vizinhos e refaz as listas ativas sem perder zumbis próximos."""
        pcx, pcy = int(jx // CHUNK_SIZE), int(jy // CHUNK_SIZE)
        if (pcx, pcy) == self.chunk_atual and not forcar:
            return
        self.chunk_atual = (pcx, pcy)

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                cx, cy = pcx + dx, pcy + dy
                if 0 <= cx * CHUNK_SIZE < MAPA_LARGURA and 0 <= cy * CHUNK_SIZE < MAPA_ALTURA:
                    self._gerar_chunk(cx, cy)

        self.arvores, self.arbustos, self.zumbis, self.itens = [], [], [], []
        zumbis_vistos = set()

        for (cx, cy), dados in self.chunks.items():
            if abs(cx - pcx) <= 2 and abs(cy - pcy) <= 2:
                self.arvores.extend(dados["arvores"])
                self.arbustos.extend(dados["arbustos"])
                self.itens.extend(dados["itens"])
                for z in dados["zumbis"]:
                    if id(z) not in zumbis_vistos:
                        zumbis_vistos.add(id(z))
                        self.zumbis.append(z)

        # Garante que zumbis fora da janela imediata mas ainda próximos do jogador não sumam
        for dados in self.chunks.values():
            for z in dados["zumbis"]:
                if id(z) not in zumbis_vistos and math.hypot(z.x - jx, z.y - jy) <= DIST_PERSEGUICAO + 200:
                    zumbis_vistos.add(id(z))
                    self.zumbis.append(z)

    def criar_cerco_acampamento(
        self,
        centro_x,
        centro_y,
        quantidade=CERCO_QTD_ZUMBIS,
        raio=CERCO_RAIO,
        atraso_perseguicao=CERCO_ATRASO_PERSEGUICAO,
    ):
        """Cria um círculo de zumbis ao redor do acampamento/personagens."""
        for i in range(quantidade):
            angulo = (2 * math.pi * i) / quantidade
            x = centro_x + math.cos(angulo) * raio - T_ZUMBI / 2
            y = centro_y + math.sin(angulo) * raio - T_ZUMBI / 2
            x = max(0, min(x, MAPA_LARGURA - T_ZUMBI))
            y = max(0, min(y, MAPA_ALTURA - T_ZUMBI))

            if self.muito_perto_acampamento(x, y, T_ZUMBI, T_ZUMBI):
                x = max(0, min(x + math.cos(angulo) * 140, MAPA_LARGURA - T_ZUMBI))
                y = max(0, min(y + math.sin(angulo) * 140, MAPA_ALTURA - T_ZUMBI))

            cx = max(0, min((MAPA_LARGURA - 1) // CHUNK_SIZE, int((x + T_ZUMBI / 2) // CHUNK_SIZE)))
            cy = max(0, min((MAPA_ALTURA - 1) // CHUNK_SIZE, int((y + T_ZUMBI / 2) // CHUNK_SIZE)))
            if (cx, cy) not in self.chunks:
                self._gerar_chunk(cx, cy)

            lista_chunk = self.chunks[(cx, cy)]["zumbis"]
            zumbi = Zumbi(
                self.assets,
                x,
                y,
                lista_chunk,
                dist_perseguicao=max(DIST_PERSEGUICAO, raio + 500),
                atraso_perseguicao=atraso_perseguicao,
            )
            lista_chunk.append(zumbi)
            if zumbi not in self.zumbis:
                self.zumbis.append(zumbi)

    # ------------------------------------------------------------ interações
    def matar_zumbi(self, zumbi):
        if zumbi in zumbi.lista:
            zumbi.lista.remove(zumbi)
        if zumbi in self.zumbis:
            self.zumbis.remove(zumbi)

    def colide_tronco(self, rect):
        """Verifica colisão apenas com o tronco das árvores ativas."""
        for arvore in self.arvores:
            if rect.colliderect(arvore.hitbox_tronco):
                return True
        return False

    def colide_acampamento(self, rect):
        """Verifica colisão do zumbi com o acampamento/base."""
        area = self.area_acampamento_rect().inflate(36, 36)
        return rect.colliderect(area)

    def colide_arvore(self, rect):
        return self.colide_tronco(rect)

    def atualizar_itens(self, dt):
        """Respawn dos itens coletados (em todos os chunks já criados)."""
        for dados in self.chunks.values():
            for item in dados["itens"]:
                item.atualizar(dt)

    def desenhar_chao(self, tela, cam_x, cam_y):
        c0, l0 = int(cam_x // TAMANHO_CHAO), int(cam_y // TAMANHO_CHAO)
        for c in range(c0, c0 + LARGURA_TELA // TAMANHO_CHAO + 2):
            for l in range(l0, l0 + ALTURA_TELA // TAMANHO_CHAO + 2):
                if 0 <= c < len(self.tiles) and 0 <= l < len(self.tiles[0]):
                    tela.blit(
                        self.assets.chao[self.tiles[c][l]],
                        (c * TAMANHO_CHAO - cam_x, l * TAMANHO_CHAO - cam_y),
                    )


# =============================================================================
# 6. JOGO
# =============================================================================
class Jogo:
    def __init__(self):
        pygame.mixer.init()
        self.janela = Window(LARGURA_TELA, ALTURA_TELA)
        self.janela.set_title("apocalipse Runaways")
        self.tela = self.janela.screen
        self.teclado = Window.get_keyboard()
        self.mouse = Mouse()
        self.menu = Menu(self.janela, Keyboard(), Mouse())
        self.assets = Assets()

        self.sobreviventes_resgatados = []
        self.resgate_aberto = False
        self.sobrevivente_selecionado = None
        self.clique_resgate_anterior = False
        self.resgataveis = []
        self.resgate_ignorado = None
        self.salvar_w = 800
        self.salvar_h = int(880 * self.salvar_w / 1568)

        self.salvar_x = (LARGURA_TELA - self.salvar_w) // 2
        self.salvar_y = (ALTURA_TELA - self.salvar_h) // 2

        escala = self.salvar_w / 1568

        self.resgate_sim_rect = pygame.Rect(
            self.salvar_x + int(555 * escala),
            self.salvar_y + int(575 * escala),
            int(200 * escala),
            int(125 * escala),
        )

        self.resgate_nao_rect = pygame.Rect(
            self.salvar_x + int(810 * escala),
            self.salvar_y + int(575 * escala),
            int(200 * escala),
            int(125 * escala),
        )

        # Volume geral: mantém os volumes originais de cada efeito e aplica
        # o controle das configurações como um multiplicador.
        self.volume_geral = 1.0
        self.sons_jogo = [
            self.assets.som_vitoria,
            self.assets.som_ambiente,
            self.assets.musica_noite,
            self.assets.som_barraca,
            self.assets.som_coleta,
            self.assets.som_morte,
            self.assets.som_empurrao,
            self.assets.som_tiro,
            self.assets.som_recupera_vida,
        ]
        self.volumes_originais = [(som, som.get_volume()) for som in self.sons_jogo if som]
        self.sons_jogo.append(self.menu.som)
        self.volumes_originais.append((self.menu.som, self.menu.som.get_volume()))
        self.volume_zumbi_atual = 0.0

        self.mundo = Mundo(self.assets, self)
        self.localidade = 0
        self.eh_noite = False
        self.tempo_periodo = 0.0
        self.escuridao = 0.0
        self.tempo_sem_dormir = 0.0
        self.jogador = Jogador(self.assets, self)
        self.base = Base(self.assets)
        self.quadrado_atual = (
            int((self.jogador.x + self.jogador.w / 2) // LARGURA_TELA),
            int((self.jogador.y + self.jogador.h / 2) // ALTURA_TELA),
        )
        self.sobrevivente = Sobrevivente(
            self.assets,
            self.jogador.x + SOBRI_OFFSET_INICIO,
            self.jogador.y,
        )
        self.resgataveis = []

        self.balas = []

        self.cam_x = self.cam_y = 0
        self.estado = "MENU"
        self.arrastando_volume = False
        self.mochila_aberta = False
        self.e_anterior = False
        self.mouse_anterior = False

        self.clique_esquerdo_mochila_anterior = False
        self.clique_direito_mochila_anterior = False
        self.ultimo_clique_mochila = None
        self.tempo_ultimo_clique_mochila = 0

        self.tempo_espera = 0.0

        # Sistema de acampamento
        self.acampamento = None
        self.tempo_acampamento = 0.0
        self.cerco_pendente = False
        self.cerco_criado_no_escuro = False

        self.c_anterior = False
        self.botao_direito_anterior = False

        self.painel_w = 600
        self.painel_h = 401
        self.painel_x = (LARGURA_TELA - self.painel_w) // 2
        self.painel_y = (ALTURA_TELA - self.painel_h) // 2

        self.sim_rect = pygame.Rect(
            self.painel_x + 0.17 * self.painel_w,
            self.painel_y + 0.50 * self.painel_h,
            0.21 * self.painel_w,
            0.26 * self.painel_h,
        )

        self.nao_rect = pygame.Rect(
            self.painel_x + 0.46 * self.painel_w,
            self.painel_y + 0.50 * self.painel_h,
            0.21 * self.painel_w,
            0.26 * self.painel_h,
        )

        self.fundo_acampamento = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self.fundo_acampamento.fill((0, 0, 0))
        self.fundo_acampamento.set_alpha(150)

        # Efeitos de tela
        self.tela_vermelha = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self.tela_vermelha.fill((255, 0, 0))
        self.tela_vermelha.set_alpha(100)
        self.tela_preta = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self.tela_preta.fill((0, 0, 0))
        self.filtro_ciclo = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self._nivel_filtro = -1
        self.fade_morte = 0.0
        self.alpha_texto_morte = 0.0

        # Ícone da mochila (canto inferior direito)
        icone = self.assets.icone_mochila
        self.pos_icone = (LARGURA_TELA - icone.get_width(), ALTURA_TELA - icone.get_height())

        # Som de zumbi: canal reservado só para ele (nenhum outro som consegue cortá-lo)
        pygame.mixer.set_reserved(1)
        self.canal_zumbi = pygame.mixer.Channel(0)
        self._debug_som_tempo = 0.0
        self.garantir_som_zumbi()

    def garantir_som_zumbi(self):
        """Liga o loop do zumbi no canal reservado, se ele não estiver tocando."""
        som = self.assets.som_zumbi
        if som and not self.canal_zumbi.get_busy():
            som.set_volume(1.0)
            self.canal_zumbi.play(som, loops=-1)
            self.canal_zumbi.set_volume(0)

    def volume_zumbi(self, volume):
        self.garantir_som_zumbi()
        self.volume_zumbi_atual = max(0.0, min(1.0, volume))
        self.canal_zumbi.set_volume(self.volume_zumbi_atual * self.volume_geral)

    def aplicar_volume_geral(self):
        """Aplica o volume escolhido sem apagar os volumes individuais dos sons."""
        for som, volume_original in self.volumes_originais:
            som.set_volume(volume_original * self.volume_geral)
        self.canal_zumbi.set_volume(self.volume_zumbi_atual * self.volume_geral)
        pygame.mixer.music.set_volume(self.volume_geral)

    def parar_som_zumbi(self):
        self.canal_zumbi.stop()

    def criar_resgataveis(self):
        self.resgataveis = []

        centro_jogador = (JOGADOR_INICIO[0] + T_PLAYER / 2, JOGADOR_INICIO[1] + T_PLAYER / 2)
        centro_base = self.base.rect.center

        while len(self.resgataveis) < 3:
            x = random.randint(100, MAPA_LARGURA - T_PLAYER - 100)
            y = random.randint(100, MAPA_ALTURA - T_PLAYER - 100)

            centro = (x + T_PLAYER / 2, y + T_PLAYER / 2)

            if math.hypot(centro[0] - centro_jogador[0], centro[1] - centro_jogador[1]) < 1200:
                continue

            if math.hypot(centro[0] - centro_base[0], centro[1] - centro_base[1]) < 1100:
                continue

            if any(
                math.hypot(centro[0] - s.rect.centerx, centro[1] - s.rect.centery) < 650
                for s in self.resgataveis
            ):
                continue

            identificacao = len(self.resgataveis) + 1
            sobrevivente = SobreviventeResgatavel(
                identificacao,
                self.assets.anim_resgataveis[identificacao],
                x,
                y,
            )
            self.resgataveis.append(sobrevivente)

    def verificar_resgate(self):
        if self.resgate_aberto:
            return

        if self.resgate_ignorado is not None:
            if not self.jogador.rect.colliderect(self.resgate_ignorado.rect):
                self.resgate_ignorado = None

        for sobrevivente in self.resgataveis:
            if sobrevivente is self.resgate_ignorado:
                continue

            if self.jogador.rect.colliderect(sobrevivente.rect):
                self.sobrevivente_selecionado = sobrevivente
                self.resgate_aberto = True
                break

    # ---------------------------------------------------------- novo jogo/menu
    def novo_jogo(self):
        self.localidade = 0
        self.eh_noite = False
        self.tempo_periodo = 0.0
        self.escuridao = 0.0
        self.tempo_sem_dormir = 0.0
        self.acampamento = None
        self.tempo_acampamento = 0.0
        self.cerco_pendente = False
        self.cerco_criado_no_escuro = False
        self.jogador.resetar()
        self.quadrado_atual = (
            int((self.jogador.x + self.jogador.w / 2) // LARGURA_TELA),
            int((self.jogador.y + self.jogador.h / 2) // ALTURA_TELA),
        )
        print("Posição inicial:", self.jogador.x, self.jogador.y)
        self.sobrevivente.restaurar(self.jogador.x + SOBRI_OFFSET_INICIO, self.jogador.y)
        self.balas.clear()
        self.botao_direito_anterior = False
        self.mundo.resetar()
        self.mundo.atualizar(self.jogador.x, self.jogador.y)
        self.sobreviventes_resgatados.clear()
        self.resgate_aberto = False
        self.sobrevivente_selecionado = None
        self.resgate_ignorado = None
        self.clique_resgate_anterior = False
        self.criar_resgataveis()
        self.fade_morte = 0
        self.alpha_texto_morte = 0
        self.mochila_aberta = False
        self.atualizar_camera()

    def ir_para_menu(self):
        if self.assets.som_morte:
            self.assets.som_morte.stop()
        if self.assets.som_ambiente:
            self.assets.som_ambiente.stop()
        self.volume_zumbi(0)
        self.assets.musica_noite.stop()
        self.mochila_aberta = False
        self.estado = "MENU"

    # ------------------------------------------------------------------ estados
    def estado_menu(self):
        acao = self.menu.atualizar()
        if acao == "JOGO":
            self.novo_jogo()
            self.tempo_espera = time.time()
            self.estado = "ESPERA"
        elif acao == "CONFIG":
            self.estado = "CONFIG"

    def estado_espera(self):
        self.tela.fill((0, 0, 0))
        if time.time() - self.tempo_espera >= 0.5:
            tocar(self.assets.som_ambiente, loops=-1)
            self.estado = "JOGO"

    def estado_config(self):
        self.tela.fill((20, 20, 40))

        fonte_titulo = pygame.font.Font(None, 54)
        fonte_texto = pygame.font.Font(None, 30)
        fonte_creditos = pygame.font.Font(None, 24)
        fonte_versao = pygame.font.Font(None, 22)

        titulo = fonte_titulo.render("CONFIGURAÇÕES", True, (255, 255, 255))
        self.tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2, 125))

        texto_volume = fonte_texto.render("VOLUME", True, (255, 255, 255))
        self.tela.blit(texto_volume, (250, 235))

        # Barra de volume: pode clicar em qualquer ponto da barra ou arrastar o círculo.
        barra = pygame.Rect(250, 285, 300, 10)
        raio = 12
        posicao_x = barra.x + int(self.volume_geral * barra.width)
        centro_y = barra.centery

        botao_esquerdo = pygame.mouse.get_pressed()[0]
        mouse_x, mouse_y = pygame.mouse.get_pos()
        area_barra = barra.inflate(raio * 2, raio * 3)
        circulo = pygame.Rect(posicao_x - raio, centro_y - raio, raio * 2, raio * 2)

        if botao_esquerdo and (
            self.arrastando_volume
            or area_barra.collidepoint(mouse_x, mouse_y)
            or circulo.collidepoint(mouse_x, mouse_y)
        ):
            self.arrastando_volume = True
            self.volume_geral = max(0.0, min(1.0, (mouse_x - barra.x) / barra.width))
            self.aplicar_volume_geral()
        elif not botao_esquerdo:
            self.arrastando_volume = False

        # Redesenha o preenchimento e o marcador com o volume atualizado.
        posicao_x = barra.x + int(self.volume_geral * barra.width)
        pygame.draw.rect(self.tela, (90, 90, 110), barra, border_radius=5)
        preenchimento = pygame.Rect(barra.x, barra.y, max(0, posicao_x - barra.x), barra.height)
        pygame.draw.rect(self.tela, (90, 190, 150), preenchimento, border_radius=5)
        pygame.draw.circle(self.tela, (245, 245, 245), (posicao_x, centro_y), raio)

        texto_porcentagem = fonte_texto.render(f"{int(self.volume_geral * 100)}%", True, (255, 255, 255))
        self.tela.blit(texto_porcentagem, (LARGURA_TELA // 2 - texto_porcentagem.get_width() // 2, 315))

        creditos = fonte_creditos.render(
            "Desenvolvido por Ana Carolina e Melissa com o PPlay", True, (220, 220, 220)
        )
        versao = fonte_versao.render("Versão 1.0", True, (190, 190, 190))
        self.tela.blit(creditos, (LARGURA_TELA // 2 - creditos.get_width() // 2, 485))
        self.tela.blit(versao, (LARGURA_TELA // 2 - versao.get_width() // 2, 520))

        if self.teclado.key_pressed("ESC"):
            self.arrastando_volume = False
            self.estado = "MENU"

    def estado_jogo(self, dt):
        if self.acampamento is None:
            e = self.teclado.key_pressed("E")

            if e and not self.e_anterior:
                self.mochila_aberta = not self.mochila_aberta

            self.e_anterior = e

        self.atualizar_acampamento(dt)

        if self.mochila_aberta and self.acampamento is None:
            self.atualizar_mochila()

        if self.resgate_aberto:
            self.atualizar_resgate()

        elif self.acampamento is None and not self.mochila_aberta:
            self.atualizar_mundo(dt)

        else:
            self.mouse_anterior = pygame.mouse.get_pressed()[0]

        self.desenhar_jogo(dt)

        self.desenhar_acampamento()
        self.desenhar_resgate()

        if self.estado == "JOGO" and self.acampamento is None and self.teclado.key_pressed("ESC"):
            self.ir_para_menu()

    def alternar_periodo(self, suave=True):
        """Troca dia/noite e reinicia o relógio do ciclo.

        suave=True  -> ciclo automático (música em fade longo)
        suave=False -> barraca (fade curto, a tela está preta)
        """
        self.eh_noite = not self.eh_noite
        self.tempo_periodo = 0.0
        fade = FADE_MUSICA_MS if suave else FADE_MUSICA_BARRACA_MS

        if self.eh_noite:
            if self.assets.som_ambiente:
                self.assets.som_ambiente.fadeout(fade)
            self.assets.musica_noite.stop()
            self.assets.musica_noite.play(loops=-1, fade_ms=fade)
        else:
            self.assets.musica_noite.fadeout(fade)
            if self.assets.som_ambiente:
                self.assets.som_ambiente.stop()
            tocar(self.assets.som_ambiente, loops=-1, fade_ms=fade)

        self.escuridao = self.calcular_escuridao()

    def calcular_escuridao(self):
        """0 = dia claro, 1 = noite fechada.

        O período fica estável e, nos últimos DURACAO_TRANSICAO segundos, caminha
        suavemente para o valor do próximo período (entardecer / amanhecer).
        """
        base = 1.0 if self.eh_noite else 0.0
        restante = DURACAO_PERIODO - self.tempo_periodo
        if restante >= DURACAO_TRANSICAO:
            return base
        progresso = max(0.0, min(1.0, 1 - restante / DURACAO_TRANSICAO))
        suave = progresso * progresso * (3 - 2 * progresso)     # começa e termina devagar
        return base + ((1 - base) - base) * suave

    def atualizar_ciclo(self, dt):
        self.tempo_periodo += dt
        self.tempo_sem_dormir += dt
        if self.tempo_periodo >= DURACAO_PERIODO:
            self.alternar_periodo()
        self.escuridao = self.calcular_escuridao()

    def esta_cansado(self):
        """Verdadeiro após passar 1 dia inteiro (1 dia + 1 noite) sem armar a barraca."""
        return self.tempo_sem_dormir >= TEMPO_LIMITE_SEM_DORMIR

    def multiplicador_velocidade_personagens(self):
        """Retorna 0.80 (20% mais lentos) após 1 dia inteiro sem armar a barraca."""
        if self.esta_cansado():
            return MULT_VELOCIDADE_CANSADO
        return 1.0

    def desenhar_filtro_ciclo(self):
        nivel = int(self.escuridao * 100)
        if nivel <= 0:
            return
        if nivel != self._nivel_filtro:         # só refaz o filtro quando muda de verdade
            self._nivel_filtro = nivel
            e = nivel / 100
            t = e ** 0.6                         # laranja do crepúsculo -> azul da noite
            cor = tuple(int(a + (b - a) * t) for a, b in zip(COR_CREPUSCULO, COR_NOITE))
            self.filtro_ciclo.fill(cor)
            self.filtro_ciclo.set_alpha(int(ALPHA_NOITE * e))
        self.tela.blit(self.filtro_ciclo, (0, 0))

    def zumbi_no_campo_de_visao(self):
        """Retorna True se há algum zumbi visível na tela / campo de visão atual."""
        return any(z.visivel(self.cam_x, self.cam_y) for z in self.mundo.zumbis)

    def criar_cerco_em_volta_dos_personagens(self):
        """Cria um círculo de zumbis ao redor dos personagens após a tela escurecer."""
        personagens = [self.jogador] + [
            s for s in self.todos_sobreviventes_ativos() if s.vivo
        ]
        centro_x = sum(p.x + p.w / 2 for p in personagens) / len(personagens)
        centro_y = sum(p.y + p.h / 2 for p in personagens) / len(personagens)
        self.mundo.criar_cerco_acampamento(
            centro_x,
            centro_y,
            quantidade=CERCO_QTD_ZUMBIS,
            raio=CERCO_RAIO,
            atraso_perseguicao=CERCO_ATRASO_PERSEGUICAO,
        )

    def atualizar_acampamento(self, dt):
        c = self.teclado.key_pressed("C")

        if c and not self.c_anterior and self.acampamento is None:
            if not self.mochila_aberta:
                self.acampamento = "confirmacao"
                self.cerco_pendente = False
                self.cerco_criado_no_escuro = False

        self.c_anterior = c
        botao_direito = self.mouse.is_button_pressed(1)

        if (
            self.acampamento == "confirmacao"
            and botao_direito
            and not self.botao_direito_anterior
        ):
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if self.sim_rect.collidepoint(mouse_x, mouse_y):
                self.acampamento = "barraca"
                self.tempo_acampamento = 0.0
                self.cerco_pendente = self.zumbi_no_campo_de_visao()
                self.cerco_criado_no_escuro = False
                tocar(self.assets.som_barraca)

            elif self.nao_rect.collidepoint(mouse_x, mouse_y):
                self.acampamento = None
                self.cerco_pendente = False
                self.cerco_criado_no_escuro = False

        self.botao_direito_anterior = botao_direito

        if self.acampamento == "barraca":
            self.tempo_acampamento += dt

            if self.tempo_acampamento >= 1.0:
                self.acampamento = "escuro"
                self.tempo_acampamento = 0.0
                if self.cerco_pendente and not self.cerco_criado_no_escuro:
                    self.criar_cerco_em_volta_dos_personagens()
                    self.cerco_criado_no_escuro = True

        elif self.acampamento == "escuro":
            self.tempo_acampamento += dt

            if self.tempo_acampamento >= 1.0:
                self.alternar_periodo(suave=False)
                self.tempo_sem_dormir = 0.0
                self.acampamento = None
                self.tempo_acampamento = 0.0
                self.cerco_pendente = False
                self.cerco_criado_no_escuro = False

    def desenhar_barraca_mundo(self):
        """Desenha a barraca no mundo (antes do filtro de ciclo para escurecer à noite)."""
        if self.acampamento != "barraca":
            return
        j = self.jogador
        barraca_x = j.x + j.w + 10 - self.cam_x
        barraca_y = j.y - 40 - self.cam_y
        barraca_img = self.assets.barraca.copy()
        if self.eh_noite:
            escuridao_barraca = pygame.Surface(barraca_img.get_size(), pygame.SRCALPHA)
            escuridao_barraca.fill((95, 95, 115, 255))
            barraca_img.blit(escuridao_barraca, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.tela.blit(barraca_img, (barraca_x, barraca_y))

    def desenhar_acampamento(self):
        if self.acampamento == "confirmacao":
            self.tela.blit(self.fundo_acampamento, (0, 0))
            self.tela.blit(self.assets.barraca_botao, (self.painel_x, self.painel_y))

        elif self.acampamento == "escuro":
            self.tela.fill((0, 0, 0))

    def estado_morte(self, dt):
        self.jogador.atualizar_morte(dt)
        self.atualizar_camera()
        self.mundo.desenhar_chao(self.tela, self.cam_x, self.cam_y)
        self.desenhar_objetos()
        self.desenhar_tela_morte(dt)

        if self.teclado.key_pressed("ESC"):
            self.ir_para_menu()

    def total_sobreviventes_salvos_vivos(self):
        """Conta quantos sobreviventes resgatados estão vivos."""
        return sum(1 for s in self.sobreviventes_resgatados if s.vivo)

    def estado_vitoria(self):
        imagem = pygame.transform.smoothscale(self.assets.vitoria, (790, 590))
        x = (LARGURA_TELA - imagem.get_width()) // 2
        y = (ALTURA_TELA - imagem.get_height()) // 2

        self.tela.fill((0, 0, 0))
        self.tela.blit(imagem, (x, y))

        qtd_vivos = self.total_sobreviventes_salvos_vivos()
        texto_salvos = f"SOBREVIVENTES SALVOS: {qtd_vivos}"
        sombra = self.assets.fonte_vitoria_sub.render(texto_salvos, True, (20, 15, 10))
        texto_surf = self.assets.fonte_vitoria_sub.render(texto_salvos, True, (255, 240, 130))

        tx = LARGURA_TELA // 2 - texto_surf.get_width() // 2
        ty = y + int(imagem.get_height() * 0.77)

        self.tela.blit(sombra, (tx + 2, ty + 2))
        self.tela.blit(texto_surf, (tx, ty))

        if self.teclado.key_pressed("ESC"):
            self.ir_para_menu()
            self.assets.som_vitoria.stop()

    # --------------------------------------------------------- atualização (JOGO)

    def verificar_transicao_localidade(self):
        j = self.jogador
        j.limitar_ao_mapa()
        quadrado = (
            int((j.x + j.w / 2) // LARGURA_TELA),
            int((j.y + j.h / 2) // ALTURA_TELA),
        )
        if quadrado != self.quadrado_atual:
            self.transicionar_localidade(quadrado)

    def transicionar_localidade(self, quadrado):
        self.localidade += 1
        self.quadrado_atual = quadrado

    def todos_sobreviventes_ativos(self):
        """Retorna o companheiro inicial e todos os sobreviventes resgatados."""
        return [self.sobrevivente] + self.sobreviventes_resgatados

    def atualizar_mundo(self, dt):
        j = self.jogador
        mult_velocidade = self.multiplicador_velocidade_personagens()
        velocidade_efetiva_jogador = VELOCIDADE_JOGADOR * mult_velocidade
        j.mover(self.teclado, dt, self.mundo, mult_velocidade=mult_velocidade)

        if self.verificar_vitoria():
            return

        self.verificar_resgate()

        if self.resgate_aberto:
            return

        self.atualizar_ciclo(dt)
        self.verificar_transicao_localidade()
        self.mundo.atualizar(j.x, j.y)

        sobreviventes_ativos = [s for s in self.todos_sobreviventes_ativos() if s.vivo]

        # Companheiro inicial segue o jogador respeitando colisão com outros sobreviventes e jogador
        outros_companheiro = [j] + [s for s in sobreviventes_ativos if s is not self.sobrevivente]
        self.sobrevivente.atualizar(
            dt,
            j.x,
            j.y,
            velocidade_efetiva_jogador,
            self.mundo,
            outros_personagens=outros_companheiro,
        )

        # Sobreviventes resgatados seguem formando fila e cercam sem se sobrepor
        for idx, resgatado in enumerate(self.sobreviventes_resgatados):
            if not resgatado.vivo:
                continue
            angulo = (2 * math.pi * idx) / max(1, len(self.sobreviventes_resgatados))
            alvo_x = j.x - math.cos(angulo) * SOBRI_DIST_SEGUIR
            alvo_y = j.y - math.sin(angulo) * SOBRI_DIST_SEGUIR
            outros = [j] + [s for s in sobreviventes_ativos if s is not resgatado]
            resgatado.atualizar(
                dt,
                alvo_x,
                alvo_y,
                velocidade_efetiva_jogador,
                self.mundo,
                outros_personagens=outros,
            )

        aliados = self.todos_sobreviventes_ativos()
        for z in self.mundo.zumbis:
            alvo = escolher_alvo(j, aliados, z)
            z.perseguir(alvo.x, alvo.y, dt, self.mundo)

        self.dano_sobrevivente()
        self.dano_zumbis()
        if self.estado != "JOGO":
            return

        self.atualizar_som_zumbi()
        self.atirar()
        self.atualizar_balas(dt)
        self.mundo.atualizar_itens(dt)
        self.coletar_itens()
        self.atualizar_camera()
        j.atualizar_efeito_dano(dt)

    def atualizar_camera(self):
        j = self.jogador
        self.cam_x = max(0, min(j.x - CAMERA_OFFSET[0], MAPA_LARGURA - LARGURA_TELA))
        self.cam_y = max(0, min(j.y - CAMERA_OFFSET[1], MAPA_ALTURA - ALTURA_TELA))

    def dano_sobrevivente(self):
        for s in self.todos_sobreviventes_ativos():
            if not s.vivo:
                continue
            for z in self.mundo.zumbis:
                if math.hypot(s.x - z.x, s.y - z.y) <= DIST_ATAQUE_ZUMBI:
                    s.receber_dano()
                    break

    def dano_zumbis(self):
        j = self.jogador
        agora = time.time()
        for z in self.mundo.zumbis:
            if (
                math.hypot(j.x - z.x, j.y - z.y) <= DIST_ATAQUE_ZUMBI
                and agora - j.ultimo_dano >= INTERVALO_DANO_ZUMBI
            ):
                j.levar_dano(z, agora)
                tocar(self.assets.som_empurrao)
                if j.morto:
                    self.iniciar_morte()
                return

    def iniciar_morte(self):
        j = self.jogador
        j.fase_morte = 0
        j.frame_morte = 0
        j.tempo_morte = 0
        self.fade_morte = 0
        self.alpha_texto_morte = 0
        self.estado = "MORTE"
        if self.assets.som_ambiente:
            self.assets.som_ambiente.stop()
        self.volume_zumbi(0)
        tocar(self.assets.som_morte)

    def atualizar_som_zumbi(self):
        j = self.jogador
        menor = 800
        for z in self.mundo.zumbis:
            menor = min(menor, math.hypot(j.x - z.x, j.y - z.y))
        self.volume_zumbi(max(0.0, min(1.0, 1 - menor / 800)))

        if DEBUG_SOM:
            agora = time.time()
            if agora - self._debug_som_tempo >= 1:
                self._debug_som_tempo = agora
                print(
                    f"[som zumbi] carregado={self.assets.som_zumbi is not None} "
                    f"tocando={self.canal_zumbi.get_busy()} "
                    f"volume_canal={self.canal_zumbi.get_volume():.2f} "
                    f"zumbi_mais_perto={menor:.0f}px "
                    f"zumbis_ativos={len(self.mundo.zumbis)} noite={self.eh_noite}"
                )
                amb = self.assets.som_ambiente
                ocupados = sum(
                    pygame.mixer.Channel(i).get_busy()
                    for i in range(pygame.mixer.get_num_channels())
                )
                print(
                    f"[sons] ambiente_copias={amb.get_num_channels() if amb else 0} "
                    f"noite_copias={self.assets.musica_noite.get_num_channels()} "
                    f"canais_ocupados={ocupados}/{pygame.mixer.get_num_channels()}"
                )

    def coletar_itens(self):
        j = self.jogador
        rect = j.rect
        for item in self.mundo.itens:
            if item.coletado or not rect.colliderect(item.rect):
                continue
            item.coletado = True
            item.tempo_respawn = 0
            tocar(self.assets.som_coleta)
            if item.tipo == "municao":
                j.balas += BALAS_POR_PACOTE
            elif item.tipo == "medkit":
                if "medkit" not in j.ordem_itens:
                    j.ordem_itens.append("medkit")
                j.medkits += 1
            elif item.tipo == "laranja":
                if "laranja" not in j.ordem_itens:
                    j.ordem_itens.append("laranja")
                j.laranjas += 1

    # ------------------------------------------------------------------- tiros
    def atirar(self):
        botao = pygame.mouse.get_pressed()[0]
        j = self.jogador
        if botao and not self.mouse_anterior and j.balas > 0:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            cx = j.x - self.cam_x + j.w / 2
            cy = j.y - self.cam_y + j.h / 2
            dx, dy = mouse_x - cx, mouse_y - cy
            d = math.hypot(dx, dy)
            if d != 0:
                j.balas -= 1
                tocar(self.assets.som_tiro)
                dx, dy = dx / d, dy / d
                angulo = math.degrees(math.atan2(dy, dx))
                imagem = pygame.transform.rotate(self.assets.tiro, -angulo)
                self.balas.append(Bala(imagem, j.x + j.w / 2, j.y + j.h / 2, dx, dy))
        self.mouse_anterior = botao

    def atualizar_balas(self, dt):
        for b in self.balas[:]:
            b.atualizar(dt)
            if b.fora_do_mapa():
                self.balas.remove(b)
                continue
            for z in self.mundo.zumbis:
                if z.acertado_por(b.x, b.y):
                    z.vida -= 1
                    self.balas.remove(b)
                    if z.vida <= 0:
                        self.mundo.matar_zumbi(z)
                    break

    # ----------------------------------------------------------------- desenho
    def desenhar_jogo(self, dt):
        self.mundo.desenhar_chao(self.tela, self.cam_x, self.cam_y)
        self.desenhar_itens_chao()
        self.base.desenhar(self.tela, self.cam_x, self.cam_y)
        self.desenhar_objetos()
        self.desenhar_barraca_mundo()
        for b in self.balas:
            b.desenhar(self.tela, self.cam_x, self.cam_y)
        self.desenhar_filtro_ciclo()
        self.desenhar_avisos_cansado()
        self.desenhar_hud(dt)
        if self.mochila_aberta:
            self.volume_zumbi(0)
            self.desenhar_mochila_tela()

    def desenhar_avisos_cansado(self):
        """Desenha 'cansado' em vermelho flutuando acima dos personagens quando cansados."""
        if not self.esta_cansado():
            return

        flutuacao = math.sin(pygame.time.get_ticks() * 0.008) * 4
        personagens = [self.jogador] + [
            s for s in self.todos_sobreviventes_ativos() if s.vivo
        ]
        texto = self.assets.texto_cansado

        for p in personagens:
            if not p.visivel(self.cam_x, self.cam_y):
                continue
            topo_barra = p.y - self.cam_y - 28 if isinstance(p, Sobrevivente) else p.y - self.cam_y
            tx = p.x - self.cam_x + p.w / 2 - texto.get_width() / 2
            ty = topo_barra - texto.get_height() - 6 + flutuacao
            self.tela.blit(texto, (tx, ty))

    def desenhar_itens_chao(self):
        for item in self.mundo.itens:
            if not item.coletado and item.visivel(self.cam_x, self.cam_y):
                item.desenhar(self.tela, self.cam_x, self.cam_y)

    def desenhar_objetos(self):
        cx, cy = self.cam_x, self.cam_y
        objs = [o for o in self.mundo.arvores if o.visivel(cx, cy)]
        objs += [a for a in self.mundo.arbustos if a.visivel(cx, cy)]
        objs += [z for z in self.mundo.zumbis if z.visivel(cx, cy)]
        objs.append(self.jogador)
        if self.sobrevivente.vivo:
            objs.append(self.sobrevivente)
        objs += [s for s in self.sobreviventes_resgatados if s.vivo]
        objs += [s for s in self.resgataveis if s.visivel(cx, cy)]
        objs.sort(key=lambda o: o.ordem_y)

        for obj in objs:
            if isinstance(obj, Sobrevivente) and obj.oculto_piscando:
                continue
            obj.desenhar(self.tela, cx, cy)
            if isinstance(obj, Zumbi):
                barra = self.assets.barra_zumbi[nivel_barra(obj.vida)]
                sx = obj.x - cx + obj.w / 2 - barra.get_width() / 2
                sy = obj.y - cy - barra.get_height() + 30
                self.tela.blit(barra, (sx, sy))
            elif isinstance(obj, Sobrevivente):
                barra = self.assets.barra_sobri[nivel_barra(obj.vida)]
                sx = obj.x - cx + obj.w / 2 - barra.get_width() / 2
                sy = obj.y - cy - 28
                self.tela.blit(barra, (sx, sy))

    def desenhar_hud(self, dt):
        j = self.jogador
        self.tela.blit(self.assets.barra_jogador[nivel_barra(j.vida)], (10, 10))

        texto = self.assets.fonte.render(f"BALAS: {j.balas}", True, (255, 255, 255))
        self.tela.blit(texto, (20, 80))

        self.tela.blit(self.assets.icone_mochila, self.pos_icone)
        self.tela.blit(
            self.assets.texto_abrir_mochila,
            (self.pos_icone[0] - 10, self.pos_icone[1] - 5),
        )

        if j.tempo_vermelho > 0:
            j.tempo_vermelho -= dt
            self.tela.blit(self.tela_vermelha, (0, 0))

    def desenhar_mochila_tela(self):
        self.tela.blit(self.assets.tela_mochila, (100, 0))

        posicoes = [
            (270, 220),
            (410, 220),
            (270, 350),
            (410, 350),
        ]

        imagens = {
            "laranja": self.assets.laranja_mochila,
            "medkit": self.assets.medkit_mochila,
        }

        quantidades = {
            "laranja": self.jogador.laranjas,
            "medkit": self.jogador.medkits,
        }

        for i, item in enumerate(self.jogador.ordem_itens):
            if i >= len(posicoes):
                break

            if quantidades[item] > 0:
                x, y = posicoes[i]

                self.tela.blit(imagens[item], (x, y))

                texto = self.assets.fonte.render(
                    f"x{quantidades[item]}",
                    True,
                    (255, 255, 255),
                )

                self.tela.blit(texto, (x + 80, y + 80))

    def atualizar_mochila(self):
        j = self.jogador

        botoes = pygame.mouse.get_pressed()
        esquerdo = botoes[0]
        direito = botoes[2]

        clique_esquerdo = esquerdo and not self.clique_esquerdo_mochila_anterior
        clique_direito = direito and not self.clique_direito_mochila_anterior

        self.clique_esquerdo_mochila_anterior = esquerdo
        self.clique_direito_mochila_anterior = direito

        if not clique_esquerdo and not clique_direito:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        posicoes = [(270, 220), (410, 220), (270, 350), (410, 350)]

        quantidades = {"laranja": j.laranjas, "medkit": j.medkits}

        for i, item in enumerate(j.ordem_itens):
            if i >= len(posicoes):
                break

            if quantidades[item] <= 0:
                continue

            x, y = posicoes[i]
            area = pygame.Rect(x, y, 110, 110)

            if not area.collidepoint(mouse_x, mouse_y):
                continue

            if clique_direito:
                if item == "laranja":
                    j.laranjas -= 1
                elif item == "medkit":
                    j.medkits -= 1

                self.ultimo_clique_mochila = None

            elif clique_esquerdo:
                tempo_atual = pygame.time.get_ticks()

                if (
                    self.ultimo_clique_mochila == item
                    and tempo_atual - self.tempo_ultimo_clique_mochila <= 350
                ):
                    if j.vida < j.vida_max:
                        if item == "medkit":
                            j.vida = min(j.vida_max, j.vida + 2)
                            j.medkits -= 1

                        elif item == "laranja":
                            j.vida = min(j.vida_max, j.vida + 1)
                            j.laranjas -= 1

                        tocar(self.assets.som_recupera_vida)

                    self.ultimo_clique_mochila = None

                else:
                    self.ultimo_clique_mochila = item
                    self.tempo_ultimo_clique_mochila = tempo_atual

            # Remove o item da ordem quando sua quantidade chega a zero
            if item == "laranja" and j.laranjas == 0:
                j.ordem_itens.remove("laranja")

            elif item == "medkit" and j.medkits == 0:
                j.ordem_itens.remove("medkit")

            break

    def desenhar_tela_morte(self, dt):
        j = self.jogador
        if j.fase_morte == 0:
            self.fade_morte += 300 * dt
            if self.fade_morte >= 255:
                self.fade_morte = 255
                j.fase_morte = 1

        self.tela_preta.set_alpha(int(self.fade_morte))
        self.tela.blit(self.tela_preta, (0, 0))

        if j.fase_morte >= 1:
            j.desenhar(self.tela, self.cam_x, self.cam_y)

        if j.fase_morte == 2:
            self.alpha_texto_morte = min(255, self.alpha_texto_morte + 100 * dt)
            alpha = int(self.alpha_texto_morte)
            t1, t2 = self.assets.texto_morte, self.assets.texto_recomecar
            t1.set_alpha(alpha)
            t2.set_alpha(alpha)
            self.tela.blit(t1, (LARGURA_TELA // 2 - t1.get_width() // 2, 450))
            self.tela.blit(t2, (LARGURA_TELA // 2 - t2.get_width() // 2, 550))

    def verificar_vitoria(self):
        if self.jogador.rect.colliderect(self.base.hitbox):
            self.estado = "VITORIA"

            if self.assets.som_ambiente:
                self.assets.som_ambiente.stop()

            self.assets.musica_noite.stop()

            self.parar_som_zumbi()

            self.assets.som_vitoria.play()

            return True
        return False

    def atualizar_resgate(self):
        botao_esquerdo = pygame.mouse.get_pressed()[0]

        clique = botao_esquerdo and not self.clique_resgate_anterior

        self.clique_resgate_anterior = botao_esquerdo

        if not self.resgate_aberto or not clique:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        sobrevivente = self.sobrevivente_selecionado

        if self.resgate_sim_rect.collidepoint(mouse_x, mouse_y):
            novo_sobrevivente = Sobrevivente(
                self.assets,
                sobrevivente.x,
                sobrevivente.y,
                self.assets.anim_resgataveis[sobrevivente.identificacao],
                dist_seguir=65,
            )

            self.sobreviventes_resgatados.append(novo_sobrevivente)

            self.resgataveis.remove(sobrevivente)

            self.resgate_aberto = False
            self.sobrevivente_selecionado = None

        # O jogador escolheu NÃO
        elif self.resgate_nao_rect.collidepoint(mouse_x, mouse_y):
            self.resgate_ignorado = sobrevivente

            self.resgate_aberto = False
            self.sobrevivente_selecionado = None

    def desenhar_resgate(self):
        if self.resgate_aberto:
            self.tela.blit(self.fundo_acampamento, (0, 0))

            imagem = pygame.transform.smoothscale(
                self.assets.salvar, (self.salvar_w, self.salvar_h)
            )

            self.tela.blit(imagem, (self.salvar_x, self.salvar_y))

    # ------------------------------------------------------------ loop principal
    def executar(self):
        while True:
            dt = self.janela.delta_time()
            if self.estado == "MENU":
                self.estado_menu()
            elif self.estado == "ESPERA":
                self.estado_espera()
            elif self.estado == "JOGO":
                self.estado_jogo(dt)
            elif self.estado == "CONFIG":
                self.estado_config()
            elif self.estado == "MORTE":
                self.estado_morte(dt)
            elif self.estado == "VITORIA":
                self.estado_vitoria()
            self.janela.update()


if __name__ == "__main__":
    Jogo().executar()