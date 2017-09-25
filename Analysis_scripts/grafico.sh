set pointsize 20
set xrange[0:24]
plot for [i=0:24] 'h'.i.'_'.i.'_prince.log' using (i):2 every ::30::31:1 title 'Node h'.i
#Grafico dei dati calcolati da prince
plot for [i=0:24] 'h'.i.'_'.i.'_prince.log' using 1:3 title 'Node h'.i

#Grafico dei dati misurati con tshark
plot for [i=0:24] 'h'.i.'_'.i.'-dump.cap.dat' using 1:2 every 3:3 title 'Node h'.i

#Grafico centralità in funzione del tempo
plot for [i=0:8] 'h'.i.'_'.i.'_prince.log' using ($1-1506179875):3 title 'Node h'.i
set arrow from (1506179834-1506179875), graph 0 to (1506179834-1506179875), graph 1 nohead
