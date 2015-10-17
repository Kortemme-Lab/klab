from tools import colortext

# Test
chars = 'A'
count = 0
for name, data in colortext.colors.iteritems():
    colortext.write(name, name)
    for effect in colortext.EFFECTS_:
        colortext.write(name, color = name, bgcolor = 'lightblue', effect = effect)
    print("")
colortext.rainbowprint("Rainbow test")
colortext.printf("\ntest1", color = 'red')
colortext.printf("test2")
colortext.bar('blue', 9, suffix = "\n")