from PPlay.sprite import *
import pygame


class Menu:

    def __init__(self, janela, teclado, mouse):

        self.janela = janela
        self.teclado = teclado
        self.mouse = mouse

        # Fundo
        self.fundo = Sprite("fundo.png")
        self.fundo.image = pygame.transform.scale(
            self.fundo.image,
            (800, 600)
        )

        # Música
        self.som = pygame.mixer.Sound("som_menu1.mp3")
        self.som.set_volume(0.3)

        # Botão
        self.botao_start = Sprite("botao.png")
        self.botao_start.image = pygame.transform.scale(
            self.botao_start.image,
            (240, 140)
        )

        self.botao_start.width = 240
        self.botao_start.height = 140

        self.botao_start.set_position(
            400 - self.botao_start.width / 2,
            470
        )
        
        self.botaoC = Sprite("botaoC.png")

        self.botaoC.image = pygame.transform.scale(
            self.botaoC.image,
            (90, 90)
        )

        self.botaoC.width = 90
        self.botaoC.height = 90

        self.botaoC.set_position(20, 20)

        self.tocando = False

    def atualizar(self):

        if not self.tocando:
            self.som.play(-1)
            self.tocando = True

        self.fundo.draw()
        self.botao_start.draw()
        self.botaoC.draw()

        # Botão START
        if (
            self.teclado.key_pressed("ENTER")
            or
            (
                self.mouse.is_over_object(self.botao_start)
                and self.mouse.is_button_pressed(1)
            )
        ):
            self.som.stop()
            self.tocando = False

            return "JOGO"

        # Botão CONFIGURAÇÕES
        if (
            self.mouse.is_over_object(self.botaoC)
            and self.mouse.is_button_pressed(1)
        ):
            self.som.stop()
            self.tocando = False

            return "CONFIG"

        return None

