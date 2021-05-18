# -*- coding: utf-8 -*-
import scrapy
import json
import re
import unidecode
from time import gmtime, strftime
from types import SimpleNamespace
from utils import Utils


class BengalaShishaSpider(scrapy.Spider):
    name = 'bengala'
    PAGINA_MAX = 100
    URL_CACHIMBAS = "https://bengalaspain.com/es/cachimbas-3"
    URL_CAZOLETAS = "https://bengalaspain.com/es/cazoletas-9"
    URL_MANGUERAS = "https://bengalaspain.com/es/mangueras-6"
    URL_ACCESORIOS = "https://bengalaspain.com/es/accesorios-10"
    URL_SABORES = "https://bengalaspain.com/es/sabores-13"
    URL_CARBON = "https://bengalaspain.com/es/carbones-11"
    # https://bengalaspain.com/es/cachimbas-3?page=2

    start_urls = [URL_CACHIMBAS, URL_CAZOLETAS, URL_MANGUERAS,
                  URL_ACCESORIOS, URL_SABORES, URL_CARBON]

    aplicadosMetadatos = False

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'BengalaSpain',
                'logo': response.css('div#desktop_logo a::attr(href)').get(
                )[0:-1] + response.css('div#desktop_logo img.img-fluid::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }

        indexWhile = 1
        while indexWhile < self.PAGINA_MAX:
            peticionShishasPagina = None
            if indexWhile == 1:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url), callback=self.executeDescRequest)
                peticionShishasPagina.cb_kwargs['typeItem'] = self.obtainTypeDependingOnUrlScrapped(
                    response.url)
            else:
                peticionShishasPagina = scrapy.Request(response.urljoin(
                    response.url+"?page="+str(indexWhile)), callback=self.executeDescRequest)
                peticionShishasPagina.cb_kwargs['typeItem'] = self.obtainTypeDependingOnUrlScrapped(
                    response.url)

            yield peticionShishasPagina
            indexWhile = indexWhile + 1

    def obtainTypeDependingOnUrlScrapped(self, url):
        if url == self.URL_CACHIMBAS:
            return "cachimba"
        elif url == self.URL_SABORES:
            return "sabor"
        elif url == self.URL_CAZOLETAS:
            return "cazoleta"
        elif url == self.URL_ACCESORIOS:
            return "accesorio"
        elif url == self.URL_CARBON:
            return "carbon"
        elif url == self.URL_MANGUERAS:
            return "manguera"

    def executeDescRequest(self, response, typeItem):
        shishas = response.css('div.js-product-miniature-wrapper')
        if (len(shishas) > 0):
            for shisha in shishas:
                thumbContainer = shisha.css('div.thumbnail-container')
                productDesc = shisha.css('div#col-product-info')

                itemFinal = {
                    'linkProducto': thumbContainer.css('a::attr(href)').get(),
                    'tipo': typeItem,
                    'categorias': [typeItem]
                }
                peticionShishaDetalle = scrapy.Request(
                    response.urljoin(itemFinal['linkProducto']), callback=self.obtenershishadetalle)
                peticionShishaDetalle.cb_kwargs['itemFinal'] = itemFinal
                yield peticionShishaDetalle

    def obtenershishadetalle(self, response, itemFinal):
        contentWrapper = response.css('div#content-wrapper')
        itemFinal['imagen'] = contentWrapper.css(
            'div.easyzoom-product a::attr(href)').get()
        coloresSinParsear = response.css(
            'div.product-variants li span.color::attr(style)').getall()
        colores = []
        color = None
        for colorSinParsear in coloresSinParsear:
            color = colorSinParsear.split(":")[1].strip()
            match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
            if match:
                colores.append(color)

        jsonData = json.loads(response.css(
            '#product-details::attr(data-product)').get())

        hayReduction = jsonData['reduction'] != 0

        precioRegular = jsonData['price_without_reduction'] if(
            hayReduction) else jsonData['price_amount']

        precioProducto = jsonData['price_amount'] if(
            hayReduction) else None
        divisa = jsonData['price'][-1]

        itemFinal['titulo'] = jsonData['name']
        itemFinal['precioOriginal'] = precioRegular
        itemFinal['precioRebajado'] = precioProducto
        itemFinal['divisa'] = divisa

        itemFinal['colores'] = colores
        itemFinal['specs'] = self.obtainSpecs(jsonData['features'])

        itemFinal['shortDesc'] = Utils.cleanhtml(self, jsonData['description_short'])

        itemFinal['fotos'] = self.obtainFotos(jsonData['images'])

        itemFinal['marca'] = Utils.flattenString(self, Utils.removeSpecificWordsFromString(self, contentWrapper.css(
            'div#product-details-tab div#product-details meta::attr(content)').get(), ['cachimba', 'shisha']))
        itemFinal['modelo'] = Utils.flattenString(self, Utils.removeSpecificWordsFromString(self,
                                                                                            (itemFinal['titulo'] if itemFinal['titulo'] is not None else '').lower(), ['cachimba', 'shisha', (itemFinal['marca'] if itemFinal['marca'] is not None else '').lower()]))
        itemFinal['agotado'] = True if len(contentWrapper.css(
            'button.add-to-cart::attr(disabled)')) > 0 else False
        itemFinal['cantidad'] = jsonData['quantity']
        itemFinal['etiquetas'] = contentWrapper.css(
            'div#content-wrapper div.product-description div.rte-content strong::text').getall()
        yield itemFinal

    def obtainSpecs(self, arraySpecs):
        res = []
        for spec in arraySpecs:
            obj = {}
            obj[spec['name']] = spec['value']
            res.append(obj)
        return res

    def obtainFotos(self, arrayImages):
        res = []
        for image in arrayImages:
            res.append(image['bySize']['large_default']['url'])
        return res
