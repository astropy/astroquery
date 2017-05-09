#!/bin/sh

if ! [ $TRAVIS_REPO_SLUG ]; then
    echo "Not building on travis. Exiting"
    exit 0
fi

if [ $TRAVIS_REPO_SLUG != "astropy/astroquery" ]; then
   echo "Not building from main repo. Exiting"
   exit 0
fi

if [ $TRAVIS_PULL_REQUEST != 'false' ]; then
    echo "Not building for pull request."
    exit 0
fi

travis login --github-token=$GITHUB_TOKEN --skip-version-check
echo "Travis astroquery Summary"
travis branches -r astropy/astroquery --skip-version-check

job_id=`travis branches -r astropy/astroquery --skip-version-check | grep $TRAVIS_BRANCH | cut -d"#" -f 2 | cut -d" " -f 1`

echo "job_id is $job_id"

if ! [ $job_id ]; then
   echo "Could not find an astropy/astroquery branch named $TRAVIS_BRANCH. Exiting"
   exit 0
fi

travis restart $job_id -r astropy/astroquery --skip-version-check
