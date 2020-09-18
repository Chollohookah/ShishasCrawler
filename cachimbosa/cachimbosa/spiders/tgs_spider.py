import scrapy
import json
from time import gmtime, strftime


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
                'logo': response.css('img.logo-img-sticky::attr(src)').get(),
                'lastUpdate': strftime("%Y-%m-%d %H:%M:%S", gmtime())
            }
        shishas = response.css('div.product-list-item')
        botonRef = response.css(
            'a.pagination-item-next-link::attr(href)')
        if botonRef is not None and len(botonRef) > 0:
            self.botonSiguiente = botonRef[0].get()
        else:
            self.botonSiguiente = None
        self.loopInfo = {
            'actualIndex': 0,
            'total': len(shishas)
        }
        for shisha in shishas:
            bloqueShishaA = shisha.css("a.woocommerce-LoopProduct-link")[0]
            detalles = bloqueShishaA.css('div.kw-details')[0]
            detallesPrecio = detalles.css('span.price')[0]
            precios = detallesPrecio.css('span.woocommerce-Price-amount::text')
            linkDeProducto = bloqueShishaA.css('::attr(href)')[0].get()

            itemFinal = {
                'linkProducto': linkDeProducto,
                'marca': linkDeProducto.split("/")[-3].upper(),
                'modelo': linkDeProducto.split("/")[-2].upper(),
                'imagen': bloqueShishaA.css('img::attr(src)')[0].get(),
                'titulo': detalles.css('h3.kw-details-title::text')[0].get(),
                'divisa': detalles.css('span.woocommerce-Price-currencySymbol::text')[0].get(),
                'precioOriginal': precios[0].get(),
                'precioRebajado': precios[1].get() if len(precios) > 1 else None
            }

            if linkDeProducto is not None:
                request = scrapy.Request(response.urljoin(
                    linkDeProducto), callback=self.obtenerInfoProducto)
                request.cb_kwargs['itemFinal'] = itemFinal
                yield request

    def obtenerInfoProducto(self, response, itemFinal):
        mainData = response.css('div.main-data')
        estaFueraDeStock = mainData.css('p.out-of-stock')
        cart = mainData.css('form.cart')
        metadatosProducto = mainData.css('div.product_meta')

        if(len(estaFueraDeStock) > 0):
            itemFinal['agotado'] = True
        else:
            itemFinal['agotado'] = False
            itemFinal['cantidad'] = cart.css('input.qty::attr(max)')[0].get()

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

    def escribirJSON(self):
        with open(self.name+'.json', 'w', encoding='utf-8') as f:
            json.dump(self.allShishasParsed, f, ensure_ascii=False, indent=4)
