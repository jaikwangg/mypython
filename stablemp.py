t = int(input())

for i in range(t):
    women = list()
    men = list()
    n = int(input())
    for j in range(n):
        l = input().split()
        women.append([int(i) for i in l])
    for j in range(n):
        l = input().split()
        men.append([int(i) for i in l])
    
    wi = [-1]*n
    mi = [1]*n
    
    while -1 in wi:
        for m0 in range(n):
            
            w0 = men[m0][mi[m0]] - 1
            if(wi[w0]<0):
                wi[w0] = m0
            else:
            
                p0 = women[w0][1:].index(wi[w0]+1)
                p1 = women[w0][1:].index(m0+1)
           
                if p1<p0: #new man
                    mi[wi[w0]] = mi[wi[w0]] + 1
                    wi[w0] = m0
                else: #same man
                    mi[m0] = mi[m0] = mi[m0] + 1
    
    for w in range(n):
	    print(w+1, wi[w] + 1)
    