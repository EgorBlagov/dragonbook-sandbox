

class Lexer:
    def __init__(self, input):
        self.input = [x for x in input]
        self.words = {
            'true': ('WORD', 'TRUE', 257),
            'false': ('WORD', 'FALSE', 257)
        }

    def scanner(self):
        peek = ' '
        line = 0
        while True:
            if peek is None:
                return

            while True:
                if peek in [' ', '\n', '\t']:
                    if peek == '\n':
                        line+=1

                    peek = self.read()
                    continue
                if peek == '/':
                    peek = self.read()
                    if peek == '/':
                        while True:
                            peek = self.read()
                            if peek == '\n':
                                peek = self.read()
                                break
                        continue

                    elif peek == '*':
                        while True:
                            peek = self.read()
                            if peek == '*':
                                peek = self.read()
                                if peek == '/':
                                    peek = self.read()
                                    break
                        continue

                break

            if peek.isdigit():
                number = 0
                is_int = True
                while peek is not None and peek.isdigit():
                    number = 10 * number + int(peek)
                    peek = self.read()

                if peek == '.':
                    peek = self.read()
                    factor = 1
                    while peek is not None and peek.isdigit():
                        number += int(peek) * 1/(10 *  factor)
                        factor *= 10
                        peek = self.read()
                    is_int = False


                yield ('NUM' if is_int else 'FLOAT', number)
                continue

            if peek in ['<', '>', '!', '=']:
                op = peek
                peek = self.read()

                if peek == '=':
                    op += peek
                    peek = self.read()

                yield ('COMPARE', op)
                continue

            if peek.isalpha():
                buf = str(peek)
                peek = self.read()
                while peek is not None and (peek.isalpha() or peek.isdigit()):
                    buf += peek
                    peek = self.read()

                if buf not in self.words:
                    self.words[buf] = ('WORD', 'ID', buf)
                    
                yield self.words[buf]
                continue

            t = ('TOK', peek)
            peek = ' '
            yield t

    def read(self):
        if self.input:
            return self.input.pop(0)


l = Lexer('''
    1+2+3-4 true    fal1se someId false 1 some
    1-10+12312312313 // some long comment that I must remove

    /* giant 123 19283 919 931982 3
    multiline comment


    which i cannot disable until * * * * * met specific combo
    like * / but without space
    // this should also be ignored and next line should be analyzed*/
    1-2+12
    1+someId

    abc>bcd
    abc>=bcd
    10<12
    15!=3
    2.1234=15.6234 // this should work as well
    2.01234=15.0006234// this should work as well
    10>=>10''')


print('\n'.join(list(map(str, l.scanner()))))
