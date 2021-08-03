import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options
import time
import os
import os.path
import json
# from subprocess import Popen, PIPE
import subprocess
import rawes
from json import loads, dumps
import socket
import errno
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

define('port', default=8888, help='Run the server on the given port', type=int)
define('upload_data_dir', default='/mnt/TEST_DATA/', help='Directory to put data', type=str)
define('upload_status_dir', default='/mnt/TEST_DATA/status/', help='Directory to put status files', type=str)
define('upload_logs_dir', default='/mnt/TEST_DATA/logs/', help='Directory to put log files in', type=str)

define('elastic_url', default='https://' + socket.gethostname() + ':9200', help='The url to access elastic search',
       type=str)
define('elastic_CA', default='/etc/ssl/SONYC/CA.pem', help='The CA for connecting to elastic search', type=str)
define('elastic_cert', default='/etc/ssl/SONYC/SONYC_cert.pem', help='The certificate for connecting to elastic search',
       type=str)
define('elastic_key', default='/etc/ssl/SONYC/SONYC_cert.key',
       help='The certificate key for connecting to elastic search', type=str)

es = None


def get_node_name(request):
    client_cert = request.headers.get('X-Client-Cert')
    client_cert = client_cert.replace("-----BEGIN CERTIFICATE-----", "")
    client_cert = client_cert.replace("-----END CERTIFICATE-----", "")
    client_cert = "-----BEGIN CERTIFICATE-----" + client_cert.replace(" ", "\n") + "-----END CERTIFICATE-----"

    cert = x509.load_pem_x509_certificate(client_cert, default_backend())
    CN = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)

    if not len(CN) == 1:
        raise Exception("Client certs should only have one CN");

    return str(CN[0].value) + ".sonyc"


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class UploadHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):

        try:
            fqdn = get_node_name(self.request)
        except Exception as e:
            print 'Could not load nodeid: ' + str(e)
            fqdn = 'unknown'

        self.file1 = self.request.files['file1'][0]
        self.orig_fname = self.file1['filename']
        try:
            if self.orig_fname.endswith('tar.gz'):
                root_path = 'audio'
            elif self.orig_fname.endswith('tar'):
                root_path = 'spl'
            else:
                root_path = 'misc_data'

            if self.orig_fname.startswith('t_'):
                test_path = 'test'
                self.orig_fname = self.orig_fname.replace('t_', '')
            else:
                test_path = ''

            file_name = os.path.splitext(os.path.basename(self.orig_fname))[0].replace('.tar', '').replace('-', '_')
            time_stamp = file_name.split('_')[1]
            float(time_stamp)
            date_string = datetime.fromtimestamp(float(time_stamp)).strftime("%Y-%m-%d")
            output_path = os.path.join(options.upload_data_dir, test_path, root_path, fqdn, date_string)
            mkdir_p(output_path)
        except Exception as e:
            print 'Failed to parse filename timestamp: ' + str(e)
            failed_data_path = '/mount/vida-sonyc/nonparsed'
            mkdir_p(failed_data_path)
            output_path = failed_data_path

        try:
            output_filename = os.path.join(output_path, self.orig_fname)
            output_filename_real = output_filename

            # Make sure file does not already exist, if it does rename including current datetime
            if os.path.exists(output_filename_real):
                output_filename_real = "%s_%s" % (output_filename, datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"))

            with open(output_filename_real, 'w') as f:
                f.write(self.file1['body'])
            self.write('Upload Successful')
        except Exception as e:
            print "Exception in writing data: " + str(e)
            self.write("error writing file on server")


class LogHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        now = datetime.now()
        date_string = now.date().isoformat()
        time_string = now.strftime("%H_%M_%S_%f")

        try:
            fqdn = get_node_name(self.request)
        except Exception as ex:
            print "Error loading nodeid: " + str(ex)
            fqdn = 'unknown'

        self.file1 = self.request.files['file1'][0]
        self.orig_fname = self.file1['filename']

        try:
            output_path = os.path.join(options.upload_logs_dir, fqdn, date_string)
            mkdir_p(output_path)
            output_filename = os.path.join(output_path, self.orig_fname)
            output_filename_real = output_filename
            if os.path.exists(output_filename_real):
                output_filename_real = "%s_%s" % (output_filename, datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f"))

            with open(output_filename_real, 'w') as f:
                f.write(self.file1['body'])
            self.write("Upload Successful")
        except Exception as ex:
            print "Exception in writing logs to file: " + str(ex)
            self.write("error writing file on server")


class PingHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        now = datetime.now()
        date_string = now.date().isoformat()
        time_string = now.strftime("%H_%M_%S_%f")

        try:
            fqdn = get_node_name(self.request)
        except Exception as e:
            print 'Could not load nodeid: ' + str(e)
            fqdn = 'unknown'

        try:
            output_path = os.path.join(options.upload_status_dir, fqdn, date_string)
            mkdir_p(output_path)

            output_filename = os.path.join(output_path, fqdn + "_" + date_string + "_" + time_string + ".json")

            with open(output_filename, 'w') as f:
                f.write(self.request.body)
        except Exception as e:
            print 'Exception in writing status file: ' + str(e)

        self.write('10')

        try:
            status_info = loads(self.request.body)

            if not isinstance(status_info, dict):
                raise Exception("Status update must be a dict")

            status_info['nodeid'] = self.request.headers.get('Id').replace(':', '')
            status_info['ingestion_server'] = socket.gethostname()

            if 'fqdn' in status_info:
                status_fqdn = status_info['fqdn']
                if not status_fqdn == fqdn:
                    print "WARNING: given fqdn %s dose not match certificate CN: %s" % (status_fqdn, fqdn)

            status_info['fqdn'] = fqdn
            es.post('status/status-type', data=status_info)
        except Exception as e:
            print 'Exception in elasticsearch operation: ' + str(e)


class Application(tornado.web.Application):
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        settings = {
            'template_path': os.path.join(base_dir, 'templates'),
            'static_path': os.path.join(base_dir, 'static'),
            'debug': True,
        }

        tornado.web.Application.__init__(self, [
            tornado.web.url(r"/upload", UploadHandler, name="Upload"),
            tornado.web.url(r"/status", PingHandler, name="Ping"),
            tornado.web.url(r"/logs", LogHandler, name="Logs")
        ], **settings)


def main():
    global es
    # Load option files if possible
    options_files = ['SONYC_server.cnf', '/etc/SONYC_server.cnf']
    for file_name in options_files:
        if os.path.isfile(file_name):
            tornado.options.parse_config_file(file_name, final=False)

    es = rawes.Elastic(
        url=options.elastic_url,
        verify=options.elastic_CA,
        cert=(options.elastic_cert, options.elastic_key)
    )

    tornado.options.parse_command_line()
    print 'Server Listening on Port: ', options.port
    Application().listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
