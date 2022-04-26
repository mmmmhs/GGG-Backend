fp = open('passenger_sessId.txt','w')
fd = open('driver_sessId.txt','w')
i = 0
while i < 100:
    print('p'+str(i), file=fp)
    print('d'+str(i), file=fd)
    i = i+1
fp.close()
fd.close()