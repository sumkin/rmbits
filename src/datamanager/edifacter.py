import sys
import os


class Edifacter:
    '''
    Class to handle edifact files.
    '''

    def __init__(self, fname):
      self.fname = fname # Name of original EDIFACT file.
      self.fin = open(fname, 'r')


    def next_line(self):
        sbuff = ''
        while True:
          s = self.fin.read(1000000)
          s = sbuff + Edifacter.to_text(s)
          if s == "": # End of file.
              return
          if "'\n" in s:
              res = s.split("'\n") 
              for e in res[:len(res)-1]:
                  yield e + "'\n"         
              sbuff = res[len(res)-1]
          else:
              sbuff = s


    @staticmethod
    def to_text(s):
        s = s.replace('\x1c', "'\n")
        s = s.replace('\x1d', '+')
        s = s.replace('\x1f', ':')
        s = s.replace('\x19', '*')
        s = s.replace('\xda', '\n')
        s = s.replace('\x03', '[EOM]\n\n')
        s = s.replace('\x01', '[SOH]')
        s = s.replace('\x02', '[SOT]')
        return s


if __name__ == "__main__":

    if len(sys.argv) == 3:
        with open(sys.argv[2],'w') as fout:
            edifacter = Edifacter(sys.argv[1])
            for line in edifacter.next_line():
                fout.write(line)
    else:
        print("Wrong number of arguments")
        transform(sys.argv[1], sys.argv[2])

