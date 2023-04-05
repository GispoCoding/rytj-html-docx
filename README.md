# rytj-html-docx
Skripti rakentaa tietomallit.ymparisto.fi-sivustosta nipun docx-tiedostoja Wordissä käsiteltäviksi. Samalla tarkistetaan

## Käyttö
0. Oletetaan että alustana on Ubuntu 22.04 ja Bash.
1. Asenna Jekyll seuraten ohjeita: https://idroot.us/install-jekyll-ubuntu-22-04/
2. Kloonaa tämä repo: `git clone --recurse-submodules git@github.com:GispoCoding/rytj-html-docx.git` ja siirry kloonaamaasi hakemistoon.
3. Asenna tarvittavat Python-paketit: `pip install -r requirements.txt`
4. Rakenna saitin HTML-puu hakemistoon `ry-tietomallit/docs/_site`:
```
pushd ry-tietomallit/docs
jekyll build
popd
```
5. Jos on tarpeen, säädä `list.py`-tiedostosta mitä kansioita otetaan mukaan. `find ry-tietomallit/docs/_site -maxdepth 2 -type d` antaa jonkinlaisen lähtökohdan.
6.  Docx-tiedostot voi muodostaa käskemällä `./convert.py`.


