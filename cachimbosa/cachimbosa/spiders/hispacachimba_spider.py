# -*- coding: utf-8 -*-
import scrapy
import json
import re
import unidecode
from time import gmtime, strftime


class HispaCachimbas(scrapy.Spider):
    name = "hispacachimba1"
    start_urls = ["https://www.hispacachimba.es/Cachimbas"]
    metadatosObtenidos = False
    errorRequest = False
    executingPagesRequests = False

    def parse(self, response):
        cachimbas = response.css('div#content div.product-grid')
        enlaces = cachimbas.css('div.image a::attr(href)').getall()
        if len(enlaces) == 0:
            self.errorRequest = True
        if self.metadatosObtenidos == False:
            self.metadatosObtenidos = True
            yield {
                'name': 'Hispacachimbaa',
                'logo': response.css('div#logo a img::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }

        for enlace in enlaces:
            itemFinal = {
                'linkProducto': enlace
            }
            peticionShishas = scrapy.Request(response.urljoin(
                enlace), callback=self.obtenerDetallShisha)
            peticionShishas.cb_kwargs['itemFinal'] = itemFinal
            yield peticionShishas

        if self.executingPagesRequests == False:
            indexWhile = 1
            self.executingPagesRequests = True
            while self.errorRequest == False and indexWhile < 100:
                yield scrapy.Request(response.urljoin("https://www.hispacachimba.es/cachimbas/page/"+str(indexWhile)+"/"),callback=self.parse,errback=self.requestFailed)
                indexWhile = indexWhile + 1

        

    def requestFailed(self):
        self.errorRequest = True

    def obtenerDetallShisha(self, response, itemFinal):
        contenido = response.css('div#content')
        itemFinal['titulo'] = contenido.css(
            '.page-title::text').get()
        # En caso de que haya ofertas se diferencian con las siguientes clases
        precioViejo = contenido.css("#product div.product-price-old::text")
        precioNuevo = contenido.css("#product div.product-price-new::text")
        precioRegular = contenido.css('.price-group .product-price::text')

        if len(precioNuevo) > 0 and len(precioViejo) > 0:
            itemFinal['precioOriginal'] = precioViejo.get()[:-1]
            itemFinal['precioRebajado'] = precioNuevo.get()[:-1]
        else:
            itemFinal['precioOriginal'] = precioRegular.get()[:-1]
            itemFinal['precioRebajado'] = None

        fotosSinParsear = response.css(
            'meta[property="og:image"]::attr(content)').getall()

        for fotoSinParsear in fotosSinParsear:
            fotoSinParsear = re.sub(
                "((0|[1-9][0-9]*)x(0|[1-9][0-9]*))\w+", "1050x1200", fotoSinParsear)
        itemFinal['fotos'] = fotosSinParsear

        itemFinal['shortDesc'] = response.css('meta[name="description"]::attr(content)').get()

        itemFinal['divisa'] = (precioRegular if len(
            precioRegular) > 0 else precioNuevo).get()[-1]

        itemFinal['imagen'] = response.css(
            'meta[name="twitter:image"]::attr(content)').get()

        itemFinal['marca'] = self.flattenString(self.removeSpecificWordsFromString(response.css('meta[property="og:image"]::attr(content)').get().split("/")[6].upper(), ['cachimba', 'shisha']))

        itemFinal['modelo'] = self.flattenString(self.removeSpecificWordsFromString(
            itemFinal['titulo'].lower(), ['cachimba']+itemFinal['marca'].lower().split())).strip()

        itemFinal['agotado'] = True if (contenido.css(
            'd#product .in-stock span::text').get()) is None else False
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = ['cachimba']
        itemFinal['etiquetas'] = contenido.css('.tags a::text').getall()
        yield itemFinal

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        if string is not None:
            edit_string_as_list = string.lower().split()
            final_list = [
                word for word in edit_string_as_list if word not in wordsToDelete]
            final_string = ' '.join(final_list)
            return final_string
        else:
            return ""

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def flattenString(self, string):
        string = string.upper()
        string = string.replace(".", " ")
        string = string.replace(",", " ")
        string = string.replace("-", " ")
        string = string.replace(" ", "")
        string = string.strip()
        string = unidecode.unidecode(string)
        return string
