### mysql connection
[Tuto Link](https://gist.github.com/nathanielove/c51f5c4ee1d79045ffa629237e835157)
```sh
sudo apt-get install libmysqlclient-dev
(sudo?) pip install mysqlclient
export DYLD_LIBRARY_PATH=/usr/local/mysql/lib/
```

### BigQuery
[Tuto Link](https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python)
```sh
pip install --upgrade google-cloud-bigquery
export GOOGLE_APPLICATION_CREDENTIALS="KEY_PATH"
```