from .Constants import *
#Linked list for IT class (Forgive me lads)

#Linked List node
class BoardState:
    fen = ""
    nextState = None
    prevState = None

    white_to_move = True
    board = []
    can_castle_queen_black = True
    can_castle_queen_white = True
    can_castle_king_black = True
    can_castle_king_white = True
    prev_move = [(-1, -1), (-1, -1)]
    en_passant_target = (-1, -1)
    moves = 0
    halfmove_clock = 0
    
    def __init__(self, fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", prevState = None, nextState = None, prev_move = [(-1, -1), (-1, -1)]):
        self.nextState = nextState
        self.prevState = prevState
        self.prev_move = prev_move
        self.fen = fen
        self.parse_fen()
    
    def parse_fen(self):
        board = []
        parts = self.fen.split()

        fen_rows = parts[0].split('/')
        for row in fen_rows:
            pieces = []
            for char in row:
                if char.isdigit():
                    for i in range(int(char)):
                        pieces.append(EMPTY)
                else:
                    pieces.append(pieces_from_letters[char])
            board += [pieces]
        self.board = np.transpose(board)

        self.white_to_move = parts[1] == "w"
        self.can_castle_king_white = "K" in parts[2]
        self.can_castle_queen_white = "Q" in parts[2]
        self.can_castle_king_black = "k" in parts[2]
        self.can_castle_queen_black = "q" in parts[2]
        
        if parts[3] == "-":
            self.en_passant_target = (-1, -1)
        else:
            file = ord(parts[3][0])-ord('a')
            rank = 8 - int(parts[3][1])
            self.en_passant_target = (file, rank)
        self.halfmove_clock = int(parts[4])
        self.moves = int(parts[5])
    
class MoveHistory:
    current_state = BoardState()

    def __init__(self, starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        self.current_state = BoardState(starting_fen)
    def has_next(self):
        return self.current_state.nextState != None
    def has_prev(self):
        return self.current_state.prevState != None
    def move_next(self):
        if self.has_next():
            self.current_state = self.current_state.nextState
        return self
    def move_prev(self):
        if self.has_prev():
            self.current_state = self.current_state.prevState
        return self
    def get_state(self):
        return self.current_state
    def add(self, fen, prev_move = [(-1, -1), (-1, -1)]):
        next = BoardState(fen=fen, prevState=self.current_state, prev_move=prev_move)
        self.current_state.nextState = next
        return self



