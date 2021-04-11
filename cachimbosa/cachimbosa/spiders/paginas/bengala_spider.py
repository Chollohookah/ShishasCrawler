# -*- coding: utf-8 -*-
import scrapy
import json
import re
import unidecode
from time import gmtime, strftime
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
                productDesc = shisha.css('div.product-description')
                precioRegular = productDesc.css('span.regular-price::text')
                precioProducto = productDesc.css(
                    'span.product-price::attr(content)')
                divisa = productDesc.css(
                    'span.product-price::text').get().split()[1]

                if precioRegular.get() is not None:
                    extraccionPrecioRegular = precioRegular.get().split()[0]

                itemFinal = {
                    'linkProducto': thumbContainer.css('a::attr(href)').get(),
                    'titulo': productDesc.css('h3.product-title a::text').get(),
                    'precioOriginal': extraccionPrecioRegular if len(precioRegular) > 0 else precioProducto.get(),
                    'precioRebajado': precioProducto.get() if len(precioRegular) > 0 else None,
                    'divisa': divisa,
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

        itemFinal['colores'] = colores

        itemFinal['shortDesc'] = Utils.cleanhtml(self, response.css(
            'div[itemprop="description"] p,strong::text').get())

        itemFinal['fotos'] = response.css(
            '#product-images-thumbs div.thumb-container img::attr(src)').getall()
        itemFinal['specs'] = self.obtenerEspecificaciones(response)

        itemFinal['marca'] = Utils.flattenString(self, Utils.removeSpecificWordsFromString(self, contentWrapper.css(
            'div#product-details-tab div#product-details meta::attr(content)').get(), ['cachimba', 'shisha']))
        itemFinal['modelo'] = Utils.flattenString(self, Utils.removeSpecificWordsFromString(self,
                                                                                            (itemFinal['titulo'] if itemFinal['titulo'] is not None else '').lower(), ['cachimba', 'shisha', (itemFinal['marca'] if itemFinal['marca'] is not None else '').lower()]))
        itemFinal['agotado'] = True if len(contentWrapper.css(
            'button.add-to-cart::attr(disabled)')) > 0 else False
        itemFinal['cantidad'] = None
        itemFinal['etiquetas'] = contentWrapper.css(
            'div#content-wrapper div.product-description div.rte-content strong::text').getall()
        yield itemFinal

    def obtenerEspecificaciones(self, response):
        objEspecificaciones = {}
        keysSpecs = response.css('section.product-features dt::text').getall()
        valueSpecs = response.css('section.product-features dd::text').getall()
        for index, item in enumerate(keysSpecs):
            if item == 'Tamaño':
                objEspecificaciones['tamanyo'] = valueSpecs[index]
            elif item == 'Altura':
                objEspecificaciones['altura'] = valueSpecs[index]
            elif item == 'Material':
                objEspecificaciones['material'] = valueSpecs[index]
        return objEspecificaciones,
