#!/bin/bash

echo "" > /home/sportak/data/zuloshisha.json
echo "" > /home/sportak/data/bengalas.json
echo "" > /home/sportak/data/hispacachimba.json
echo "" > /home/sportak/data/medusa.json
echo "" > /home/sportak/data/tgs.json

scrapy runspider cachimbosa/cachimbosa/spiders/cachimbas/zuloshishas_spider.py -o /home/sportak/data/zuloshisha.json
#sleep 1m
scrapy runspider cachimbosa/cachimbosa/spiders/cachimbas/bengala_spider.py -o /home/sportak/data/bengalas.json
#sleep 1m
scrapy runspider cachimbosa/cachimbosa/spiders/cachimbas/hispacachimba_spider.py -o /home/sportak/data/hispacachimba.json
#sleep 1m
scrapy runspider cachimbosa/cachimbosa/spiders/cachimbas/medusa_spider.py -o /home/sportak/data/medusa.json
#sleep 1m
scrapy runspider cachimbosa/cachimbosa/spiders/cachimbas/tgs_spider.py -o /home/sportak/data/tgs.json
#sleep 1m


if [ "$?" != "0" ]; then
	echo "[Error] scrawleamiento fallado"
	exit 1
fi

echo "[Success] scrawl multiple exitoso"
echo "[INFO] iniciando subida base de datos"

python3 cachimbosa/cachimbosa/scripts/file_exporter.py "10052001Tsonyo"

if [ "$?" != "0" ]; then
        echo "[Error] Guardado en base de datos fallado"
        exit 1
fi

echo "[Success] guardado en base de datos exitoso"


echo "EXITAZO!"