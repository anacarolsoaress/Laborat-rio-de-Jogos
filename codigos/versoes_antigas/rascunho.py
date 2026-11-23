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

        posicoes = [(270, 220),(410, 220),(270, 350),(410, 350)]

        quantidades = {"laranja": j.laranjas,"medkit": j.medkits}

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

                    self.ultimo_clique_mochila = None

                else:
                    self.ultimo_clique_mochila = item
                    self.tempo_ultimo_clique_mochila = tempo_atual

        # Remove o item da ordem quando sua quantidade chega a zero
            if quantidades[item] > 0:
                pass

            if item == "laranja" and j.laranjas == 0:
                j.ordem_itens.remove("laranja")

            elif item == "medkit" and j.medkits == 0:
                j.ordem_itens.remove("medkit")

            break 