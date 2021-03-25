#!/bin/bash

echo "" > /home/ubuntu/data/zuloshisha.json
echo "" > /home/ubuntu/data/bengalas.json
echo "" > /home/ubuntu/data/hispacachimba.json
echo "" > /home/ubuntu/data/medusa.json
echo "" > /home/ubuntu/data/tgs.json

/usr/local/bin/scrapy runspider /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/spiders/zuloshishas_spider.py -o /home/ubuntu/data/zuloshisha.json
sleep 1m
/usr/local/bin/scrapy runspider /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/spiders/bengala_spider.py -o /home/ubuntu/data/bengalas.json
sleep 1m
/usr/local/bin/scrapy runspider /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/spiders/hispacachimba_spider.py -o /home/ubuntu/data/hispacachimba.json
sleep 1m
/usr/local/bin/scrapy runspider /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/spiders/medusa_spider.py -o /home/ubuntu/data/medusa.json
sleep 1m
/usr/local/bin/scrapy runspider /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/spiders/tgs_spider.py -o /home/ubuntu/data/tgs.json
sleep 1m


if [ "$?" != "0" ]; then
	echo "[Error] scrawleamiento fallado"
	exit 1
fi

echo "[Success] scrawl multiple exitoso"
echo "[INFO] iniciando subida base de datos"

#python3 /home/ubuntu/scripts/ShishasCrawler/cachimbosa/cachimbosa/scripts/file_exporter.py "10052001Tsonyo"

if [ "$?" != "0" ]; then
        echo "[Error] Guardado en base de datos fallado"
        exit 1
fi

echo "[Success] guardado en base de datos exitoso"
