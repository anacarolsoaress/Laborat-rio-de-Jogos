
class Sobrevivente(Entidade):
    """Companheiro que segue o jogador e possui vida própria."""

    def __init__(self, assets, x, y, anim=None):
        # Se nenhuma animação for informada, usa a do companheiro original.
        if anim is None:
            anim = assets.anim_sobri

        imagem = anim["idle"]["frente"]

        super().__init__(imagem, x, y, T_SOBRI, T_SOBRI)

        self.anim = anim
        self.vida_maxima = SOBRI_VIDA
        self.restaurar(x, y)

    def restaurar(self, x, y):
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
        return self.tempo_piscar > 0 and int(self.tempo_piscar * 10) % 2 == 0

    def atualizar(self, dt, jogador_x, jogador_y, velocidade_jogador, mundo):
        if not self.vivo:
            return

        dx = jogador_x - self.x
        dy = jogador_y - self.y
        dist = math.hypot(dx, dy)

        if dist > SOBRI_DIST_SEGUIR:
            dx /= dist
            dy /= dist

            velocidade = velocidade_jogador * SOBRI_MULT_VELOCIDADE

            self.x += dx * velocidade * dt
            self.y += dy * velocidade * dt

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

        if self.tempo_piscar > 0:
            self.tempo_piscar -= dt

    def receber_dano(self, agora=None):
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
