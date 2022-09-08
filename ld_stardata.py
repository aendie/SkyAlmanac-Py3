#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# star data for ld_charts.py (Lunar Distance chart)

#   Copyright (C) 2022  Andrew Bauer

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <https://www.gnu.org/licenses/>.


# list of popular stars (Hipparcos #, Name)
popstars = """
   677 Alpheratz
   746 Caph
  1067 Algenib
  2081 Ankaa
  3179 Schedar
  3419 Diphda
  5447 Mirach
  7588 Achernar
  8903 Sheratan
  9640 Almach
  9884 Hamal
 11767 Polaris
 13847 Acamar
 14135 Menkar
 14576 Algol
 15863 Mirfak
 17499 Electra
 17531 Taygeta
 17573 Maia
 17608 Merope
 17702 Alcyone
 17847 Atlas
 18543 Zaurak
 21421 Aldebaran
 24436 Rigel
 24608 Capella
 25336 Bellatrix
 25428 Elnath
 25606 Nihal
 25930 Mintaka
 25985 Arneb
 26311 Alnilam
 26727 Alnitak
 27366 Saiph
 27989 Betelgeuse
 28360 Menkalinan
 30324 Mirzam
 30438 Canopus
 31681 Alhena
 32349 Sirius
 33579 Adhara
 34444 Wezen
 36850 Castor
 37279 Procyon
 37826 Pollux
 39429 Naos
 41037 Avior
 44816 Suhail
 45238 Miaplacidus
 46390 Alphard
 49669 Regulus
 50583 Algieba
 53910 Merak
 54061 Dubhe
 55203 HIP55203
 57632 Denebola
 58001 Phecda
 59316 Minkar
 59774 Megrez
 59803 Gienah
 60718 Acrux
 61084 Gacrux
 62434 Mimosa
 62956 Alioth
 63608 Vindemiatrix
 65378 Mizar
 65474 Spica
 65477 Alcor
 67301 Alkaid
 68702 Hadar
 68756 Thuban
 68933 Menkent
 69673 Arcturus
 71683 Rigil Kent.
 72105 Izar
 72607 Kochab
 72622 Zuben'ubi
 76267 Alphecca
 77070 Unukalhai
 78727 HIP78727
 80331 Athebyne
 80763 Antares
 82273 Atria
 84012 Sabik
 84345 Rasalgethi
 85927 Shaula
 86032 Rasalhague
 86742 Cebalrai
 87833 Eltanin
 90185 Kaus Aust.
 91262 Vega
 92420 Sheliak
 92855 Nunki
 93194 Sulafat
 95241 Arkab Prior
 95294 Arkab Posterior
 95347 Rukbat
 95947 Albireo
 97278 Tarazed
 97649 Altair
 98036 Alshain
100453 Sadr
100751 Peacock
102098 Deneb
105199 Alderamin
106032 Alfirk
106278 Sadalsuud
107315 Enif
107556 Deneb Algedi
109074 Sadalmelik
109268 Al Na'ir
113368 Fomalhaut
113881 Scheat
113963 Markab
"""

# List of navigational stars with magnitude <= 1.5 (with Hipparcos Catalog Number) plus Polaris
navstars = """
Achernar,5,7588,0.4233
Polaris,0,11767,2.1077
Aldebaran,10,21421,1.0024
Rigel,11,24436,0.1930
Capella,12,24608,0.2385
Betelgeuse,16,27989,0.4997
Canopus,17,30438,-0.5536
Sirius,18,32349,-1.0876
Adhara,19,33579,1.4160
Procyon,20,37279,0.4607
Pollux,21,37826,1.2947
Regulus,26,49669,1.3232
Acrux,30,60718,0.6739
Spica,33,65474,0.8891
Hadar,35,68702,0.5366
Arcturus,37,69673,0.1114
Rigil Kent.,38,71683,0.1373
Antares,42,80763,0.9757
Vega,49,91262,0.0868
Altair,51,97649,0.8273
Deneb,53,102098,1.2966
Fomalhaut,56,113368,1.1808
"""

constellations = """
Tucana:9.0,-61.5
alf 110130
gam 114996
zet 1599
kap 5896
b01 2484
eps 118322
del 110838
b02 2487
nu. 111310
alf-gam-b01-zet-eps-del-alf
#Pisces:0.5,8.1
Pisces:332.0,3.1
eta 7097
alf 9487
omi 8198
eps 4906
del 3786
nu. 7884
tau 5586
ksi 8833
chi 5571
phi 5742
ups 6193
mu. 7007
gam 114971
ome 118268
iot 116771
the 115830
bet 113889
lam 116928
kap 115738
phi-ups-tau-phi-eta-omi-alf-nu.-eps-ome-iot-the-gam-kap-lam-iot
Pegasus:0.5,20.0
del 677
eps 107315
bet 113881
alf 113963
gam 1067
chi 1168
eta 112158
zet 112029
mu. 112748
the 109427
iot 109176
lam 112440
kap 107354
pi. 109410
ksi 112447
ups 115623
tau 115250
psi 118131
omi 112051
nu. 109068
rho 113186
del=gam=alf=bet=del;bet-eta;alf-zet-the-eps;bet-mu.-lam-iot-kap
Aquarius:13.0,-4.0
bet 106278
alf 109074
del 113136
zet 110960
c02 114341
lam 112961
eps 102618
gam 110395
b01 115438
eta 111497
tau 112716
the 110003
phi 114724
psi 114855
iot 109139
b02 115669
ps2 115033
c01 114119
om2 116971
nu. 104459
ksi 106786
mu. 103045
omi 108874
pi. 110672
sig 111123
chi 114939
om1 116758
ps3 115115
eps=bet=alf=gam=zet-pi.-alf;zet=eta;alf-the-lam-phi-psi-del-tau-lam;c02-psi-b01;bet-iot
Grus:13.0,-44.0
alf 109268
bet 112122
gam 108085
eps 112623
iot 114421
d01 110997
zet 113638
d02 111043
the 114131
lam 109111
mu1 109908
rho 112203
eta 112374
gam-lam-mu1-d01-bet-alf-d01;bet-eps-zet
Piscis Austrinus:15.0,-35.0
alf 113368
eps 111954
del 113246
bet 111188
iot 107380
gam 112948
mu. 109285
tau 109422
ups 109289
the 107608
alf-eps-mu.-the-iot-mu.-bet-gam-del-alf
Lacerta:23.0,43.5
alf 111169
rrr 109937
sss 111022
bet 110538
qqq 109754
ttt 111944
uuu 111104
vvv 110351
www 110609
xxx 111674
yyy 111841
zzz 112917
sss-alf-bet-www-sss-vvv-uuu-ttt-sss;uuu-qqq-rrr
Cepheus:20.9,61.5
alf 105199
gam 116727
bet 106032
zet 109492
eta 102422
iot 112724
del 110991
eps 109857
the 101093
mu. 107259
nu. 107418
ksi 108917
kap 99255
pi. 114222
ups 102431
omi 115088
alf-mu.-eps-zet-del-iot-gam-bet-alf-eta-the;iot-bet
Indus:38.0,-55.4
alf 101772
bet 103227
the 105319
del 108431
eta 102333
eps 108870
zet 102790
alf-eta-bet-del-the-alf
Capricornus:20.0,-21.8
del 107556
bet 100345
alf 100064
gam 106985
zet 105881
the 104139
ome 102978
psi 102485
iot 105515
al1 100027
eps 106723
kap 107188
nu. 100310
rho 101027
eta 104019
alf-bet-psi-ome-zet-del-gam-iot-the-alf
Delphinus:41.0,18.5
bet 101769
alf 101958
eps 101421
gam 102532
del 102281
zet 101589
eps-bet-alf-gam-del-bet
Cygnus:58.0,38.5
alf 102098
gam 100453
eps 102488
del 97165
bet 95947
zet 104732
ksi 104060
tau 104887
iot 95853
kap 94779
om2 99675
eta 98110
nu. 103413
om3 99848
rho 106481
xxx 101076
sig 105102
pi2 107533
yyy 99655
ups 105138
the 96441
mu. 107310
lam 102589
phi 96683
pi1 107136
om1 99639
psi 98055
ome 101138
alf-nu.-zet-eps=gam=del-iot-om3-alf=gam=eta=bet;iot-kap
Sagitta:57.0,21
gam 98337
del 97365
alf 96757
bet 96837
gam-del-alf;del-bet
Aquila:59.2,-5.0
alf 97649
gam 97278
zet 93747
the 99473
del 95501
lam 93805
bet 98036
eta 97804
eps 93244
iot 96468
mu. 96229
nu. 95585
ksi 97938
kap 96483
rho 99742
zet-lam=del=gam-alf-bet;del=eta=the-iot-lam;del=zet-eps
Microscopium:
gam 103738
eps 105140
the 105382
alf 102831
----
#Octans:34.0,-75.0
#nu. 107089
#bet 112405
#del 70638
#the 122
#nu.-bet-del-nu.
Pavo:57.3,-62.6
alf 100751
bet 102395
del 99240
eta 86929
eps 98495
zet 91792
gam 105858
lam 92609
pi. 88866
ksi 90098
kap 93015
nu. 90797
phi 101612
rho 101773
alf=del=bet-gam-alf;del-lam-ksi-pi.-kap-del;del-zet;del-eps;pi.-eta
Lyra:77.0,42.0
alf 91262
gam 93194
bet 92420
R.. 92862
del 92791
kap 89826
zet 91971
the 94713
eta 94481
ep2 91926
ep1 91919
lam 93279
alf-zet-del-gam-bet-zet-ep1-alf
Sagittarius:64.0,-33.0
eps 90185
sig 92855
zet 93506
del 89931
lam 90496
pi. 94141
gam 88635
eta 89642
phi 92041
tau 93864
ksi 93085
omi 93683
mu. 89341
rho 95168
b01 95241
alf 95347
iot 98032
b02 95294
the 98412
ups 95176
ga1 88567
ome 98066
nu1 92761
psi 94643
zet=tau=sig=phi=zet=eps=del=phi=lam=del=gam=eps=eta
Serpens_Cauda:78.0,6.0;79.1,3.0
eta 84012
et2 89962
nu. 88048
ksi 86263
omi 86565
nu2 84880
zet 88175
the 92946
eta-ksi-nu.-et2-the
Hercules:92.0,31.5
bet 80816
alf 84345
zet 81693
del 84379
pi. 84380
rho 85112
mu. 86974
eta 81833
ksi 87933
gam 80170
iot 86414
omi 88794
xxx 90139
the 87808
tau 79992
eps 83207
sig 81126
phi 79101
lam 85693
nu. 87998
chi 77760
ups 78592
ome 80463
zet=bet=alf=del=eps=zet=eta=pi.=eps;del=lam=mu.=ksi=omi;bet=gam-ome;eta=sig=tau;pi.=rho=the=iot
Ophiuchus:94.0,-2.5
alf 86032
eta 84012
zet 81377
del 79593
bet 86742
kap 83000
eps 79882
the 84970
ddd 85423
nu. 88048
gam 87108
lam 80883
chi 80569
phi 80894
sig 85355
iot 82673
ksi 84893
ome 80975
psi 80343
rho 80473
mu. 86284
ups 80628
bet=alf=kap=lam=del=eps=zet=eta=bet-gam-nu.;kap=zet;eta-the
Ara:98.3,-55.5
bet 85258
alf 85792
zet 83081
gam 85267
del 85727
the 88714
eta 82363
eps 83153
sig 86092
lam 86486
the-alf-eps-zet-eta-del-gam;alf-bet
Scorpius:98.2,-29.0
alf 80763
lam 85927
the 86228
del 78401
eps 82396
kap 86670
bet 78820
ups 85696
tau 81266
pi. 78265
sig 80112
i01 87073
mu1 82514
ggg 87261
gam 73714
eta 84143
mu2 82545
z02 82729
rho 78104
ome 78933
nu. 79374
#ksi 78727 returns 'nan'
om2 78990
omi 80079
z01 82671
i02 87294
#bt2 78821 near duplicate of 'bet'
psi 79375
ggg=lam=ups=kap=i01=the=eta=z02=z01=mu1=eps=tau=alf=sig=del=bet;del=pi.-rho
Draco:120.0,64.0
gam 87833
eta 80331
bet 85670
del 94376
zet 83895
chi 89937
ksi 87585
eps 97433
the 78527
phi 89908
tau 94648
rho 98702
psi 86614
pi. 95081
omi 92512
sig 96100
ome 86201
ups 92782
nu2 85829
nu1 85819
mu. 83608
ksi-nu2-bet-gam-ksi-del-eps;del-phi-zet-eta-the
Draco2:81.0,57.0
the 78527
iot 75458
alf 68756
kap 61281
lam 56211
the-iot-alf-kap-lam
Tri. Aust.:113.7,-68.0
alf 82273
bet 77952
gam 74946
del 79664
eps 76440
zet 80686
alf-bet-gam-alf
Serpens_Caput:123.6,16.0;124.8,13.0
#Serpens_Caput:122.5,2.0;123.8,-2.0
alf 77070
dl2 79593
mu. 77516
bet 77233
eps 77622
del 76276
gam 78072
kap 77450
lam 77257
iot 76852
dl2-mu.-eps-alf-del-bet-gam-kap-iot-bet
Cor. Bor.:112.5,24.0
alf 76267
bet 75695
gam 76952
the 76127
eps 78159
del 77512
tau 79119
kap 77655
ksi 80181
iot 78493
eta 75312
iot-eps-del-gam-alf-bet-the
Libra:133.0,-11.0
bet 74785
alf 72622
sig 73714
ups 76470
tau 76600
gam 76333
the 77853
iot 74392
kap 76880
del 73473
eps 75379
sig-alf=bet=gam-ups-tau;alf=gam
Apus:127.0,-77.0
alf 72370
gam 81065
bet 81852
del 80047
zet 84969
eta 69896
alf-del-bet-gam
Lupus:114.0,-43.5
alf 71860
bet 73273
gam 76297
del 75141
eps 75264
zet 74395
eta 78384
iot 69996
ph1 75177
kap 74376
pi. 73807
chi 77634
rho 71536
lam 74117
the 78918
mu. 74911
omi 72683
ta2 70576
ome 76552
sig 71121
ph2 75304
ta1 70574
ps1 76705
ps2 76945
nu. 75206
alf-zet-mu.-eps-gam-eta-ph1-chi-eta-zet;gam-del-bet
Centaurus:153.0,-45.0
alf 71683
bet 68702
a02 71681
the 68933
gam 61932
eps 66657
eta 71352
zet 68002
del 59196
iot 65109
lam 56561
kap 73334
nu. 67464
mu. 67472
phi 68245
tau 61622
up1 68282
pi. 55425
sig 60823
rho 59449
psi 70090
ks2 64004
up2 68523
chi 68862
ks1 63724
alf-bet-eps-zet-mu.-nu.-the-psi-chi-phi-up1-up2-zet-gam-eps;phi-eta
#Ursa_Minor:152.0,83.0;152.0,80.0
#alf 11767
#bet 72607
#gam 75097
#eps 82080
#yyy 5372
#zzz 70692
#zet 77055
#del 85822
#eta 79822
#zet-eta-gam-bet-zet-eps-del-alf
Boötes:131.5,33.4
alf 69673
eps 72105
gam 71075
eta 67927
del 74666
bet 73555
rho 71053
the 70497
lam 69732
mu. 75411
zet 71795
ups 67459
sig 71284
pi. 71762
tau 67275
psi 73745
kap 69483
ksi 72659
omi 72125
iot 69713
ome 73568
nu. 76041
alf=eps=del=bet=gam=rho=alf;gam-lam-the-kap-lam;alf-zet;alf-eta-tau
Canes Venatici:159.0,35.5
alf 63125
bet 61317
alf-bet
Virgo:152.0,4.0
alf 65474
gam 61941
eps 63608
zet 66249
del 63090
bet 57757
xxx 72220
mu. 71957
eta 60129
nu. 57380
iot 69701
omi 58948
kap 69427
tau 68520
the 64238
lam 69974
pi. 58590
chi 61740
psi 62985
sig 64852
phi 70755
rho 61960
alf=the=gam=eta=omi=nu.=bet=eta;gam=del=eps;gam=zet=tau=xxx;zet=iot=mu.
Hydra:154.0,-28.5
gam 64962
pi. 68895
bet 57936
kkk 70306
psi 64166
lll 70753
ksi 56343
CRb 54682
pi.-gam-bet-ksi-CRb
Coma_Berenices:162.0,25.0;162.0,22.0
bet 64394
alf 64241
gam 60742
rrr 60351
sss 61394
ttt 64022
uuu 63462
vvv 62886
www 60697
xxx 59847
yyy 62763
zzz 60746
alf-bet-gam
Corvus:159.0,-17.0
gam 59803
bet 61359
del 60965
eps 59316
alf 59199
eta 61174
zet 60189
alf-eps-gam-del-bet-eps;del-eta
Musca:171.5,-70.8
alf 61585
bet 62322
del 63613
lam 57363
gam 61199
eps 59929
mu. 57581
eta 64661
alf-bet-del-gam-alf-eps-lam
Crux:177.0,-58.4
alf 60718
bet 62434
gam 61084
del 59747
eps 60260
mu. 63003
zet 60009
eta 59072
th1 58758
lam 63007
iot 62268
th2 58867
bet-del;alf-gam
Crater:185.0,-12.0
del 55282
gam 55705
alf 53740
bet 54682
alf-bet-gam-del-alf
Ursa Major:164.0,50.0
eps 62956
alf 54061
eta 67301
zet 65378
bet 53910
gam 58001
psi 54539
mu. 50801
iot 44127
the 46853
del 59774
omi 41704
lam 50372
nu. 55219
kap 44471
hhh 46733
chi 57399
ups 48319
#ksi 55203 returns 'nan'
ggg 65477
phi 48402
pi. 42527
ome 53295
tau 45075
rho 44390
sig 45038
eta=zet=eps=del=alf=bet=gam=del;gam-chi;nu.-chi-psi-mu.-lam;alf-hhh-ups-bet;hhh-omi-ups-the-kap-iot
Leo:195.0,22.8
alf 49669
gam 50583
bet 57632
del 54872
eps 47908
the 54879
zet 50335
eta 49583
omi 47508
rho 51624
mu. 48455
iot 55642
sig 55434
ups 56647
lam 46750
phi 55084
kap 46146
chi 54182
pi. 49029
p02 53907
tau 55945
ksi 46771
alf=eta=the=bet=del=gam=zet=mu.=eps;the=del;eta-gam
Sextans:
alf 49641
----
Hydra2:203.3,-4.0
alf 46390
zet 43813
nu. 52943
eps 43109
lam 49841
mu. 51069
the 45336
iot 47431
u01 48356
del 42313
#bet 57936
eta 42799
rho 43234
sig 42402
t02 46776
t01 46509
u02 49402
CRa 53740
CRa-nu.-mu.-lam-u02-u01-alf-iot-the-zet-eps-del-sig-eta-rho
#pi.-gam-bet-ksi-CRb;CRa-nu.-mu.-lam-u02-u01-alf-iot-the-zet-eps-del-sig-eta-rho
Cancer:221.6,20.1
bet 40526
del 42911
iot 43103
alf 44066
gam 42806
alf-del-bet;del-gam-iot
Vela:212.5,-48.5
gam 39953
del 42913
lam 44816
kap 45941
mu. 52727
phi 48774
psi 46651
omi 42536
qqq 50191
gam-lam-psi-qqq-mu.-phi-kap-del-gam
Carina:241.0,-57.0
alf 30438
bet 45238
eps 41037
iot 45556
the 52419
ups 48002
ome 50099
ppp 51576
qqq 50371
aaa 45080
chi 38827
uuu 53253
VEg 39953
VEd 42913
Pnu 31685
alf-bet-ome-the-ppp-qqq-iot-eps-chi-VEg;iot-VEd;ppp-uuu;alf-Pnu
Chamaeleon:207.0,-83.5
alf 40702
gam 51839
bet 60000
the 40888
del 52633
eps 58484
alf-the-gam-eps-bet-del-gam
Pyxis:219.5,-33.0
alf 42828
bet 42515
gam 43409
kap 44824
the 45902
lam 46026
zet 42483
del 43825
Pze 39429
gam-alf-bet-Pze
Lynx:240.0,44.0
alf 45860
rrr 45688
qqq 44248
sss 41075
ttt 33449
uuu 30060
ppp 44700
vvv 36145
www 39847
ooo 47029
xxx 32438
yyy 33485
zzz 37609
nnn 29919
alf-rrr-ppp-qqq-sss-vvv-ttt-uuu
Volans:240.5,-66.0
bet 41312
gam 34481
zet 37504
del 35228
alf 44382
eps 39794
alf-eps-del-gam-eps-bet-alf
Puppis:239.2,-35.0
zet 39429
pi. 35264
rho 39757
tau 32768
nu. 31685
sig 36377
ksi 38170
alf 38414
kap 37229
omi 38070
up1 35363
pi2 37173
chi 38901
VEg 39953
zet-rho-ksi-kap-pi.-nu.;zet-VEg
Monoceros:241.5,-4.5
bet 30867
alf 37447
gam 29651
del 34769
zet 39863
eps 30419
alf-zet-del-bet-gam
Canis Minor:239.0,11.0
alf 37279
bet 36188
gam 36284
eps 36041
alf=bet
Gemini:247.0,25.0
bet 37826
gam 31681
alf 36850
mu. 30343
eps 32246
eta 29655
ksi 32362
del 35550
kap 37740
lam 35350
iot 36046
zet 34088
ups 36962
nu. 30883
rho 36366
sig 37629
tau 34693
chi 39424
phi 38538
ksi=lam=del=ups=bet;kap=ups=iot=tau=eps=nu.;eps=mu.=eta;del=zet=gam;tau=alf
Canis_Major:245.0,-18.0;245.0,-21.5
alf 32349
eps 33579
del 34444
bet 30324
eta 35904
zet 30122
om2 33977
sig 33856
kap 32759
om1 33152
nu2 31592
ome 35037
the 33160
gam 34045
ks1 31125
iot 33347
tau 35415
nu3 31700
ks2 31416
pi. 33302
pi1 33092
eta=del=alf=bet=nu2=om1=eps=del
Orion:263.5,2.3
bet 24436
alf 27989
gam 25336
eps 26311
zet 26727
kap 27366
del 25930
iot 26241
pi3 22449
eta 25281
lam 26207
tau 24674
pi4 22549
pi5 22797
sig 26549
om2 22957
ph2 26366
mu. 28614
pi2 22509
ph1 26176
ch1 27913
nu. 29038
ksi 29426
rho 24331
pi6 23123
ome 26594
psi 25473
ups 25923
pi1 22845
ch2 28716
om1 22667
ps1 25302
the 26220
kap=zet=alf=gam=del=eta=tau=bet;alf=lam=gam-pi3-pi4-pi5-pi6;pi3-pi2-pi1-om2
Columba:271.6,-40.0
alf 26634
bet 27628
del 30277
eps 25859
eta 28328
gam 28199
kap 29807
omi 24659
lam 27810
ksi 28010
del-bet-eta;bet-alf-eps
Dorado:278.0,-54.0
alf 21281
bet 26069
gam 19893
del 27100
xxx 27890
zet 23693
the 24372
alf-zet-bet-xxx-del-bet-alf-gam
Lepus:273.0,-25.5
alf 25985
bet 25606
eps 23685
mu. 24305
zet 27288
gam 27072
eta 28103
del 27654
lam 24845
kap 24327
iot 24244
the 28910
alf=bet=eps=mu.=alf-zet-eta-the-del-gam-bet
Auriga:278.5,35.5
alf 24608
gam 25428
bet 28360
the 28380
iot 23015
eps 23416
eta 23767
zet 23453
del 28358
nu. 27673
pi. 28404
kap 29696
tau 27483
lam 24813
chi 25984
ups 27639
ps2 31832
mu. 24340
ps9 33485
ps1 30520
ome 23179
ksi 27949
ps7 32844
zet-eps-alf-del-bet-alf-eta-iot-gam-the-bet
Camelopardalis:270.0,70.0
bet 23522
hhh 16228
alf 22783
ggg 17884
aaa 23040
iii 16281
bbb 33694
gam 17959
ddd 29997
vz. 36547
ccc 27949
eee 33104
fff 17854
aaa-bet-alf-ddd-bbb;alf-gam;fff-ggg-hhh
Taurus:295.7,16.0
alf 21421
bet 25428
eta 17702
zet 26451
th2 20894
lam 18724
eps 20889
omi 15900
gam 20205
ksi 16083
del 20455
th1 20885
nu. 18907
kap 20635
mu. 19860
tau 21881
ups 20711
xxx 16852
de3 20648
iot 23497
rho 21273
sig 21683
pi. 20732
de2 20542
ome 19990
phi 20250
zet=alf=th1=gam=lam=ksi-nu.;bet=eps=del=gam;omi-xxx
Reticulum:300.0,-67.0
alf 19780
bet 17440
eps 19921
gam 18744
del 18597
kap 16245
iot 18772
alf-bet-del-eps-alf
Eridanus:295.0,-17.0
alf 7588
bet 23875
the 13847
gam 18543
del 17378
up4 20042
phi 10602
chi 9007
ta4 15474
eps 16537
up2 21393
eta 13701
nu. 21444
up3 20535
mu. 22109
om1 19587
ta3 14146
iot 12486
ggg 17874
ta6 17651
kap 11407
lam 23972
ta5 16611
eee 15510
ome 22701
pi. 17593
om2 19849
ta1 12843
up1 21248
yyy 16870
ta9 18673
ta8 18216
sss 12413
ta2 13288
zet 15197
psi 23364
CET 12770
bet-mu.-nu.-om1-gam-pi.-del-eps-eta-CET-ta1-ta3-ta4-ta5-ta6-ta8-ta9-up1-up2-up3-up4-ggg-yyy-eee-the-iot-sss-kap-chi-alf
Hydrus:330.0,-72.5
bet 2021
alf 9236
gam 17678
del 11001
eps 12394
eta 8928
nu. 13244
zet 12876
alf-bet-gam-alf
Cetus:337.0,-13.3
bet 3419
alf 14135
eta 5364
gam 12706
tau 8102
iot 1562
the 6537
zet 8645
ups 9347
del 12387
pi. 12770
mu. 12828
ks2 11484
ks1 10324
chi 8497
lam 13954
sig 11783
phi 3455
eps 12390
kap 15457
nu. 12093
rho 11345
gam-alf-lam-mu.-ks2-nu.-gam-del-zet-the-eta-iot-bet-tau-zet
Perseus:306.0,37.5
alf 15863
bet 14576
zet 18246
eps 18532
gam 14328
del 17358
rho 14354
ups 7607
eta 13268
nu. 17529
kap 14668
omi 17448
tau 13531
ccc 19343
ksi 18614
phi 8068
iot 14632
the 12777
mu. 19812
lam 19167
psi 16826
sig 16335
bbb 20070
ome 14817
pi. 13879
omi-zet-ksi-eps-del-alf-iot-kap-bet-eps;bet-rho;iot-the-phi;del-ccc-mu.-bbb-lam;alf-gam-eta-tau-iot;gam-tau
Aries:316.0,24.0
alf 9884
bet 8903
ccc 13209
gam 8832
del 14838
eps 13914
lam 9153
zet 15110
ccc-alf=bet=gam
Phoenix:338.0,-42.0
alf 2081
bet 5165
gam 6867
eps 765
kap 2072
del 7083
zet 5348
eta 3405
psi 8837
mu. 3245
iot 116389
nu. 5862
bet-alf-eps-bet-gam-del-zet-bet
Sculptor:353.5,-32.0
alf 4577
bet 116231
gam 115102
del 117452
eta 2210
alf-del-gam-bet
Triangulum:311.0,32.0
bet 10064
alf 8796
gam 10670
del 10644
iot 10280
alf-bet-gam-alf
Cassiopeia:333.0,64.5
gam 4427
alf 3179
bet 746
del 6686
eps 8886
eta 3821
zet 2920
kap 2599
iot 11569
omi 3504
rho 117863
up2 4422
chi 7294
psi 6692
lam 2505
ksi 3300
up1 4292
tau 117301
sig 118243
nu. 3801
pi. 3414
phi 6242
ome 9009
bet-alf-gam-del-eps
Andromeda:346.5,43.0
alf 677
bet 5447
gam 9640
del 3092
xxx 7607
omi 113726
lam 116584
mu. 4436
zet 3693
ups 7513
kap 116805
phi 5434
iot 116631
pi. 2912
eps 3031
eta 4463
sig 1473
nu. 3881
the 1366
ome 6813
ksi 6411
tau 7818
psi 117221
alf-del-eps-zet-eta;gam-bet-del-pi.-bet-mu.-nu.-phi-xxx;pi.-iot-kap-lam;iot-omi
"""

