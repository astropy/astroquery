CWD=$PWD

echo ${CWD}

# ALL of these must pass!
cd .. && \
git checkout gh-pages && \
git checkout master -- README.rst && \
rst2html.py --stylesheet=stylesheets/styles.css,stylesheets/pygment_trac.css,stylesheets/normalize.css,stylesheets/ie.css --link-stylesheet README.rst index.html && \
rm README.rst && \
git reset && \
git add index.html && \
git commit -m "Index.html generated." && \
git checkout master

git checkout master
git checkout master
git checkout master

echo $PWD
echo $CWD
echo `git branch`

if [ -d frontpage ]
then
    echo "directory frontpage exists."
    cd frontpage
else
    echo "directory frontpage does not exist"
fi 

if [ -d ${CWD} ]
then
    echo "directory ${CWD} exists."
    cd ${CWD}
    cd ${CWD}
else
    echo "directory ${CWD} does not exist."
fi
