# Definition of parameters
target=3552
ep=now
observer=X05

# For each type of coordinates:
# https://ssp.imcce.fr/webservices/miriade/api/ephemcc/
# rplane=1 -> equatorial
for tcoor in 1 2 3 4 5; 
do
	echo ${tcoor}-rplane1

	url="https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php?-name=a:${target}&-type=&-ep=${ep}&-nbd=1&-step=1d&-tscale=UTC&-observer=${observer}&-theory=INPOP&-teph=1&-tcoor=${tcoor}&-oscelem=astorb&-mime=votable&-output=--jd,--rv&-from=TestAstropy"
	file="${target}_coordtype${tcoor}-rplane1.dat"

	wget ${url} -O ${file}
done

# an example with rplane=2 -> ecliptic
tcoor=1
echo ${tcoor}-rplane2
url="https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php?-name=a:${target}&-type=&-ep=${ep}&-nbd=1&-step=1d&-tscale=UTC&-observer=${observer}&-theory=INPOP&-teph=1&-tcoor=${tcoor}&-rplane=2&-oscelem=astorb&-mime=votable&-output=--jd,--rv&-from=TestAstropy"
file="${target}_coordtype${tcoor}-rplane2.dat"
wget ${url} -O ${file}
