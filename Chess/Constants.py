import numpy as np

BLACK = 1
WHITE = 0

BLACK = 0x100
WHITE = 0x00


EMPTY = 0x1000
KING = 0x01
QUEEN = 0x02
PAWN = 0x04
BISHOP = 0x08
KNIGHT = 0x10
ROOK = 0x20

BLACK_KING = KING + BLACK
BLACK_QUEEN = QUEEN + BLACK
BLACK_PAWN = PAWN + BLACK
BLACK_BISHOP = BISHOP + BLACK
BLACK_KNIGHT = KNIGHT + BLACK
BLACK_ROOK = ROOK + BLACK

WHITE_KING = KING + WHITE
WHITE_QUEEN = QUEEN + WHITE
WHITE_PAWN = PAWN + WHITE
WHITE_BISHOP = BISHOP + WHITE
WHITE_KNIGHT = KNIGHT + WHITE
WHITE_ROOK = ROOK + WHITE

STARTING_POSITION = [[BLACK_ROOK, BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK],
                     [BLACK_PAWN, BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,  BLACK_PAWN, BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN],
                     [EMPTY,      EMPTY,        EMPTY,        EMPTY,       EMPTY,      EMPTY,        EMPTY,        EMPTY     ],
                     [EMPTY,      EMPTY,        EMPTY,        EMPTY,       EMPTY,      EMPTY,        EMPTY,        EMPTY     ],
                     [EMPTY,      EMPTY,        EMPTY,        EMPTY,       EMPTY,      EMPTY,        EMPTY,        EMPTY     ],
                     [EMPTY,      EMPTY,        EMPTY,        EMPTY,       EMPTY,      EMPTY,        EMPTY,        EMPTY     ],
                     [WHITE_PAWN, WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,  WHITE_PAWN, WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN],
                     [WHITE_ROOK, WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK]]

letters = {
            BLACK_KING: 'k',
            BLACK_PAWN: 'p',
            BLACK_BISHOP: 'b',
            BLACK_QUEEN: 'q',
            BLACK_KNIGHT: 'n',
            BLACK_ROOK: 'r',
            WHITE_KING: 'K',
            WHITE_PAWN: 'P',
            WHITE_BISHOP: 'B',
            WHITE_QUEEN: 'Q',
            WHITE_ROOK: 'R',
            WHITE_KNIGHT: 'N'
        }
pieces_from_letters = {
            'k': BLACK_KING,
            'p': BLACK_PAWN,
            'b': BLACK_BISHOP,
            'q': BLACK_QUEEN,
            'n': BLACK_KNIGHT,
            'r': BLACK_ROOK,
            'K': WHITE_KING,
            'P': WHITE_PAWN,
            'B': WHITE_BISHOP,
            'Q': WHITE_QUEEN,
            'R': WHITE_ROOK,
            'N': WHITE_KNIGHT
        }

STARTING_POSITION = np.transpose(STARTING_POSITION)


