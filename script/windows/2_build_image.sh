boot2docker start
boot2docker ssh "
cd $(pwd)
if [ ${PWD##*/} = 'windows' ]; then
    cd ../..
fi
docker build --no-cache -t "venture" .

echo 'Press enter to continue...'
read -n1 -s
"