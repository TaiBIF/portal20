# TaiBIF Portal website 台灣生物多樣資訊入口網站

TaiBIF (Taiwan Biodiversity Information Facility)

## Installing TaiBIF portal

To install project, follow these steps:

Development:
```
docker-compose -f docker-compose.yml -f docker-compose-develop.yml build
docker-compose -f docker-compose.yml -f docker-compose-develop.yml up -d
```

### Frontend

Install [nvm](https://github.com/nvm-sh/nvm)

```
$ nvm install lts/fermium
$ nvm use lts/fermium
$ npm install
$ npm run dev
```

## make translate (english)

```
$ docker-compose exec web bash
$ python manage.py makemessages -l en
$ python manage.py compilemessages -l en
```
## Installing solr
```bash
# In project repo directory
$ docker-compose exec solr bash

# In solr docker
$ bin/solr create_core -c taibif_occurrence
$ cp /workspace/conf-taibif-occur/taibif_occurrence/managed-schema /var/solr/data/taibif_occurrence/conf/
$ cp /workspace/conf-taibif-occur/taibif_occurrence/solrconfig.xml /var/solr/data/taibif_occurrence/conf/
$ cp /workspace/jts-core-1.18.1.jar /opt/solr-8.9.0/server/solr-webapp/webapp/WEB-INF/lib

# In project repo directory
$ docker-compose restart solr
$ docker-compose exec solr bash
$ post -c taibif_occurrence /workspace/conf-taibif-occur/taibif_occurrence/file.csv
```

<!--
## Contributing to <project_name>

To contribute to <project_name>, follow these steps:

1. Fork this repository.
2. Create a branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create the pull request.

Alternatively see the GitHub documentation on [creating a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

## Contributors

Thanks to the following people who have contributed to this project:

* [@scottydocs](https://github.com/scottydocs) 📖
* [@cainwatson](https://github.com/cainwatson) 🐛
* [@calchuchesta](https://github.com/calchuchesta) 🐛

You might want to consider using something like the [All Contributors](https://github.com/all-contributors/all-contributors) specification and its [emoji key](https://allcontributors.org/docs/en/emoji-key).

## Contact

If you want to contact me you can reach me at <your_email@address.com>.
-->
## License

This project uses the following license: MIT license
