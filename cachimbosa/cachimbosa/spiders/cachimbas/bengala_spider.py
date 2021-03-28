# -*- coding: utf-8 -*-
import scrapy
import json
import re
import unidecode
from time import gmtime, strftime


class BengalaShishaSpider(scrapy.Spider):
    name = 'bengala'
    start_urls = ["https://bengalaspain.com/es/cachimbas-3"]
    aplicadosMetadatos = False

    def parse(self, response):
        shishas = response.css('div.js-product-miniature-wrapper')
        paginacion = response.css('nav.pagination ul li a.next')
        if self.aplicadosMetadatos is False:
            self.aplicadosMetadatos = True
            yield {
                'name': 'BengalaSpain',
                'logo': response.css('div#desktop_logo a::attr(href)').get(
                )[0:-1] + response.css('div#desktop_logo img.img-fluid::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }

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
                'divisa': divisa
            }
            peticionShishaDetalle = scrapy.Request(
                response.urljoin(itemFinal['linkProducto']), callback=self.obtenershishadetalle)
            peticionShishaDetalle.cb_kwargs['itemFinal'] = itemFinal
            yield peticionShishaDetalle

        if paginacion is not None and paginacion.attrib['href'] is not None:
            peticionMasShishas = scrapy.Request(
                response.urljoin(paginacion.attrib['href']), callback=self.parse
            )
            yield peticionMasShishas

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

        itemFinal['shortDesc'] = self.cleanhtml(response.css(
            'div[itemprop="description"] p,strong::text').get())

        itemFinal['fotos'] = response.css(
            '#product-images-thumbs div.thumb-container img::attr(src)').getall()
        itemFinal['specs'] = self.obtenerEspecificaciones(response)

        itemFinal['marca'] = self.flattenString(self.removeSpecificWordsFromString(contentWrapper.css(
            'div#product-details-tab div#product-details meta::attr(content)').get(), ['cachimba', 'shisha']))
        itemFinal['modelo'] = self.flattenString(self.removeSpecificWordsFromString(
            (itemFinal['titulo'] if itemFinal['titulo'] is not None else '').lower(), ['cachimba', 'shisha', (itemFinal['marca'] if itemFinal['marca'] is not None else '').lower()]))
        itemFinal['agotado'] = True if len(contentWrapper.css(
            'button.add-to-cart::attr(disabled)')) > 0 else False
        itemFinal['cantidad'] = None
        itemFinal['tipo'] = 'cachimba'
        itemFinal['categorias'] = ['cachimba']
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
