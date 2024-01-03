keys = [   
            'basesite',
            'pagessite', 'titlesandlinksclass', 'titlesextrainfo', 'titlesgtname', 'titlesgturl', 'firsttitlesfilter', 'secondtitlesfilter',
            'descriptionclass', 'descriptionextrainfo', 'descriptiontxt', 'firstdescriptionfilter', 'seconddescriptionfilter',
            'capsnamesandidsclass', 'capsextrainfo', 'capsgtname', 'capsgturl', 'firstcapfilter', 'secondcapfilter',
            'pagescapclass', 'cappagesextrainfo', 'pgsgturl', 'firstpgscapfilter', 'secondpgscapfilter',
        ]
values = {
            'BR Mangás':      [
                                'https://www.brmangas.net/',
                                '/page/{}/?s', 'item', 'div', 'title', 'href', None, 'a',
                                'None', 'p', 'text', 'content clearfix', None,
                                'row lista_ep', 'li', 'text', 'href', 'capitulos', 'a',
                                None, 'img', 'src', 'col-sm-12 text-center', None,
                              ],
            'Manga Katana':   [
                                'https://mangakatana.com/',
                                '/manga/page/{}', 'title', 'h3', 'text', 'href', 'uk-width-large-7-10', 'a',
                                'summary', 'div', 'text', None, 'p',
                                'chapter', 'div', 'text', 'href', 'chapters', 'a',
                                'None', 'img', 'data-src', None, None,
                              ],
            'Kissmanga':   [
                                'https://kissmanga.org/',
                                '/manga_list?page={}&action=list&q=', 'item_movies_link', 'a', 'text', 'href', 'listing full', None,
                                'summary', 'div', 'text', None, 'p',
                                'None', 'h3', 'text', 'href', 'listing listing8515 full', 'a',
                                'None', 'img', 'src', 'full watch_container', None,
                              ],
            }
