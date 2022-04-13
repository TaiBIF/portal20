FROM solr:8.11.1
WORKDIR /workspace
COPY ./conf-taibif-occur/taibif_occurrence/managed-schema /var/solr/data/taibif_occurrence/conf/
COPY ./conf-taibif-occur/taibif_occurrence/solrconfig.xml /var/solr/data/taibif_occurrence/conf/
COPY ./jts-core-1.18.1.jar /opt/solr-8.11.1/server/solr-webapp/webapp/WEB-INF/lib
# RUN precreate-core
WORKDIR /opt/solr-8.11.1


