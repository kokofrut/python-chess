import sys
import subprocess
import pkg_resources


import pygame as pg
import asyncio
import os
from pygame import freetype
import pieces
#from stockfish import Stockfish
import chess.engine
import time
from concurrent.futures import ThreadPoolExecutor
#from playsound import playsound
#engine = chess.engine.SimpleEngine.popen_uci(
 #   'stockfish_13/stockfish_13.exe'
#)
w = 1024
h = 720
BLACK = (0, 0, 0)
PASTELE_URANGE = (255, 223, 135)
URANGE = (255, 188, 71)
LIGHT_GREEN = (66, 245, 126)
BG_GREEN = (90, 145, 109)
WHITE = (255, 255, 255)
DARK_RED = (194, 13, 0)
#GREY = (142, 142, 142)
GREY = (252, 255, 161)
SILVER = (192, 192, 192)
LIGHT = (252, 204, 116)
# DARK = (87, 58, 46)
DARK = (166, 101, 75)
GREEN = (0, 255, 0)
RED = (255, 74, 74)
CYAN = (79, 250, 255)
BLUE = (63, 94, 251)
ORANGE = (255, 165, 0)
transcript_or, turn_number,transcript_1,transcript_15,transcript_27,transcript_39 = '', 0, '', '', '', ''
fenst = ''
count_castle_lock_black, count_castle_lock_white = 0, 0
castle = ''
info_d, info_t = (0,0), (0,0)
size = width, height = (300, 430)
count_pass = 0
count_castle = 0
last_o = None
last_d = None
PAT = False


def gradientRect( window, left_colour, right_colour, target_rect ):
    """ Draw a horizontal-gradient filled rectangle covering <target_rect> """
    colour_rect = pg.Surface( ( 2, 2 ) )                                   
    pg.draw.line( colour_rect, left_colour,  ( 0,0 ), ( 0,1 ) )            
    pg.draw.line( colour_rect, right_colour, ( 1,0 ), ( 1,1 ) )            
    colour_rect = pg.transform.smoothscale( colour_rect, ( target_rect.width, target_rect.height ) )  
    window.blit( colour_rect, target_rect )  

def coords_to_notation(coords):
    return f'{chr(97 + coords[0])}{8 - coords[1]}'

def coords_to_notation_passant(coords, turn, flipped, ai):
    if turn == 'white':
        if flipped == False:
            if ai == False:
                return f'{chr(97 + coords[0])}{7 - coords[1]}'
            else:
                return f'{chr(97 + coords[0])}{7 - coords[1]}'
        else:
            if ai == False:
                return f'{chr(97 + coords[0])}{7 - coords[1]}'
            else:
                return f'{chr(97 + coords[0])}{7 - coords[1]}' 
    else:
        if flipped == True:
            if ai == False:
                return f'{chr(97 + coords[0])}{9 - coords[1]}'
            else:
                return f'{chr(97 + coords[0])}{9 - coords[1]}'
        else:
            if ai == False:
                return f'{chr(97 + coords[0])}{9 - coords[1]}'
            else:
                return f'{chr(97 + coords[0])}{9 - coords[1]}' 

def notation_to_coords(notation):
    return ord(notation[0]) - 97, 8 - int(notation[1])


def reset_board(with_pieces=True):
    def generate_pieces(colour):
        return [pieces.Rook(colour), pieces.Knight(colour), pieces.Bishop(colour), pieces.Queen(colour),
                pieces.King(colour), pieces.Bishop(colour), pieces.Knight(colour), pieces.Rook(colour)]
    board = [[None for x in range(8)] for x in range(8)]
    if with_pieces:
        board[0] = generate_pieces("black")
        board[7] = generate_pieces("white")
        board[1] = [pieces.Pawn("black") for square in board[1]]
        board[6] = [pieces.Pawn("white") for square in board[6]]
    return board


def draw_squares(screen):
    colour_dict = {True: GREY, False: DARK}
    current_colour = True
    for row in range(8):
        for square in range(8):
            pg.draw.rect(screen, colour_dict[current_colour], ((
                40 + (square * 50)), 40 + (row * 50), 50, 50))
            current_colour = not current_colour
        current_colour = not current_colour

def draw_move(screen, destination, true_target, turn, turn_number, playing):
    if not playing and turn_number == 1 and turn == 'white':
        pass
    else:
        pg.draw.rect(screen, RED, ((40 + (destination[0] * 50)), 40 + (destination[1] * 50), 50, 50))
        pg.draw.rect(screen, BLACK, ((40 + (destination[0] * 50)), 40 + (destination[1] * 50), 50, 50), width = 1)
        pg.draw.rect(screen, RED, ((40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50)) 
        pg.draw.rect(screen, BLACK, ((40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50), width = 1) 

def draw_coords(screen, font, flipped):
    for row in range(8):
        if flipped:
            font.render_to(screen, (10, 45 + (row * 50)), chr(49 + row))
        else:
            font.render_to(screen, (10, 45 + (row * 50)), chr(56 - row))
    for col in range(8):
        if flipped:
            font.render_to(screen, (45 + (col * 50), 450), chr(72 - col))
        else:
            font.render_to(screen, (45 + (col * 50), 450), chr(65 + col))


def draw_pieces(screen, font, board, flipped):
    for row, pieces in enumerate(board[::(-1 if flipped else 1)]):
        for square, piece in enumerate(pieces[::(-1 if flipped else 1)]):
            if piece:
                font.render_to(screen, (piece.img_adjust[0] + (square * 50), piece.img_adjust[1] + (row * 50)),
                               piece.image, BLACK)


def find_square(x, y, flipped):
    true_target = int((x - 40) / 50), int((y - 40) / 50)
    if flipped:
        target_square = 7 - true_target[0], 7 - true_target[1]
    else:
        target_square = true_target
    return true_target, target_square

def draw_buttons(screen, font, font1, depth, promotion, font_chess, show_move, auto_flip, ai):
    #pg.draw.rect(screen, LIGHT, (725, 50, 50, 50))
    pg.draw.rect(screen, BLACK, (725, 50, 50, 50), width = 2)
    pg.draw.rect(screen, LIGHT, (778, 50, 100, 50))
    pg.draw.rect(screen, BLACK, (778, 50, 100, 50), width = 2)
    
    #pg.draw.rect(screen, LIGHT, (881, 50, 50, 50))
    pg.draw.rect(screen, BLACK, (881, 50, 50, 50), width = 2)
    font1.render_to(screen, (785,64), f'Depth: {depth}', BLACK)
    font1.render_to(screen, (800, 125), 'Reset', BLACK)
    font1.render_to(screen, (808, 185), 'Quit', BLACK)
    font1.render_to(screen, (772, 245), 'Auto-Flip', BLACK)
    promote_dict = {'queen': 'w', 'rook': 't',
                    'bishop': 'n', 'nknight': 'j'}
    font1.render_to(screen, (766, 305), f'Promote to ', BLACK)
    font1.render_to(screen, (728, 365), 'Show best move ', BLACK)
    font1.render_to(screen, (760, 425), 'AI opponent ', BLACK)
    font_chess.render_to(screen, (888, 303), f'{promote_dict[promotion]}')
    #pg.draw.rect(screen, LIGHT, (725, 110, 206, 50))
    pg.draw.rect(screen, BLACK, (724, 109, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (724, 169, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (724, 229, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (724, 289, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (724, 349, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (724, 409, 207, 51), width = 2)
    pg.draw.rect(screen, BLACK, (900, 365, 20, 20), width = 3)
    pg.draw.rect(screen, GREEN if show_move else DARK_RED, (902, 367, 16, 16))
    pg.draw.rect(screen, BLACK, (875, 245, 20, 20), width = 3)
    pg.draw.rect(screen, GREEN if auto_flip else DARK_RED, (877, 247, 16, 16))
    pg.draw.rect(screen, BLACK, (885, 425, 20, 20), width = 3)
    pg.draw.rect(screen, GREEN if ai else DARK_RED, (887, 427, 16, 16))
    

def draw_text(screen, font, font2, turn, turn_number, colour, check, playing, promotion, auto_flip, info1, info2, info3, font1, flipped, PAT):
    counter_colour = BLACK if turn == 'white' else WHITE
    #pg.draw.rect(screen, BLACK, (718, 43, 304, 434), width = 2)
    if flipped:
        pg.draw.rect(screen, WHITE, (460, 42, 20, 200))
        pg.draw.rect(screen, BLACK, (460, 242, 20, 200))
    else:
        pg.draw.rect(screen, BLACK, (460, 42, 20, 215))
        pg.draw.rect(screen, WHITE, (460, 242, 20, 200))
    #pg.draw.rect(screen, LIGHT, (720, 45, 300, 430))
    pg.draw.rect(screen, BLACK, (500, 45, 209, 130), width=1)
    pg.draw.rect(screen, BLACK, (500, 345, 209, 130), width=1)
    pg.draw.rect(screen, colour, (500, 190, 200, 140))
    pg.draw.rect(screen, DARK, (500, 190, 200, 140), width = 2)
    pg.draw.rect(screen, LIGHT, (20, 510, 1000, 180))
    pg.draw.rect(screen, DARK, (20, 510, 1000, 180), width = 2)
    if playing:
        font.render_to(screen, (515, 200), f'{turn} to move ', counter_colour)
    else:
        if PAT:
            font.render_to(screen, (515, 200), "stalemate", counter_colour)
        else:
            font.render_to(screen, (515, 200), f'{turn} wins', counter_colour)
    # pg.draw.rect(screen, counter_colour, (515, 230, 20, 20), width=3)
    # if auto_flip:
    #     font.render_to(screen, (515, 230), '✓', GREEN)
    font1.render_to(screen, (25, 520), f'Best move is: {info1}', BLACK)
    font1.render_to(screen, (25, 550), f'Score is: {info3} for {turn}', BLACK)  
    font2.render_to(screen, (25, 640), f'{transcript_39}', BLACK)  
    font2.render_to(screen, (25, 620), f'{transcript_27}', BLACK) 
    font2.render_to(screen, (25, 600), f'{transcript_15}', BLACK)
    font2.render_to(screen, (25, 580), f'{transcript_1}', BLACK)
    # font.render_to(screen, (540, 230), 'a - auto-rotate', counter_colour)
    # font.render_to(screen, (465, 260), {info1}, counter_colour)
    # promote_dict = {'queen': 9813, 'rook': 9814,
    #                 'bishop': 9815, 'nknight': 9816}
    # font.render_to(screen, (515, 260),
    #                f'promote: {chr(promote_dict[promotion])}', counter_colour)
    if check:
        font.render_to(screen, (515, 300), ('CHECK' if playing else 'CHECKMATE'),
                       counter_colour if playing else RED)
    if PAT:
        font.render_to(screen, (515, 300), 'STALEMATE', RED)



def draw_legal_moves(screen, colour, moves, board, flipped):
    for move in moves:
        if flipped:
            pg.draw.circle(
                screen, GREEN, ((65 + ((7 - move[0]) * 50), 65 + ((7 - move[1]) * 50))), 5)
        else:
            pg.draw.circle(
                screen, GREEN, ((65 + (move[0] * 50), 65 + (move[1] * 50))), 5)

def draw_last_move(screen, destination, true_target, turn, turn_number, playing):
    if not playing and turn_number == 1 and turn == 'white':
        pass
    else:
        pg.draw.rect(screen, URANGE, ((40 + (destination[0] * 50)), 40 + (destination[1] * 50), 50, 50))
        pg.draw.rect(screen, BLACK, ((40 + (destination[0] * 50)), 40 + (destination[1] * 50), 50, 50), width = 1)
        pg.draw.rect(screen, URANGE, ((40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50)) 
        pg.draw.rect(screen, BLACK, ((40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50), width = 1)


def draw_captures(screen, font, captures, flipped):
    for e, piece in enumerate([i for i in captures if i.colour == ('white' if flipped else 'black')]):
        if e < 6:
            font.render_to(screen, (456 + piece.img_adjust[0] + (e * 35), 300 + piece.img_adjust[1]), piece.image,
                           BLACK)
        elif e < 12:
            font.render_to(screen, (456 + piece.img_adjust[0] + ((e - 6) * 35), 340 + piece.img_adjust[1]), piece.image,
                           BLACK)
        else:
            font.render_to(screen, (456 + piece.img_adjust[0] + ((e - 12) * 35), 380 + piece.img_adjust[1]),
                           piece.image, BLACK)
    for e, piece in enumerate([i for i in captures if i.colour == ('black' if flipped else 'white')]):
        if e < 6:
            font.render_to(
                screen, (456 + piece.img_adjust[0] + (e * 30), piece.img_adjust[1]), piece.image, BLACK)
        elif e < 12:
            font.render_to(screen, (456 + piece.img_adjust[0] + ((e - 6) * 35), 40 + piece.img_adjust[1]), piece.image,
                           BLACK)
        else:
            font.render_to(screen, (456 + piece.img_adjust[0] + ((e - 12) * 35), 80 + piece.img_adjust[1]), piece.image,
                           BLACK)


def cancel_move(board, target, kings, origin, destination, captures, promotion, cancel, count_pass, count_castle, board_flipped):
    tmp = destination
    destination = origin
    origin = tmp
    cancel = True
    return move_piece(board, target, kings, origin, destination, captures, promotion, cancel, count_pass, board_flipped)

def pre_move(board, target, origin, destination, turn, flipped, ai):
    pre = ''
    for row in board:
        for piece in row:
            if piece and piece.name == 'pawn' and piece.en_passant:
                pre += coords_to_notation_passant(origin, turn, flipped, ai)
    return board, target, pre
def move_piece(board, target, kings, origin, destination, captures, promotion, cancel, count_pass, board_flipped):
    global transcript_or, turn_number, transcript_1, transcript_15, transcript_27, transcript_39, count_castle, last_o, last_d
    # start transcript
    if turn_number == 39 and target.colour == 'white':
        transcript_or = ''
    if turn_number == 27 and target.colour == 'white':
        transcript_or = ''
    if turn_number == 15 and target.colour == 'white':
        transcript_or = ''
    if target.colour == 'white' and turn_number != 0:
        transcript_or += f'{turn_number}. '
    elif target.colour == 'white' and turn_number == 0:
        turn_number += 1
        transcript_or += f'{turn_number}. '
    count_pass += 1
    # piece move conditions

    for row in board:
        for piece in row:
            if piece and piece.name == 'pawn' and piece.en_passant:
                piece.en_passant = False
    promoting = False
    if target.name == 'pawn':
        count_pass = 0
        if target.double_move:
            target.double_move = False
        if abs(origin[1] - destination[1]) == 2:
            target.en_passant = True
        if origin[0] != destination[0] and not board[destination[1]][destination[0]]:
            count_pass = 0
            captures.append(
                board[destination[1] - target.direction][destination[0]])
            board[destination[1] - target.direction][destination[0]] = None
            transcript_or += coords_to_notation(origin)[0]
        if destination[1] == (0 if target.colour == 'white' else 7):
            promoting = True
            piece_dict = {'queen': pieces.Queen(target.colour), 'nknight': pieces.Knight(target.colour),
                          'rook': pieces.Rook(target.colour), 'bishop': pieces.Bishop(target.colour)}
    if target.name == 'king':
        kings[int(target.colour == "black")] = destination
        if target.castle_rights:
            target.castle_rights = False
            if count_castle != 4:
                count_castle += 2
        if destination[0] - origin[0] == 2:
            board[target.back_rank][5] = board[target.back_rank][7]
            board[target.back_rank][7] = None
            transcript_or += 'O-O '
        if origin[0] - destination[0] == 2:
            board[target.back_rank][3] = board[target.back_rank][0]
            board[target.back_rank][0] = None
            transcript_or += 'O-O-O '
    if target.name == 'rook' and target.castle_rights:
        target.castle_rights = False

    # finish transcript
    if transcript_or[-2] != 'O':
        if target.name != 'pawn':
            transcript_or += target.name[0].upper(
            ) if target.name != 'nknight' else 'N'
        elif board[destination[1]][destination[0]]:
            transcript_or += coords_to_notation(origin)[0]
        transcript_or += f'x{coords_to_notation(destination)} ' if board[destination[1]
                                                                      ][destination[0]] else f'{coords_to_notation(destination)} '

    # add any existing piece to captures list
    if cancel == False:
        if board[destination[1]][destination[0]]:
            count_pass = 0
            captures.append(board[destination[1]][destination[0]])

    # move piece
    
    if not promoting:
        board[destination[1]][destination[0]] = target
    else:
        board[destination[1]][destination[0]] = piece_dict[promotion]
        transcript_or = transcript_or[:-1] + \
            f'={promotion[0].upper()} ' if promotion != 'nknight' else '=N '
    board[origin[1]][origin[0]] = None
    if turn_number < 15:
        transcript_1 = transcript_or
    if turn_number == 15:
        transcript_15 = transcript_or
    if turn_number > 14 and turn_number < 27:
        transcript_15 = transcript_or
    if turn_number > 26 and turn_number < 39:
        transcript_27 = transcript_or
    if turn_number > 38 and turn_number < 40:
        transcript_39 = transcript_or
    # any checks with new board status
    last_o = origin
    last_d = destination
    if board_flipped:
        last_o = 7 - last_o[0], 7 - last_o[1]
        last_d = 7 - last_d[0], 7 - last_d[1]
    enemy_king = kings[int(target.colour == "white")]
    check = board[enemy_king[1]][enemy_king[0]].in_check(board, enemy_king)
    if not check:
        pass
        #playsound('move.mp3')
    elif check:
        pass
        #playsound('check.mp3')
    return board, captures, kings, check, count_pass, origin, destination


def draw_check(screen, board, kings, flipped, turn, checkmate):
    if checkmate:
        king = kings[1 if turn == 'black' else 0]
    else:
        king = kings[0 if turn == 'white' else 1]
    if flipped:
        pg.draw.circle(screen, LIGHT_GREEN if checkmate else ORANGE, ((
            65 + ((7 - king[0]) * 50), 65 + ((7 - king[1]) * 50))), 25, width=3)
        #pg.draw.rect(screen, RED if checkmate else ORANGE, (65 + ((7 - king[0]) * 50), 65 + ((7 - king[1]) * 75), w / 8, h / 8), width=3)

    else:
        pg.draw.circle(screen, RED if checkmate else ORANGE, ((
            65 + (king[0] * 50), 65 + (king[1] * 50))), 25, width=3)
        #pg.draw.rect(screen, RED if checkmate else ORANGE, (65 + (king[0] * 45), (40 + (king[1] * 50)), (w / 14) + 4, h / 10), width = 3)


def check_for_quit():
    """Event Management for exiting the screen"""

    for event in pg.event.get():
        keys = pg.key.get_pressed()
        if event.type == pg.QUIT:
            return True
        elif keys[pg.K_ESCAPE]:
            return True
    pg.event.pump()
    return False


def checkmate(board, turn, kings):
    global transcript_or
    for y, row in enumerate(board):
        for x, square in enumerate(row):
            if square and square.colour == turn:
                moves = square.find_moves(board, (x, y), kings, True)
                if moves:
                    transcript_or = transcript_or[:-1] + '+ '
                    return False
    transcript_or = transcript_or[:-1] + '# '
    return True

def fen(board, turn, turn_number, fenst, target_square, destination, target, count_pass, ai, flipped):
    fenst = ''
    global count_castle, count_castle_lock_black, count_castle_lock_white
    pre = ''
    for row in board:
        count = 0
        for piece in row:
            if piece:
                if count != 0:  # если фигура то сначала ставит те пробелы потом фигуру
                    fenst += str(count)
                if piece.colour == 'white':
                    fenn = str(piece.name[0])
                    fenn1 = fenn.upper()
                    fenn = fenn1
                    fenst = fenst + fenn
                    count = 0
                else:
                    fenn = str(piece.name[0])
                    fenst = fenst + fenn
                    count = 0
            else:
                count += 1  # счетчик пробелов
        if count != 0:
            fenst += str(count)
        fenst = fenst + '/'
    fenst = fenst[:-1]
    fenst = fenst + " " + str(turn[0]) + " "
    color = ''
    castle = ''
    count = 0
    for row in reversed(board):
        for piece in row:
            if piece:
                if piece.name == 'king' and piece.castle_rights == True:
                    if board[piece.back_rank][0] and board[piece.back_rank][0].name == 'rook' and board[piece.back_rank][0].castle_rights:
                        if piece.can_castle(board) == 'q' or piece.can_castle(board) == 'k' or piece.can_castle(board) == 'kq':
                            if piece.colour == 'white':
                                color = str(piece.can_castle(board))
                                color1 = color.upper()
                                castle = castle + color1
                            else:
                                color = str(piece.can_castle(board))
                                castle = castle + color
                        else:
                            continue
                    elif board[piece.back_rank][7] and board[piece.back_rank][7].name == 'rook' and board[piece.back_rank][7].castle_rights:
                        if piece.can_castle(board) == 'q' or piece.can_castle(board) == 'k' or piece.can_castle(board) == 'kq':
                            if piece.colour == 'white':
                                color = str(piece.can_castle(board))
                                color1 = color.upper()
                                castle = castle + color1
                            else:
                                color = str(piece.can_castle(board))
                                castle = castle + color
                        else:
                            continue
                    elif (not board[piece.back_rank][7] and not board[piece.back_rank][0]) or (board[piece.back_rank][7].castle_rights == False and board[piece.back_rank][0].castle_rights == False) or (not board[piece.back_rank][7] and board[piece.back_rank][0].castle_rights == False) or (not board[piece.back_rank][0] and board[piece.back_rank][7].castle_rights == False):
                        piece.castle_rights = False
                        if piece.colour == 'white' and count_castle_lock_white == 0:
                            count_castle_lock_white = 1
                            count_castle += 2
                        elif piece.colour == 'black' and count_castle_lock_black == 0:
                            count_castle_lock_black = 1
                            count_castle += 2
                    else:
                        continue
                #elif piece.name == 'king' and piece.castle_rights == False:
                #    count_castle += 2
                else:
                    continue
            else:
                continue
    for row in reversed(board):
        for piece in row:
            if piece:
                if piece.name == 'pawn' and piece.en_passant == True:
                    pass               
    if count_castle == 4:
        castle = castle + '-'
        
    fenst = fenst + castle
    board, target, pre = pre_move(board, target, target_square, destination,turn, flipped, ai)
    fenst += ' '
    if pre != '':
        fenst += pre
    else:
        fenst += '-'
    fenst += ' '
    fenst += str(count_pass)
    fenst += ' '
    fenst += str(turn_number)
    fenst = fenst + ''
    return fenst


def change_tt(turn, turn_number):
    if turn == 'white':
        turn = 'black'
    else: 
        turn = 'white'
        turn_number += 1
    return turn, turn_number


async def analyse_t(board, engine, depth_b):
    info = await engine.analyse(board, chess.engine.Limit(depth = depth_b))
    return info


async def main():
    global transcript_or, turn_number, transcript_1, transcript_15, transcript_27, transcript_39
    global count_castle, last_o, last_d

    transport, engine = await chess.engine.popen_uci('chess-main_1/stockfish_13/stockfish_13.exe')
    basepath = 'chess-main_1/'
    pg.init()
    clock = pg.time.Clock()
    window_logo = pg.image.load('chess-main_1/images/chess_piece_king.png')
    arr_u = pg.image.load(os.path.join(basepath, "images/arr_u.png"))
    arr_u = pg.transform.scale(arr_u, (50, 50))
    arr_d = pg.image.load(os.path.join(basepath,"images/arr_d.png"))
    arr_d = pg.transform.scale(arr_d, (50, 50))
    pg.display.set_caption('Chess Solver')
    pg.display.set_icon(window_logo)
    screen = pg.display.set_mode((w, h))
    surface_1 = pg.Surface(size)
    bg = pg.image.load(os.path.join(basepath,"images/angryimg.png"))

    # font/pieces init: the piece icons come from the unicode of this font
    freetype.init()
    font = freetype.Font('chess-main_1/fonts/FreeSerif-4aeK.ttf', 50)
    micro_font = freetype.Font('chess-main_1/fonts/FreeSerif-4aeK.ttf', 25)
    font1 = freetype.Font('chess-main_1/fonts/textfont1.otf', 25)
    micro_font1 = freetype.Font('chess-main_1/fonts/textfont1.otf', 15)
    font2 = freetype.Font('chess-main_1/fonts/depth.ttf', 27)
    font_chess = freetype.Font('chess-main_1/fonts/CHEQ_TT.ttf', 27)
    # board init
    board = reset_board()
    # declare vars
    playing = True
    cancel = False
    depth_b = 16
    turn = 'white'
    info = ''
    count_pass = 0
    info1 = ''
    info2 = ''
    info3 = ''
    info_d, info_t = (0,0), (0,0)
    check = False
    board_flipped = False
    auto_flip = False
    kings = [(4, 7), (4, 0)]
    promotion = 'queen'
    target_square = None
    target = None
    show_move = True
    captures = []
    legal_moves = []
    ai = False
    ai_n = 0
    ai_move = True
    ai_first_move = 0
    PAT = False

    while True:
        # screen.fill(GREY)

        screen.blit(bg, (0, 0))
        screen.blit(arr_d, (726, 51))
        screen.blit(arr_u, (889, 51))
        COLOUR = WHITE if turn == 'white' else BLACK
        draw_squares(screen)
        if playing and turn_number == 0 and turn == 'white':
            pass
        else:
            # origin = 7 - origin[0], 7 - origin[1]
            # destination = 7 - destination[0], 7 - destination[1] #симафор
            draw_last_move(screen, last_o, last_d, turn, turn_number, playing)
            if show_move:
                draw_move(screen, info_d, info_t, turn, turn_number, playing)
            #draw_pieces(screen, font, board, board_flipped)
        if show_move == False:
            info1 = "Try your best"
        if turn_number == 75.:
            playing = False
            PAT = True
            info1 = ''  
        if target_square:
            pg.draw.rect(screen, BG_GREEN, ((
                40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50))
            pg.draw.rect(screen, GREEN, ((
                40 + (true_target[0] * 50)), 40 + (true_target[1] * 50), 50, 50), width=2)
        draw_coords(screen, font, board_flipped)
        draw_pieces(screen, font, board, board_flipped)
        pg.draw.rect(screen, LIGHT, (725, 110, 206, 50))
        pg.draw.rect(screen, LIGHT, (881, 50, 50, 50))
        pg.draw.rect(screen, LIGHT, (725, 50, 50, 50))
        pg.draw.rect(screen, LIGHT, (725, 170, 206, 50))
        pg.draw.rect(screen, LIGHT, (725, 230, 206, 50))
        pg.draw.rect(screen, LIGHT, (725, 290, 206, 50))
        pg.draw.rect(screen, LIGHT, (725, 350, 206, 50))
        pg.draw.rect(screen, LIGHT, (725, 410, 206, 50))
            
        qwerty = pg.mouse.get_pos()
        if 925 > qwerty[0] > 725 and 160 > qwerty[1] > 110:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725,110, 206, 50 ))
        if 775 > qwerty[0] > 725 and 100 > qwerty[1] > 50:
            gradientRect(screen, CYAN, BLUE, pg.Rect(725, 50, 50, 50))
        if 931 > qwerty[0] > 881 and 100 > qwerty[1] > 50:
            gradientRect(screen, CYAN, BLUE, pg.Rect(881, 50, 50, 50))
        if 925 > qwerty[0] > 725 and 220 > qwerty[1] > 170:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725,170, 206, 50 ))
        if 925 > qwerty[0] > 725 and 280 > qwerty[1] > 230:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725, 230, 206, 50 ))
        if 925 > qwerty[0] > 725 and 340 > qwerty[1] > 290:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725, 290, 206, 50 ))
        if 925 > qwerty[0] > 725 and 400 > qwerty[1] > 350:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725, 350, 206, 50 ))
        if 925 > qwerty[0] > 725 and 460 > qwerty[1] > 410:
            gradientRect(screen, CYAN, BLUE, pg.Rect( 725, 410, 206, 50 ))
        if ai and turn_number == 0:
            auto_flip = False
        if ai and turn_number != 0:
            auto_flip = False
            if board_flipped == False and turn == 'black':
                info = await analyse_t(board2, engine, depth_b)
                print(fenstr)
                if "pv" in info:
                    info1 = info["pv"]
                    info1 = info1[00]
                    info1_uci = info1.uci()
                    info_t = notation_to_coords(info1_uci[:2])
                    info_d = notation_to_coords(info1_uci[2:4])
                target_0 = info_t[0]
                target_1 = info_t[1]
                target = board[target_1][target_0]
                board, captures, kings, check, count_pass, origin, destination = move_piece(board, target, kings, info_t, info_d, captures, promotion, cancel, count_pass, board_flipped)
                
                turn, turn_number = change_tt(turn, turn_number)
                fenstr = fen(board, turn, turn_number, fenst, info_t, info_d, target, count_pass, ai, board_flipped)
                board2 = chess.Board(fenstr)
                info = await analyse_t(board2, engine, depth_b)
                print(fenstr)
                if "pv" in info:
                    info1 = info["pv"]
                    info1 = info1[00]
                    info1_uci = info1.uci()
                    info_t = notation_to_coords(info1_uci[:2])
                    info_d = notation_to_coords(info1_uci[2:4])
                else:
                    info1 = 'Mate'
                if "score" in info:
                    info2 = info["score"]
                    print(info2)
                    info3 = info2.relative
                    if hasattr(info3, 'cp'):
                        info3 = info3.cp / 100
                    else:
                        if info3.moves != 0:
                            info3 = f'Mate in {info3.moves}'
                        else: 
                            info3 = 'Mate, Congrats!!!'
                else:
                    info2 = 'Waiting'
                if check and checkmate(board, turn, kings):
                    target_square = None
                if legal_moves == False and turn_number != 0:
                    print("good")
                ai_n += 1
                if show_move:
                    draw_move(screen, info_d, info_t, turn, turn_number, playing)
                draw_last_move(screen, last_o, last_d, turn, turn_number, playing)
                draw_pieces(screen, font, board, board_flipped)
                # time.sleep(2)
            elif board_flipped == True and turn == 'white':
                info = await analyse_t(board2, engine, depth_b)
                print(fenstr)
                if "pv" in info:
                    info1 = info["pv"]
                    info1 = info1[00]
                    info1_uci = info1.uci()
                    info_t = notation_to_coords(info1_uci[:2])
                    info_d = notation_to_coords(info1_uci[2:4])
                target_0 = info_t[0]
                target_1 = info_t[1]
                #target_fix = (target_0, target_1)
                target = board[target_1][target_0]
                board, captures, kings, check, count_pass, origin, destination = move_piece(board, target, kings, info_t, info_d, captures, promotion, cancel, count_pass, board_flipped)
                turn, turn_number = change_tt(turn, turn_number)
                fenstr = fen(board, turn, turn_number, fenst, info_t, info_d, target, count_pass, ai, board_flipped)
                board2 = chess.Board(fenstr)
                info = await analyse_t(board2, engine, depth_b)
                print(fenstr)
                if "pv" in info:
                    info1 = info["pv"]
                    info1 = info1[00]
                    info1_uci = info1.uci()
                    info_t = notation_to_coords(info1_uci[:2])
                    info_d = notation_to_coords(info1_uci[2:4])
                else:
                    info1 = 'Mate'
                if "score" in info:
                    info2 = info["score"]
                    print(info2)
                    info3 = info2.relative
                    if hasattr(info3, 'cp'):
                        info3 = info3.cp / 100
                    else:
                        if info3.moves != 0:
                            info3 = f'Mate in {info3.moves}'
                        else: 
                            info3 = 'Mate, Congrats!!!'
                else:
                    info2 = 'Waiting'
                if check and checkmate(board, turn, kings):
                    target_square = None
                ai_n += 1
                if show_move:
                    info_d = 7 - info_d[0], 7 - info_d[1]
                    info_t = 7 - info_t[0], 7 - info_t[1]
                    draw_move(screen, info_d, info_t, turn, turn_number, playing)
                    draw_last_move(screen, last_o, last_d, turn, turn_number, playing)
                if board_flipped == True:
                    origin = 7 - origin[0], 7 - origin[1]
                    destination = 7 - destination[0], 7 - destination[1]
                draw_pieces(screen, font, board, board_flipped)
                # time.sleep(2)
                    
                    
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                if playing and 441 > event.pos[0] > 39 and 441 > event.pos[1] > 39:
                    if event.button != 3:
                        ev0 = event.pos[0]
                        ev1 = event.pos[1]
                        true_target, target_square = find_square(
                            event.pos[0], event.pos[1], board_flipped)
                        target = board[target_square[1]][target_square[0]]
                        if target and turn == target.colour:
                            legal_moves = target.find_moves(
                                board, target_square, kings, check)
                    elif target_square and target:
                        true_target, destination = find_square(
                            event.pos[0], event.pos[1], board_flipped)
                        if destination in legal_moves:
                                                      
                            if turn_number == 1 and turn == 'white':
                                fenstr = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
                            board, captures, kings, check, count_pass, origin, destination = move_piece(board, target, kings, target_square, destination, captures, promotion, cancel, count_pass, board_flipped)
                            turn, turn_number = change_tt(turn, turn_number) 
                            fenstr = fen(board, turn, turn_number, fenst, target_square, destination, target, count_pass, ai, board_flipped)
                            print(fenstr)
                            board2 = chess.Board(fenstr)
                            board1 = chess.Board('r1bqkbnr/pppppppp/8/8/8/3n4/PPP2PPP/RNBQKBNR w KQkq - 0 4')
                            info = await analyse_t(board2, engine, depth_b)
                            if "pv" in info:
                                info1 = info["pv"]
                                info1 = info1[00]
                                info1_uci = info1.uci()
                                info_t = notation_to_coords(info1_uci[:2])
                                info_d = notation_to_coords(info1_uci[2:4])
                                if board_flipped:
                                    info_d = 7 - info_d[0], 7 - info_d[1] 
                                    info_t = 7 - info_t[0], 7 - info_t[1] 
                            else:
                                info1 = 'Mate'
                            if "score" in info:
                                info2 = info["score"]
                                print(info2)
                                info3 = info2.relative
                                if hasattr(info3, 'cp'):
                                    info3 = info3.cp / 100
                                else:
                                    if info3.moves != 0:
                                        info3 = f'Mate in {info3.moves}'
                                    else: 
                                        info3 = 'Mate, Congrats!!!'
                            else:
                                info2 = 'Waiting'
                            if check and checkmate(board, turn, kings):
                                playing = False
                                target_square = None
                            #draw_pieces(screen, font, board, board_flipped)
                            
                            if cancel == False:
                                #turn = 'black' if turn == 'white' else 'white'
                                if auto_flip and board_flipped == (turn == 'white'):
                                    board_flipped = not board_flipped
                                    if target_square:
                                        true_target = 7 - \
                                            true_target[0], 7 - \
                                            true_target[1]
                            legal_moves = []
                        else:
                            target_square = None
                    else:
                        target_square = None
                elif 775 > event.pos[0] > 725 and 100 > event.pos[1] > 50:
                    target_square = None
                    if depth_b > 1:
                        depth_b -= 1
                        if turn_number != 0:
                            info = await analyse_t(board2, engine, depth_b)
                            if "pv" in info:
                                info1 = info["pv"]
                                info1 = info1[00]
                                info1_uci = info1.uci()
                                info_t = notation_to_coords(info1_uci[:2])
                                info_d = notation_to_coords(info1_uci[2:4])
                                if board_flipped:
                                    info_d = 7 - info_d[0], 7 - info_d[1] 
                                    info_t = 7 - info_t[0], 7 - info_t[1] 
                                    origin = 7 - origin[0], 7 - origin[1]
                                    destination = 7 - destination[0], 7 - destination[1]
                                if show_move:
                                    draw_move(screen, info_d, info_t, turn, turn_number, playing)
                                draw_pieces(screen, font, board, board_flipped)
                            else:
                                info1 = 'Mate'
                            if "score" in info:
                                info2 = info["score"]
                                print(info2)
                                info3 = info2.relative
                                if hasattr(info3, 'cp'):
                                    info3 = info3.cp / 100
                                else:
                                    if info3.moves != 0:
                                        info3 = f'Mate in {info3.moves}'
                                    else: 
                                        info3 = 'Mate, Congrats!!!'
                elif 931 > event.pos[0] > 725 and 460 > event.pos[1] > 410:     
                    if ai == True:
                        ai_first_move = 0
                        ai = False
                        auto_flip = False
                    elif ai == False:
                        ai_first_move = 1
                        ai = True  
                        auto_flip = False         
                elif 931 > event.pos[0] > 881 and 100 > event.pos[1] > 50:
                    target_aquare = None
                    if depth_b < 25:    
                        depth_b += 1
                        if turn_number != 0:
                            info = await analyse_t(board2, engine, depth_b)
                            if "pv" in info:
                                info1 = info["pv"]
                                info1 = info1[00]
                                info1_uci = info1.uci()
                                info_t = notation_to_coords(info1_uci[:2])
                                info_d = notation_to_coords(info1_uci[2:4])
                                if board_flipped:
                                    info_d = 7 - info_d[0], 7 - info_d[1] 
                                    info_t = 7 - info_t[0], 7 - info_t[1] 
                                    origin = 7 - origin[0], 7 - origin[1]
                                    destination = 7 - destination[0], 7 - destination[1]
                                if show_move:
                                    draw_move(screen, info_d, info_t, turn, turn_number, playing)
                                draw_pieces(screen, font, board, board_flipped)
                            else:
                                info1 = 'Mate'
                            if "score" in info:
                                info2 = info["score"]
                                print(info2)
                                info3 = info2.relative
                                if hasattr(info3, 'cp'):
                                    info3 = info3.cp / 100
                                else:
                                    if info3.moves != 0:
                                        info3 = f'Mate in {info3.moves}'
                                    else: 
                                        info3 = 'Mate, Congrats!!!'   
                elif 925 > event.pos[0] > 725 and 160 > event.pos[1] > 110: 
                    board = reset_board()
                    kings = [(4, 7), (4, 0)]
                    turn = 'white'
                    check = False
                    board_flipped = False
                    target_square = None
                    captures = []
                    playing = True
                    count_castle = 0
                    info3 = ''
                    info1 = ''
                    transcript_or, turn_number, transcript_15, transcript_27, transcript_39 = '', 0, '', '', ''
                    transcript_1 = ''
                    draw_text(screen, micro_font, micro_font1, turn, turn_number, COLOUR, check,
                        playing, promotion, auto_flip, info1, info2, info3, font1, board_flipped, PAT)
                    pg.display.update()
                elif 925 > event.pos[0] > 725 and  220 > event.pos[1] > 170:
                    pg.quit()
                elif 925 > event.pos[0] > 725 and 340 > event.pos[1] > 290:
                    if promotion == 'queen':
                        promotion = 'nknight'
                    elif promotion == 'nknight':
                        promotion = 'rook'
                    elif promotion == 'rook':
                        promotion = 'bishop'
                    elif promotion == 'bishop':
                        promotion = 'queen'
                elif 925 > event.pos[0] > 725 and 400 > event.pos[1] > 350:
                    show_move = not show_move
                elif 925 > event.pos[0] > 725 and 280 > event.pos[1] > 230:
                    auto_flip = not auto_flip
                else:
                    target_square = None
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    board_flipped = not board_flipped
                    if target_square:
                        true_target = 7 - true_target[0], 7 - true_target[1]
                    info_d = 7 - info_d[0], 7 - info_d[1] 
                    info_t = 7 - info_t[0], 7 - info_t[1] 
                    if turn_number != 0:
                        last_o = 7 - last_o[0], 7 - last_o[1]
                        last_d = 7 - last_d[0], 7 - last_d[1]
                        draw_last_move(screen, last_o, last_d, turn, turn_number, playing)
                    if show_move:
                        draw_move(screen, info_d, info_t, turn, turn_number, playing)
                    draw_pieces(screen, font, board, board_flipped)
                if event.key == pg.K_r:
                    board = reset_board()
                    kings = [(4, 7), (4, 0)]
                    turn = 'white'
                    check = False
                    board_flipped = False
                    target_square = None
                    captures = []
                    playing = True
                    info3 = ''
                    info1 = ''
                    transcript_or, turn_number, transcript_15, transcript_27, transcript_39 = '', 0, '', '', ''
                    transcript_1 = ''
                if event.key == pg.K_a:
                    auto_flip = not auto_flip
                if event.key == pg.K_1:
                    promotion = 'queen'
                if event.key == pg.K_2:
                    promotion = 'nknight'
                if event.key == pg.K_3:
                    promotion = 'rook'
                if event.key == pg.K_4:
                    promotion = 'bishop'
                if event.key == pg.K_p:
                    print(transcript_or)
                if event.key == pg.K_i:
                    ai = not ai
                if event.key == pg.K_c:
                    cancel_move(board, target, kings, target_square,
                                destination, captures, promotion, cancel, count_pass, count_castle, board_flipped)
                    if turn == 'white':
                        turn = 'black'
                    else:
                        turn = 'white'
                #if event.key == pg.K_e:
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
        draw_text(screen, micro_font, micro_font1, turn, turn_number, COLOUR, check,
                  playing, promotion, auto_flip, info1, info2, info3, font1, board_flipped, PAT)
        draw_buttons(screen, micro_font, font2, depth_b, promotion, font_chess, show_move, auto_flip, ai)
        
        if target_square and target and turn == target.colour and legal_moves:
            draw_legal_moves(screen, COLOUR, legal_moves, board, board_flipped)
        if captures:
            draw_captures(screen, font, captures, board_flipped)
        if check:
            draw_check(screen, board, kings, board_flipped, turn, not playing)
        if check_for_quit():
            sys.exit()
            engine.quit()
        screen.blit(arr_d, (725, 51))
        screen.blit(arr_u, (882, 51))
        pg.display.update()
        clock.tick(60)

if __name__ == '__main__':
       
    asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
    asyncio.run(main())
