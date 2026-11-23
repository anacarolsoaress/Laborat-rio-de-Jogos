"""Apocalipse Runaways - versão 2 organizada.

Estrutura:
  1. CONFIGURAÇÕES   - constantes do jogo
  2. UTILIDADES      - funções auxiliares (imagens, sons)
  3. ASSETS          - carregamento de imagens, fontes e sons (uma vez só)
  4. ENTIDADES       - Entidade, Arvore, Zumbi, Item, Bala, Jogador
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
from Sobrevivente import Sobrevivente

# =============================================================================
# 1. CONFIGURAÇÕES
# =============================================================================
LARGURA_TELA, ALTURA_TELA = 800, 600
MAPA_LARGURA, MAPA_ALTURA = 9600, 6000
CHUNK_SIZE = 1200
TAMANHO_CHAO = 600

JOGADOR_INICIO = (400, 300)
CAMERA_OFFSET = (350, 250)          # posição do jogador na tela

T_PLAYER = 100
T_ZUMBI = 125
T_ARVORE = 200

VELOCIDADE_JOGADOR = 500
VELOCIDADE_ZUMBI = 100
VELOCIDADE_BALA = 800
INTERVALO_ANIM_JOGADOR = 10 / 100   # segundos por frame
INTERVALO_ANIM_ZUMBI = 10 / 70

# Zumbis
DIST_PERSEGUICAO = 800
DIST_ATAQUE_ZUMBI = 70
DIST_MIN_SPAWN_ZUMBI = 800
INTERVALO_DANO_ZUMBI = 3
DANO_ZUMBI = 1
FORCA_EMPURRAO = 50
HITBOX_ZUMBI = (45, 75)

# Árvores
DIST_MIN_ARVORES = 150

# Efeitos de dano
DURACAO_VERMELHO = 0.2
DURACAO_BRANCO = 0.4
PISCADAS_DANO = 20
INTERVALO_PISCADA = 0.1

# Munição
BALAS_INICIAIS = 10
BALAS_POR_PACOTE = 10

# Itens espalhados pelo mapa (prob = chance de aparecer em cada chunk)
ITENS_CFG = {
    "municao": {"arquivo": "balas", "tam": (50, 50), "respawn": 10, "prob": 0.75, "realocar": True},
    "medkit": {"arquivo": "medkit", "tam": (50, 50), "respawn": 15, "prob": 0.125, "realocar": False},
    "laranja": {"arquivo": "laranja", "tam": (40, 40), "respawn": 10, "prob": 0.375, "realocar": False},
}

# Direções: tecla -> (dx, dy, direção)
TECLAS_MOVIMENTO = {
    "LEFT": (-1, 0, "esquerda"),
    "RIGHT": (1, 0, "direita"),
    "UP": (0, -1, "tras"),
    "DOWN": (0, 1, "frente"),
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

        # Personagens
        self.anim_jogador = self._animacao_jogador()
        self.anim_zumbi = self._animacao_zumbi()
        self.zumbi_parado = img("zumbiF1", (T_ZUMBI, T_ZUMBI))
        self.sobri_parado = img("sobriF1", (T_SOBRI, T_SOBRI))
        self.morte = [img("normal", (100, 100))]
        self.morte += [img(f"trans{i}", (100, 100)) for i in range(1, 10)]
        self.morte.append(img("morte", (100, 100)))

        # Itens, tiros e mochila
        self.itens = {tipo: img(c["arquivo"], c["tam"]) for tipo, c in ITENS_CFG.items()}
        self.tiro = img("tiro", (60, 30))
        self.icone_mochila = img("icone_mochila", (90, 90))
        self.tela_mochila = img("mochila", (600, 600))
        self.laranja_mochila = img("laranja", (100, 100))
        self.medkit_mochila = img("medkit",(100,100))

        # Barras de vida
        self.barra_jogador = {i: img(f"barra_vida_{i}", (200, 70)) for i in range(5)}
        self.barra_zumbi = {i: img(f"barra_zumbi_{i}", (100, 20)) for i in range(5)}

        # Fontes e textos que não mudam (renderizados uma única vez)
        try:
            fonte_morte = pygame.font.Font("Creepster.ttf", 90)
        except Exception:
            fonte_morte = pygame.font.Font(None, 90)
        self.fonte = pygame.font.Font(None, 30)
        self.texto_morte = fonte_morte.render("VOCÊ É UM DE NÓS...", True, (255, 0, 0))
        self.texto_recomecar = self.fonte.render("clique ESC para recomeçar", True, (255, 255, 255))
        self.texto_abrir_mochila = self.fonte.render("E para abrir", True, (255, 255, 255))

        # Sons
        self.som_ambiente = carregar_som("ambiente", 0.1)
        self.som_morte = carregar_som("morte", 0.2)
        self.som_empurrao = carregar_som("empurrao")
        self.som_zumbi = carregar_som("som_zumbi", 0)
        self.som_tiro = carregar_som("som_tiro", 0.09)

    @staticmethod
    def _animacao_jogador():
        """{'idle': {dir: img}, 'walk': {dir: [img, img]}}"""
        anim = {"idle": {}, "walk": {}}
        for direcao, letra in LETRA_DIRECAO.items():
            tam = TAMANHO_JOGADOR_DIRECAO[direcao]
            anim["idle"][direcao] = carregar_imagem(f"boneco{letra}1", tam)
            anim["walk"][direcao] = [carregar_imagem(f"boneco{letra}2", tam),
                                     carregar_imagem(f"boneco{letra}3", tam)]
        return anim

    @staticmethod
    def _animacao_zumbi():
        """{dir: [img, img]}"""
        tam = (T_ZUMBI, T_ZUMBI)
        return {d: [carregar_imagem(f"zumbi{l}2", tam), carregar_imagem(f"zumbi{l}3", tam)]
                for d, l in LETRA_DIRECAO.items()}


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
    def ordem_y(self):
        """Ordena o desenho: quem está mais abaixo aparece na frente."""
        return self.y + self.h

    def visivel(self, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        return sx + self.w > 0 and sx < LARGURA_TELA and sy + self.h > 0 and sy < ALTURA_TELA

    def desenhar(self, tela, cam_x, cam_y):
        tela.blit(self.image, (self.x - cam_x, self.y - cam_y))


class Arvore(Entidade):
    @property
    def ordem_y(self):
        return self.y + self.h - 30


class Zumbi(Entidade):
    def __init__(self, assets, x, y, lista):
        super().__init__(assets.zumbi_parado, x, y, T_ZUMBI, T_ZUMBI)
        self.anim = assets.anim_zumbi
        self.lista = lista              # lista do chunk onde ele nasceu
        self.vida_maxima = 4
        self.vida = 4
        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0.0

    def perseguir(self, jx, jy, dt):
        dx, dy = jx - self.x, jy - self.y
        dist = math.hypot(dx, dy)
        if dist > DIST_PERSEGUICAO:
            return
        if dist != 0:
            self.x += dx / dist * VELOCIDADE_ZUMBI * dt
            self.y += dy / dist * VELOCIDADE_ZUMBI * dt

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
            if cfg["realocar"]:      # reaparece em outro lugar do mesmo chunk
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
    def __init__(self, assets, x, y):
        super().__init__(
            assets.sobri_parado,
            x,
            y,
            T_SOBRI,
            T_SOBRI
        )

        self.vida_maxima = 2
        self.vida = 2

        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0.0
        
    @property
    def vivo(self):
        return self.vida > 0
    
    def receber_dano(self):
        if not self.vivo:
            return False

        agora = time.time()

        if agora - self.ultimo_dano < self.intervalo_dano:
            return False

        self.vida -= 1
        self.ultimo_dano = agora

        return True
    def resetar(self, x, y):
        self.x = x
        self.y = y

        self.vida = self.vida_maxima

        self.ultimo_dano = float("-inf")

        self.direcao = "frente"
        self.frame = 0
        self.timer_anim = 0.0

        self.image = self.image
    
def escolher_alvo(jogador, sobrevivente, zumbi):
    alvos = [jogador]

    if sobrevivente.vida > 0:
        alvos.append(sobrevivente)

    return min(
        alvos,
        key=lambda alvo: math.hypot(
            alvo.x - zumbi.x,
            alvo.y - zumbi.y
        )
    )

class Jogador(Entidade):
    def __init__(self, assets):
        super().__init__(assets.anim_jogador["idle"]["direita"], *JOGADOR_INICIO, T_PLAYER, T_PLAYER)
        self.assets = assets
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

        self.fase_morte = 0     # 0 = escurecendo, 1 = animação, 2 = texto final
        self.frame_morte = 0
        self.tempo_morte = 0.0
        

    # --------------------------------------------------------------- movimento
    def mover(self, teclado, dt):
        andando = False
        for tecla, (dx, dy, direcao) in TECLAS_MOVIMENTO.items():
            if teclado.key_pressed(tecla):
                self.x += dx * VELOCIDADE_JOGADOR * dt
                self.y += dy * VELOCIDADE_JOGADOR * dt
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
                setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        return self._cache_branco[chave]

    def desenhar(self, tela, cam_x, cam_y):
        img = self._imagem_branca() if self.branco else self.image
        tela.blit(img, (self.x - cam_x, self.y - cam_y))


# =============================================================================
# 5. MUNDO
# =============================================================================
class Mundo:
    """Chão + chunks. Só os chunks perto do jogador são criados e processados."""

    def __init__(self, assets):
        self.assets = assets
        colunas, linhas = MAPA_LARGURA // TAMANHO_CHAO, MAPA_ALTURA // TAMANHO_CHAO
        # chão, chao2, chao3 com as mesmas chances do jogo original (25% / 56% / 19%)
        self.tiles = [[random.choices((0, 1, 2), weights=(25, 56, 19))[0] for _ in range(linhas)]
                      for _ in range(colunas)]
        self.chunks = {}
        self.chunk_atual = None
        self.arvores, self.zumbis, self.itens = [], [], []

    def resetar(self):
        self.chunks.clear()
        self.chunk_atual = None
        self.arvores, self.zumbis, self.itens = [], [], []

    # -------------------------------------------------------------- geração
    def _gerar_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            return
        rnd = random.Random(int(cx * 73856093 ^ cy * 19349663) % (2 ** 32))
        base_x, base_y = cx * CHUNK_SIZE, cy * CHUNK_SIZE

        # Árvores (sem ficarem coladas umas nas outras)
        arvores = []
        for _ in range(rnd.randint(10, 15)):
            for _ in range(100):
                x = base_x + rnd.randint(0, CHUNK_SIZE - T_ARVORE)
                y = base_y + rnd.randint(0, CHUNK_SIZE - T_ARVORE)
                if all(math.hypot(x - a.x, y - a.y) >= DIST_MIN_ARVORES for a in arvores):
                    arvores.append(Arvore(self.assets.arvore, x, y, T_ARVORE, T_ARVORE))
                    break

        # Zumbis (longe do ponto onde o jogador nasce)
        zumbis = []
        for _ in range(rnd.choice([0, 1, 1, 2, 2])):
            for _ in range(20):
                x = base_x + rnd.randint(0, CHUNK_SIZE - T_ZUMBI)
                y = base_y + rnd.randint(0, CHUNK_SIZE - T_ZUMBI)
                if math.hypot(x - JOGADOR_INICIO[0], y - JOGADOR_INICIO[1]) >= DIST_MIN_SPAWN_ZUMBI:
                    zumbis.append(Zumbi(self.assets, x, y, zumbis))
                    break

        # Itens
        itens = []
        for tipo, cfg in ITENS_CFG.items():
            if rnd.random() < cfg["prob"]:
                w, h = cfg["tam"]
                itens.append(Item(tipo, self.assets.itens[tipo],
                                  base_x + rnd.randint(0, CHUNK_SIZE - w),
                                  base_y + rnd.randint(0, CHUNK_SIZE - h),
                                  (base_x, base_y)))

        self.chunks[(cx, cy)] = {"arvores": arvores, "zumbis": zumbis, "itens": itens}

    def atualizar(self, jx, jy, forcar=False):
        """Cria chunks vizinhos e refaz as listas ativas (só quando muda de chunk)."""
        pcx, pcy = int(jx // CHUNK_SIZE), int(jy // CHUNK_SIZE)
        if (pcx, pcy) == self.chunk_atual and not forcar:
            return
        self.chunk_atual = (pcx, pcy)

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cx, cy = pcx + dx, pcy + dy
                if 0 <= cx * CHUNK_SIZE < MAPA_LARGURA and 0 <= cy * CHUNK_SIZE < MAPA_ALTURA:
                    self._gerar_chunk(cx, cy)

        self.arvores, self.zumbis, self.itens = [], [], []
        for (cx, cy), dados in self.chunks.items():
            if abs(cx - pcx) <= 2 and abs(cy - pcy) <= 2:
                self.arvores.extend(dados["arvores"])
                self.zumbis.extend(dados["zumbis"])
                self.itens.extend(dados["itens"])

    # ------------------------------------------------------------ interações
    def matar_zumbi(self, zumbi):
        zumbi.lista.remove(zumbi)
        self.zumbis.remove(zumbi)

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
                    tela.blit(self.assets.chao[self.tiles[c][l]],
                              (c * TAMANHO_CHAO - cam_x, l * TAMANHO_CHAO - cam_y))


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
        self.menu = Menu(self.janela, Keyboard(), Mouse())

        self.assets = Assets()
        self.mundo = Mundo(self.assets)
        self.jogador = Jogador(self.assets)
        self.sobrevivente = Sobrevivente(
            self.assets,
            self.jogador.x + 100,
            self.jogador.y
        )
        self.balas = []

        self.cam_x = self.cam_y = 0
        self.estado = "MENU"
        self.mochila_aberta = False
        self.e_anterior = False
        self.mouse_anterior = False
        self.tempo_espera = 0.0

        # Efeitos de tela
        self.tela_vermelha = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self.tela_vermelha.fill((255, 0, 0))
        self.tela_vermelha.set_alpha(100)
        self.tela_preta = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        self.tela_preta.fill((0, 0, 0))
        self.fade_morte = 0.0
        self.alpha_texto_morte = 0.0

        # Ícone da mochila (canto inferior direito)
        icone = self.assets.icone_mochila
        self.pos_icone = (LARGURA_TELA - icone.get_width(), ALTURA_TELA - icone.get_height())

        # Som de zumbi toca em loop; só o volume muda conforme a distância
        tocar(self.assets.som_zumbi, loops=-1)

    # ---------------------------------------------------------- novo jogo/menu
    def novo_jogo(self):
        self.jogador.resetar()
        self.sobrevivente.resetar(
            self.jogador.x + 100,
            self.jogador.y
        )
        self.balas.clear()
        self.mundo.resetar()
        self.mundo.atualizar(self.jogador.x, self.jogador.y)
        self.fade_morte = 0
        self.alpha_texto_morte = 0
        self.mochila_aberta = False
        self.acampamento= None
        self.tempo_acampamento=0.0
        self.c_anterior= False
        self.atualizar_camera()

    def ir_para_menu(self):
        if self.assets.som_morte:
            self.assets.som_morte.stop()
        if self.assets.som_ambiente:
            self.assets.som_ambiente.stop()
        if self.assets.som_zumbi:
            self.assets.som_zumbi.set_volume(0)
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
        # configurações aqui
        if self.teclado.key_pressed("ESC"):
            self.estado = "MENU"

    def estado_jogo(self, dt):
        e = self.teclado.key_pressed("E")
        if e and not self.e_anterior:
            self.mochila_aberta = not self.mochila_aberta
        self.e_anterior = e

        if not self.mochila_aberta:
            self.atualizar_mundo(dt)
        self.desenhar_jogo(dt)

        if self.estado == "JOGO" and self.teclado.key_pressed("ESC"):
            self.ir_para_menu()

    def estado_morte(self, dt):
        self.jogador.atualizar_morte(dt)
        self.atualizar_camera()
        self.mundo.desenhar_chao(self.tela, self.cam_x, self.cam_y)
        self.desenhar_objetos()
        self.desenhar_tela_morte(dt)

        if self.teclado.key_pressed("ESC"):
            self.ir_para_menu()

    # --------------------------------------------------------- atualização (JOGO)
    def atualizar_mundo(self, dt):
        j = self.jogador
        j.mover(self.teclado, dt)
        self.mundo.atualizar(j.x, j.y)

        for z in self.mundo.zumbis:
            alvo = escolher_alvo(j, sobrevivente, z)
            z.perseguir(alvo.x, alvo.y, dt)
        if sobrevivente.vivo:
            for z in self.mundo.zumbis:
                if z.rect.colliderect(sobrevivente.rect):
                    sobrevivente.receber_dano()

        self.dano_zumbis()
        if self.estado != "JOGO":
            return

        self.atualizar_som_zumbi()
        self.atirar()
        self.atualizar_balas(dt)
        self.mundo.atualizar_itens(dt)
        self.coletar_itens()
        j.limitar_ao_mapa()
        j.atualizar_efeito_dano(dt)
        self.atualizar_camera()

    def atualizar_camera(self):
        j = self.jogador
        self.cam_x = max(0, min(j.x - CAMERA_OFFSET[0], MAPA_LARGURA - LARGURA_TELA))
        self.cam_y = max(0, min(j.y - CAMERA_OFFSET[1], MAPA_ALTURA - ALTURA_TELA))

    def dano_zumbis(self):
        j = self.jogador
        agora = time.time()
        for z in self.mundo.zumbis:
            if (math.hypot(j.x - z.x, j.y - z.y) <= DIST_ATAQUE_ZUMBI
                    and agora - j.ultimo_dano >= INTERVALO_DANO_ZUMBI):
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
        if self.assets.som_zumbi:
            self.assets.som_zumbi.set_volume(0)
        tocar(self.assets.som_morte)

    def atualizar_som_zumbi(self):
        som = self.assets.som_zumbi
        if not som:
            return
        j = self.jogador
        menor = 800
        for z in self.mundo.zumbis:
            menor = min(menor, math.hypot(j.x - z.x, j.y - z.y))
        som.set_volume(max(0.0, min(1.0, 1 - menor / 800)))

    def coletar_itens(self):
        j = self.jogador
        rect = j.rect
        for item in self.mundo.itens:
            if item.coletado or not rect.colliderect(item.rect):
                continue
            item.coletado = True
            item.tempo_respawn = 0
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
        self.desenhar_objetos()
        for b in self.balas:
            b.desenhar(self.tela, self.cam_x, self.cam_y)
        self.desenhar_hud(dt)
        if self.mochila_aberta:
            if self.assets.som_zumbi:
                self.assets.som_zumbi.set_volume(0)
            self.desenhar_mochila_tela()

    def desenhar_itens_chao(self):
        for item in self.mundo.itens:
            if not item.coletado and item.visivel(self.cam_x, self.cam_y):
                item.desenhar(self.tela, self.cam_x, self.cam_y)

    def desenhar_objetos(self):
        cx, cy = self.cam_x, self.cam_y
        objs = [o for o in self.mundo.arvores if o.visivel(cx, cy)]
        objs += [z for z in self.mundo.zumbis if z.visivel(cx, cy)]
        objs.append(self.jogador)
        objs.sort(key=lambda o: o.ordem_y)

        for obj in objs:
            obj.desenhar(self.tela, cx, cy)
            if isinstance(obj, Zumbi):
                barra = self.assets.barra_zumbi[nivel_barra(obj.vida)]
                sx = obj.x - cx + obj.w / 2 - barra.get_width() / 2
                sy = obj.y - cy - barra.get_height() + 30
                self.tela.blit(barra, (sx, sy))

    def desenhar_hud(self, dt):
        j = self.jogador
        self.tela.blit(self.assets.barra_jogador[nivel_barra(j.vida)], (10, 10))

        texto = self.assets.fonte.render(f"BALAS: {j.balas}", True, (255, 255, 255))
        self.tela.blit(texto, (20, 80))

        self.tela.blit(self.assets.icone_mochila, self.pos_icone)
        self.tela.blit(self.assets.texto_abrir_mochila,
                       (self.pos_icone[0] - 10, self.pos_icone[1] - 5))

        if j.tempo_vermelho > 0:
            j.tempo_vermelho -= dt
            self.tela.blit(self.tela_vermelha, (0, 0))

    def desenhar_mochila_tela(self):
        self.tela.blit(self.assets.tela_mochila, (100, 0))

        posicoes = [
            (270, 220),
            (410, 220),
            (270, 350),
            (410, 350)
        ]

        imagens = {
            "laranja": self.assets.laranja_mochila,
            "medkit": self.assets.medkit_mochila
        }

        quantidades = {
            "laranja": self.jogador.laranjas,
            "medkit": self.jogador.medkits
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
                    (255, 255, 255)
                )

                self.tela.blit(texto, (x + 80, y + 80))

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
            self.janela.update()


if __name__ == "__main__":
    Jogo().executar()
