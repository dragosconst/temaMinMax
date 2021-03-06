import copy
import time
import pygame
import sys
from statistics import median
from threading import Thread, Timer

class Joc:
    JMIN = None
    JMAX = None
    GOL = "#"
    NR_LINII = None
    NR_COLOANE = None

    def __init__(self, matr=None, NR_LINII=None, NR_COLOANE=None, ultima_mutare=None):
        # creez proprietatea ultima_mutare # (l,c)

        if matr:
            # e data tabla, deci suntem in timpul jocului
            self.matr = copy.deepcopy(matr)
        else:
            # nu e data tabla deci suntem la initializare
            self.matr = [[self.__class__.GOL] * NR_COLOANE for i in range(NR_LINII)]
            for j in range(NR_COLOANE):
                if j == 0:
                    self.matr[0][j] = "a"
                    self.matr[NR_LINII - 1][j] = "a"
                elif j == NR_COLOANE - 1:
                    self.matr[0][j] = "n"
                    self.matr[NR_LINII - 1][j] = "n"
                else:
                    self.matr[0][j] = "n"
                    self.matr[NR_LINII - 1][j] = "a"
            for i in range(1, NR_LINII):
                self.matr[i][0] = "a"
                self.matr[i][NR_COLOANE - 1] = "n"

            if NR_LINII is not None:
                self.__class__.NR_LINII = NR_LINII
            if NR_COLOANE is not None:
                self.__class__.NR_COLOANE = NR_COLOANE

        # ultima mutare o sa fie de forma (negru_mutare_ultim, alb_mutare_ultim)
        if ultima_mutare is not None:
            self.ultima_mutare = ultima_mutare
        else:
            self.ultima_mutare = (None, None)

    def deseneaza_grid(self, coloana_marcaj=None, piesa_marcata=None,
                       cr_juc=None, mutare_calculator=None, cul_mutare=(207, 14, 56)):  # tabla de exemplu este ["#","a","#","n",......]

        for ind in range(self.__class__.NR_COLOANE * self.__class__.NR_LINII):
            linie = ind // self.__class__.NR_COLOANE  # // inseamna div
            coloana = ind % self.__class__.NR_COLOANE

            directii = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            culoare = (255, 255, 255)
            if cr_juc is None:
                cr_juc = self.__class__.JMIN
            if piesa_marcata is not None:
                for dx, dy in directii:
                    i, j = piesa_marcata
                    if culoare == (255, 255, 0):  # deja am gasit ca se poate ajunge din piesa la patratul respectiv
                        break
                    while i >= 0 and j >= 0 and i < self.__class__.NR_LINII and j < self.__class__.NR_COLOANE:
                        if self.matr[i][j] == Joc.jucator_opus(cr_juc) or (
                                self.matr[i][j] == cr_juc and (i, j) != piesa_marcata):
                            break
                        if i == linie and coloana == j:
                            culoare = (255, 255, 0)
                            break
                        i += dx
                        j += dy


            if mutare_calculator is not None:
                init_i, init_j, fin_i, fin_j = mutare_calculator
                dx, dy = None, None
                if init_i < fin_i:
                    dx, dy = (1, 0)
                elif init_i > fin_i:
                    dx, dy = (-1, 0)
                elif init_j < fin_j:
                    dx, dy = (0, 1)
                elif init_j > fin_j:
                    dx, dy = (0, -1)
                i, j = init_i, init_j
                while i != fin_i + dx or j != fin_j + dy:
                    if i == linie and j == coloana:
                        culoare = cul_mutare
                        break
                    i += dx
                    j += dy

            if coloana == coloana_marcaj:
                # daca am o patratica selectata, o desenez cu rosu
                culoare = (255, 255, 0)

            pygame.draw.rect(self.__class__.display, culoare, self.__class__.celuleGrid[ind])  # alb = (255,255,255)
            if self.matr[linie][coloana] == 'a':
                self.__class__.display.blit(self.__class__.alb_img, (
                    coloana * (self.__class__.dim_celula + 1), linie * (self.__class__.dim_celula + 1)))
            elif self.matr[linie][coloana] == 'n':
                self.__class__.display.blit(self.__class__.negru_img, (
                    coloana * (self.__class__.dim_celula + 1), linie * (self.__class__.dim_celula + 1)))
        # pygame.display.flip()
        pygame.display.update()

    @classmethod
    def jucator_opus(cls, jucator):
        return cls.JMAX if jucator == cls.JMIN else cls.JMIN

    # x_img = alb_img
    # negru_img = negru_img
    @classmethod
    def initializeaza(cls, display, NR_LINII=7, NR_COLOANE=7, dim_celula=100):
        cls.display = display
        cls.dim_celula = dim_celula
        cls.alb_img = pygame.image.load('alb.png')
        cls.alb_img = pygame.transform.scale(cls.alb_img, (dim_celula, dim_celula))
        cls.negru_img = pygame.image.load('negru.png')
        cls.negru_img = pygame.transform.scale(cls.negru_img, (dim_celula, dim_celula))
        cls.celuleGrid = []  # este lista cu patratelele din grid
        for linie in range(NR_LINII):
            for coloana in range(NR_COLOANE):
                patr = pygame.Rect(coloana * (dim_celula + 1), linie * (dim_celula + 1), dim_celula, dim_celula)
                cls.celuleGrid.append(patr)

    # functie folosita pentru mutarile manuale, facute de jucator
    def mutare_valida(self, poz, jucator, piesa):
        (pi, pj) = poz
        (i, j) = piesa
        negru_last, alb_last = self.ultima_mutare
        if jucator == "a" and self.back_to_old((i, j, pi, pj), alb_last):
            return False
        if jucator == "n" and self.back_to_old((i, j, pi, pj), negru_last):
            return False
        return True

    # Metoda asta merge pe directia (dx, dy) si cauta piesa de culoarea jucator
    # Daca gaseste, returneaza True
    def parcurgere(self, dx, dy, poz, jucator):
        (i, j) = poz
        if self.matr[i][j] == jucator:
            return (True, i, j)
        while i >= 0 and j >= 0 and i < self.__class__.NR_LINII and j < self.__class__.NR_COLOANE:
            if self.matr[i][j] == jucator:
                negru_last, alb_last = self.ultima_mutare
                if jucator == "n" and not self.back_to_old((i, j, poz[0], poz[1]), negru_last):
                    return (True, i, j)
                if jucator == "a" and not self.back_to_old((i, j, poz[0], poz[1]), alb_last):
                    return (True, i, j)
                return (False, -1, -1)
            elif self.matr[i][j] != self.__class__.GOL:
                return (False, -1, -1)  # adica daca a dat mai intai de o piesa a celuilalt jucator
            i += dx
            j += dy
        return (False, -1, -1)

    def final(self):
        aCanMove = False
        nCanMove = False
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == self.__class__.GOL:
                    if self.parcurgere(-1, 0, (i, j), "a")[0] or self.parcurgere(0, 1, (i, j), "a")[0] \
                            or self.parcurgere(1, 0, (i, j), "a")[0] or self.parcurgere(0, -1, (i, j), "a")[0]:
                        aCanMove = True
                    if self.parcurgere(-1, 0, (i, j), "n")[0] or self.parcurgere(0, 1, (i, j), "n")[0] \
                            or self.parcurgere(1, 0, (i, j), "n")[0] or self.parcurgere(0, -1, (i, j), "n")[0]:
                        nCanMove = True
                    if nCanMove and aCanMove:
                        break
            if nCanMove and aCanMove:
                break
        if nCanMove and aCanMove:
            return False
        if aCanMove:
            return "a"
        if nCanMove:
            return "b"
        return "remiza"

    # verific daca mutarea ar aduce tabla jucatorului in configuratia precedenta
    def back_to_old(self, pos_move, old_config):
        (pi, pj, npi, npj) = pos_move
        if old_config is None:  # adica e printre primele mutari
            if ((npi == 0 or npi == self.__class__.NR_LINII - 1) and npj == pj) \
                    or ((npj == 0 or npj == self.__class__.NR_COLOANE - 1) and npi == pi):
                return True
            return False  # ma uit daca se intoarce pe o linie\coloana de inceput, caz in care ar fi un pas inapoi
        (opi, opj, onpi, onpj) = old_config
        if onpi == pi and onpj == pj and npi == opi and npj == opj:
            return True
        return False

    def mutari(self, jucator):
        l_mutari = []
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == self.__class__.GOL:
                    negru_last, alb_last = self.ultima_mutare
                    if self.parcurgere(-1, 0, (i, j), jucator)[0]:
                        true, old_i, old_j = self.parcurgere(-1, 0, (i, j), jucator)
                        if (jucator == "n" and not self.back_to_old((old_i, old_j, i, j), negru_last)) \
                                or (jucator == "a" and not self.back_to_old((old_i, old_j, i, j), alb_last)):
                            pos_move = copy.deepcopy(self.matr)
                            pos_move[i][j] = jucator
                            pos_move[old_i][old_j] = self.__class__.GOL
                            if jucator == "n":
                                negru_last = (old_i, old_j, i, j)
                            else:
                                alb_last = (old_i, old_j, i, j)
                            next_joc = Joc(pos_move, self.__class__.NR_LINII, self.__class__.NR_COLOANE, (negru_last,
                                                                                                          alb_last))
                            next_joc.check_and_mark(jucator, (i, j))
                            l_mutari.append(next_joc)
                    if self.parcurgere(0, 1, (i, j), jucator)[0]:
                        true, old_i, old_j = self.parcurgere(0, 1, (i, j), jucator)
                        if (jucator == "n" and not self.back_to_old((old_i, old_j, i, j), negru_last)) \
                                or (jucator == "a" and not self.back_to_old((old_i, old_j, i, j), alb_last)):
                            pos_move = copy.deepcopy(self.matr)
                            pos_move[i][j] = jucator
                            pos_move[old_i][old_j] = self.__class__.GOL
                            if jucator == "n":
                                negru_last = (old_i, old_j, i, j)
                            else:
                                alb_last = (old_i, old_j, i, j)
                            next_joc = Joc(pos_move, self.__class__.NR_LINII, self.__class__.NR_COLOANE, (negru_last,
                                                                                                          alb_last))
                            next_joc.check_and_mark(jucator, (i, j))
                            l_mutari.append(next_joc)
                    if self.parcurgere(1, 0, (i, j), jucator)[0]:
                        true, old_i, old_j = self.parcurgere(1, 0, (i, j), jucator)
                        if (jucator == "n" and not self.back_to_old((old_i, old_j, i, j), negru_last)) \
                                or (jucator == "a" and not self.back_to_old((old_i, old_j, i, j), alb_last)):
                            pos_move = copy.deepcopy(self.matr)
                            pos_move[i][j] = jucator
                            pos_move[old_i][old_j] = self.__class__.GOL
                            if jucator == "n":
                                negru_last = (old_i, old_j, i, j)
                            else:
                                alb_last = (old_i, old_j, i, j)
                            next_joc = Joc(pos_move, self.__class__.NR_LINII, self.__class__.NR_COLOANE, (negru_last,
                                                                                                          alb_last))
                            next_joc.check_and_mark(jucator, (i, j))
                            l_mutari.append(next_joc)
                    if self.parcurgere(0, -1, (i, j), jucator)[0]:
                        true, old_i, old_j = self.parcurgere(0, -1, (i, j), jucator)
                        if (jucator == "n" and not self.back_to_old((old_i, old_j, i, j), negru_last)) \
                                or (jucator == "a" and not self.back_to_old((old_i, old_j, i, j), alb_last)):
                            pos_move = copy.deepcopy(self.matr)
                            pos_move[i][j] = jucator
                            pos_move[old_i][old_j] = self.__class__.GOL
                            if jucator == "n":
                                negru_last = (old_i, old_j, i, j)
                            else:
                                alb_last = (old_i, old_j, i, j)
                            next_joc = Joc(pos_move, self.__class__.NR_LINII, self.__class__.NR_COLOANE, (negru_last,
                                                                                                          alb_last))
                            next_joc.check_and_mark(jucator, (i, j))
                            l_mutari.append(next_joc)
        return l_mutari

    # verifica unde se termina o linie, pe directia (dx, dy)
    # daca se termina intr-un capat al tablei, returneaza None
    def line_ends(self, dx, dy, poz):
        (i, j) = poz
        jucator_cautat = self.matr[i][j]
        while i >= 0 and j >= 0 and i < self.__class__.NR_LINII and j < self.__class__.NR_COLOANE:
            if self.matr[i][j] != jucator_cautat:
                break
            i += dx
            j += dy
        if i == -1 or j == -1 or i == self.__class__.NR_LINII \
                or j == self.__class__.NR_COLOANE:
            return None
        return (i, j)

    # o metoda care testeaza daca un jucator poate ajunge in orice fel posibil la pozitia data
    def poate_ajunge(self, poz, jucator):
        if self.parcurgere(-1, 0, poz, jucator)[0] or self.parcurgere(0, 1, poz, jucator)[0] \
                or self.parcurgere(1, 0, poz, jucator)[0] or self.parcurgere(0, -1, poz, jucator)[0]:
            return True
        return False

    # verific daca plecand din piesa, pot ajunge in poz, unde poz trebuie sa fie un spatiu gol
    # mergand pe (dx, dy)
    def parcurgere_din_piesa(self, dx, dy, poz, jucator, piesa):
        (i, j) = poz
        (pi, pj) = piesa
        if pi == i and pj == j:
            return True
        while pi >= 0 and pj >= 0 and pi < self.__class__.NR_LINII and pj < self.__class__.NR_COLOANE:
            if self.matr[pi][pj] == Joc.jucator_opus(jucator):  # a dat de o piesa de a oponentului
                return False
            if pi == i and pj == j:  # a putut ajunge in poz fara probleme
                # totusi, din nou trebuie verificat daca nu e cumva o configuratie precedenta a tablei
                # pos_move = copy.deepcopy(self.matr)
                # pos_move[i][j] = jucator
                # pos_move[piesa[0]][piesa[1]] = self.__class__.GOL
                negru_last, alb_last = self.ultima_mutare
                if (jucator == "n" and not self.back_to_old((piesa[0], piesa[1], i, j), negru_last)) \
                        or (jucator == "a" and not self.back_to_old((piesa[0], piesa[1], i, j), alb_last)):
                    return True
                return False
            pi += dx
            pj += dy
        return False  # a terminat tabla

    # verific daca se poate ajunge pe orice directie in poz, folosind piesa data
    def poate_ajunge_piesa(self, poz, jucator, piesa):
        if self.parcurgere_din_piesa(-1, 0, poz, jucator, piesa) or self.parcurgere_din_piesa(0, 1, poz, jucator, piesa) \
                or self.parcurgere_din_piesa(1, 0, poz, jucator, piesa) or self.parcurgere_din_piesa(0, -1, poz,
                                                                                                     jucator, piesa):
            return True
        return False

    # numara cate capturi ar fi posibile din viitor si le puncteaza in functie de cat de
    # probabile sunt, din starea actuala
    def capturi_posibile(self, jucator):
        opposite_jucator = Joc.jucator_opus(jucator)
        score = 0.0
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == self.__class__.GOL and self.poate_ajunge((i, j), jucator):
                    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                    for dx, dy in directions:
                        new_i = i + dx
                        new_j = j + dy
                        if new_i < 0 or new_j < 0 or new_i >= self.__class__.NR_LINII or new_j >= self.__class__.NR_COLOANE:
                            continue
                        if self.matr[new_i][new_j] == opposite_jucator and self.line_ends(dx, dy,
                                                                                          (new_i, new_j)) is not None:
                            (capat_i, capat_j) = self.line_ends(dx, dy, (new_i, new_j))
                            # calculez cate piese ar captura asa
                            if dx == -1:
                                piese_capturate = i - capat_i - 1
                            elif dy == 1:
                                piese_capturate = capat_j - j - 1
                            elif dx == 1:
                                piese_capturate = capat_i - i - 1
                            elif dy == -1:
                                piese_capturate = j - capat_j - 1
                            modifier = 0
                            if self.matr[capat_i][capat_j] == jucator:
                                if self.poate_ajunge((i, j), opposite_jucator):
                                    modifier = 2.0
                                else:
                                    modifier = 4.0
                            else:
                                if self.poate_ajunge((i, j), opposite_jucator) and self.poate_ajunge((capat_i, capat_j),
                                                                                                     opposite_jucator):
                                    modifier = 0.5
                                elif self.poate_ajunge((i, j), opposite_jucator) or self.poate_ajunge(
                                        (capat_i, capat_j), opposite_jucator):
                                    modifier = 1.0
                                else:
                                    modifier = 1.5
                            score += modifier * piese_capturate
                elif self.matr[i][j] == jucator:
                    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                    for dx, dy in directions:
                        new_i = i + dx
                        new_j = j + dy
                        if new_i < 0 or new_j < 0 or new_i >= self.__class__.NR_LINII or new_j >= self.__class__.NR_COLOANE:
                            continue
                        if self.matr[new_i][new_j] == opposite_jucator and self.line_ends(dx, dy,
                                                                                          (new_i, new_j)) is not None:
                            (capat_i, capat_j) = self.line_ends(dx, dy, (new_i, new_j))
                            if not self.poate_ajunge((capat_i, capat_j), jucator):
                                continue
                            # calculez cate piese ar captura asa
                            if dx == -1:
                                piese_capturate = i - capat_i - 1
                            elif dy == 1:
                                piese_capturate = capat_j - j - 1
                            elif dx == 1:
                                piese_capturate = capat_i - i - 1
                            elif dy == -1:
                                piese_capturate = j - capat_j - 1
                            modifier = 0
                            # ambele capete sunt inchise de o piesa, dar nu e neaparat o mutare f buna
                            # ca e posibil sa fie piese care nu au fost mutate acum, deci nu ar putea
                            # captura
                            if self.matr[capat_i][capat_j] == jucator:
                                modifier = 3.0
                            else:
                                if self.poate_ajunge((capat_i, capat_j), opposite_jucator):
                                    modifier = 2.0
                                else:
                                    modifier = 4.0
                            score += modifier * piese_capturate
        return score / 2

    # merge pe dx, dy pana cand da de o piesa jucator
    # daca da de o piesa jucator la final, toate piesele parcurse sunt trecute de partea lui
    def try_to_mark(self, dx, dy, start_pos, jucator):
        i, j = start_pos
        can_mark = False
        while i >= 0 and j >= 0 and i < self.__class__.NR_LINII and j < self.__class__.NR_COLOANE:
            if self.matr[i][j] == jucator:
                can_mark = True
                break
            if self.matr[i][j] == self.__class__.GOL:
                break
            i += dx
            j += dy
        if can_mark:
            i, j = start_pos

            while i >= 0 and j >= 0 and i < self.__class__.NR_LINII and j < self.__class__.NR_COLOANE:
                if self.matr[i][j] == jucator:
                    break
                self.matr[i][j] = jucator
                i += dx
                j += dy

    # scaneaza tabla de joc pentru capturi ale jucatorului specificat, cu piesa mutata la mutarea
    # curenta
    def scan_table_for_captures(self, jucator, piesa_mutata):
        (i, j) = piesa_mutata
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for dx, dy in directions:
            new_i = i + dx
            new_j = j + dy
            if new_i >= 0 and new_j >= 0 and new_i < self.__class__.NR_LINII and new_j < self.__class__.NR_COLOANE:
                if self.matr[new_i][new_j] == Joc.jucator_opus(jucator):
                    self.try_to_mark(dx, dy, (new_i, new_j), jucator)

    # ar putea fi scoasa metoda, in versiuni precedente servea un scop diferit si apela
    # scan_table_for_captures de doua ori (cu jucatori diferiti)
    def check_and_mark(self, jucator, piesa_mutata):
        self.scan_table_for_captures(jucator, piesa_mutata)

    # numara in cate directii se poate muta o piesa
    def directii_libere(self, piesa):
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        i, j = piesa
        directii = 0
        for dx, dy in directions:
            new_i = i + dx
            new_j = j + dy
            if new_i < 0 or new_j < 0 or new_i >= self.__class__.NR_LINII or new_j >= self.__class__.NR_COLOANE:
                continue
            # ma uit sa vad daca ar putea face o mutare in directia respectiva
            # trebuie tinut cont, de asemenea, daca se intoarce intr-o mutare precedenta
            if self.matr[new_i][new_j] != self.__class__.GOL:
                continue
            pos_move = copy.deepcopy(self.matr)
            pos_move[new_i][new_j], pos_move[i][j] = self.matr[i][j], self.matr[new_i][new_j]
            negru_last, alb_last = self.ultima_mutare
            if self.matr[i][j] == "n":
                relevant_last = negru_last
            else:
                relevant_last = alb_last
            # merg pe spatii libere pana sigur nu e o mutare precedenta
            while self.back_to_old((i, j, new_i, new_j), relevant_last) and \
                    (
                            new_i >= 0 and new_j >= 0 and new_i < self.__class__.NR_LINII and new_j < self.__class__.NR_COLOANE):
                pos_move[new_i][new_j], pos_move[i][j] = self.matr[new_i][new_j], self.matr[i][j]
                if self.matr[new_i][new_j] != self.__class__.GOL:
                    break
                pos_move[new_i][new_j], pos_move[i][j] = self.matr[i][j], self.matr[new_i][new_j]
                new_i += dx
                new_j += dy
            if new_i < 0 or new_j < 0 or new_i >= self.__class__.NR_LINII or new_j >= self.__class__.NR_COLOANE:
                continue
            if self.matr[new_i][new_j] != self.__class__.GOL:
                continue
            directii += 1
        return directii

    # numara in cate directii se poate misca jucatorul actual IN TOTAL
    def count_free(self, jucator):
        dir_libere = 0.0
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == jucator:
                    dir_libere += self.directii_libere((i, j))
        return dir_libere / 2.2  # impart la un numar relativ mic, pentru ca pot avea cazul cand sunt numarate un pic
        # prea multe directii, de ex n#n ar numara 2 directii libere, desi in realitate e una
        # singura; desigur, nu se intampla mereu asta

    # numara cate piese are fiecare
    def count_pieces(self, jucator):
        nr = 0
        modifier = 1.5
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == jucator:
                    nr += 1
        return nr * modifier

    # numara cate blocheaza JMAX
    # ideea e sa il motivez cumva sa incerce sa blocheze cat mai multe piese, pentru ca doar numaratul
    # directiilor libere poate conduce la comportamentul in care isi muta piesele doar ca sa formeze
    # un fel de cruci, pe care are mobilitate (teoretica) mai crescuta
    def count_blocking(self):
        blocking = 0.0
        for i in range(self.__class__.NR_LINII):
            for j in range(self.__class__.NR_COLOANE):
                if self.matr[i][j] == self.__class__.JMAX:
                    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                    for dx, dy in directions:
                        new_i = i + dx
                        new_j = j + dy
                        if new_i < 0 or new_j < 0 or new_i >= self.__class__.NR_LINII or new_j >= self.__class__.NR_COLOANE:
                            continue
                        if self.matr[new_i][new_j] == self.__class__.JMIN:
                            blocking += 0.25
        return blocking

    # scorul final e calculat folosind 4 metode diferite, pentru a tine cont de:
    # - cate capturi ar putea realiza in viitor (si cat de probabil e sa le realizeze)
    # - cate piese poate misca libere (pentru a tine cont de victoria prin blocare)
    # - cate piese are in comparatie cu celalalt jucator (pentru a puncta capturi realizate)
    # - cate piese de-ale adversarului blocheaza
    def estimeaza_scor(self, adancime):
        t_final = self.final()

        if t_final == self.__class__.JMAX:
            return adancime + 10 ** 3
        elif t_final == self.__class__.JMIN:
            return - adancime - (10 ** 3)
        elif t_final == "remiza":
            return 0.0
        else:
            return (self.capturi_posibile(self.__class__.JMAX) - self.capturi_posibile(self.__class__.JMIN)) \
                   + (self.count_free(self.__class__.JMAX) - self.count_free(self.__class__.JMIN)) \
                   + (self.count_pieces(self.__class__.JMAX) - self.count_pieces(self.__class__.JMIN)) \
                   + self.count_blocking()


    # metoda asta modeleaza o inteligenta mai agresiva, care foloseste pentru estimari doar numarul
    # de capturi posibile si numarul de piese detinute, in total
    def estimare_doar_capturi(self, adancime):
        t_final = self.final()

        if t_final == self.__class__.JMAX:
            return adancime + 10 ** 3
        elif t_final == self.__class__.JMIN:
            return - adancime - (10 ** 3)
        elif t_final == "remiza":
            return 0.0
        else:
            return (self.capturi_posibile(self.__class__.JMAX) - self.capturi_posibile(self.__class__.JMIN)) \
                    + (self.count_pieces(self.__class__.JMAX) - self.count_pieces(self.__class__.JMIN))

    def sirAfisare(self):
        sir = "  |"
        sir += " ".join([str(i) for i in range(self.NR_COLOANE)]) + "\n"
        sir += "-" * (self.NR_COLOANE + 1) * 2 + "\n"
        sir += "\n".join([str(i) + " |" + " ".join([str(x) for x in self.matr[i]]) for i in range(len(self.matr))])
        return sir

    def __str__(self):
        return self.sirAfisare()

    def __repr__(self):
        return self.sirAfisare()


class Stare:
    """
    Clasa folosita de algoritmii minimax si alpha-beta
    Are ca proprietate tabla de joc
    Functioneaza cu conditia ca in cadrul clasei Joc sa fie definiti JMIN si JMAX (cei doi jucatori posibili)
    De asemenea cere ca in clasa Joc sa fie definita si o metoda numita mutari() care ofera lista cu configuratiile posibile in urma mutarii unui jucator
    """

    def __init__(self, tabla_joc, j_curent, adancime, parinte=None, scor=None):
        self.tabla_joc = tabla_joc
        self.j_curent = j_curent

        # adancimea in arborele de stari
        self.adancime = adancime

        # scorul starii (daca e finala) sau al celei mai bune stari-fiice (pentru jucatorul curent)
        self.scor = scor

        # lista de mutari posibile din starea curenta
        self.mutari_posibile = []

        # cea mai buna mutare din lista de mutari posibile pentru jucatorul curent
        self.stare_aleasa = None

    def mutari(self):
        l_mutari = self.tabla_joc.mutari(self.j_curent)
        juc_opus = Joc.jucator_opus(self.j_curent)
        l_stari_mutari = [Stare(mutare, juc_opus, self.adancime - 1, parinte=self) for mutare in l_mutari]

        return l_stari_mutari

    def __str__(self):
        sir = str(self.tabla_joc) + "(Juc curent:" + self.j_curent + ")\n"
        return sir

    def __repr__(self):
        sir = str(self.tabla_joc) + "(Juc curent:" + self.j_curent + ")\n"
        return sir


""" Algoritmul MinMax """


def min_max(stare, estimator=None):
    global nr_noduri_gen
    nr_noduri_gen += 1


    if stare.adancime == 0 or stare.tabla_joc.final():
        if estimator is None or estimator == "n":
            stare.scor = stare.tabla_joc.estimeaza_scor(stare.adancime)
        else:
            stare.scor = stare.tabla_joc.estimare_doar_capturi(stare.adancime)
        return stare
    # calculez toate mutarile posibile din starea curenta
    stare.mutari_posibile = stare.mutari()

    # aplic algoritmul minimax pe toate mutarile posibile (calculand astfel subarborii lor)
    mutari_scor = [min_max(mutare, estimator) for mutare in stare.mutari_posibile]

    if stare.j_curent == Joc.JMAX:
        # daca jucatorul e JMAX aleg starea-fiica cu scorul maxim
        stare.stare_aleasa = max(mutari_scor, key=lambda x: x.scor)
    else:
        # daca jucatorul e JMIN aleg starea-fiica cu scorul minim
        stare.stare_aleasa = min(mutari_scor, key=lambda x: x.scor)
    stare.scor = stare.stare_aleasa.scor
    return stare


def alpha_beta(alpha, beta, stare, estimator=None):
    global nr_noduri_gen
    nr_noduri_gen += 1

    if stare.adancime == 0 or stare.tabla_joc.final():
        if estimator is None or estimator == "n":
            stare.scor = stare.tabla_joc.estimeaza_scor(stare.adancime)
        else:
            stare.scor = stare.tabla_joc.estimare_doar_capturi(stare.adancime)
        return stare

    if alpha > beta:
        return stare  # este intr-un interval invalid deci nu o mai procesez

    stare.mutari_posibile = stare.mutari()

    if stare.j_curent == Joc.JMAX:
        scor_curent = float('-inf')

        for mutare in stare.mutari_posibile:
            # calculeaza scorul
            stare_noua = alpha_beta(alpha, beta, mutare, estimator)

            if (scor_curent < stare_noua.scor):
                stare.stare_aleasa = stare_noua
                scor_curent = stare_noua.scor
            if (alpha < stare_noua.scor):
                alpha = stare_noua.scor
                if alpha >= beta:
                    break

    elif stare.j_curent == Joc.JMIN:
        scor_curent = float('inf')

        for mutare in stare.mutari_posibile:

            stare_noua = alpha_beta(alpha, beta, mutare, estimator)

            if (scor_curent > stare_noua.scor):
                stare.stare_aleasa = stare_noua
                scor_curent = stare_noua.scor

            if (beta > stare_noua.scor):
                beta = stare_noua.scor
                if alpha >= beta:
                    break
    stare.scor = stare.stare_aleasa.scor
    return stare


def afis_daca_final(stare_curenta):
    final = stare_curenta.tabla_joc.final()
    if (final):
        if (final == "remiza"):
            print("Remiza!")
        else:
            print("A castigat " + final)

        return True

    return False


class Buton:
    def __init__(self, display=None, left=0, top=0, w=0, h=0, culoareFundal=(53, 80, 115),
                 culoareFundalSel=(89, 134, 194), text="", font="arial", fontDimensiune=16, culoareText=(255, 255, 255),
                 valoare=""):
        self.display = display
        self.culoareFundal = culoareFundal
        self.culoareFundalSel = culoareFundalSel
        self.text = text
        self.font = font
        self.w = w
        self.h = h
        self.selectat = False
        self.fontDimensiune = fontDimensiune
        self.culoareText = culoareText
        # creez obiectul font
        fontObj = pygame.font.SysFont(self.font, self.fontDimensiune)
        self.textRandat = fontObj.render(self.text, True, self.culoareText)
        self.dreptunghi = pygame.Rect(left, top, w, h)
        # aici centram textul
        self.dreptunghiText = self.textRandat.get_rect(center=self.dreptunghi.center)
        self.valoare = valoare

    def selecteaza(self, sel):
        self.selectat = sel
        self.deseneaza()

    def selecteazaDupacoord(self, coord):
        if self.dreptunghi.collidepoint(coord):
            self.selecteaza(True)
            return True
        return False

    def updateDreptunghi(self):
        self.dreptunghi.left = self.left
        self.dreptunghi.top = self.top
        self.dreptunghiText = self.textRandat.get_rect(center=self.dreptunghi.center)

    def deseneaza(self):
        culoareF = self.culoareFundalSel if self.selectat else self.culoareFundal
        pygame.draw.rect(self.display, culoareF, self.dreptunghi)
        self.display.blit(self.textRandat, self.dreptunghiText)


class GrupButoane:
    def __init__(self, listaButoane=[], indiceSelectat=0, spatiuButoane=10, left=0, top=0):
        self.listaButoane = listaButoane
        self.indiceSelectat = indiceSelectat
        self.listaButoane[self.indiceSelectat].selectat = True
        self.top = top
        self.left = left
        leftCurent = self.left
        for b in self.listaButoane:
            b.top = self.top
            b.left = leftCurent
            b.updateDreptunghi()
            leftCurent += (spatiuButoane + b.w)

    def selecteazaDupacoord(self, coord):
        for ib, b in enumerate(self.listaButoane):
            if b.selecteazaDupacoord(coord):
                self.listaButoane[self.indiceSelectat].selecteaza(False)
                self.indiceSelectat = ib
                return True
        return False

    def deseneaza(self):
        # atentie, nu face wrap
        for b in self.listaButoane:
            b.deseneaza()

    def getValoare(self):
        return self.listaButoane[self.indiceSelectat].valoare


############# ecran initial ########################
def deseneaza_alegeri(display):
    btn_alg = GrupButoane(
        top=30,
        left=30,
        listaButoane=[
            Buton(display=display, w=80, h=30, text="minimax", valoare="minimax"),
            Buton(display=display, w=80, h=30, text="alphabeta", valoare="alphabeta")
        ],
        indiceSelectat=1)
    btn_juc = GrupButoane(
        top=100,
        left=30,
        listaButoane=[
            Buton(display=display, w=35, h=30, text="alb", valoare="a"),
            Buton(display=display, w=35, h=30, text="negru", valoare="n")
        ],
        indiceSelectat=0)
    btn_dif = GrupButoane(
        top=230,
        left=30,
        listaButoane=[
            Buton(display=display, w=60, h=30, text="foarte usor", valoare="fusor"),
            Buton(display=display, w=35, h=30, text="usor", valoare="usor"),
            Buton(display=display, w=35, h=30, text="mediu", valoare="mediu"),
            Buton(display=display, w=35, h=30, text="greu", valoare="greu")
        ],
        indiceSelectat=1
    )
    btn_dim = GrupButoane(
        top=300,
        left=30,
        listaButoane=[
            Buton(display=display, w=35, h=30, text="7x7", valoare="7"),
            Buton(display=display, w=35, h=30, text="8x8", valoare="8"),
            Buton(display=display, w=35, h=30, text="9x9", valoare="9")
        ],
        indiceSelectat=0
    )
    btn_pvp = GrupButoane(
        top=400,
        left=30,
        listaButoane=[
            Buton(display=display, w=150, h=30, text="JucatorVSJucator", valoare="pvp"),
            Buton(display=display, w=150, h=30, text="JucatorVSCalculator", valoare="pve"),
            Buton(display=display, w=150, h=30, text="CalculatorVSCalculator", valoare="eve")
        ],
        indiceSelectat=1
    )
    ok = Buton(display=display, top=450, left=30, w=40, h=30, text="ok", culoareFundal=(155, 0, 55))
    btn_alg.deseneaza()
    btn_juc.deseneaza()
    btn_dif.deseneaza()
    btn_dim.deseneaza()
    btn_pvp.deseneaza()
    ok.deseneaza()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if not btn_alg.selecteazaDupacoord(pos):
                    if not btn_juc.selecteazaDupacoord(pos):
                        if not btn_dim.selecteazaDupacoord(pos):
                            if not btn_dif.selecteazaDupacoord(pos):
                                if not btn_pvp.selecteazaDupacoord(pos):
                                    if ok.selecteazaDupacoord(pos):
                                        display.fill((0, 0, 0))  # stergere ecran
                                        return btn_juc.getValoare(), btn_alg.getValoare(), btn_dif.getValoare(), btn_dim.getValoare(), btn_pvp.getValoare()
        pygame.display.update()

nr_noduri_gen = 0
def main():
    global nr_noduri_gen
    # setari interf grafica
    pygame.init()
    pygame.display.set_caption("Dragos-Constantin Tantaru - Ming Mang")
    # dimensiunea ferestrei in pixeli
    nl = 10
    nc = 10
    w = 50
    ecran = pygame.display.set_mode(size=(nc * (w + 1) - 1, nl * (w + 1) - 1))  # N *w+ N-1= N*(w+1)-1
    Joc.initializeaza(ecran, NR_LINII=nl, NR_COLOANE=nc, dim_celula=w)

    # initializare tabla
    JMIN, tip_algoritm, difficulty, dimensiune_tabla, pvp = deseneaza_alegeri(ecran)
    dimensiune_tabla = int(dimensiune_tabla)
    Joc.initializeaza(ecran, NR_LINII=dimensiune_tabla, NR_COLOANE=dimensiune_tabla,
                      dim_celula=int(w * nl / dimensiune_tabla))
    Joc.JMIN = JMIN
    nl = nc = dimensiune_tabla
    tabla_curenta = Joc(NR_LINII=dimensiune_tabla, NR_COLOANE=dimensiune_tabla)
    tabla_curenta.deseneaza_grid()
    print(Joc.JMIN, tip_algoritm, difficulty, dimensiune_tabla)

    Joc.JMAX = 'n' if Joc.JMIN == 'a' else 'a'
    print(Joc.JMAX, Joc.JMIN)

    print("Tabla initiala")
    print(str(tabla_curenta))

    ADANCIME_MAX = 4 if difficulty == "greu" else 3 if difficulty == "mediu" else 2 if difficulty == "usor" else 1
    # creare stare initiala
    stare_curenta = Stare(tabla_curenta, 'n', ADANCIME_MAX)

    tabla_curenta.deseneaza_grid()
    t_total_start = int(round(time.time()))
    sg_buton = Buton(display=ecran, top=10, left=450, w=15, h=15, text="x", culoareFundal=(155, 0, 55))
    mutari_player = 0
    mutari_pc = 0
    if pvp == "pve":
        selected_piesa = None
        # timpii de gandire pt AI
        tmin = None
        tmax = None
        all_times = []
        nmin = None
        nmax = None
        all_nodes = []
        t_inainte_player = None
        while True:

            if (stare_curenta.j_curent == Joc.JMIN):

                #
                # O sa fac in felul urmator: mai intai dai click pe ce piesa vrei sa muti, si dupa iti face cu galben
                # directiile posibile. Dai click undeva valid si te muta acolo. Daca dai click pe alta piesa de a ta,
                # o sa te schimbe sa muti pe ea
                if t_inainte_player is None:
                    t_inainte_player = int(round(time.time() * 1000))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        # iesim din program
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()  # coordonatele cursorului la momentul clickului
                        if sg_buton.selecteazaDupacoord(pos):
                            pygame.quit()
                            print("-"*50)
                            print("Timp total de joc: " + str(round(time.time() - t_total_start, 2)) + " secunde")
                            print("Nr. mutari jucator: " + str(mutari_player))
                            print("Nr. mutari calculator: " + str(mutari_pc))
                            sys.exit()

                        for np in range(len(Joc.celuleGrid)):

                            if Joc.celuleGrid[np].collidepoint(pos):
                                # linie=np//Joc.NR_COLOANE
                                coloana = np % Joc.NR_COLOANE
                                linie = np // Joc.NR_LINII
                                ###############################

                                if stare_curenta.tabla_joc.matr[linie][coloana] == Joc.JMIN:
                                    selected_piesa = (linie, coloana)
                                    stare_curenta.tabla_joc.deseneaza_grid(piesa_marcata=selected_piesa)
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                elif selected_piesa is not None and stare_curenta.tabla_joc.matr[linie][
                                    coloana] == Joc.GOL \
                                        and stare_curenta.tabla_joc.poate_ajunge_piesa((linie, coloana), Joc.JMIN,
                                                                                       selected_piesa) \
                                        and stare_curenta.tabla_joc.mutare_valida((linie, coloana), Joc.JMIN,
                                                                                  selected_piesa):
                                    mutari_player += 1
                                    stare_curenta.tabla_joc.matr[linie][coloana] = Joc.JMIN
                                    stare_curenta.tabla_joc.matr[selected_piesa[0]][selected_piesa[1]] = Joc.GOL
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    if Joc.JMIN == "a":
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                        negru_last, (selected_piesa[0], selected_piesa[1], linie
                                                     , coloana))
                                    else:
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                        (selected_piesa[0], selected_piesa[1], linie
                                         , coloana),
                                        alb_last)
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    print(negru_last)
                                    print(alb_last)
                                    stare_curenta.tabla_joc.check_and_mark(Joc.JMIN, (linie, coloana))
                                    # afisarea starii jocului in urma mutarii utilizatorului
                                    print("\nTabla dupa mutarea jucatorului")
                                    print(str(stare_curenta))

                                    t_dupa = int(round(time.time() * 1000))
                                    print("Jucatorul a gandit timp de " + str(
                                        t_dupa - t_inainte_player) + " milisecunde.")

                                    stare_curenta.tabla_joc.deseneaza_grid()
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                    # testez daca jocul a ajuns intr-o stare finala
                                    # si afisez un mesaj corespunzator in caz ca da
                                    if (afis_daca_final(stare_curenta)):
                                        break

                                    # S-a realizat o mutare. Schimb jucatorul cu cel opus
                                    stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)

            # --------------------------------
            else:  # jucatorul e JMAX (calculatorul)
                # Mutare calculator
                selected_piesa = None
                t_inainte_player = None
                nr_noduri_gen = 0

                # preiau timpul in milisecunde de dinainte de mutare
                t_inainte = int(round(time.time() * 1000))
                if tip_algoritm == 'minimax':
                    stare_actualizata = min_max(stare_curenta)
                else:  # tip_algoritm=="alphabeta"
                    stare_actualizata = alpha_beta(-500, 500, stare_curenta)
                stare_curenta.tabla_joc = stare_actualizata.stare_aleasa.tabla_joc
                negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                init_i, init_j, fin_i, fin_j = negru_last if Joc.JMAX == "n" else alb_last
                print("Scorul estimat mutarii: " + str(stare_actualizata.scor))

                print("Tabla dupa mutarea calculatorului\n" + str(stare_curenta))

                print("Noduri generate de algoritm: " + str(nr_noduri_gen))
                if nmin is None or nr_noduri_gen < nmin:
                    nmin = nr_noduri_gen
                if nmax is None or nr_noduri_gen > nmax:
                    nmax = nr_noduri_gen
                all_nodes += [nr_noduri_gen]
                print("Nr noduri minim generat la o mutare " + str(nmin))
                print("Nr noduri maxim generat la o mutare " + str(nmax))
                print("Nr noduri median generat la o mutare " + str(median(all_nodes)))

                # preiau timpul in milisecunde de dupa mutare
                t_dupa = int(round(time.time() * 1000))
                if tmin is None or t_dupa - t_inainte < tmin:
                    tmin = t_dupa - t_inainte
                if tmax is None or t_dupa - t_inainte > tmax:
                    tmax = t_dupa - t_inainte
                all_times += [t_dupa - t_inainte]
                print("Calculatorul a \"gandit\" timp de " + str(t_dupa - t_inainte) + " milisecunde.")
                print("Timp minim de gandire pana acum " + str(tmin))
                print("Timp maxim de gandire pana acum " + str(tmax))
                print("Timp median de gandire pana acum " + str(median(all_times)))
                mutari_pc += 1

                stare_curenta.tabla_joc.deseneaza_grid(mutare_calculator=(init_i, init_j, fin_i, fin_j))
                sg_buton.deseneaza()
                pygame.display.update()
                if (afis_daca_final(stare_curenta)):
                    break

                # S-a realizat o mutare. Schimb jucatorul cu cel opus
                stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)
    elif pvp == "pvp":
        selected_piesa_jmin = None
        selected_piesa_jmax = None
        t_inainte_player1 = None
        t_inainte_player2 = None
        while True:

            if (stare_curenta.j_curent == Joc.JMIN):
                selected_piesa_jmax = None
                t_inainte_player2 = None
                #
                # O sa fac in felul urmator: mai intai dai click pe ce piesa vrei sa muti, si dupa iti face cu galben
                # directiile posibile. Dai click undeva valid si te muta acolo. Daca dai click pe alta piesa de a ta,
                # o sa te schimbe sa muti pe ea
                if t_inainte_player1 is None:
                    t_inainte_player1 = int(round(time.time() * 1000))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        # iesim din program
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:

                        pos = pygame.mouse.get_pos()  # coordonatele cursorului la momentul clickului
                        if sg_buton.selecteazaDupacoord(pos):
                            pygame.quit()
                            print("-"*50)
                            print("Timp total de joc: " + str(round(time.time() - t_total_start, 2)) + " secunde")
                            print("Nr. mutari jucator 1 : " + str(mutari_player))
                            print("Nr. mutari jucator 2: " + str(mutari_pc))
                            sys.exit()

                        for np in range(len(Joc.celuleGrid)):

                            if Joc.celuleGrid[np].collidepoint(pos):
                                # linie=np//Joc.NR_COLOANE
                                coloana = np % Joc.NR_COLOANE
                                linie = np // Joc.NR_LINII
                                ###############################

                                if stare_curenta.tabla_joc.matr[linie][coloana] == Joc.JMIN:
                                    selected_piesa_jmin = (linie, coloana)
                                    stare_curenta.tabla_joc.deseneaza_grid(piesa_marcata=selected_piesa_jmin,
                                                                       cr_juc=Joc.JMIN)
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                elif selected_piesa_jmin is not None and stare_curenta.tabla_joc.matr[linie][
                                    coloana] == Joc.GOL \
                                        and stare_curenta.tabla_joc.poate_ajunge_piesa((linie, coloana), Joc.JMIN,
                                                                                       selected_piesa_jmin) \
                                        and stare_curenta.tabla_joc.mutare_valida((linie, coloana), Joc.JMIN,
                                                                                  selected_piesa_jmin):
                                    mutari_player += 1
                                    stare_curenta.tabla_joc.matr[linie][coloana] = Joc.JMIN
                                    stare_curenta.tabla_joc.matr[selected_piesa_jmin[0]][
                                        selected_piesa_jmin[1]] = Joc.GOL
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    if Joc.JMIN == "a":
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                            negru_last, (selected_piesa_jmin[0], selected_piesa_jmin[1], linie
                                                         , coloana))
                                    else:
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                            (selected_piesa_jmin[0], selected_piesa_jmin[1], linie
                                             , coloana),
                                            alb_last)
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    stare_curenta.tabla_joc.check_and_mark(Joc.JMIN, (linie, coloana))
                                    # afisarea starii jocului in urma mutarii utilizatorului
                                    print("\nTabla dupa mutarea jucatorului")
                                    print(str(stare_curenta))

                                    t_dupa = int(round(time.time() * 1000))
                                    print("Jucatorul 1 a gandit timp de " + str(
                                        t_dupa - t_inainte_player1) + " milisecunde.")

                                    stare_curenta.tabla_joc.deseneaza_grid()
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                    # testez daca jocul a ajuns intr-o stare finala
                                    # si afisez un mesaj corespunzator in caz ca da
                                    if (afis_daca_final(stare_curenta)):
                                        break

                                    # S-a realizat o mutare. Schimb jucatorul cu cel opus
                                    stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)
            else:
                selected_piesa_jmin = None
                t_inainte_player1 = None

                if t_inainte_player2 is None:
                    t_inainte_player2 = int(round(time.time() * 1000))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        # iesim din program
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:

                        pos = pygame.mouse.get_pos()  # coordonatele cursorului la momentul clickului
                        if sg_buton.selecteazaDupacoord(pos):
                            pygame.quit()
                            print("-"*50)
                            print("Timp total de joc: " + str(round(time.time() - t_total_start, 2)) + " secunde")
                            print("Nr. mutari jucator 1: " + str(mutari_player))
                            print("Nr. mutari jucator 2: " + str(mutari_pc))
                            sys.exit()

                        for np in range(len(Joc.celuleGrid)):

                            if Joc.celuleGrid[np].collidepoint(pos):
                                # linie=np//Joc.NR_COLOANE
                                coloana = np % Joc.NR_COLOANE
                                linie = np // Joc.NR_LINII
                                print(coloana, linie, stare_curenta.tabla_joc.matr[linie][coloana], Joc.JMAX,
                                      selected_piesa_jmax)
                                ###############################

                                if stare_curenta.tabla_joc.matr[linie][coloana] == Joc.JMAX:
                                    selected_piesa_jmax = (linie, coloana)
                                    stare_curenta.tabla_joc.deseneaza_grid(piesa_marcata=selected_piesa_jmax,
                                                                       cr_juc=Joc.JMAX)
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                elif selected_piesa_jmax is not None and stare_curenta.tabla_joc.matr[linie][
                                    coloana] == Joc.GOL \
                                        and stare_curenta.tabla_joc.poate_ajunge_piesa((linie, coloana), Joc.JMAX,
                                                                                       selected_piesa_jmax) \
                                        and stare_curenta.tabla_joc.mutare_valida((linie, coloana), Joc.JMAX,
                                                                                  selected_piesa_jmax):
                                    mutari_pc += 1
                                    stare_curenta.tabla_joc.matr[linie][coloana] = Joc.JMAX
                                    stare_curenta.tabla_joc.matr[selected_piesa_jmax[0]][
                                        selected_piesa_jmax[1]] = Joc.GOL
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    if Joc.JMAX == "a":
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                            negru_last, (selected_piesa_jmax[0], selected_piesa_jmax[1], linie
                                                         , coloana))
                                    else:
                                        stare_curenta.tabla_joc.ultima_mutare = (
                                            (selected_piesa_jmax[0], selected_piesa_jmax[1], linie
                                             , coloana),
                                            alb_last)
                                    negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                                    print(negru_last)
                                    print(alb_last)
                                    stare_curenta.tabla_joc.check_and_mark(Joc.JMAX, (linie, coloana))
                                    # afisarea starii jocului in urma mutarii utilizatorului
                                    print("\nTabla dupa mutarea jucatorului")
                                    print(str(stare_curenta))

                                    t_dupa = int(round(time.time() * 1000))
                                    print("Jucatorul 2 a gandit timp de " + str(
                                        t_dupa - t_inainte_player2) + " milisecunde.")

                                    stare_curenta.tabla_joc.deseneaza_grid()
                                    sg_buton.deseneaza()
                                    pygame.display.update()
                                    # testez daca jocul a ajuns intr-o stare finala
                                    # si afisez un mesaj corespunzator in caz ca da
                                    if (afis_daca_final(stare_curenta)):
                                        break

                                    # S-a realizat o mutare. Schimb jucatorul cu cel opus
                                    stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)
    else:
        tmin1 = None
        tmax1 = None
        all_times1 = []
        nmin1 = None
        nmax1 = None
        all_nodes1 = []

        tmin2 = None
        tmax2 = None
        all_times2 = []
        nmin2 = None
        nmax2 = None
        all_nodes2 = []
        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()  # coordonatele cursorului la momentul clickului
                    if sg_buton.selecteazaDupacoord(pos):
                        pygame.quit()
                        print("-" * 50)
                        print("Timp total de joc: " + str(round(time.time() - t_total_start, 2)) + " secunde")
                        print("Nr. mutari calculator 1: " + str(mutari_player))
                        print("Nr. mutari calculator 2: " + str(mutari_pc))
                        sys.exit()

            if stare_curenta.j_curent == "a":
                Joc.JMAX = "a"
                Joc.JMIN = "n"
                nr_noduri_gen = 0

                # preiau timpul in milisecunde de dinainte de mutare
                t_inainte = int(round(time.time() * 1000))
                if tip_algoritm == 'minimax':
                    stare_actualizata = min_max(stare_curenta, stare_curenta.j_curent)
                else:  # tip_algoritm=="alphabeta"
                    stare_actualizata = alpha_beta(-500, 500, stare_curenta, stare_curenta.j_curent)
                stare_curenta.tabla_joc = stare_actualizata.stare_aleasa.tabla_joc
                negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                init_i, init_j, fin_i, fin_j = alb_last
                print("Scorul estimat mutarii: " + str(stare_actualizata.scor))

                print("Noduri generate de algoritm: " + str(nr_noduri_gen))
                if nmin1 is None or nr_noduri_gen < nmin1:
                    nmin1 = nr_noduri_gen
                if nmax1 is None or nr_noduri_gen > nmax1:
                    nmax1 = nr_noduri_gen
                all_nodes1 += [nr_noduri_gen]
                print("Nr noduri minim generat la o mutare " + str(nmin1))
                print("Nr noduri maxim generat la o mutare " + str(nmax1))
                print("Nr noduri median generat la o mutare " + str(median(all_nodes1)))

                print("Tabla dupa mutarea calculatorului 1\n" + str(stare_curenta))


                t_dupa = int(round(time.time() * 1000))
                if tmin1 is None or t_dupa - t_inainte < tmin1:
                    tmin1 = t_dupa - t_inainte
                if tmax1 is None or t_dupa - t_inainte > tmax1:
                    tmax1 = t_dupa - t_inainte
                all_times1 += [t_dupa - t_inainte]
                print("Calculatorul 1 a \"gandit\" timp de " + str(t_dupa - t_inainte) + " milisecunde.")
                print("Timp minim de gandire pana acum " + str(tmin1))
                print("Timp maxim de gandire pana acum " + str(tmax1))
                print("Timp median de gandire pana acum " + str(median(all_times1)))
                mutari_player += 1
                stare_curenta.tabla_joc.deseneaza_grid(mutare_calculator=(init_i, init_j, fin_i, fin_j))
                sg_buton.deseneaza()
                pygame.display.update()
                if (afis_daca_final(stare_curenta)):
                    break

                # S-a realizat o mutare. Schimb jucatorul cu cel opus
                stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)

            else:
                Joc.JMAX = "n"
                Joc.JMIN = "a"
                nr_noduri_gen = 0

                # preiau timpul in milisecunde de dinainte de mutare
                t_inainte = int(round(time.time() * 1000))
                if tip_algoritm == 'minimax':
                    stare_actualizata = min_max(stare_curenta, stare_curenta.j_curent)
                else:  # tip_algoritm=="alphabeta"
                    stare_actualizata = alpha_beta(-500, 500, stare_curenta, stare_curenta.j_curent)
                stare_curenta.tabla_joc = stare_actualizata.stare_aleasa.tabla_joc
                negru_last, alb_last = stare_curenta.tabla_joc.ultima_mutare
                init_i, init_j, fin_i, fin_j = negru_last
                print("Scorul estimat mutarii: " + str(stare_actualizata.scor))

                print("Noduri generate de algoritm: " + str(nr_noduri_gen))
                if nmin2 is None or nr_noduri_gen < nmin2:
                    nmin2 = nr_noduri_gen
                if nmax2 is None or nr_noduri_gen > nmax2:
                    nmax2 = nr_noduri_gen
                all_nodes2 += [nr_noduri_gen]
                print("Nr noduri minim generat la o mutare " + str(nmin2))
                print("Nr noduri maxim generat la o mutare " + str(nmax2))
                print("Nr noduri median generat la o mutare " + str(median(all_nodes2)))

                print("Tabla dupa mutarea calculatorului 2\n" + str(stare_curenta))

                # preiau timpul in milisecunde de dupa mutare
                t_dupa = int(round(time.time() * 1000))
                if tmin2 is None or t_dupa - t_inainte < tmin2:
                    tmin2 = t_dupa - t_inainte
                if tmax2 is None or t_dupa - t_inainte > tmax2:
                    tmax2 = t_dupa - t_inainte
                all_times2 += [t_dupa - t_inainte]
                print("Calculatorul 2 a \"gandit\" timp de " + str(t_dupa - t_inainte) + " milisecunde.")
                print("Timp minim de gandire pana acum " + str(tmin2))
                print("Timp maxim de gandire pana acum " + str(tmax2))
                print("Timp median de gandire pana acum " + str(median(all_times2)))
                mutari_pc += 1
                stare_curenta.tabla_joc.deseneaza_grid(mutare_calculator=(init_i, init_j, fin_i, fin_j))
                sg_buton.deseneaza()
                pygame.display.update()
                if (afis_daca_final(stare_curenta)):
                    break

                # S-a realizat o mutare. Schimb jucatorul cu cel opus
                stare_curenta.j_curent = Joc.jucator_opus(stare_curenta.j_curent)

    # se afiseaza doar daca a castigat cineva meciul
    print("-" * 50)
    print("Timp total de joc: " + str(round(time.time() - t_total_start, 2)) + " secunde")
    print("Nr. mutari calculator 1: " + str(mutari_player))
    print("Nr. mutari calculator 2: " + str(mutari_pc))
    sys.exit()

if __name__ == "__main__":
    main()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
