# -*- coding: utf-8 -*-
import scrapy
import re
import json
from time import gmtime, strftime
import unidecode


class ZuloShishasPider(scrapy.Spider):
    name = 'zulo'
    PAGINA_MAX = 100
    URL_MANGUERAS = "https://www.zuloshishas.es/mangueras-cachimba-4"
    URL_CAZOLETAS = "https://www.zuloshishas.es/cazoletas-cachimbas-5"
    URL_CARBON = "https://www.zuloshishas.es/carbones-cachimba-6"
    URL_CACHIMBAS = "https://www.zuloshishas.es/cachimbas-3"
    URL_ESENCIAS = "https://www.zuloshishas.es/esencias-y-potenciadores-de-sabor-7"
    URL_ACCESORIOS = "https://www.zuloshishas.es/accesorios-cachimba-8"

    start_urls = [URL_MANGUERAS, URL_CAZOLETAS, URL_CARBON,
                  URL_CACHIMBAS, URL_ESENCIAS, URL_ACCESORIOS]
    aplicadosMetadatos = False

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'ZuloShishas',
                'logo': response.css('a#header_logo img.logo::attr(src)').get(),
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
                    response.url+"?p="+str(indexWhile)), meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302, 301]
                }, callback=self.executeDescRequest)
                peticionShishasPagina.cb_kwargs['typeItem'] = self.obtainTypeDependingOnUrlScrapped(
                    response.url)

            yield peticionShishasPagina
            indexWhile = indexWhile + 1

    def obtainTypeDependingOnUrlScrapped(self, url):
        if url == self.URL_CACHIMBAS:
            return "cachimba"
        elif url == self.URL_ESENCIAS:
            return "esencias"
        elif url == self.URL_CAZOLETAS:
            return "cazoleta"
        elif url == self.URL_ACCESORIOS:
            return "accesorio"
        elif url == self.URL_CARBON:
            return "carbon"
        elif url == self.URL_MANGUERAS:
            return "manguera"
        else:
            return "otros"

    def executeDescRequest(self, response, typeItem):
        contenedorProducto = response.css('div.product-container')
        if(len(contenedorProducto) > 0):
            for shisha in contenedorProducto:
                linkProducto = shisha.css(
                    'a.product_img_link::attr(href)').get()
                itemFinal = {
                    'linkProducto': linkProducto,
                    'tipo': typeItem
                }
                request = scrapy.Request(response.urljoin(
                    linkProducto), callback=self.obtenerInfoProducto)
                request.cb_kwargs['itemFinal'] = itemFinal
                yield request

    def obtenerInfoProducto(self, response, itemFinal):
        contenidoPrincipal = response.css('div.main_content_area')
        hayStock = self.hayStock(
            contenidoPrincipal.css('div#oosHook::attr(style)'))
        fotosExtraShisha = response.css(
            '#thumbs_list ul li a::attr(href)').getall()
        descCorta = self.cleanhtml(response.css(
            '#short_description_content p,strong::text').get())

        precioOriginal = contenidoPrincipal.css(
            'span#our_price_display::text').get()
        precioRebajado = contenidoPrincipal.css(
            ' p#old_price:not(.hidden) span#old_price_display::text')
        itemFinal['fotos'] = fotosExtraShisha
        itemFinal['shortDesc'] = descCorta
        itemFinal['titulo'] = contenidoPrincipal.css('h1.heading::text').get()
        itemFinal['modelo'] = self.flattenString(self.removeSpecificWordsFromString(
            contenidoPrincipal.css('h1.heading::text').get(), ['cachimba', 'shisha', itemFinal['tipo']]))
        itemFinal['marca'] = self.flattenString(self.removeSpecificWordsFromString(contenidoPrincipal.css(
            'a#product_manufacturer_logo meta::attr(content)').get(), ['cachimba', 'shisha', itemFinal['tipo']]))
        itemFinal['imagen'] = contenidoPrincipal.css(
            'img#bigpic::attr(src)').get()
        itemFinal['divisa'] = precioOriginal.split(" ")[-1]
        itemFinal['precioOriginal'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) == 0 else precioRebajado.get().split(" ")[-2]
        itemFinal['precioRebajado'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) > 0 else None
        itemFinal['agotado'] = not hayStock
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = [itemFinal['tipo']]
        itemFinal['etiquetas'] = contenidoPrincipal.css(
            'div#idTab211 div.pa_content a::text').getall()
        itemFinal['specs'] = self.obtenerEspecificaciones(response)
        yield itemFinal

    def obtenerEspecificaciones(self, response):
        # Indice par Key, indice inpar Valor
        arrayEspecificaciones = response.css('#idTab2 table td::text').getall()
        objEspecificaciones = {}
        for index, item in enumerate(arrayEspecificaciones):
            if item == 'Incluye cazoleta':
                objEspecificaciones['cazoleta'] = True if (
                    arrayEspecificaciones[(index+1)] == 'Sí') else False
            elif item == 'Tamaño aprox.':
                objEspecificaciones['tamanyo'] = arrayEspecificaciones[(
                    index+1)]
            elif item == 'Material principal':
                objEspecificaciones['material'] = arrayEspecificaciones[(
                    index+1)]
            elif item == 'Tipo de cierre':
                objEspecificaciones['cierre'] = arrayEspecificaciones[(
                    index+1)]
            elif item == 'Color predominante':
                objEspecificaciones['color'] = arrayEspecificaciones[(index+1)]
            elif item == 'Incluye base':
                objEspecificaciones['incluyeBase'] = True if (
                    arrayEspecificaciones[(index+1)] == 'Sí') else False
            elif item == 'Incluye manguera':
                objEspecificaciones['incluyeManguera'] = True if (
                    arrayEspecificaciones[(index+1)] == 'Sí') else False
            elif item == 'Tipo':
                objEspecificaciones['tipo'] = arrayEspecificaciones[(index+1)]
            elif item == 'Material':
                objEspecificaciones['material'] = arrayEspecificaciones[(
                    index+1)]
            elif item == 'Procedencia':
                objEspecificaciones['procedencia'] = arrayEspecificaciones[(
                    index+1)]
        return objEspecificaciones

    def hayStock(self, seleccionOOSstyle):
        style = seleccionOOSstyle.get()
        if style == "" or style == None or len(style) == 0:
            return False
        return True

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

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
