# -*- coding: utf-8 -*-
import scrapy
import re
import json
from time import gmtime, strftime
import unidecode


class ZuloShishasPider(scrapy.Spider):
    name = 'zulo'
    start_urls = ['https://www.zuloshishas.es/cachimbas-3']
    aplicadosMetadatos = False

    def parse(self, response):
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'ZuloShishas',
                'logo': response.css('a#header_logo img.logo::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
        contenedorProducto = response.css('div.product-container')
        loopInfo = {
            'actualIndex': 0,
            'total': len(contenedorProducto)
        }
        self.nextPageClass = response.css(
            'li#pagination_next_bottom::attr(class)')
        self.nextPageElement = response.css(
            'li#pagination_next_bottom a::attr(href)')
        for shisha in contenedorProducto:

            linkProducto = shisha.css('a.product_img_link::attr(href)').get()
            itemFinal = {
                'linkProducto': linkProducto
            }
            request = scrapy.Request(response.urljoin(
                linkProducto), callback=self.obtenerInfoProducto)
            request.cb_kwargs['itemFinal'] = itemFinal
            request.cb_kwargs['loopInfo'] = loopInfo
            yield request

    def obtenerInfoProducto(self, response, itemFinal, loopInfo):
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
            contenidoPrincipal.css('h1.heading::text').get(), ['cachimba', 'shisha']))
        itemFinal['marca'] = self.flattenString(self.removeSpecificWordsFromString(contenidoPrincipal.css(
            'a#product_manufacturer_logo meta::attr(content)').get(), ['cachimba', 'shisha']))
        itemFinal['imagen'] = contenidoPrincipal.css(
            'img#bigpic::attr(src)').get()
        itemFinal['divisa'] = precioOriginal.split(" ")[-1]
        itemFinal['precioOriginal'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) == 0 else precioRebajado.get().split(" ")[-2]
        itemFinal['precioRebajado'] = precioOriginal.split(" ")[-2] if len(
            precioRebajado) > 0 else None
        itemFinal['agotado'] = not hayStock
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = 'cachimba',
        itemFinal['etiquetas'] = contenidoPrincipal.css(
            'div#idTab211 div.pa_content a::text').getall()
        itemFinal['specs'] = self.obtenerEspecificaciones(response)
        yield itemFinal

        if loopInfo['actualIndex'] == (loopInfo['total'] - 1):
            if self.haySiguiente(self.nextPageClass):
                request = scrapy.Request(response.urljoin(
                    self.nextPageElement.get()), callback=self.parse)
                yield request

        loopInfo['actualIndex'] += 1

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

    def haySiguiente(self, botonSiguienteClass):
        if "disabled" in botonSiguienteClass.get().split(" "):
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