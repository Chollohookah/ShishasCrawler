echo "Deteniendo contenedores"
docker stop $(docker ps -a -q)
echo "Eliminando contenedores"
docker rm $(docker ps -a -q)
echo "Eliminando imagenes"
docker rmi -f $(docker images -a -q)

echo "Lanzando back chollohookah"
cd /home/ubuntu/CholloHokas-BackLB4
docker-compose up -d

echo "Lanzando pagina personal"
cd /home/ubuntu/personal-blog-tss-BACK
docker-compose up -d

echo "Exitoso"
docker ps -a