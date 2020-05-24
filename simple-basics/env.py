from enum import Enum

class TokenIds(Enum):
    SYM = 1
    ID = 2
    TYPE = 3
    EOF = 4

'''
{
    bool x;
    {
        int x;
        char y;
        {
            ...
        }
        x;
        y;
        x;
    }
    y;
    x;
}
grammar:

programm := block

block := '{' decls stmnts '}'
decls := decl decls | ''
decl := type id ';'
stmnts := stmnt stmnts | ''
stmnt := id ';' | block 
type := int | char | double | float
id := letter id | ''
letter := 'a-zA-Z'

'''

class Token:
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "Token: {}".format(self.id.name)

class Id(Token):
    def __init__(self, lexeme):
        super().__init__(TokenIds.ID)
        self.lexeme = lexeme

    def __str__(self):
        return 'ID: {}'.format(self.lexeme)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.lexeme == rhs.lexeme and self.id == rhs.id

    def __len__(self):
        return len(self.lexeme)


class Word(Token):
    def __init__(self, type, lexeme):
        super().__init__(type)
        self.lexeme = lexeme


    def __str__(self):
        return 'WORD: {} ({})'.format(self.lexeme, self.id.name)

    def __len__(self):
        return len(self.lexeme)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.lexeme == rhs.lexeme and self.id == rhs.id

class Sym(Token):
    def __init__(self, sym):
        super().__init__(TokenIds.SYM)
        self.sym = sym

    def __str__(self):
        return 'SYM: {}'.format(self.sym)

    def __len__(self):
        return len(self.sym)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.sym == rhs.sym and self.id == rhs.id

class Eof(Token):
    def __init__(self):
        super().__init__(TokenIds.EOF)

    def __str__(self):
        return 'EOF'

    def __len__(self):
        return 0

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.id == rhs.id

class Lexer:
    def __init__(self, data):
        self.words = {}
        self.data = data
        self.pos = -1
        self.info_line = 0
        self.info_offset = 0
        self.last_token = None
        self.peek = None
        self.peek = self._read()

        self._reserve(Word(TokenIds.TYPE, 'char'))
        self._reserve(Word(TokenIds.TYPE, 'int'))
        self._reserve(Word(TokenIds.TYPE, 'double'))
        self._reserve(Word(TokenIds.TYPE, 'float'))
        self._reserve(Word(TokenIds.TYPE, 'bool'))

    def _save_token(self, token):
        self.last_token = token

    def _reserve(self, word):
        self.words[word.lexeme] = word

    def _read(self):
        self.pos += 1
        self.info_offset += 1
        
        if self.pos >= len(self.data):
            return None

        return self.data[self.pos]

    def token_gen(self):
        while True:
            tok = self.next_token()
            yield tok
            if tok is None:
                return

    def next_token(self):
        result = self._get_next_token()
        self._save_token(result)

        return result

    def _get_next_token(self):
        while self.peek is not None and self.peek.isspace():
            if self.peek == '\n':
                self.info_line += 1
                self.info_offset = 0

            self.peek = self._read()

        if self.peek is None:
            return Eof()

        if self.peek.isalpha():
            w = self.peek
            self.peek = self._read()
            while self.peek is not None and (self.peek.isalpha() or self.peek.isdigit()):
                w += self.peek
                self.peek = self._read()

            if w not in self.words:
                self.words[w] = Word(TokenIds.ID, w)

            return self.words[w]

        result = Sym(self.peek)
        self.peek = self._read()
        return result

    def err(self, msg):
        lines = self.data.splitlines()
        underline = '~' * (len(self.last_token)-1)
        txt = '{}^{} Syntax error: {}'.format(' '*(self.info_offset-len(self.last_token)-1), underline, msg)
        lines.insert(self.info_line + 1, txt)
    
        raise ValueError('\n'+'\n'.join(lines))

class Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.table = {}

    def __len__(self):
        x = 0
        it = self.parent

        while it is not None:
            x += 1
            it = it.parent

        return x

    def __setitem__(self, key, value):
        self.table[key] = value

    def __getitem__(self, key):
        if key in self.table:
            return self.table[key]

        if self.parent is not None:
            return self.parent[key]

        return None


class Symbol:
    def __init__(self, _type):
        self.type = _type

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None
        self.topEnv = None
        self._read_next_token()

    def parse(self):
        self.block()
        self.match(Eof())

    def _indent_print(self, msg, new_line=False, indent=None):
        tabs = len(self.topEnv) if self.topEnv is not None else 0
        if indent is not None:
            tabs = indent

        print('{}{}'.format('    '*tabs, msg), end='')
        if new_line:
            print()



    def block(self):    
        self.match(Sym('{'))

        saved = self.topEnv
        self.topEnv = Env(saved)
        self._indent_print('{', True)

        self.decls()
        self.stmnts()

        self._indent_print('}', True)
        self.topEnv = saved
        

        self.match(Sym('}'))

    def decls(self):
        while self.token.id == TokenIds.TYPE:
            self.decl()
        
    def decl(self):
        _type = self.token
        if _type.id != TokenIds.TYPE:
            self.lexer.err('Expected Type, got: {} ({})'.format(_type.id, _type.lexeme))

        self.match(self.token)
        _id = self.token
        if _id.id != TokenIds.ID:
            self.lexer.err('Expected ID')

        self.match(self.token)
        self.match(Sym(';'))

        s = Symbol(_type.lexeme)
        self.topEnv[_id.lexeme] = s

    def stmnts(self):
        while self.token.id == TokenIds.ID or (self.token.id == TokenIds.SYM and self.token.sym == '{'):
            self.stmnt()

    def stmnt(self):
        if self.token.id == TokenIds.ID:
            self.id()
            self.match(Sym(';'))
            self._indent_print(';', True, 0)

        else:
            self.block()

    def id(self):
        if self.token.id == TokenIds.ID:
            s = self.topEnv[self.token.lexeme]
            if s is None:
                self.lexer.err('Not declared variable')
            
            self._indent_print("    {}: {}".format(self.token.lexeme, s.type))
            self.match(self.token)

        else:
            self.lexer.err("Expected ID")


    def match(self, token):
        if self.token == token:
            self._read_next_token()
        else:
            self.lexer.err('Expected "{}"'.format(token))


    def _read_next_token(self):
        self.token = self.lexer.next_token()

example = '''{
    int x1; int b10; char hehe; char x; {
        int bha;
        bool y;
        x;
        y;
        {
double x;
            int bha;
            x;
            y;
            x;
        }
        x;y;x1;b10;
        {
            float b10;
            b10;
        }
    }
}'''


parser = Parser(Lexer(example))
parser.parse()

