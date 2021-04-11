#!/bin/bash

echo "" > $HOME/data/zuloshisha.json
echo "" > $HOME/data/bengalas.json
echo "" > $HOME/data/hispacachimba.json
echo "" > $HOME/data/medusa.json
echo "" > $HOME/data/tgs.json
echo "" > $HOME/data/bakkali.json


/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/zuloshishas_spider.py -o $HOME/data/zuloshisha.json
sleep 1m
/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/bengala_spider.py -o $HOME/data/bengalas.json
sleep 1m
/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/hispacachimba_spider.py -o $HOME/data/hispacachimba.json
sleep 1m
/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/medusa_spider.py -o $HOME/data/medusa.json
sleep 1m
/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/tgs_spider.py -o $HOME/data/tgs.json
sleep 1m
/usr/local/bin/scrapy runspider $HOME/ShishasCrawler/cachimbosa/cachimbosa/spiders/paginas/bakkali_spider.py -o $HOME/data/bakkali.json
sleep 1m

if [ "$?" != "0" ]; then
	echo "[Error] scrawleamiento fallado"
	exit 1
fi

echo "[Success] scrawl multiple exitoso"
echo "[INFO] iniciando subida base de datos"

python3 $HOME/ShishasCrawler/cachimbosa/cachimbosa/scripts/file_exporter.py $1

if [ "$?" != "0" ]; then
        echo "[Error] Guardado en base de datos fallado"
        exit 1
fi

echo "[Success] guardado en base de datos exitoso"
