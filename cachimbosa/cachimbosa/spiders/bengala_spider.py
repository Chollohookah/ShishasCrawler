import scrapy
import json
import re
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
                'lastUpdate':strftime("%Y-%m-%d %H:%M:%S", gmtime())
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

        if paginacion is not None:
            peticionMasShishas = scrapy.Request(
                response.urljoin(paginacion.attrib['href']), callback=self.parse
            )
            yield peticionMasShishas

    def obtenershishadetalle(self, response, itemFinal):
        contentWrapper = response.css('div#content-wrapper')
        itemFinal['imagen'] = contentWrapper.css(
            'div.easyzoom-product a::attr(href)').get()
        itemFinal['marca'] = contentWrapper.css(
            'div#product-details-tab div#product-details meta::attr(content)').get()
        itemFinal['modelo'] = self.removeSpecificWordsFromString(
            itemFinal['titulo'].lower(), ['cachimba', itemFinal['marca'].lower()])
        itemFinal['agotado'] = True if len(contentWrapper.css(
            'button.add-to-cart::attr(disabled)')) > 0 else False
        itemFinal['cantidad'] = None
        itemFinal['categorias'] = ['cachimba']
        itemFinal['etiquetas'] = contentWrapper.css(
            'div#content-wrapper div.product-description div.rte-content strong::text').getall()
        yield itemFinal

    def removeSpecificWordsFromString(self, string, wordsToDelete):
        edit_string_as_list = string.split()
        final_list = [
            word for word in edit_string_as_list if word not in wordsToDelete]
        final_string = ' '.join(final_list)
        return final_string
