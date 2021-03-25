import scrapy
import json
from time import gmtime, strftime
import time
import unidecode


class TheGoodShishaSpider(scrapy.Spider):
    name = "tgs"
    start_urls = ['https://www.thegoodshisha.com/product-category/shishas/']
    itemFinal = {}
    allShishasParsed = []
    aplicadosMetadatos = False

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'TheGoodShisha',
                'logo': response.css('link[rel="icon"][sizes="192x192"]::attr(href)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
        shishas = response.css('li.product')
        botonRef = response.css('a.next::attr(href)')
        if botonRef is not None and len(botonRef) > 0:
            self.botonSiguiente = botonRef[0].get()
        else:
            self.botonSiguiente = None
        self.loopInfo = {
            'actualIndex': 0,
            'total': len(shishas)
        }

        for shisha in shishas:
            enlace = shisha.css("a.woocommerce-LoopProduct-link")
            enlaceHref = enlace.css("::attr(href)").get()
            precios = shisha.css('span.woocommerce-Price-amount bdi::text')
           # shortDescYielded = ("".join(response.css('div.woocommerce-Tabs-panel--description p:nth-of-type(1) *::text').getall()))
            itemFinal = {
                'linkProducto': enlaceHref,
                'marca': self.flattenString(self.removeSpecificWordsFromString(enlaceHref.split("/")[-3].upper(), ['cachimba', 'shisha'])),
                'modelo': self.flattenString(self.removeSpecificWordsFromString(enlaceHref.split("/")[-2].upper(), ['cachimba', 'shisha'])),
                'imagen': enlace.css('img::attr(src)').get(),
                'titulo': shisha.css('h2.woocommerce-loop-product__title::text').get(),
                'divisa': shisha.css('span.woocommerce-Price-currencySymbol::text').get(),
                'precioOriginal': precios[0].get(),
                'precioRebajado': precios[1].get() if len(precios) > 1 else None
            }

            if enlaceHref is not None:
                request = scrapy.Request(response.urljoin(
                    enlaceHref), callback=self.obtenerInfoProducto, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                request.cb_kwargs['itemFinal'] = itemFinal
                yield request

    def obtenerInfoProducto(self, response, itemFinal):
        mainData = response.css('div.inside-article')
        estaFueraDeStock = mainData.css('p.out-of-stock')
        cart = mainData.css('form.cart')
        metadatosProducto = mainData.css('div.product_meta')

        if(len(estaFueraDeStock) > 0):
            itemFinal['agotado'] = True
        else:
            itemFinal['agotado'] = False
            # itemFinal['cantidad'] = cart.css('input.qty::attr(max)')[0].get()
        itemFinal['shortDesc'] = ("".join(response.css(
            'div.woocommerce-Tabs-panel--description p:nth-of-type(1) *::text').getall()))
        itemFinal['categorias'] = metadatosProducto.css(
            'span.posted_in a[rel="tag"]::text').getall()
        itemFinal['etiquetas'] = metadatosProducto.css(
            'span.tagged_as a[rel="tag"]::text').getall()

        # self.allShishasParsed.append(itemFinal)
        yield itemFinal
        if self.loopInfo['actualIndex'] == (self.loopInfo['total'] - 1):
            if self.botonSiguiente is not None:
                request = scrapy.Request(response.urljoin(
                    self.botonSiguiente), callback=self.parse)
                yield request

        self.loopInfo['actualIndex'] += 1

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        if string is not None:
            edit_string_as_list = string.lower().split()
            final_list = [
                word for word in edit_string_as_list if word not in wordsToDelete]
            final_string = ' '.join(final_list)
            return final_string
        else:
            return ""

    def flattenString(self, string):
        string = string.upper()
        string = string.replace(".", " ")
        string = string.replace(",", " ")
        string = string.replace("-", " ")
        string = string.replace(" ", "")
        string = string.strip()
        string = unidecode.unidecode(string)
        return string
