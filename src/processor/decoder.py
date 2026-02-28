# 0: {
            #     0: {
            #         0: lambda x=8, y=0: self._mov(x,y),
            #         1: lambda x=8, y=1: self._mov(x,y),
            #         2: lambda x=8, y=2: self._mov(x,y),
            #         8: lambda x=8, y=8: self._mov(x,y),
            #         9: lambda x=8, y=9: self._mov(x,y)
            #     },
            #     1: {
            #         0: lambda x=16, y=0: self._mov(x,y),
            #         1: lambda x=16, y=1: self._mov(x,y),
            #         2: lambda x=16, y=2: self._mov(x,y),
            #         8: lambda x=16, y=8: self._mov(x,y),
            #         9: lambda x=16, y=9: self._mov(x,y)
            #     },
            #     2: {
            #         0: lambda x=32, y=0: self._mov(x,y),
            #         1: lambda x=32, y=1: self._mov(x,y),
            #         2: lambda x=32, y=2: self._mov(x,y),
            #         8: lambda x=32, y=8: self._mov(x,y),
            #         9: lambda x=32, y=9: self._mov(x,y)
            #     },
            #     3: {
            #         0: lambda x=64, y=0: self._mov(x,y),
            #         1: lambda x=64, y=1: self._mov(x,y),
            #         2: lambda x=64, y=2: self._mov(x,y),
            #         8: lambda x=64, y=8: self._mov(x,y),
            #         9: lambda x=64, y=9: self._mov(x,y)
            #     },
            #     15: self._nop
            # }

'''
r = 00
i = 01
m = 10
n = 11
'''


class Decoder:
    def __init__(self, dp):
        self._dp = dp
        self.binary2function = {
            15: {
                0: self._nop,
                1: self._hlt
            },
            13: {
                0: {
                    0: lambda z, x=8, y=0: self._str(x,y,z),
                }
            }
        }
