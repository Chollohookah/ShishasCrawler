import scrapy
import json
import re


class HispaCachimbas(scrapy.Spider):
    name = "hispacachimba"
    start_urls = ["https://www.hispacachimba.es/Cachimbas-Shishas"]

    def parse(self, response):
        cachimbas = response.css('div.product-thumb')
        enlaces = cachimbas.css('div.image a::attr(href)').getall()
        yield {
            'name':'Hispacachimbaa',
            'logo':response.css('a#site_logo img::attr(src)').get()
        }
        for enlace in enlaces:
            itemFinal = {
                'linkProducto': enlace
            }
            peticionShishas = scrapy.Request(response.urljoin(
                enlace), callback=self.obtenerDetallShisha)
            peticionShishas.cb_kwargs['itemFinal'] = itemFinal
            yield peticionShishas

    def obtenerDetallShisha(self, response, itemFinal):
        contenido = response.css('section#content')
        itemFinal['titulo'] = contenido.css(
            'div.tb_system_page_title h1::text').get()
        # En caso de que haya ofertas se diferencian con las siguientes clases
        precioViejo = contenido.css('span.price-old')
        precioNuevo = contenido.css('span.price-new')
        precioRegular = contenido.css('span.price-regular')

        if len(precioNuevo) > 0 and len(precioViejo) > 0:
            itemFinal['precioOriginal'] = self.obtenerPrecioJunto(precioViejo)
            itemFinal['precioRebajado'] = self.obtenerPrecioJunto(precioNuevo)
        else:
            itemFinal['precioOriginal'] = self.obtenerPrecioJunto(
                precioRegular)
            itemFinal['precioRebajado'] = None

        itemFinal['divisa'] = (precioRegular if len(
            precioRegular) > 0 else precioNuevo).css('span.tb_currency::text').get()
        itemFinal['imagen'] = response.css(
            'meta[name="twitter:image"]::attr(content)').get()
        itemFinal['marca'] = itemFinal['imagen'].split("/")[6].upper()

        itemFinal['modelo'] = self.removeSpecificWordsFromString(
            itemFinal['titulo'].lower(), ['cachimba', itemFinal['marca'].lower()])
        itemFinal['agotado'] = True if (contenido.css(
            'dl.dl-horizontal dd span::text').get().lower()) == 'en stock' else False
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = ['cachimba']
        itemFinal['etiquetas'] = contenido.css('ul.tb_tags li a::text').getall()
        yield itemFinal
    # se le pasa el elemento price-old, price-new o price-regular

    def obtenerPrecioJunto(self, elemento):
        integer = elemento.css('span.tb_integer::text').get()
        decimalPoint = elemento.css('span.tb_decimal_point::text').get()
        decimal = elemento.css('span.tb_decimal::text').get()
        return integer+decimalPoint+decimal

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        edit_string_as_list = string.split()
        final_list = [
            word for word in edit_string_as_list if word not in wordsToDelete]
        final_string = ' '.join(final_list)
        return final_string
