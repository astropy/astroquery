# Definition of parameters
target=3552
ep=now
observer=X05

# For each type of coordinates:
# https://ssp.imcce.fr/webservices/miriade/api/ephemcc/
for tcoor in 1 2 3 4 5; 
do
	echo ${tcoor}

	url="https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php?-name=a:${target}&-type=&-ep=${ep}&-nbd=1&-step=1d&-tscale=UTC&-observer=${observer}&-theory=INPOP&-teph=1&-tcoor=${tcoor}&-oscelem=astorb&-mime=votable&-output=--jd,--rv&-from=TestAstropy"
	file="${target}_coordtype${tcoor}.dat"

	wget ${url} -O ${file}
done

