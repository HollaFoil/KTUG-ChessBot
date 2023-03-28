import copy
import os
import pygame
import datetime
import cv2
from .Constants import *
from .MoveHistory import BoardState, MoveHistory

_margin = 8
_piece_size = 96

_highlight_color = (150, 183, 206, 100)
_move_color = (158, 219, 243, 100)
_possible_move_color = (40, 100, 40, 150)
_check_color = (255, 0, 0, 100)
_check_mate_color = (255, 0, 0, 200)
_stale_mate_color = (255, 240, 0, 150)
_black_time_location = (800, 25)
_white_time_location = (800, 700)

from pygame import gfxdraw

def drawAACircle(surf, color, center, radius, offset=0):
    circle_image = np.zeros((radius*2+4, radius*2+4, 4), dtype = np.uint8)
    circle_image = cv2.circle(circle_image, (radius+2, radius+2), offset, color, thickness=2*(radius-2), lineType=cv2.LINE_AA)  
    circle_surface = pygame.image.frombuffer(circle_image.flatten(), (radius*2+4, radius*2+4), 'RGBA')
    surf.blit(circle_surface, circle_surface.get_rect(center = center))

class Board:
    status = "Begin"
    should_send_fen = True
    selected_piece = (-1, -1)
    has_piece_selected = False
    holding_piece = False
    width = 1000
    height = 784


    white_victory = False
    white_to_move = True
    clock_win = False
    draw_insufficient_material = False
    checkmate = False
    stalemate = False
    moves = 1
    halfmove_clock = 0

    can_castle_queen_black = True
    can_castle_queen_white = True
    can_castle_king_black = True
    can_castle_king_white = True
    en_passant_target = (-1, -1)
    prev_move = [(-1, -1), (-1, -1)]
    positions = {"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR": 1}
    cached_moves = None

    increment = 3000            #milliseconds
    time_left_black = 5*60*1000 #milliseconds
    time_left_white = 5*60*1000 #milliseconds
    start_time_black = datetime.datetime.now()
    start_time_white = datetime.datetime.now()
    is_clock_ticking = False

    history = MoveHistory()

    pygame.font.init()
    text_font = pygame.font.Font('./Assets/Segoe UI Mono Bold.ttf', 55)

    def __init__(self, width, height):
        self.board = copy.deepcopy(STARTING_POSITION)
        self.load_from_state(self.history.get_state())
        self.load_images()
        self.width = width
        self.height = height

    def is_game_ended(self):
        return self.clock_win or self.checkmate or self.stalemate or self.draw_insufficient_material

    def render_board(self):
        surf = pygame.Surface((self.width, self.height))
        surf.fill((50, 50, 50))
        surf.blit(self.board_img, (0, 0))

        if self.has_piece_selected:
            x, y = self.selected_piece
            s = pygame.Surface((_piece_size,_piece_size), pygame.SRCALPHA)
            s.fill(_highlight_color)  
            surf.blit(s, self.get_location((x, y)))

        if self.prev_move[0] != (-1, -1):
            x, y = self.prev_move[0]
            x2, y2 = self.prev_move[1]
            s = pygame.Surface((_piece_size,_piece_size), pygame.SRCALPHA)
            s.fill(_move_color)  
            surf.blit(s, self.get_location((x, y)))
            surf.blit(s, self.get_location((x2, y2)))

        if self.has_piece_selected:
            if self.cached_moves == None:
                self.cached_moves = self.get_possible_moves(self.selected_piece)
            for (x, y) in self.cached_moves:
                s = pygame.Surface((_piece_size,_piece_size), pygame.SRCALPHA)
                mouse_x, mouse_y = pygame.mouse.get_pos()
                file = int((mouse_x - _margin)/_piece_size)
                rank = int((mouse_y - _margin)/_piece_size)
                if (file, rank) == (x, y):
                    pygame.draw.rect(s, _possible_move_color, pygame.rect.Rect(0, 0, _piece_size, _piece_size))
                elif self.board[x][y] == EMPTY:
                    drawAACircle(s, _possible_move_color, (int(_piece_size/2), int(_piece_size/2)), 13)
                    #draw_circle(s, int(_piece_size/2), int(_piece_size/2), 13, _possible_move_color)
                    #pygame.draw.circle(s, _possible_move_color, (_piece_size/2,_piece_size/2), 13)
                else:
                    drawAACircle(s, _possible_move_color, (int(_piece_size/2), int(_piece_size/2)), 47, 100)
                    #pygame.draw.circle(s, (0,0,0,0), (_piece_size/2,_piece_size/2), 54)
                #s.set_alpha(_possible_move_color[3])
                surf.blit(s, self.get_location((x, y)))

        if self.is_in_check(BLACK) or (self.clock_win and self.white_victory):
            color = _check_mate_color if self.checkmate else _stale_mate_color if self.stalemate else _check_color
            for file in range(8):
                for rank in range(8):
                    piece = self.board[file][rank]
                    if piece != BLACK_KING:
                        continue
                    s = pygame.Surface((_piece_size,_piece_size), pygame.SRCALPHA)
                    s.fill(color)  
                    surf.blit(s, self.get_location((file, rank)))

        if self.is_in_check(WHITE) or (self.clock_win and not self.white_victory):
            color = _check_mate_color if self.checkmate else _stale_mate_color if self.stalemate else _check_color
            for file in range(8):
                for rank in range(8):
                    piece = self.board[file][rank]
                    if piece != WHITE_KING:
                        continue
                    s = pygame.Surface((_piece_size,_piece_size), pygame.SRCALPHA)
                    s.fill(color)  
                    surf.blit(s, self.get_location((file, rank)))


        for file in range(8):
            for rank in range(8):
                piece = self.board[file][rank]
                if piece == EMPTY:
                    continue
                if (file, rank) == self.selected_piece and self.holding_piece:
                    continue
                surf.blit(self.piece_images[piece], self.get_location((file, rank)))
        
        if self.holding_piece:
            held_piece = self.get_piece(self.selected_piece)
            x, y = pygame.mouse.get_pos()
            surf.blit(self.piece_images[held_piece], (x - _piece_size/2, y-_piece_size/2))

        surfaces = self.draw_ui_surf()
        surf.blit(surfaces[0], _black_time_location)
        surf.blit(surfaces[1], _white_time_location)

        return surf

    def draw_ui_surf(self):
        white_time_text = str(int((self.time_left_white / (60 * 1000)))) + ":" \
                        + "{:0.3f}".format(self.time_left_white % (60 * 1000) / 1000).zfill(6)
        black_time_text = str(int((self.time_left_black / (60 * 1000)))) + ":" \
                        + "{:0.3f}".format(self.time_left_black % (60 * 1000) / 1000).zfill(6)
        black_surface = self.text_font.render(black_time_text, True, (255, 255, 255))
        white_surface = self.text_font.render(white_time_text, True, (255, 255, 255))
        return [black_surface, white_surface]

    def get_location(self, pos):
        file, rank = pos
        return (_margin + _piece_size*file, _margin + _piece_size*rank)

    def start_clock(self):
        if self.is_clock_ticking:
            return
        if self.white_to_move:
            self.start_time_white = datetime.datetime.now()
        else:
            self.start_time_black = datetime.datetime.now()
        self.is_clock_ticking = True

    def tick_clock(self):
        self.stop_clock()
        self.check_for_clock_win()
        if not self.is_game_ended():
            self.start_clock()

    def check_for_clock_win(self):
        if self.time_left_white <= 0:
            self.clock_win = True
            self.time_left_white = 0
        elif self.time_left_black <= 0:
            self.clock_win = True
            self.white_victory = True
            self.time_left_black = 0
        if self.clock_win:
            self.stop_clock()
            self.status = ("White" if self.white_victory else "Black") + " win by timeout"


    def stop_clock(self):
        if not self.is_clock_ticking:
            return
        time_now = datetime.datetime.now()
        if self.white_to_move:
            elapsed_time = time_now - self.start_time_white
            elapsed_milliseconds = np.floor(elapsed_time.total_seconds()*1000)
            self.time_left_white -= elapsed_milliseconds
        else:
            elapsed_time = time_now - self.start_time_black
            elapsed_milliseconds = np.floor(elapsed_time.total_seconds()*1000)
            self.time_left_black -= elapsed_milliseconds
        self.is_clock_ticking = False

    def add_increment(self):
        if self.white_to_move:
            self.time_left_white += self.increment
        else:
            self.time_left_black += self.increment

    def on_mouse_down_event(self):
        clicked_x, clicked_y = pygame.mouse.get_pos()
        file = int((clicked_x - _margin)/_piece_size)
        rank = int((clicked_y - _margin)/_piece_size)
        self.cached_moves = None
        if not ((0 <= file <= 7) and (0 <= rank <= 7)):
            return
        
        piece = self.board[file, rank]
        if piece == EMPTY:
            return
        if self.is_piece_white(piece) != self.white_to_move:
            return

        self.selected_piece = (file, rank)
        self.has_piece_selected = True
        self.holding_piece = True
    

    def get_piece(self, pos):
        x, y = pos
        return self.board[x][y]

    def set_piece(self, pos, piece):
        x, y = pos
        self.board[x][y] = piece

    def get_possible_moves(self, frompos, checks = True):
        piece = self.get_piece(frompos)
        is_white = self.is_piece_white(piece)
        color = WHITE if is_white else BLACK
        moves = []
        if piece&BISHOP > 0:
            moves = self.get_bishop_moves(frompos, is_white)
        elif piece&ROOK > 0:
            moves =  self.get_rook_moves(frompos, is_white)
        elif piece&KNIGHT > 0:
            moves =  self.get_knight_moves(frompos, is_white)
        elif piece&QUEEN > 0:
            moves =  self.get_queen_moves(frompos, is_white)
        elif piece&PAWN > 0:
            moves =  self.get_pawn_moves(frompos, is_white)
        elif piece&KING > 0:
            moves =  self.get_king_moves(frompos, is_white)
        if not checks:
            return moves

        legal_moves = []
        for move in moves:
            x1, y1 = frompos
            x2, y2 = move
            piece_at = self.get_piece(move)
            self.set_piece(move, piece)
            self.set_piece(frompos, EMPTY)
            if piece & PAWN > 0 and move == self.en_passant_target:
                self.set_piece((x2, y1), EMPTY)

            if not self.is_in_check(color):
                legal_moves += [move]
            if piece & PAWN > 0 and move == self.en_passant_target:
                self.set_piece((x2, y1), BLACK_PAWN if is_white else WHITE_PAWN)
            self.set_piece(move, piece_at)
            self.set_piece(frompos, piece)

        return legal_moves
    
    def get_bishop_moves(self, frompos, is_white):
        dir = [[1, 1], [-1, -1], [1, -1], [-1, 1]]
        legal_moves = []

        for direction in dir:
            x, y = frompos
            x += direction[0]
            y += direction[1]
            while self.within_bounds(x, y):
                piece_at_target = self.get_piece((x, y))
                if piece_at_target == EMPTY:
                    legal_moves += [(x, y)]
                    x += direction[0]
                    y += direction[1]

                elif self.is_piece_white(piece_at_target) == is_white:
                    break
                else:
                    legal_moves += [(x, y)]
                    break
                
        return legal_moves

    def get_queen_moves(self, frompos, is_white):
        dir = [[1, 0], [-1, 0], [0, -1], [0, 1], [1, 1], [-1, -1], [1, -1], [-1, 1]]
        legal_moves = []

        for direction in dir:
            x, y = frompos
            x += direction[0]
            y += direction[1]
            while self.within_bounds(x, y):
                piece_at_target = self.get_piece((x, y))
                if piece_at_target == EMPTY:
                    legal_moves += [(x, y)]
                    x += direction[0]
                    y += direction[1]
                    
                elif self.is_piece_white(piece_at_target) == is_white:
                    break
                else:
                    legal_moves += [(x, y)]
                    break
                
        return legal_moves

    def get_king_moves(self, frompos, is_white):
        dir = [[1, 0], [-1, 0], [0, -1], [0, 1], [1, 1], [-1, -1], [1, -1], [-1, 1]]
        legal_moves = []
        color = WHITE if is_white else BLACK


        for direction in dir:
            x, y = frompos
            x += direction[0]
            y += direction[1]
            if not self.within_bounds(x, y):
                continue
            piece_at_target = self.get_piece((x, y))
                
            if self.is_piece_white(piece_at_target) == is_white and piece_at_target != EMPTY:
                continue
            else:
                legal_moves += [(x, y)]
                continue
        
        x, y = frompos
        if ((is_white and self.can_castle_queen_white) or (not is_white and self.can_castle_queen_black)) and x-3 >= 0:
            if self.board[x-1][y] == EMPTY and self.board[x-2][y] == EMPTY and self.board[x-3][y] == EMPTY:
                self.set_piece((x-1, y), self.get_piece(frompos))
                self.set_piece((x-2, y), self.get_piece(frompos))
                if not self.is_in_check(color):
                    legal_moves += [(x-2, y)] 
                self.set_piece((x-1, y), EMPTY)
                self.set_piece((x-2, y), EMPTY)
        if ((is_white and self.can_castle_king_white) or (not is_white and self.can_castle_king_black)) and x+2 <= 7:
            if self.board[x+1][y] == EMPTY and self.board[x+2][y] == EMPTY:
                self.set_piece((x+1, y), self.get_piece(frompos))
                self.set_piece((x+2, y), self.get_piece(frompos))
                if not self.is_in_check(color):
                    legal_moves += [(x+2, y)] 
                self.set_piece((x+1, y), EMPTY)
                self.set_piece((x+2, y), EMPTY)

        return legal_moves

    def get_rook_moves(self, frompos, is_white):
        dir = [[1, 0], [-1, 0], [0, -1], [0, 1]]
        legal_moves = []

        for direction in dir:
            x, y = frompos
            x += direction[0]
            y += direction[1]
            while self.within_bounds(x, y):
                piece_at_target = self.get_piece((x, y))
                if piece_at_target == EMPTY:
                    legal_moves += [(x, y)]
                    x += direction[0]
                    y += direction[1]
                    
                elif self.is_piece_white(piece_at_target) == is_white:
                    break
                else:
                    legal_moves += [(x, y)]
                    break
                
        return legal_moves

    def get_knight_moves(self, frompos, is_white):
        dir = [[2, 1], [2, -1], [-2, 1], [-2, -1], [1, 2], [-1, 2], [1, -2], [-1, -2]]
        legal_moves = []

        for direction in dir:
            x, y = frompos
            x += direction[0]
            y += direction[1]
            if not self.within_bounds(x, y):
                continue
            piece_at_target = self.get_piece((x, y))  
            if self.is_piece_white(piece_at_target) == is_white and piece_at_target != EMPTY:
                continue
            else:
                legal_moves += [(x, y)]
                continue
                
        return legal_moves

    def get_pawn_moves(self, frompos, is_white):
        legal_moves = []
        x, y = frompos

        starting_rank = 6 if is_white else 1
        up = -1 if is_white else 1
        two_up = up*2

        if self.within_bounds(x, y + up) and self.get_piece((x, y+up)) == EMPTY:
            legal_moves += [(x, y+up)]
        if y == starting_rank and self.within_bounds(x, y + two_up) and self.get_piece((x, y+two_up)) == EMPTY and self.get_piece((x, y+up)) == EMPTY:
            legal_moves += [(x, y+two_up)]


        if self.within_bounds(x+1, y+up) and self.is_piece_white(self.get_piece((x+1, y+up))) != is_white and self.get_piece((x+1, y+up)) != EMPTY:
            legal_moves += [(x+1, y+up)]
        if self.within_bounds(x-1, y+up) and self.is_piece_white(self.get_piece((x-1, y+up))) != is_white and self.get_piece((x-1, y+up)) != EMPTY:
            legal_moves += [(x-1, y+up)]
        if self.within_bounds(x-1, y+up) and (x-1, y+up) == self.en_passant_target:
            legal_moves += [(x-1, y+up)]
        if self.within_bounds(x+1, y+up) and (x+1, y+up) == self.en_passant_target:
            legal_moves += [(x+1, y+up)]

        return legal_moves

    def is_piece_white(self, piece):
        return piece&BLACK == 0
    
    def within_bounds(self, x, y):
        return ((0 <= x <= 7) and (0 <= y <= 7))

    def is_in_check(self, color):
        move_color = WHITE if WHITE != color else BLACK
        moves = self.get_all_moves(move_color)
        is_white = True if color == WHITE else False

        for file in range(8):
            for rank in range(8):
                piece = self.get_piece((file, rank))
                if self.is_piece_white(piece) != is_white:
                    continue
                if piece & KING == 0:
                    continue
                if moves.count((file, rank)) > 0:
                    return True
        return False

    def on_mouse_up_event(self):
        if not self.has_piece_selected:
            return

        self.holding_piece = False
        released_x, released_y = pygame.mouse.get_pos()
        file = int((released_x - _margin)/_piece_size)
        rank = int((released_y - _margin)/_piece_size)

        if self.selected_piece == (file, rank):
            return
        
        if file > 7 or rank > 7 or file < 0 or rank < 0:
            return

        self.make_move(self.selected_piece, (file, rank))

    def get_all_moves(self, color, checks = False):
        is_white = True if color == WHITE else False
        moves = []
        for file in range(8):
            for rank in range(8):
                piece = self.get_piece((file, rank))
                if self.is_piece_white(piece) != is_white:
                    continue
                moves += self.get_possible_moves((file, rank), checks)

        moves = list(set(moves))
        return moves

    def make_move(self, from_pos, to_pos, promotion_piece = ""):
        piece = self.get_piece(from_pos)
        piece_at = self.get_piece(to_pos)
        x1, y1 = from_pos
        x2, y2 = to_pos
        if self.white_to_move != self.is_piece_white(piece):
            return False
        if not self.is_move_legal(from_pos, to_pos):
            return False

        self.stop_clock()
        self.add_increment()
        #Check if should revoke castling rights
        self.check_for_castling(from_pos, to_pos)

        self.should_send_fen = True
        #Move piece, handle state (set en passant targets, mouse selection)
        self.set_piece(to_pos, piece)
        self.set_piece(from_pos, EMPTY)
        if piece == PAWN and to_pos == self.en_passant_target:
            self.set_piece((x2, y1), EMPTY)
        self.prev_move = [(x1,y1), (x2,y2)]
        self.white_to_move = not self.white_to_move
        self.has_piece_selected = False
        self.selected_piece = (-1, -1)
        self.holding_piece = False
        self.en_passant_target = (-1, -1)

        #If pawn promotion
        if piece == BLACK_PAWN and y2 == 7:
            new_piece = BLACK_QUEEN if promotion_piece == "" else pieces_from_letters[promotion_piece]
            self.set_piece(to_pos, new_piece)
        if piece == WHITE_PAWN and y2 == 0:
            new_piece = WHITE_QUEEN if promotion_piece == "" else pieces_from_letters[promotion_piece.upper()]
            self.set_piece(to_pos, new_piece)

        #Check en passant target
        if piece & PAWN > 0 and abs(y2 - y1) == 2:
            self.en_passant_target = (x2, int((y1 + y2)/2))

        #If castled, move rook 
        if piece & KING > 0 and abs(x1 - x2) == 2:
            rook = WHITE_ROOK if self.is_piece_white(piece) else BLACK_ROOK
            self.set_piece((int((x1+x2)/2), y2), rook)
            if x2 < x1:
                self.set_piece((0, y2), EMPTY)
            else:
                self.set_piece((7, y2), EMPTY)

        #Handle move clock
        is_white = self.is_piece_white(self.get_piece(to_pos))
        color = BLACK if is_white else WHITE
        moves = self.get_all_moves(color, checks=True)
        is_in_check = self.is_in_check(color)
        if color == WHITE:
            self.moves += 1
        if piece & PAWN > 0 or piece_at != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        #Generate fen, handle threefold repetition and history
        fen = self.generate_fen()
        self.history.add(fen, prev_move=self.prev_move).move_next()
        position = fen.split()[0]
        if position in self.positions:
            self.positions[position] = self.positions[position] + 1
        else:
            self.positions[position] = 1

        self.status = fen

        #Handle game result
        if self.clock_win:
            self.status = ("White" if self.white_victory else "Black") + " win by timeout"
        elif len(moves) == 0 and is_in_check:
            self.checkmate = True
            self.status = "Checkmate"
        elif len(moves) == 0 and not is_in_check:
            self.stalemate = False
            self.status = "Stalemate"
        elif self.halfmove_clock >= 100:
            self.stalemate = True
            self.status = "Draw by 50-move rule"
        elif self.positions[position] >= 3:
            self.stalemate = True
            self.status = "Draw by repetition"

        print (fen)
        

        return True
    
    def check_for_castling(self, moved_from_pos, moved_to_pos):
        piece_from = self.get_piece(moved_from_pos)
        piece_to = self.get_piece(moved_to_pos)
        is_white_from = self.is_piece_white(piece_from)
        is_white_to = self.is_piece_white(piece_to)
        color_from = BLACK if is_white_from else WHITE
        color_to = BLACK if is_white_to else WHITE
        if piece_from == BLACK_KING:
            self.can_castle_king_black = False
            self.can_castle_queen_black = False
        elif piece_from == WHITE_KING:
            self.can_castle_king_white = False
            self.can_castle_queen_white = False

        elif piece_from == BLACK_ROOK:
            if moved_from_pos == (0, 0):
                self.can_castle_queen_black = False
            elif moved_from_pos == (7, 0):
                self.can_castle_king_black = False
        elif piece_from == WHITE_ROOK:
            if moved_from_pos == (0, 7):
                self.can_castle_queen_white = False
            elif moved_from_pos == (7, 7):
                self.can_castle_king_white = False

        elif piece_to == BLACK_ROOK:
            if moved_to_pos == (0, 0):
                self.can_castle_queen_black = False
            elif moved_to_pos == (7, 0):
                self.can_castle_king_black = False
        elif piece_to == WHITE_ROOK:
            if moved_to_pos == (0, 7):
                self.can_castle_queen_white = False
            elif moved_to_pos == (7, 7):
                self.can_castle_king_white = False

    def load_from_state(self, state):
        self.board = copy.deepcopy(state.board)
        self.white_to_move = state.white_to_move
        self.can_castle_king_black = state.can_castle_king_black
        self.can_castle_king_white = state.can_castle_king_white
        self.can_castle_queen_black = state.can_castle_queen_black
        self.can_castle_queen_white = state.can_castle_queen_white
        self.en_passant_target = state.en_passant_target
        self.moves = state.moves
        self.halfmove_clock = state.halfmove_clock
        self.prev_move = state.prev_move

    def key_right_event(self):
        if self.history.has_next():
            self.load_from_state(self.history.move_next().get_state())
            position = self.history.get_state().fen.split()[0]
            self.positions[position] += 1

    def key_left_event(self):
        if self.history.has_prev():
            position = self.history.get_state().fen.split()[0]
            self.positions[position] -= 1
            self.load_from_state(self.history.move_prev().get_state())

    def generate_fen(self):
        
        total = 0
        fen = ""
        for rank in range(8):
            for file in range(8):
                piece = self.get_piece((file, rank))
                if piece == EMPTY:
                    total += 1
                elif total != 0:
                    fen += str(total)
                    fen += letters[piece]
                    total = 0
                else:
                    fen += letters[piece]
            if total != 0:
                fen += str(total)
                total = 0
            if rank != 7:
                fen += "/"
        fen += (" w " if self.white_to_move else " b ")
        castling = ""
        if self.can_castle_king_white:
            castling += "K"
        if self.can_castle_queen_white:
            castling += "Q"
        if self.can_castle_king_black:
            castling += "k"
        if self.can_castle_queen_black:
            castling += "q"
        if castling == "":
            castling = "-"
        fen += castling + " "

        if self.en_passant_target != (-1, -1):
            x, y = self.en_passant_target
            fen += chr(ord('a') + x) + str(8-y) + " "
        else:
            fen += "- "   
        fen += str(self.halfmove_clock) + " "
        fen += str(self.moves) + " "
        fen += str(int(self.time_left_white)) + " "
        fen += str(int(self.time_left_black))
        return fen 


    def is_move_legal(self, from_pos, to_pos):
        moves = self.get_possible_moves(from_pos)
        piece = self.get_piece(from_pos)
        if moves.count((to_pos)) > 0:
            return True
        return False
        

    def load_images(self):
        self.board_img = pygame.image.load("./Assets/board.png").convert_alpha()
        self.piece_images = {
            BLACK_KING: pygame.transform.smoothscale(pygame.image.load("./Assets/black-king.png"), (_piece_size, _piece_size)).convert_alpha(),
            BLACK_PAWN: pygame.transform.smoothscale(pygame.image.load("./Assets/black-pawn.png"), (_piece_size, _piece_size)).convert_alpha(),
            BLACK_BISHOP: pygame.transform.smoothscale(pygame.image.load("./Assets/black-bishop.png"), (_piece_size, _piece_size)).convert_alpha(),
            BLACK_QUEEN: pygame.transform.smoothscale(pygame.image.load("./Assets/black-queen.png"), (_piece_size, _piece_size)).convert_alpha(),
            BLACK_KNIGHT: pygame.transform.smoothscale(pygame.image.load("./Assets/black-knight.png"), (_piece_size, _piece_size)).convert_alpha(),
            BLACK_ROOK: pygame.transform.smoothscale(pygame.image.load("./Assets/black-rook.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_KING: pygame.transform.smoothscale(pygame.image.load("./Assets/white-king.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_PAWN: pygame.transform.smoothscale(pygame.image.load("./Assets/white-pawn.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_BISHOP: pygame.transform.smoothscale(pygame.image.load("./Assets/white-bishop.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_QUEEN: pygame.transform.smoothscale(pygame.image.load("./Assets/white-queen.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_ROOK: pygame.transform.smoothscale(pygame.image.load("./Assets/white-rook.png"), (_piece_size, _piece_size)).convert_alpha(),
            WHITE_KNIGHT: pygame.transform.smoothscale(pygame.image.load("./Assets/white-knight.png"), (_piece_size, _piece_size)).convert_alpha()
        }