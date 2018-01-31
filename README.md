
# NLS Data Downloader QGIS plugin

This plugin makes possible to download data NLS.fi open data (CC-BY 4.0), such as, topographic data based on municipal regions. It utilizes the NLS Open data file updating service (Atom feed). You need to order a user-specific identification key from NLS to be able to use this plugin: http://www.maanmittauslaitos.fi/en/e-services/open-data-file-download-service/open-data-file-updating-service-interface.

Finnish instructions for use below.

## Asennusohjeet

Lisäosa on vielä varhaista beta-laatua (esim. virhetilanteiden varalta ei ole käsittelyä) mutta sen voi kuitenkin asentaa ja kokeilla QGIS 2.x versioilla. Palaute on tervetullutta: erno@gispo.fi

Pythonin [requests kirjasto](http://docs.python-requests.org/) tulee olla asennettuna. Tarvittaessa sen voi asentaa komentoriviltä komennolla:

```pip install requests```

1. Lisäosa tulee asentaa erillisestä sijainnista ja sen takia QGIS:ssä valitse ensiksi Laajennusosat | Hallitse ja asenna laajennusosia... | Asetukset.
2. Asetuksissa kytke käyttöön "Näytä myös kokeelliset laajennusosat" ja edelleen napauta "Lisää..."-painiketta.
3. Avautuvassa dialogissa anna haluamasi nimi esim. "MML-lisäosa" ja anna URL-kentän arvoksi https://s3.eu-central-1.amazonaws.com/gispoqgisplugins/gispo_qgis_plugins.xml ja napauta OK.
4. Valitse edelleen avoinna olevassa Laajennusosat-ikkunassa Kaikki-välilehti. Hae lisäosa nimellä "NLS Data Downloader" ja napauta "Asenna laajennusosa"-painiketta.
5. Asennuksen jälkeen voit sulkea Laajennusosat-ikkunan.

## Käyttö

Lisäosan ajo onnistuu Laajennusosat-valikosta: Laajennusosat | MML-aineistonlataustyökalu | Lataa MML:n aineistoja. Kun lisäosan ajaa ensimmäisen kerran, avautuu dialogi, jossa täytyy antaa MML:n muunnostietopalvelun tunnisteavain. Muita asetuksia voi halutessaan muokata nyt tai myöhemminkin. Ko. dialogin OK-painikkeen napautuksen jälkeen aukeaa toinen dialogi, jossa voi valita kunnan ja yhden tai useampia aineistoja (maastotietokannasta voi valita haluamansa aineistot, kun taas laserkeilausaineisto ja ortokuvat eivät ole listassa), jotka haetaan ja riippuen valituista asetuksista lisätään tasoina QGIS:iin tai ainoastaan tallenetaan levylle, kun painaa OK-painiketta.

Aineistot haetaan MML:n muutostietopalvelusta, jossa ne on riippuen aineistosta jaoteltu erikokoisten UTM-lehtien mukaan kuten MML:n tiedostopalvelussa. Lisäosa hakee sellaisten lehtien mukaiset aineistot, jotka leikkaavat kunnan geometriaa. Kuntajako perustuu 31.1.2018 MML:n muunnostietopalvelussaan tarjoamaan 1:10 000 -kuntajakoaineistoon.

Mikäli MML:n API-avaimen haluaa jostakin syystä poistaa, sen voi tehdä QGIS:n Asetukset | Valinnat | Edistyneet piirteet | NLSAtomClient | userKey -kohdasta.


