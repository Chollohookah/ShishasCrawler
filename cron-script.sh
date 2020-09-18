#!/bin/bash

(rm zuloshisha.json bengalas.json hispacachimba.json medusa.json tgs.json) || echo "no hay ficheros que eliminar"

scrapy runspider cachimbosa/cachimbosa/spiders/zuloshishas_spider.py -o zuloshisha.json
scrapy runspider cachimbosa/cachimbosa/spiders/bengala_spider.py -o bengalas.json
scrapy runspider cachimbosa/cachimbosa/spiders/hispacachimba_spider.py -o hispacachimba.json
scrapy runspider cachimbosa/cachimbosa/spiders/medusa_spider.py -o medusa.json
scrapy runspider cachimbosa/cachimbosa/spiders/tgs_spider.py -o tgs.json

if [ "$?" != "0" ]; then
	echo "[Error] scrawleamiento fallado"
	exit 1
fi

echo "[Success] scrawl multiple exitoso"
echo "[INFO] iniciando subida base de datos"

python3 cachimbosa/cachimbosa/scripts/file_exporter.py $1

if [ "$?" != "0" ]; then
        echo "[Error] Guardado en base de datos fallado"
        exit 1
fi

echo "[Success] guardado en base de datos exitoso"
