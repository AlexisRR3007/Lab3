import numpy as np


def sauvola(I, k, R, n, taille_filtre, type_inter):
    """
    Applique l'algorithme de Sauvola
    :param I: Image à traitée
    :param k: Paramètre de la formule de Sauvola
    :param R: Paramètre de la formule de Sauvola
    :param n: Distance entre 2 pixels où on applique la formule
    :param taille_filtre: Taille du filtre
    :param type_inter: Type d'interpolation si n!=1 (1 : moyennes simples, 2 : moyennes pondérées)
    :return: Image traitée
    """

    # Definition des différente grandeurs
    X, Y = I.shape                  # Taile de l'image
    J = np.copy(I)                  # Copie de l'image. L'algo va modifier l'image J puis la renvoyée
    w = int(taille_filtre/2)        # Moitié de la taille du filtre
    BX = np.arange(0, int(np.ceil(X / n))) * n  # Calcul des points X sur lesquels on va appliquer l'algo
    BY = np.arange(0, int(np.ceil(Y / n))) * n  # Calcul des points X sur lesquels on va appliquer l'algo

    M = calc_moy(I, BX, BY, w, n)  # Calcul de la matrice des moyennes

    V = calc_ect(I, BX, BY, w, n, M)  # Calcul de la matrice des variances

    # T : Tableau des valeurs de seuillage pour chaque pixel
    # Les valeurs de seuillage étant positives, on place la valeur -1 pour les pixels non traitées
    # Si le pixel n'est pas à traité, la moyennes vaut -1
    # On applique donc la formule aux seuls pixels ayant une moyenne > -1
    T = np.where(M > -1, M * (1 + k * (V / R - 1)), -1)

    # On interpole seulement si n!=1
    if n != 1:
        if type_inter == 1:
            Interpolation(T, BX, BY, n)
        if type_inter == 2:
            Interpolation2(T, BX, BY, n)

    J[I > T] = 255
    J[I <= T] = 0

    return J


def calc_moy(I, BX, BY, w, n):
    """
    Calcul la matrice des moyennes. Les moyennes sont calculées en faisant glisser une fenêtre
    le long de l'image, de gauche à droite puis arriver en bout de ligne, on descend.
    Pour chaque pixel k, on récupère la somme des pixels entourant le pixel k-1 à laquelle on
    soustrait les valeurs des pixels qui ne sont plus dans la fenêtre de filtrage du pixel k.
    Puis on rajoute les pixels qui sont apparus dans la fenêtre du pixel k.
    Tout au long du processus, on adapte la norme.
    :param I: Image à traitée
    :param BX: Vecteur des points en X à traité
    :param BY: Vecteur des points en Y à traité
    :param w: Moitié de la taille du filtre
    :param n: Distance entre 2 pixels où on applique la formule
    :return: Tableau des moyennes avec comme valeur -1 si le pixel n'a pas été traité
    """

    X, Y = I.shape
    # Matrice des moyennes de chaque pixel. La première dimension contient la somme des pixels
    # entourant le pixel de calcul et la deuxième le nombre de pixel entourant le pixel de calcul
    # (ie la norme).
    # Avec cette initialisation, les sommes valent 1 et les normes -1, si un pixel n'est pas traité
    # sa valeur moyenne renvoyée sera 1/-1=-1 permettant par la suite de l'identifier.
    M = np.ones((X, Y, 2))
    M[:, :, 1] -= 2

    # Permet de détecter un changement de ligne, en effet pour un pixel situé sur une ligne
    # on récupère la moyenne du pixel 'à sa gauche'. Lors d'un changment de ligne, il faut
    # récupérer la valeur de la moyenne du pixel supérieur.
    chgt_ligne = 0

    # Signification des compteurs
    # ci : Indice x du pixel de calcul
    # cj : Indice y du pixel de calcul
    # cci : Variation autour de ci
    # ccj : Variation autoue de cj
    if 2*w > n:  # Si superposition de fenêtre de moyennage entre 2 pixels
        for ci in BX:
            for cj in BY:
                m = 0
                norm = 0
                if ci == BX[0] and cj == BY[0]:  # On traite le premier pixel pour démarrer le 'glissement'
                    for cci in range(ci - w, ci + w + 1):
                        for ccj in range(cj - w, cj + w + 1):
                            if InImage(cci, ccj, X, Y):
                                m += I[cci, ccj]
                                norm += 1
                else:
                    if chgt_ligne == 1:  # Si on vient de changer de ligne
                        m = M[ci-n, cj, 0]
                        norm = M[ci-n, cj, 1]
                        # On enlève les pixels n'étant plus concernée
                        for cci in range(ci - n - w, ci - w):
                            for ccj in range(cj - w, cj + w + 1):
                                if InImage(cci, ccj, X, Y):
                                    m -= I[cci, ccj]
                                    norm -= 1
                        # On ajoute les nouveaux pixels
                        for cci in range(ci - n + w + 1, ci + w + 1):
                            for ccj in range(cj - w, cj + w + 1):
                                if InImage(cci, ccj, X, Y):
                                    m += I[cci, ccj]
                                    norm += 1
                        chgt_ligne = 0
                    else:
                        m = M[ci, cj-n, 0]
                        norm = M[ci, cj-n, 1]
                        # On enlève les pixels n'étant plus concernée
                        for cci in range(ci - w, ci + w + 1):
                            for ccj in range(cj - n - w, cj - w):
                                if InImage(cci, ccj, X, Y):
                                    m -= I[cci, ccj]
                                    norm -= 1
                        # On ajoute les nouveaux pixels
                        for cci in range(ci - w, ci + w + 1):
                            for ccj in range(cj - n + w + 1, cj + w + 1):
                                if InImage(cci, ccj, X, Y):
                                    m += I[cci, ccj]
                                    norm += 1
                M[ci, cj, 0] = m
                M[ci, cj, 1] = norm
            chgt_ligne = 1
    else:
        for ci in BX:
            for cj in BY:
                m = 0
                norm = 0
                for cci in range(ci - w, ci + w + 1):
                    for ccj in range(cj - w, cj + w + 1):
                        if InImage(cci, ccj, X, Y):
                            m += I[cci, ccj]
                            norm += 1
                M[ci, cj, 0] = m
                M[ci, cj, 1] = norm
    return (M[:, :, 0] / M[:, :, 1]).astype(np.int32)


def calc_ect(I, BX, BY, w, n, M):
    """
    Calcul la matrice des ecart-tyes. Le principe est le même que pour les moyennes, néanmoins
    on applique le principe que si la moyenne du pixel k est la même que la moyenne du pixel k-1.
    Sinon on recalcul la variance de facon 'classique'
    :param I: Image à traitée
    :param BX: Vecteur des points en X à traité
    :param BY: Vecteur des points en Y à traité
    :param w: Moitié de la taille du filtre
    :param n: Distance entre 2 pixels où on applique la formule
    :param M: Tableau des moyennes
    :return: Tableau des ecart-types avec comme valeur 0 si le pixel n'a pas été traité
    """
    X, Y = I.shape

    V = np.zeros((X, Y, 2))
    V[:, :, 1] += 1

    chgt_ligne = 0

    if 2*w > n:
        for ci in BX:
            for cj in BY:
                va = 0
                norm = 0
                if ci == BX[0] and cj == BY[0]:
                    for cci in range(ci - w, ci + w + 1):
                        for ccj in range(cj - w, cj + w + 1):
                            if InImage(cci, ccj, X, Y):
                                va += (I[cci, ccj] - M[ci, cj])**2
                                norm += 1
                else:
                    m = M[ci, cj]
                    if chgt_ligne == 1:
                        if M[ci, cj] == M[ci - n, cj]:
                            va = V[ci-n, cj, 0]
                            norm = V[ci-n, cj, 1]
                            for cci in range(ci - n - w, ci - w):
                                for ccj in range(cj - w, cj + w + 1):
                                    if InImage(cci, ccj, X, Y):
                                        va -= (I[cci, ccj] - m) ** 2
                                        norm -= 1
                            for cci in range(ci - n + w + 1, ci + w + 1):
                                for ccj in range(cj - w, cj + w + 1):
                                    if InImage(cci, ccj, X, Y):
                                        va += (I[cci, ccj] - m) ** 2
                                        norm += 1
                        else:
                            for cci in range(ci - w, ci + w + 1):
                                for ccj in range(cj - w, cj + w + 1):
                                    if InImage(cci, ccj, X, Y):
                                        va += (I[cci, ccj] - m) ** 2
                                        norm += 1
                        chgt_ligne = 0
                    else:
                        if M[ci, cj] == M[ci, cj-n]:
                            va = V[ci, cj-n, 0]
                            norm = V[ci, cj-n, 1]
                            for cci in range(ci - w, ci + w + 1):
                                for ccj in range(cj - n - w, cj - w):
                                    if InImage(cci, ccj, X, Y):
                                        va -= (I[cci, ccj] - m)**2
                                        norm -= 1
                            for cci in range(ci - w, ci + w + 1):
                                for ccj in range(cj - n + w + 1, cj + w + 1):
                                    if InImage(cci, ccj, X, Y):
                                        va += (I[cci, ccj] - m)**2
                                        norm += 1
                        else:
                            for cci in range(ci - w, ci + w + 1):
                                for ccj in range(cj - w, cj + w + 1):
                                    if InImage(cci, ccj, X, Y):
                                        va += (I[cci, ccj] - m) ** 2
                                        norm += 1
                V[ci, cj, 0] = va
                V[ci, cj, 1] = norm
            chgt_ligne = 1
    else:
        for ci in BX:
            for cj in BY:
                va = 0
                norm = 0
                for cci in range(ci - w, ci + w + 1):
                    for ccj in range(cj - w, cj + w + 1):
                        if InImage(cci, ccj, X, Y):
                            va += (I[cci, ccj] - M[ci, cj])**2
                            norm += 1
                V[ci, cj, 0] = va
                V[ci, cj, 1] = norm
    V = V[:, :, 0] / V[:, :, 1]
    return V**(1/2)


def Interpolation(T, BX, BY, n):
    """
    Calcul les valeurs de seuillage manquantes avec des moyennes simples
    Voir : https://fr.wikipedia.org/wiki/Pond%C3%A9ration_inverse_%C3%A0_la_distance
    :param T: Tableau des valeurs de seuillage
    :param BX: Vecteur des points en X à traité
    :param BY: Vecteur des points en Y à traité
    :param n: Distance entre 2 pixels où on applique la formule
    """

    X, Y = T.shape

    nto = X*Y - len(BX)*len(BY)

    for ci in BX:
        for cj in BY:
            for cci in range(n):
                for ccj in range(n):
                    temp = 0
                    norm = 1
                    if InImage(ci + cci, cj + ccj, X, Y):
                        if T[ci + cci, cj + ccj] == -1:
                            temp += T[ci, cj]
                            if InImage(ci, cj + n, X, Y):
                                temp += T[ci, cj + n]
                                norm += 1
                            if InImage(ci + n, cj, X, Y):
                                temp += T[ci + n, cj]
                                norm += 1
                            if InImage(ci + n, cj + n, X, Y):
                                temp += T[ci + n, cj + n]
                                norm += 1
                            T[ci + cci, cj + ccj] = temp/norm


def Interpolation2(T, BX, BY, n):
    """
    Calcul les valeurs de seuillage manquantes avec des moyennes pondérées
    :param T: Tableau des valeurs de seuillage
    :param BX: Vecteur des points en X à traité
    :param BY: Vecteur des points en Y à traité
    :param n: Distance entre 2 pixels où on applique la formule
    """

    MA, MB, MC, MD = MDistance(n)
    X, Y = T.shape

    nto = X*Y - len(BX)*len(BY)

    for ci in BX:
        for cj in BY:
            MAA = MA * T[ci, cj]
            if InImage(ci, cj + n, X, Y):
                MBB = MB * T[ci, cj + n]
            if InImage(ci + n, cj, X, Y):
                MCC = MC * T[ci + n, cj]
            if InImage(ci + n, cj + n, X, Y):
                MDD = MD * T[ci + n, cj + n]
            for cci in range(n):
                for ccj in range(n):
                    temp = 0
                    norm = 0
                    if InImage(ci + cci, cj + ccj, X, Y):
                        if T[ci + cci, cj + ccj] == -1:
                            temp += MAA[cci, ccj]
                            norm += MA[cci, ccj]
                            if InImage(ci, cj + n, X, Y):
                                temp += MBB[cci, ccj]
                                norm += MB[cci, ccj]
                            if InImage(ci + n, cj, X, Y):
                                temp += MCC[cci, ccj]
                                norm += MC[cci, ccj]
                            if InImage(ci + n, cj + n, X, Y):
                                temp += MDD[cci, ccj]
                                norm += MD[cci, ccj]
                            T[ci+cci, cj+ccj] = temp/norm


def MDistance(n):
    """
    Calcul la matrice des distances inverses
    :param n: Distance entre 2 pixels où on applique la formule
    :return: Matrice des distances inverses
    """

    M = np.zeros((n+1, n+1))
    for ci in range(n+1):
        for cj in range(n+1):
            M[ci, cj] = (ci**2+cj**2)**(1/2)
    M[0, 0] = 1
    return M, np.rot90(M, 3), np.rot90(M, 1), np.rot90(M, 2)


def InImage(i, j, X, Y):
    """
    Vérifie si une position est dans l'image
    :param i: Position selon X
    :param j: Position selon Y
    :param X: Valeur maximum des X
    :param Y: Valeur maximum des Y
    :return: Boolean valant True si le point est dans l'image
    """
    return not (i < 0 or i >= X or j < 0 or j >= Y)