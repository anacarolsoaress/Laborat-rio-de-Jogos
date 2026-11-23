from PPlay.window import *
from PPlay.sprite import *
from PPlay.keyboard import *
from PPlay.mouse import *
from menu import Menu
import pygame
import random
import math

janela = Window(800, 600)
janela.set_title("apocalipse Runaways")
teclado2 = Keyboard()
mouse = Mouse()
som_ambiente = pygame.mixer.Sound("ambiente.mp3")
som_ambiente.set_volume(0.1)

menu = Menu(janela, teclado2, mouse)

# ==========================================
# PERSONAGEM
# ==========================================

personagem = Sprite("bonecoD1.png")

personagem.image = pygame.transform.scale(
    personagem.image,
    (100, 100)
)

personagem.width = 100
personagem.height = 100
personagem.rect = personagem.image.get_rect()

imagem_morte = pygame.transform.scale(
    pygame.image.load("morte.png"),
    (100, 100)
)

idle_direita = pygame.transform.scale(pygame.image.load("bonecoD1.png"), (100, 100))
idle_esquerda = pygame.transform.scale(pygame.image.load("bonecoE1.png"),(95, 100))
idle_frente = pygame.transform.scale(pygame.image.load("bonecoF1.png"), (100, 105))
idle_tras = pygame.transform.scale(pygame.image.load("bonecoT1.png"), (100, 105))

direita = [
    pygame.transform.scale(pygame.image.load("bonecoD2.png"), (100, 100)),
    pygame.transform.scale(pygame.image.load("bonecoD3.png"), (100, 100))
]

esquerda = [
    pygame.transform.scale(pygame.image.load("bonecoE2.png"), (95, 100)),
    pygame.transform.scale(pygame.image.load("bonecoE3.png"), (95, 100))
]

frente = [
    pygame.transform.scale(pygame.image.load("bonecoF2.png"), (100, 105)),
    pygame.transform.scale(pygame.image.load("bonecoF3.png"), (100, 105))
]

tras = [
    pygame.transform.scale(pygame.image.load("bonecoT2.png"), (100, 105)),
    pygame.transform.scale(pygame.image.load("bonecoT3.png"), (100, 105))
]

vida_maxima = 400
vida_atual = 400

tempo_vermelho = 0
duracao_vermelho = 0.2

tempo_branco = 0
duracao_branco = 0.4
personagem_branco = False
quantidade_piscadas = 0
efeito_dano_ativo = False

fade_morte = 0
alpha_texto_morte = 0
fonte_morte = pygame.font.Font("Creepster.ttf", 90)
texto_morte = fonte_morte.render("VOCÊ É UM DE NÓS...", True, (255, 0, 0))
som_morte = pygame.mixer.Sound("morte.mp3")
som_morte.set_volume(0.2)

# ==========================================
# ZUMBIS
# ==========================================

zumbis = []

imagem_zumbi = pygame.transform.scale(
    pygame.image.load("zumbiF1.png"),
    (125, 125)
)

quantidade_zumbis = 50
distancia_minima = 800
velocidade_zumbi = 100

distancia_perseguicao = 800
dano_zumbi = 100
distancia_ataque_zumbi = 70
intervalo_dano_zumbi = 3
ultimo_dano_zumbi = 0
forca_empurrao = 50

som_empurrao = pygame.mixer.Sound("empurrao.mp3")
som_zumbi = pygame.mixer.Sound("som_zumbi.mp3")
som_zumbi.set_volume(0)
som_zumbi.play(-1)
# ==========================================
# ARVORES
# ==========================================
arvores = []

imagem_arvore = pygame.transform.scale(
    pygame.image.load("arvore.png"),
    (200, 200)
)

quantidade_arvores = 500
distancia_minima_arvores = 150

# ==========================================
# TAMANHO DO MAPA
# ==========================================

TAMANHO_CHAO = 600

MAPA_LARGURA = 9600
MAPA_ALTURA = 6000

chao = []

for x in range(0, MAPA_LARGURA, TAMANHO_CHAO):
    for y in range(0, MAPA_ALTURA, TAMANHO_CHAO):

        if random.randint(1, 4) == 1:
            parte = Sprite("chao.png")
        elif random.randint(1, 4) == 2:
            parte = Sprite("chao3.png")
        else:
            parte = Sprite("chao2.png")

        parte.image = pygame.transform.scale(
            parte.image,
            (TAMANHO_CHAO, TAMANHO_CHAO)
        )

        parte.mundo_x = x
        parte.mundo_y = y

        chao.append(parte)


# ==========================================
# JOGADOR
# ==========================================

jogador_x = 400
jogador_y = 300

velocidade = 500


# ==========================================
# CÂMERA
# ==========================================

camera_x = 0
camera_y = 0


teclado = Window.get_keyboard()

# ==========================================
# TIROS
# ==========================================
som_tiro = pygame.mixer.Sound("som_tiro.mp3")
som_tiro.set_volume(0.2)

balas = []

velocidade_bala = 800

botao_mouse_anterior = False

imagem_bala = pygame.transform.scale(
    pygame.image.load("tiro.png"),
    (60, 30)
)

# ==========================================
# VARIAVEIS
# ==========================================

frame = 0
tempo_animacao = 0
velocidade_animacao = 10

direcao = "direita"

# ==========================================
# FUNÇOES
# ==========================================

def atualizar_jogador(dt):

    global jogador_x
    global jogador_y

    global direcao
    global frame
    global tempo_animacao


    andando = False


    # Movimento

    if teclado.key_pressed("LEFT"):

        jogador_x -= velocidade * dt

        direcao = "esquerda"

        andando = True


    if teclado.key_pressed("RIGHT"):

        jogador_x += velocidade * dt

        direcao = "direita"

        andando = True


    if teclado.key_pressed("UP"):

        jogador_y -= velocidade * dt

        direcao = "tras"

        andando = True


    if teclado.key_pressed("DOWN"):

        jogador_y += velocidade * dt

        direcao = "frente"

        andando = True


    # Animação

    if andando:

        tempo_animacao += 100 * dt


        if tempo_animacao >= velocidade_animacao:

            tempo_animacao = 0

            frame += 1


            if direcao == "direita":

                if frame >= len(direita):

                    frame = 0


            elif direcao == "esquerda":

                if frame >= len(esquerda):

                    frame = 0


            elif direcao == "frente":

                if frame >= len(frente):

                    frame = 0


            elif direcao == "tras":

                if frame >= len(tras):

                    frame = 0


        if direcao == "frente":

            personagem.image = frente[frame]


        elif direcao == "tras":

            personagem.image = tras[frame]


        elif direcao == "direita":

            personagem.image = direita[frame]


        elif direcao == "esquerda":

            personagem.image = esquerda[frame]


    else:

        frame = 0

        tempo_animacao = 0


        if direcao == "frente":

            personagem.image = idle_frente


        elif direcao == "tras":

            personagem.image = idle_tras


        elif direcao == "direita":

            personagem.image = idle_direita


        elif direcao == "esquerda":

            personagem.image = idle_esquerda



# =================================================


def desenhar_barra_vida():

    largura = 200
    altura = 25

    x = 20
    y = 20


    # Fundo

    pygame.draw.rect(
        janela.screen,
        (60, 60, 60),
        (
            x - 3,
            y - 3,
            largura + 6,
            altura + 6
        )
    )


    pygame.draw.rect(
        janela.screen,
        (10, 10, 10),
        (
            x,
            y,
            largura,
            altura
        )
    )


    # Vida

    largura_vida = int(
        largura *
        (vida_atual / vida_maxima)
    )


    pygame.draw.rect(
        janela.screen,
        (0, 100, 225),
        (
            x,
            y,
            largura_vida,
            altura
        )
    )


    # Divisões

    pygame.draw.rect(
        janela.screen,
        (10, 10, 10),
        (
            x + 50,
            y,
            5,
            altura
        )
    )


    pygame.draw.rect(
        janela.screen,
        (10, 10, 10),
        (
            x + 100,
            y,
            5,
            altura
        )
    )


    pygame.draw.rect(
        janela.screen,
        (10, 10, 10),
        (
            x + 150,
            y,
            5,
            altura
        )
    )



# =================================================


def atualizar_zumbis(dt):

    for zumbi in zumbis:

        dx = jogador_x - zumbi.mundo_x
        dy = jogador_y - zumbi.mundo_y

        distancia = (
            dx ** 2 +
            dy ** 2
        ) ** 0.5


        if distancia <= distancia_perseguicao:

            if distancia != 0:

                dx /= distancia
                dy /= distancia


                zumbi.mundo_x += (
                    dx *
                    velocidade_zumbi *
                    dt
                )


                zumbi.mundo_y += (
                    dy *
                    velocidade_zumbi *
                    dt
                )



# =================================================


def criar_zumbis():

    for i in range(quantidade_zumbis):

        zumbi = Sprite(
            "zumbiF1.png"
        )


        zumbi.image = imagem_zumbi

        zumbi.width = 125
        zumbi.height = 125


        zumbi.hitbox_largura = 45
        zumbi.hitbox_altura = 75


        zumbi.vida_maxima = 400
        zumbi.vida = zumbi.vida_maxima


        while True:

            zumbi.mundo_x = random.randint(
                0,
                MAPA_LARGURA - zumbi.width
            )


            zumbi.mundo_y = random.randint(
                0,
                MAPA_ALTURA - zumbi.height
            )


            dx = (
                zumbi.mundo_x -
                jogador_x
            )

            dy = (
                zumbi.mundo_y -
                jogador_y
            )


            distancia = (
                dx ** 2 +
                dy ** 2
            ) ** 0.5


            if distancia >= distancia_minima:

                break


        zumbis.append(zumbi)



# =================================================


def dano_zumbis():

    global vida_atual
    global ultimo_dano_zumbi

    global jogador_x
    global jogador_y

    global tempo_vermelho

    global tempo_branco
    global personagem_branco
    global quantidade_piscadas
    global efeito_dano_ativo

    global estado
    global fade_morte
    global alpha_texto_morte


    tempo_atual = (
        pygame.time.get_ticks()
        / 1000
    )


    for zumbi in zumbis:

        dx = jogador_x - zumbi.mundo_x
        dy = jogador_y - zumbi.mundo_y


        distancia = (
            dx ** 2 +
            dy ** 2
        ) ** 0.5


        if distancia <= distancia_ataque_zumbi:

            if (
                tempo_atual -
                ultimo_dano_zumbi
                >= intervalo_dano_zumbi
            ):

                # Dano

                vida_atual -= dano_zumbi

                ultimo_dano_zumbi = tempo_atual


                personagem_branco = True

                som_empurrao.play()


                tempo_vermelho = duracao_vermelho

                tempo_branco = duracao_branco

                quantidade_piscadas = 0

                efeito_dano_ativo = True


                # Direção do empurrão

                if distancia != 0:

                    dx /= distancia
                    dy /= distancia


                    jogador_x += (
                        dx *
                        forca_empurrao
                    )


                    jogador_y += (
                        dy *
                        forca_empurrao
                    )


                if vida_atual <= 0:

                    personagem_branco = False

                    efeito_dano_ativo = False

                    tempo_branco = 0

                    vida_atual = 0


                    personagem.image = imagem_morte


                    fade_morte = 0

                    alpha_texto_morte = 0


                    estado = "MORTE"



# =================================================


def atualizar_som_zumbi():

    menor_distancia = 800


    for zumbi in zumbis:

        dx = jogador_x - zumbi.mundo_x
        dy = jogador_y - zumbi.mundo_y


        distancia = (
            dx ** 2 +
            dy ** 2
        ) ** 0.5


        if distancia < menor_distancia:

            menor_distancia = distancia


    volume = 1 - (
        menor_distancia / 800
    )


    if volume < 0:

        volume = 0


    if volume > 1:

        volume = 1


    som_zumbi.set_volume(volume)



# =================================================


def desenhar_dano_vermelho(dt):

    global tempo_vermelho


    if tempo_vermelho > 0:

        tempo_vermelho -= dt


        tela_vermelha = pygame.Surface(
            (800, 600)
        )


        tela_vermelha.set_alpha(100)

        tela_vermelha.fill(
            (255, 0, 0)
        )


        janela.screen.blit(
            tela_vermelha,
            (0, 0)
        )



# =================================================


def atualizar_efeito_dano(dt):

    global tempo_branco
    global personagem_branco
    global quantidade_piscadas
    global efeito_dano_ativo


    if not efeito_dano_ativo:

        return


    if tempo_branco > 0:

        tempo_branco -= dt


    else:

        quantidade_piscadas += 1


        if quantidade_piscadas < 20:

            personagem_branco = (
                not personagem_branco
            )

            tempo_branco = 0.1


        else:

            personagem_branco = False

            efeito_dano_ativo = False



# =================================================


def desenhar_morte(dt):

    global fade_morte
    global alpha_texto_morte


    # Escurece a tela

    fade_morte += 150 * dt


    if fade_morte > 255:

        fade_morte = 255


    tela_preta = pygame.Surface(
        (800, 600)
    )


    tela_preta.set_alpha(
        int(fade_morte)
    )


    tela_preta.fill(
        (0, 0, 0)
    )


    janela.screen.blit(
        tela_preta,
        (0, 0)
    )


    # Texto

    if fade_morte >= 255:

        alpha_texto_morte += 100 * dt


        if alpha_texto_morte > 255:

            alpha_texto_morte = 255


        texto_morte = fonte_morte.render(
            "VOCÊ É UM DE NÓS...",
            True,
            (255, 0, 0)
        )


        texto_morte.set_alpha(
            int(alpha_texto_morte)
        )


        janela.screen.blit(
            texto_morte,
            (
                400 -
                texto_morte.get_width() // 2,
                500
            )
        )



# =================================================


def criar_arvores():

    for i in range(quantidade_arvores):

        arvore = Sprite(
            "arvore.png"
        )


        arvore.image = imagem_arvore

        arvore.width = 200
        arvore.height = 200


        pode_criar = False


        for tentativa in range(100):

            arvore.mundo_x = random.randint(
                0,
                MAPA_LARGURA - arvore.width
            )


            arvore.mundo_y = random.randint(
                0,
                MAPA_ALTURA - arvore.height
            )


            pode_criar = True


            for outra_arvore in arvores:

                dx = (
                    arvore.mundo_x -
                    outra_arvore.mundo_x
                )

                dy = (
                    arvore.mundo_y -
                    outra_arvore.mundo_y
                )


                distancia = (
                    dx ** 2 +
                    dy ** 2
                ) ** 0.5


                if distancia < distancia_minima_arvores:

                    pode_criar = False

                    break


            if pode_criar:

                break


        if pode_criar:

            arvores.append(arvore)



# =================================================


def atirar():

    global botao_mouse_anterior


    botao_mouse = pygame.mouse.get_pressed()[0]


    if (
        botao_mouse
        and
        not botao_mouse_anterior
    ):

        som_tiro.play()


        mouse_x, mouse_y = pygame.mouse.get_pos()


        personagem_centro_x = (
            jogador_x -
            camera_x +
            personagem.width / 2
        )


        personagem_centro_y = (
            jogador_y -
            camera_y +
            personagem.height / 2
        )


        dx = (
            mouse_x -
            personagem_centro_x
        )


        dy = (
            mouse_y -
            personagem_centro_y
        )


        distancia = (
            dx ** 2 +
            dy ** 2
        ) ** 0.5


        if distancia != 0:

            dx /= distancia
            dy /= distancia


            bala = Sprite(
                "tiro.png"
            )


            bala.image = pygame.transform.scale(
                bala.image,
                (60, 30)
            )


            bala.mundo_x = (
                jogador_x +
                personagem.width / 2
            )


            bala.mundo_y = (
                jogador_y +
                personagem.height / 2
            )


            bala.direcao_x = dx
            bala.direcao_y = dy


            angulo = math.degrees(
                math.atan2(dy, dx)
            )


            bala.image = pygame.transform.rotate(
                bala.image,
                -angulo
            )


            balas.append(bala)


    botao_mouse_anterior = botao_mouse



# =================================================


def atualizar_balas(dt):

    for bala in balas[:]:

        bala.mundo_x += (
            bala.direcao_x *
            velocidade_bala *
            dt
        )


        bala.mundo_y += (
            bala.direcao_y *
            velocidade_bala *
            dt
        )


        for zumbi in zumbis[:]:

            zumbi_centro_x = (
                zumbi.mundo_x +
                zumbi.width / 2
            )


            zumbi_centro_y = (
                zumbi.mundo_y +
                zumbi.height / 2
            )


            if (
                bala.mundo_x >
                zumbi_centro_x -
                zumbi.hitbox_largura / 2

                and

                bala.mundo_x <
                zumbi_centro_x +
                zumbi.hitbox_largura / 2

                and

                bala.mundo_y >
                zumbi_centro_y -
                zumbi.hitbox_altura / 2

                and

                bala.mundo_y <
                zumbi_centro_y +
                zumbi.hitbox_altura / 2
            ):

                zumbi.vida -= 100


                balas.remove(bala)


                if zumbi.vida <= 0:

                    zumbis.remove(zumbi)


                break



# =================================================


def limitar_jogador():

    global jogador_x
    global jogador_y


    if jogador_x < 0:

        jogador_x = 0


    if jogador_x > (
        MAPA_LARGURA -
        personagem.width
    ):

        jogador_x = (
            MAPA_LARGURA -
            personagem.width
        )


    if jogador_y < 0:

        jogador_y = 0


    if jogador_y > (
        MAPA_ALTURA -
        personagem.height
    ):

        jogador_y = (
            MAPA_ALTURA -
            personagem.height
        )



# =================================================


def atualizar_camera():

    global camera_x
    global camera_y


    camera_x = jogador_x - 350
    camera_y = jogador_y - 250


    # Limite esquerdo

    if camera_x < 0:

        camera_x = 0


    # Limite superior

    if camera_y < 0:

        camera_y = 0


    # Limite direito

    if camera_x > (
        MAPA_LARGURA - 800
    ):

        camera_x = (
            MAPA_LARGURA - 800
        )


    # Limite inferior

    if camera_y > (
        MAPA_ALTURA - 600
    ):

        camera_y = (
            MAPA_ALTURA - 600
        )



# =================================================


def desenhar_chao():

    for parte in chao:

        parte.x = (
            parte.mundo_x -
            camera_x
        )


        parte.y = (
            parte.mundo_y -
            camera_y
        )


        if (
            parte.x + parte.width > 0
            and
            parte.x < 800
            and
            parte.y + parte.height > 0
            and
            parte.y < 600
        ):

            parte.draw()



# =================================================


def remover_balas():

    for bala in balas[:]:

        if (
            bala.mundo_x < 0
            or
            bala.mundo_x > MAPA_LARGURA
            or
            bala.mundo_y < 0
            or
            bala.mundo_y > MAPA_ALTURA
        ):

            balas.remove(bala)



# =================================================


def desenhar_balas():

    for bala in balas:

        bala.x = (
            bala.mundo_x
            - camera_x
            - bala.image.get_width() / 2
        )


        bala.y = (
            bala.mundo_y
            - camera_y
            - bala.image.get_height() / 2
        )


        bala.draw()



# =================================================


def desenhar_zumbis():

    for zumbi in zumbis:

        zumbi.x = (
            zumbi.mundo_x -
            camera_x
        )


        zumbi.y = (
            zumbi.mundo_y -
            camera_y
        )


        if (
            zumbi.x + zumbi.width > 0
            and
            zumbi.x < 800
            and
            zumbi.y + zumbi.height > 0
            and
            zumbi.y < 600
        ):

            zumbi.draw()



# =================================================


def desenhar_arvores():

    for arvore in arvores:

        arvore.x = (
            arvore.mundo_x -
            camera_x
        )


        arvore.y = (
            arvore.mundo_y -
            camera_y
        )


        if (
            arvore.x + arvore.width > 0
            and
            arvore.x < 800
            and
            arvore.y + arvore.height > 0
            and
            arvore.y < 600
        ):

            arvore.draw()



# =================================================


def desenhar_objetos():

    personagem.mundo_x = jogador_x
    personagem.mundo_y = jogador_y


    objetos = []


    for arvore in arvores:

        objetos.append(arvore)


    for zumbi in zumbis:

        objetos.append(zumbi)


    objetos.append(personagem)


    def profundidade(objeto):

        if objeto in arvores:

            return (
                objeto.mundo_y +
                objeto.height -
                30
            )

        else:

            return (
                objeto.mundo_y +
                objeto.height
            )


    objetos.sort(
        key=profundidade
    )


    for objeto in objetos:

        objeto.x = (
            objeto.mundo_x -
            camera_x
        )


        objeto.y = (
            objeto.mundo_y -
            camera_y
        )


        if (
            objeto.x + objeto.width > 0
            and
            objeto.x < 800
            and
            objeto.y + objeto.height > 0
            and
            objeto.y < 600
        ):

            if (
                objeto == personagem
                and
                personagem_branco
            ):

                imagem_original = (
                    objeto.image.copy()
                )


                # Máscara do personagem

                mascara = pygame.mask.from_surface(
                    imagem_original
                )


                imagem_branca = mascara.to_surface(
                    setcolor=(
                        255,
                        255,
                        255,
                        255
                    ),

                    unsetcolor=(
                        0,
                        0,
                        0,
                        0
                    )
                )


                objeto.image = imagem_branca

                objeto.draw()


                # Recupera imagem normal

                objeto.image = imagem_original


            else:

                objeto.draw()

# ==========================================
# CRIA OS OBJETOS
# ==========================================

criar_zumbis()
criar_arvores()
            
# ==========================================
# LOOP
# ==========================================
estado = "MENU"

while True:

    dt = janela.delta_time()

    # -------- MENU --------
    if estado == "MENU":

        som_morte.stop()

        acao = menu.atualizar()

        if acao == "JOGO":

            personagem.image = idle_direita
            jogador_x = 400
            jogador_y = 300
            balas.clear()

            tempo_espera = pygame.time.get_ticks()

            estado = "ESPERA"

        elif acao == "CONFIG":

            estado = "CONFIG"


    # -------- ESPERA --------
    elif estado == "ESPERA":

        janela.screen.fill((0, 0, 0))

        if pygame.time.get_ticks() - tempo_espera >= 500:

            som_ambiente.play(-1)

            estado = "JOGO"


    # -------- JOGO --------
    elif estado == "JOGO":

        atualizar_jogador(dt)

        atualizar_zumbis(dt)

        dano_zumbis()

        atualizar_som_zumbi()

        atirar()

        atualizar_balas(dt)

        limitar_jogador()

        atualizar_efeito_dano(dt)

        atualizar_camera()

        remover_balas()


        desenhar_chao()

        desenhar_objetos()

        desenhar_balas()

        desenhar_barra_vida()

        desenhar_dano_vermelho(dt)


        if teclado.key_pressed("ESC"):

            som_ambiente.stop()

            estado = "MENU"


    # -------- CONFIGURAÇÕES --------
    elif estado == "CONFIG":

        janela.screen.fill((20, 20, 40))

        # configurações aqui


    # -------- MORTE --------
    elif estado == "MORTE":

        som_ambiente.stop()
        som_zumbi.set_volume(0)
        som_morte.play()

        atualizar_camera()

        desenhar_chao()
        desenhar_objetos()

        desenhar_morte(dt)

        personagem.x = personagem.mundo_x - camera_x
        personagem.y = personagem.mundo_y - camera_y

        personagem.draw()


    janela.update()